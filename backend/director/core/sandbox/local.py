"""Local backend for the sandbox executor: runs each call as a subprocess on this machine.

Where the OS supports it, each call is wrapped in Seatbelt (macOS) or
bubblewrap (Linux): it can write only to its run folder and can't read
credentials. Elsewhere it runs unisolated and reports `isolated = False`.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence
from urllib.parse import urlsplit

from director.core.sandbox.base import BaseSandboxExecutor, ExecResult
from director.core.sandbox.egress import (
    DEFAULT_ALLOWED_HOSTS,
    EgressProxy,
    parse_hosts,
)
from director.core.sandbox.isolation import (
    Bubblewrap,
    Policy,
    detect,
    readable_paths,
    secret_paths,
)

logger = logging.getLogger(__name__)

# Host variables a subprocess needs to find tools, on macOS, Linux and Windows.
# Nothing else from the server's environment (LLM keys, DB URLs) is passed through.
PASSTHROUGH_ENV = (
    "PATH",
    "LANG",
    "LC_ALL",
    "USERPROFILE",
    "SYSTEMROOT",
    "PATHEXT",
    "COMSPEC",
    "APPDATA",
    "LOCALAPPDATA",
)
# Home and temp point at the run folder, so nothing lands in (or is read from) the user's own.
RUN_FOLDER_ENV = ("HOME", "TMPDIR", "TEMP", "TMP")
PROXY_ENV = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")

TIMEOUT_EXIT_CODE = 124

# Director's own settings files hold LLM and database keys.
BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
DIRECTOR_ENV_FILES = (os.path.join(BACKEND_DIR, ".env"),)


@dataclass(frozen=True)
class LocalHandle:
    workdir: str
    env: dict
    token: Optional[str] = None


class LocalSandboxExecutor(BaseSandboxExecutor[LocalHandle]):
    """Runs code and commands on this machine, each call in a fresh temp directory.

    SANDBOX_ISOLATION: `auto` (default) uses Seatbelt or bubblewrap when available; `off` never does.
    SANDBOX_NETWORK: `open` (default), or `allowlist` to allow only SANDBOX_ALLOWED_HOSTS.
    """

    def __init__(
        self,
        *,
        python: str = sys.executable,
        timeout: int = 300,
        isolation: Optional[str] = None,
        network: Optional[str] = None,
        allowed_hosts: Optional[List[str]] = None,
    ) -> None:
        # The server's own interpreter, so videodb and the other backend
        # packages are importable from run_code.
        self._python = python
        self._bash = shutil.which("bash")
        self.supports_bash = self._bash is not None
        self._timeout = timeout

        setting = (isolation or os.getenv("SANDBOX_ISOLATION") or "auto").lower()
        if setting not in ("auto", "off"):
            logger.warning("Unknown SANDBOX_ISOLATION %r, using auto", setting)
            setting = "auto"
        self._isolation = detect() if setting == "auto" else None
        self.isolated = self._isolation is not None
        if self.isolated:
            logger.info("Local sandbox isolation: %s", self._isolation.name)
        elif setting == "auto":
            logger.warning(
                "No sandbox isolation on this machine (needs sandbox-exec on macOS or "
                "bwrap on Linux). Code runs as the server's user, so chats default to Ask."
            )

        self._proxy: Optional[EgressProxy] = None
        network = (network or os.getenv("SANDBOX_NETWORK") or "open").lower()
        if network == "allowlist":
            hosts = allowed_hosts or parse_hosts(os.getenv("SANDBOX_ALLOWED_HOSTS", ""))
            if not hosts:
                hosts = list(DEFAULT_ALLOWED_HOSTS) + _base_url_host()
            self._proxy = EgressProxy(
                hosts, unix_socket=isinstance(self._isolation, Bubblewrap)
            )
            logger.info("Sandbox network allowlist: %s", ", ".join(hosts))
            if not self.isolated:
                logger.warning(
                    "SANDBOX_NETWORK=allowlist without isolation only sets proxy variables; "
                    "code that ignores them can still reach any host."
                )
        elif network != "open":
            logger.warning("Unknown SANDBOX_NETWORK %r, using open", network)

    def skills_path(self, local_path: str, skills_dir: str) -> str:
        # Forward slashes work in Python and in Git Bash on Windows.
        return local_path.replace(os.sep, "/")

    def _create_sandbox(self, secrets: Mapping[str, str] | None) -> LocalHandle:
        workdir = os.path.realpath(tempfile.mkdtemp(prefix="director-sandbox-"))
        env = {key: os.environ[key] for key in PASSTHROUGH_ENV if key in os.environ}
        env.update({key: workdir for key in RUN_FOLDER_ENV})
        token = None
        if self._proxy:
            token = self._proxy.open_run()
            url = self._proxy_url()
            scheme, rest = url.split("://", 1)
            env.update({key: f"{scheme}://run:{token}@{rest}" for key in PROXY_ENV})
            env["NO_PROXY"] = env["no_proxy"] = ""
        env.update(secrets or {})
        return LocalHandle(workdir=workdir, env=env, token=token)

    def _proxy_url(self) -> str:
        policy = self._policy()
        if self._isolation:
            return self._isolation.proxy_url(policy)
        return f"http://127.0.0.1:{self._proxy.port}"

    def _policy(self) -> Policy:
        from director.core.skills import get_skills_dir

        return Policy(
            hidden=secret_paths(DIRECTOR_ENV_FILES),
            readable=readable_paths(get_skills_dir()),
            proxy_port=self._proxy.port if self._proxy else None,
            proxy_socket=self._proxy.socket_path if self._proxy else None,
        )

    def _exec(
        self, handle: LocalHandle, argv: Sequence[str], timeout: int | None
    ) -> ExecResult:
        if argv[0] == "python":
            argv = [self._python, *argv[1:]]
        elif argv[0] == "bash" and self._bash:
            argv = [self._bash, *argv[1:]]
        if self._isolation:
            argv = self._isolation.wrap(argv, handle.workdir, self._policy())
        timeout = timeout or self._timeout
        try:
            result = subprocess.run(
                list(argv),
                cwd=handle.workdir,
                env=handle.env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as e:
            stdout = _text(e.stdout)
            stderr = _text(e.stderr) + f"\nTimed out after {timeout}s"
            code = TIMEOUT_EXIT_CODE
        return ExecResult(
            stdout=stdout, stderr=stderr + self._blocked_note(handle), exit_code=code
        )

    def _blocked_note(self, handle: LocalHandle) -> str:
        if not (self._proxy and handle.token):
            return ""
        blocked = self._proxy.close_run(handle.token)
        if not blocked:
            return ""
        return (
            "\nDirector's network allowlist blocked: "
            + ", ".join(blocked)
            + ". Only these hosts are reachable: "
            + ", ".join(self._proxy.allowed)
            + ". Tell the user if the task needs another host."
        )

    def _terminate(self, handle: LocalHandle) -> None:
        if self._proxy and handle.token:
            self._proxy.close_run(handle.token)
        shutil.rmtree(handle.workdir, ignore_errors=True)


def _base_url_host() -> List[str]:
    host = urlsplit(os.getenv("VIDEO_DB_BASE_URL", "")).hostname
    return [host] if host else []


def _text(output) -> str:
    # TimeoutExpired carries bytes even when run() was called with text=True.
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output or ""

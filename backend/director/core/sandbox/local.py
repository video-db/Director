"""Local backend for the sandbox executor: runs each call as a subprocess on this machine."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Mapping, Sequence

from director.core.sandbox.base import BaseSandboxExecutor, ExecResult

# Host variables a subprocess needs to find tools and a home directory, on
# macOS, Linux and Windows. Nothing else from the server's environment (LLM
# keys, DB URLs) is passed through.
PASSTHROUGH_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "USERPROFILE",
    "SYSTEMROOT",
    "PATHEXT",
    "COMSPEC",
    "TEMP",
    "TMP",
    "APPDATA",
    "LOCALAPPDATA",
)

TIMEOUT_EXIT_CODE = 124


@dataclass(frozen=True)
class LocalHandle:
    workdir: str
    env: dict


class LocalSandboxExecutor(BaseSandboxExecutor[LocalHandle]):
    """Runs code and commands on this machine, each call in a fresh temp directory.

    This is not isolation: the process can read and write anything the server's
    user can. Use it for local development; use Modal when the code is untrusted.
    """

    def __init__(self, *, python: str = sys.executable, timeout: int = 300) -> None:
        # The server's own interpreter, so videodb and the other backend
        # packages are importable from run_code.
        self._python = python
        self._bash = shutil.which("bash")
        self.supports_bash = self._bash is not None
        self._timeout = timeout

    def skills_path(self, local_path: str, skills_dir: str) -> str:
        # Forward slashes work in Python and in Git Bash on Windows.
        return local_path.replace(os.sep, "/")

    def _create_sandbox(self, secrets: Mapping[str, str] | None) -> LocalHandle:
        env = {key: os.environ[key] for key in PASSTHROUGH_ENV if key in os.environ}
        env.update(secrets or {})
        return LocalHandle(
            workdir=tempfile.mkdtemp(prefix="director-sandbox-"), env=env
        )

    def _exec(
        self, handle: LocalHandle, argv: Sequence[str], timeout: int | None
    ) -> ExecResult:
        if argv[0] == "python":
            argv = [self._python, *argv[1:]]
        elif argv[0] == "bash" and self._bash:
            argv = [self._bash, *argv[1:]]
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
        except subprocess.TimeoutExpired as e:
            return ExecResult(
                stdout=_text(e.stdout),
                stderr=_text(e.stderr) + f"\nTimed out after {timeout}s",
                exit_code=TIMEOUT_EXIT_CODE,
            )
        return ExecResult(
            stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode
        )

    def _terminate(self, handle: LocalHandle) -> None:
        shutil.rmtree(handle.workdir, ignore_errors=True)


def _text(output) -> str:
    # TimeoutExpired carries bytes even when run() was called with text=True.
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output or ""

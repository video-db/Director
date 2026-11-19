"""OS-level isolation for the local sandbox: Seatbelt on macOS, bubblewrap on Linux.

Both wrap one command so it can write only to its run folder, can't read the
user's credentials or Director's own `.env`, and, with a network allowlist, can
reach the internet only through Director's egress proxy.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

logger = logging.getLogger(__name__)

SANDBOX_EXEC = "/usr/bin/sandbox-exec"

# Credential stores under the user's home that sandboxed code must never read.
SECRET_HOME_PATHS = (
    ".ssh", ".aws", ".azure", ".config", ".gnupg", ".kube", ".docker",
    ".netrc", ".git-credentials", ".npmrc", ".pypirc", ".modal.toml",
    "Library/Keychains", "Library/Cookies", "Library/Application Support",
    "Library/Messages", "Library/Mail",
)  # fmt: skip

# macOS services that hand out keychain items or drive other apps.
BLOCKED_MACH_SERVICES = (
    "com.apple.SecurityServer",
    "com.apple.securityd",
    "com.apple.securityd.xpc",
)

# Inside bubblewrap's private network, the bridge listens here and forwards to the proxy.
BRIDGE_PORT = 3128
BRIDGE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netbridge.py")


@dataclass
class Policy:
    """What one run may touch, beyond its own run folder."""

    # Files and folders that must not be readable (credentials, Director's .env).
    hidden: List[str] = field(default_factory=list)
    # Folders inside home that stay readable, since home itself is hidden.
    readable: List[str] = field(default_factory=list)
    # When set, network goes only through the egress proxy.
    proxy_port: Optional[int] = None
    proxy_socket: Optional[str] = None


class Isolation:
    name = ""

    def wrap(self, argv: Sequence[str], workdir: str, policy: Policy) -> List[str]:
        raise NotImplementedError

    def proxy_url(self, policy: Policy) -> Optional[str]:
        """The proxy address as seen from inside the sandbox."""
        if policy.proxy_port is None:
            return None
        return f"http://127.0.0.1:{policy.proxy_port}"


def _sb(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class Seatbelt(Isolation):
    """macOS: run under `sandbox-exec` with a profile built for this run."""

    name = "seatbelt"

    def profile(self, workdir: str, policy: Policy) -> str:
        workdir = os.path.realpath(workdir)
        lines = [
            "(version 1)",
            "(allow default)",
            "(deny file-write*)",
            "(allow file-write*",
            f"  (subpath {_sb(workdir)})",
            '  (literal "/dev/null") (literal "/dev/zero") (literal "/dev/tty")',
            '  (literal "/dev/stdout") (literal "/dev/stderr") (regex #"^/dev/fd/"))',
        ]
        # Home is unreadable except the folders a run needs. Metadata stays
        # readable so path lookups through home still work.
        home = _home()
        if home:
            lines.append(f"(deny file-read-data (subpath {_sb(home)}))")
            readable = [p for p in _existing(policy.readable) if _inside(p, home)]
            if readable:
                lines.append(
                    "(allow file-read-data "
                    + " ".join(f"(subpath {_sb(p)})" for p in readable)
                    + ")"
                )
        hidden = [os.path.realpath(p) for p in policy.hidden]
        if hidden:
            lines.append(
                "(deny file-read* file-write* "
                + " ".join(f"(subpath {_sb(p)})" for p in hidden)
                + ")"
            )
        lines.append(
            "(deny mach-lookup "
            + " ".join(f"(global-name {_sb(s)})" for s in BLOCKED_MACH_SERVICES)
            + ")"
        )
        lines.append("(deny appleevent-send)")
        if policy.proxy_port is not None:
            # Only the proxy is reachable; DNS goes through it too.
            lines.append("(deny network-outbound)")
            lines.append(
                f'(allow network-outbound (remote ip "localhost:{policy.proxy_port}"))'
            )
        return "\n".join(lines)

    def wrap(self, argv, workdir, policy):
        return [SANDBOX_EXEC, "-p", self.profile(workdir, policy), *argv]


class Bubblewrap(Isolation):
    """Linux: run under `bwrap` with a read-only root, a blank home and a private /tmp."""

    name = "bubblewrap"

    def __init__(self, bwrap: str, mount_proc: bool = True):
        self.bwrap = bwrap
        # Containers often refuse a fresh /proc; the host's stays visible read-only then.
        self.mount_proc = mount_proc

    def proxy_url(self, policy):
        if policy.proxy_socket is None:
            return None
        return f"http://127.0.0.1:{BRIDGE_PORT}"

    def wrap(self, argv, workdir, policy):
        home = _home()
        args = [
            self.bwrap,
            "--die-with-parent",
            "--new-session",
            "--unshare-pid",
            "--ro-bind", "/", "/",
            "--dev", "/dev",
            *(["--proc", "/proc"] if self.mount_proc else []),
            "--tmpfs", "/tmp",
        ]  # fmt: skip
        if home:
            args += ["--tmpfs", home]
            for path in _existing(policy.readable):
                if _inside(path, home):
                    args += ["--ro-bind", path, path]
        args += ["--bind", workdir, workdir]
        for path in _existing(policy.hidden):
            if os.path.isdir(path):
                args += ["--tmpfs", path]
            else:
                args += ["--ro-bind", "/dev/null", path]

        if policy.proxy_socket is not None:
            # No network at all, except a bridge to the proxy's socket.
            sock_dir = os.path.dirname(policy.proxy_socket)
            args += ["--unshare-net", "--ro-bind", sock_dir, sock_dir]
            args += ["--ro-bind", BRIDGE_SCRIPT, BRIDGE_SCRIPT]
            argv = [
                sys.executable, BRIDGE_SCRIPT, policy.proxy_socket, str(BRIDGE_PORT),
                "--", *argv,
            ]  # fmt: skip
        args += ["--chdir", workdir, "--", *argv]
        return args


def _home() -> Optional[str]:
    home = os.path.realpath(os.path.expanduser("~"))
    return home if home != "/" and os.path.isdir(home) else None


def _inside(path: str, root: str) -> bool:
    """Strictly inside root, so re-exposing it never re-exposes root itself."""
    return path.startswith(root.rstrip(os.sep) + os.sep)


def _existing(paths: Sequence[str]) -> List[str]:
    seen, out = set(), []
    for path in paths:
        real = os.path.realpath(path)
        if real not in seen and os.path.exists(real):
            seen.add(real)
            out.append(real)
    return out


def _works(argv: Sequence[str]) -> bool:
    try:
        return subprocess.run(list(argv), capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def detect() -> Optional[Isolation]:
    """The isolation this machine supports, or None. Each is tried once, since a tool can be installed but unusable (e.g. bwrap without user namespaces)."""
    if sys.platform == "darwin" and os.path.exists(SANDBOX_EXEC):
        seatbelt = Seatbelt()
        if _works(seatbelt.wrap(["/usr/bin/true"], "/tmp", Policy())):
            return seatbelt
        logger.warning("sandbox-exec is present but failed a test run")
    elif sys.platform.startswith("linux"):
        bwrap = shutil.which("bwrap")
        if bwrap:
            for mount_proc in (True, False):
                bubblewrap = Bubblewrap(bwrap, mount_proc=mount_proc)
                if _works(bubblewrap.wrap(["true"], "/tmp", Policy())):
                    return bubblewrap
            logger.warning("bwrap is installed but failed a test run (user namespaces may be off)")
    return None


def secret_paths(extra: Sequence[str] = ()) -> List[str]:
    home = os.path.expanduser("~")
    return [os.path.join(home, p) for p in SECRET_HOME_PATHS] + [p for p in extra if p]


def readable_paths(skills_dir: str) -> List[str]:
    """Folders a run needs when the home folder is hidden: the interpreter, tools on PATH and the skills."""
    paths = [sys.prefix, sys.base_prefix, os.path.dirname(os.path.realpath(sys.executable))]
    paths += [p for p in sys.path if "site-packages" in p or "dist-packages" in p]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if entry:
            # A bin folder usually needs its siblings (lib, share) too.
            paths.append(os.path.dirname(entry) if os.path.basename(entry) == "bin" else entry)
    if skills_dir and os.path.isdir(skills_dir):
        paths.append(skills_dir)
        for name in os.listdir(skills_dir):
            paths.append(os.path.realpath(os.path.join(skills_dir, name)))
    return paths

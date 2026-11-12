"""
Provider-agnostic sandboxed code/command execution for agent loops.

Base contract: one fresh, isolated sandbox per call, with guaranteed teardown.
Backends live alongside this module (`local.py`, `modal.py`) and
implement the three primitives at the bottom of `BaseSandboxExecutor`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Mapping, Sequence, TypeVar

# Native sandbox handle type — each backend binds this to its own type.
H = TypeVar("H")


@dataclass(frozen=True)
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class BaseSandboxExecutor(ABC, Generic[H]):
    """
    One fresh, isolated sandbox per call. The lifecycle contract lives here so
    every backend inherits it:

        create -> exec -> capture -> terminate    (teardown guaranteed)

    Holds no per-call mutable state, so `run_code` / `run_bash` are safe to fan
    out across parallel tool calls. To add a backend, subclass and implement the
    three primitives at the bottom — you get output capture, secret threading,
    and guaranteed teardown for free.
    """

    # Whether run_bash works here. Local executors without bash (e.g. Windows
    # without Git Bash) set this to False and bash_executor is not offered.
    supports_bash: bool = True

    def skills_path(self, local_path: str, skills_dir: str) -> str:
        """Where a file under the local skills_dir is visible inside this sandbox."""
        return local_path

    # ---- agent-facing API (shared; don't override) ----

    def run_code(
        self,
        code: str,
        secrets: Mapping[str, str] | None = None,
        timeout: int | None = None,
    ) -> ExecResult:
        # argv is passed element-by-element (no shell), so multi-line `code`
        # in a single arg is safe — no quoting/escaping needed.
        return self._run(["python", "-c", code], secrets, timeout)

    def run_bash(
        self,
        command: str,
        secrets: Mapping[str, str] | None = None,
        timeout: int | None = None,
    ) -> ExecResult:
        return self._run(["bash", "-c", command], secrets, timeout)

    def _run(
        self,
        argv: Sequence[str],
        secrets: Mapping[str, str] | None,
        timeout: int | None,
    ) -> ExecResult:
        handle = self._create_sandbox(secrets)
        try:
            return self._exec(handle, argv, timeout)
        finally:
            # Tear it down no matter what, so an ephemeral sandbox only bills
            # for execution.
            self._terminate(handle)

    # ---- provider primitives (implement these per backend) ----

    @abstractmethod
    def _create_sandbox(self, secrets: Mapping[str, str] | None) -> H:
        """Spin up one ephemeral sandbox; return its native handle."""

    @abstractmethod
    def _exec(self, handle: H, argv: Sequence[str], timeout: int | None) -> ExecResult:
        """Run argv, block until done, return captured stdout/stderr/exit code."""

    @abstractmethod
    def _terminate(self, handle: H) -> None:
        """Tear the sandbox down. Must be safe to call exactly once per handle."""

"""Modal backend for the sandbox executor: each call runs in a fresh remote container."""

from __future__ import annotations

import os
import posixpath
from pathlib import Path
from typing import Mapping, Sequence

try:
    import modal
except ImportError:
    modal = None  # type: ignore[assignment]

from director.core.sandbox.base import BaseSandboxExecutor, ExecResult


def _ensure_modal_ready() -> None:
    """Fail at construction, not inside the first tool call."""
    if modal is None:
        raise ImportError(
            "The 'modal' package is required for SANDBOX_PROVIDER=modal. "
            "Install it with: pip install modal"
        )
    if os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET"):
        return
    if Path("~/.modal.toml").expanduser().exists():
        return
    raise EnvironmentError(
        "No Modal credentials found. Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET "
        "or run `modal setup`."
    )


class ModalSandboxExecutor(BaseSandboxExecutor["modal.Sandbox"]):
    """Runs each call in a fresh Modal container.

    Skills are not copied in. Set MODAL_IMAGE to an image that already has them
    at MODAL_SKILLS_DIR; without it, a slim image with only videodb is used.
    """

    def __init__(
        self,
        *,
        app_name: str = "director-sandbox",
        pip_packages: Sequence[str] = ("videodb",),
        image: "modal.Image | None" = None,
        image_name: str | None = None,
        skills_dir: str | None = None,
        timeout: int = 300,  # hard wall-clock cap per sandbox
        idle_timeout: int | None = 60,  # safety net if a call stalls
        region: str | None = None,
    ) -> None:
        # App and image are resolved once here, so the image build (or cache
        # hit) stays off the per-call path.
        _ensure_modal_ready()
        self._app = modal.App.lookup(app_name, create_if_missing=True)
        image_name = image_name or os.getenv("MODAL_IMAGE")
        if image:
            self._image = image
        elif image_name:
            self._image = modal.Image.from_registry(image_name)
        else:
            self._image = modal.Image.debian_slim().pip_install(*pip_packages)
        self._skills_dir = (
            skills_dir or os.getenv("MODAL_SKILLS_DIR") or "/root/.agents/skills"
        )
        self._timeout = timeout
        self._idle_timeout = idle_timeout
        self._region = region

    def skills_path(self, local_path: str, skills_dir: str) -> str:
        rel = os.path.relpath(local_path, skills_dir).replace(os.sep, "/")
        return posixpath.join(self._skills_dir, rel)

    def _create_sandbox(self, secrets: Mapping[str, str] | None) -> "modal.Sandbox":
        modal_secrets = [modal.Secret.from_dict(dict(secrets))] if secrets else []
        return modal.Sandbox.create(
            app=self._app,
            image=self._image,
            timeout=self._timeout,
            idle_timeout=self._idle_timeout,
            secrets=modal_secrets,
            region=self._region,
        )

    def _exec(
        self, sb: "modal.Sandbox", argv: Sequence[str], timeout: int | None
    ) -> ExecResult:
        p = sb.exec(*argv, timeout=timeout)
        p.wait()  # Modal buffers streams in memory, so wait-then-read is safe.
        return ExecResult(
            stdout=p.stdout.read(),
            stderr=p.stderr.read(),
            exit_code=p.returncode,
        )

    def _terminate(self, sb: "modal.Sandbox") -> None:
        sb.terminate()

import logging
import os
from functools import lru_cache
from typing import Optional

from director.core.sandbox.base import BaseSandboxExecutor, ExecResult
from director.core.sandbox.local import LocalSandboxExecutor
from director.core.sandbox.modal import ModalSandboxExecutor

logger = logging.getLogger(__name__)

# Adding a backend is one entry here plus its subclass.
_PROVIDERS: dict[str, type[BaseSandboxExecutor]] = {
    "local": LocalSandboxExecutor,
    "modal": ModalSandboxExecutor,
}

DEFAULT_SANDBOX_PROVIDER = "local"
DISABLED = "none"


@lru_cache(maxsize=None)
def get_default_sandbox(provider: str = None) -> Optional[BaseSandboxExecutor]:
    """The configured sandbox executor, built once per provider.

    Resolution order: explicit `provider` arg, then `SANDBOX_PROVIDER` env, then
    `DEFAULT_SANDBOX_PROVIDER`. Returns None when the provider is "none" or
    can't be built (unknown name, missing package or credentials), so the code
    and bash agents are left out instead of failing every chat.
    """
    name = (
        provider or os.getenv("SANDBOX_PROVIDER") or DEFAULT_SANDBOX_PROVIDER
    ).lower()
    if name == DISABLED:
        return None
    cls = _PROVIDERS.get(name)
    if cls is None:
        logger.error(
            f"Unknown SANDBOX_PROVIDER {name!r}. Available: {sorted(_PROVIDERS)} or {DISABLED!r}"
        )
        return None
    try:
        sandbox = cls()
    except Exception:
        logger.exception(f"Sandbox provider {name!r} is unavailable")
        return None
    logger.info(f"Using sandbox provider: {name}")
    return sandbox


__all__ = [
    "BaseSandboxExecutor",
    "ExecResult",
    "LocalSandboxExecutor",
    "ModalSandboxExecutor",
    "get_default_sandbox",
    "DEFAULT_SANDBOX_PROVIDER",
]

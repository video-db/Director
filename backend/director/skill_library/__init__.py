"""Skill management for the web UI. This module is the composition root: it picks the adapters."""

from __future__ import annotations

import ipaddress
import os
from functools import lru_cache
from typing import Optional

from director.core.skills import VIDEODB_SKILL, VIDEODB_SKILL_SOURCE, get_skills_dir
from director.skill_library.folder_store import FolderStore
from director.skill_library.ports import SkillError
from director.skill_library.service import SkillLibrary
from director.skill_library.skills_cli import SkillsCliSource

__all__ = ["SkillError", "get_library", "manage_problem"]


@lru_cache(maxsize=1)
def get_library() -> SkillLibrary:
    return SkillLibrary(
        store=lambda: FolderStore(get_skills_dir()),
        source=SkillsCliSource(),
        required=[(VIDEODB_SKILL_SOURCE, VIDEODB_SKILL)],
    )


def manage_problem(sandbox, host: str) -> Optional[str]:
    """Why installing or removing skills from the web page is off, or None when it's allowed."""
    if sandbox is not None and sandbox.skills_location != "host":
        return (
            "This server runs code on Modal, which reads skills from MODAL_IMAGE. "
            "Add skills to that image; installing into a Modal volume isn't built yet."
        )
    if not _loopback(host) and os.getenv("DIRECTOR_SKILLS_MANAGE") != "1":
        return (
            "Installing skills installs code, and this server is reachable from other machines "
            "without logins. Set DIRECTOR_SKILLS_MANAGE=1 to allow it."
        )
    return None


def _loopback(host: str) -> bool:
    if host in ("localhost", ""):
        return host == "localhost"
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False

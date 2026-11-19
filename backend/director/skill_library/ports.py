"""Ports for managing skills: where installed skills live, and where new ones come from.

Installing is always stage-then-publish: a SkillSource puts the skill's files in
a temporary folder, a SkillStore copies them to wherever the sandbox reads skills
(a local folder today, a Modal volume later), and the temporary folder is deleted.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


class SkillError(Exception):
    """A user-facing failure: bad input, a missing tool, or a source that failed."""


@dataclass
class InstalledSkill:
    name: str
    description: str = ""
    # Where it was installed from (e.g. "video-db/skills"), when Director installed it.
    source: Optional[str] = None
    # Set when the folder can't be loaded, e.g. SKILL.md lacks a description.
    problem: Optional[str] = None
    # Installed by a link to another folder; removing it only removes the link.
    linked: bool = False
    installed_at: Optional[int] = None


@dataclass
class CatalogEntry:
    source: str
    skill: str
    installs: str = ""
    url: str = ""


@dataclass
class StagedSkill:
    """A skill's files in a temporary folder, ready to publish."""

    name: str
    path: str
    source: str
    # Scan results reported by the source, shown to the user after install.
    security: dict = field(default_factory=dict)


class SkillStore(ABC):
    """Where the sandbox reads skills from."""

    @abstractmethod
    def list(self) -> List[InstalledSkill]: ...

    @abstractmethod
    def read(self, name: str) -> str:
        """The skill's SKILL.md. Raises SkillError when it isn't installed."""

    @abstractmethod
    def publish(self, staged: StagedSkill) -> InstalledSkill:
        """Add or replace the skill with the staged files."""

    @abstractmethod
    def remove(self, name: str) -> None: ...


class SkillSource(ABC):
    """Where new skills come from."""

    @abstractmethod
    def available(self) -> Optional[str]:
        """None when usable, otherwise why not (shown to the user)."""

    @abstractmethod
    def search(self, query: str) -> List[CatalogEntry]: ...

    @abstractmethod
    def preview(self, source: str, skill: str) -> str:
        """A skill's SKILL.md without installing it."""

    @abstractmethod
    def stage(self, source: str, skill: str, folder: str) -> StagedSkill:
        """Fetch the skill's files into `folder`."""

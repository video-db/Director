"""SkillStore for a skills folder on this machine (`<SKILLS_DIR>/<name>/SKILL.md`)."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import threading
import time
from typing import Dict, List

from director.core.skills import SKILL_FILENAME, check_skill
from director.skill_library.ports import InstalledSkill, SkillError, SkillStore, StagedSkill

# Where Director records what it installed; the skill loader ignores dot files.
MANIFEST = ".director-skills.json"


class FolderStore(SkillStore):
    def __init__(self, folder: str):
        self.folder = folder
        self._lock = threading.Lock()

    def list(self) -> List[InstalledSkill]:
        if not os.path.isdir(self.folder):
            return []
        manifest = self._manifest()
        skills = []
        for entry in sorted(os.listdir(self.folder)):
            path = os.path.join(self.folder, entry)
            if entry.startswith(".") or not os.path.isdir(path):
                continue
            skill, problem = check_skill(path)
            record = manifest.get(entry, {})
            skills.append(
                InstalledSkill(
                    name=entry,
                    description=skill.description if skill else "",
                    source=record.get("source"),
                    problem=problem,
                    linked=os.path.islink(path),
                    installed_at=record.get("installed_at"),
                )
            )
        return skills

    def read(self, name: str) -> str:
        path = os.path.join(self._existing(name), SKILL_FILENAME)
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            raise SkillError(f"{name} has no readable {SKILL_FILENAME}")

    def publish(self, staged: StagedSkill) -> InstalledSkill:
        name = staged.name
        if not _safe_name(name):
            raise SkillError(f"{name!r} isn't a valid skill folder name")
        os.makedirs(self.folder, exist_ok=True)
        dest = os.path.join(self.folder, name)
        tag = secrets.token_hex(4)
        incoming = os.path.join(self.folder, f".{name}.incoming-{tag}")
        old = os.path.join(self.folder, f".{name}.old-{tag}")

        # Copy beside the target, then swap, so a run never sees a half-copied skill.
        shutil.copytree(staged.path, incoming, symlinks=False)
        with self._lock:
            if os.path.islink(dest):
                os.unlink(dest)
            elif os.path.exists(dest):
                os.rename(dest, old)
            os.rename(incoming, dest)
            self._record(name, {"source": staged.source, "installed_at": int(time.time())})
        shutil.rmtree(old, ignore_errors=True)
        return next(s for s in self.list() if s.name == name)

    def remove(self, name: str) -> None:
        path = self._existing(name)
        with self._lock:
            if os.path.islink(path):
                os.unlink(path)  # the linked folder itself is left alone
            else:
                shutil.rmtree(path)
            self._record(name, None)

    def _existing(self, name: str) -> str:
        # Only names actually listed in the folder, so a name can never reach outside it.
        if not _safe_name(name) or name not in _entries(self.folder):
            raise SkillError(f"{name} isn't installed")
        return os.path.join(self.folder, name)

    def _manifest(self) -> Dict[str, dict]:
        try:
            with open(os.path.join(self.folder, MANIFEST), encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _record(self, name: str, record) -> None:
        manifest = self._manifest()
        if record is None:
            manifest.pop(name, None)
        else:
            manifest[name] = record
        path = os.path.join(self.folder, MANIFEST)
        tmp = f"{path}.{secrets.token_hex(4)}"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        os.replace(tmp, path)


def _safe_name(name: str) -> bool:
    return bool(name) and not name.startswith(".") and "/" not in name and "\\" not in name and name not in ("..",)


def _entries(folder: str) -> List[str]:
    try:
        return os.listdir(folder)
    except OSError:
        return []

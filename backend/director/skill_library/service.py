"""Lists, previews, installs, updates and removes skills through a SkillStore and a SkillSource.

Installs and updates clone git repos, so they run as background jobs the page polls.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import asdict
from typing import Callable, Dict, List, Optional

from director.skill_library.ports import SkillError, SkillSource, SkillStore
from director.skill_library.skills_cli import check_skill_name, check_source

logger = logging.getLogger(__name__)

# Finished jobs are kept this long for the page to read their result.
JOB_TTL = 3600


class SkillLibrary:
    def __init__(
        self,
        store: Callable[[], SkillStore],
        source: SkillSource,
        required: List[tuple],
    ):
        # A factory, so a changed SKILLS_DIR applies without a restart.
        self._store = store
        self.source = source
        self.required = required
        self._jobs: Dict[str, dict] = {}
        self._busy: set = set()
        self._lock = threading.Lock()

    @property
    def store(self) -> SkillStore:
        return self._store()

    def overview(self, manage_problem: Optional[str]) -> dict:
        skills = self.store.list()
        installed = {s.name for s in skills if not s.problem}
        return {
            "skills": [asdict(s) for s in skills],
            "missing_required": [
                {"source": src, "skill": name} for src, name in self.required if name not in installed
            ],
            "manage": {"enabled": manage_problem is None, "reason": manage_problem},
        }

    def source_status(self) -> dict:
        problem = self.source.available()
        return {"available": problem is None, "reason": problem}

    def read(self, name: str) -> str:
        return self.store.read(name)

    def search(self, query: str):
        self._need_source()
        return [asdict(e) for e in self.source.search(query)]

    def preview(self, source: str, skill: str) -> str:
        self._need_source()
        return self.source.preview(source, skill)

    def install(self, source: str, skill: str) -> dict:
        source, skill = check_source(source), check_skill_name(skill)
        existing = next((s for s in self.store.list() if s.name == skill), None)
        if existing and not existing.source:
            raise SkillError(
                f"{skill} is already installed outside Director. Remove it first to reinstall it here."
            )
        self._need_source()
        return self._start("install", skill, lambda: self._install(source, skill))

    def update(self, name: str) -> dict:
        skill = next((s for s in self.store.list() if s.name == name), None)
        if skill is None:
            raise SkillError(f"{name} isn't installed")
        if not skill.source:
            raise SkillError(
                f"{name} was installed outside Director, so Director doesn't know where to update it from."
            )
        self._need_source()
        return self._start("update", name, lambda: self._install(skill.source, name))

    def remove(self, name: str) -> None:
        with self._lock:
            if name in self._busy:
                raise SkillError(f"{name} is being installed or updated")
        self.store.remove(name)

    def job(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if job is None:
            raise SkillError("Unknown job")
        return job

    def _install(self, source: str, skill: str) -> dict:
        folder = tempfile.mkdtemp(prefix="director-skill-")
        try:
            staged = self.source.stage(source, skill, folder)
            installed = self.store.publish(staged)
            return {"skill": asdict(installed), "security": staged.security}
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def _start(self, kind: str, name: str, work: Callable[[], dict]) -> dict:
        with self._lock:
            self._expire()
            if name in self._busy:
                raise SkillError(f"{name} is already being installed or updated")
            self._busy.add(name)
            job = {
                "id": uuid.uuid4().hex,
                "kind": kind,
                "skill": name,
                "status": "running",
                "error": None,
                "result": None,
                "started_at": int(time.time()),
                "finished_at": None,
            }
            self._jobs[job["id"]] = job

        def run():
            try:
                job["result"] = work()
                job["status"] = "done"
            except SkillError as e:
                job.update(status="failed", error=str(e))
            except Exception as e:
                logger.exception("Skill %s %s failed", kind, name)
                job.update(status="failed", error=f"Unexpected error: {e}")
            finally:
                job["finished_at"] = int(time.time())
                with self._lock:
                    self._busy.discard(name)

        threading.Thread(target=run, daemon=True).start()
        return job

    def _expire(self):
        cutoff = time.time() - JOB_TTL
        for job_id in [j for j, job in self._jobs.items() if (job["finished_at"] or time.time()) < cutoff]:
            self._jobs.pop(job_id, None)

    def _need_source(self):
        problem = self.source.available()
        if problem:
            raise SkillError(problem)

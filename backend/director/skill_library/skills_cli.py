"""SkillSource backed by the `skills` CLI (https://skills.sh), run as SKILLS_CLI (default `npx --yes skills`).

Staging installs with `-a universal` into a temporary folder, so the CLI never
touches the user's own skill folders or links skills into other agents.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from typing import List, Optional, Sequence

from director.skill_library.ports import CatalogEntry, SkillError, SkillSource, StagedSkill

DEFAULT_COMMAND = "npx --yes skills"
TIMEOUT = 300
MIN_NODE = (22, 20)

SOURCE_RE = re.compile(
    r"^(?:https://github\.com/)?[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*(?:\.git)?/?$"
)
SKILL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\r")
FIND_RE = re.compile(
    r"^(?P<source>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<skill>\S+)\s+(?P<installs>[\d.,]+[KMB]?)\s+installs?"
)
URL_RE = re.compile(r"(https?://\S+)")

# What the CLI needs from the server's environment: tools, npm and git settings. Not LLM or DB keys.
ENV_KEYS = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "TMPDIR", "SHELL", "SSH_AUTH_SOCK",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
            "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMROOT", "PATHEXT", "COMSPEC")  # fmt: skip
ENV_PREFIXES = ("npm_config_", "NPM_CONFIG_", "NODE_", "GIT_")


def check_source(source: str) -> str:
    source = (source or "").strip()
    if not SOURCE_RE.match(source):
        raise SkillError("Use a GitHub repo like owner/repo, or its https://github.com URL")
    return source


def check_skill_name(skill: str) -> str:
    skill = (skill or "").strip()
    if not SKILL_RE.match(skill):
        raise SkillError(f"{skill!r} isn't a valid skill name")
    return skill


class SkillsCliSource(SkillSource):
    def __init__(self, command: Optional[str] = None):
        self.command = shlex.split(command or os.getenv("SKILLS_CLI") or DEFAULT_COMMAND)
        self._ready = False

    def available(self) -> Optional[str]:
        if self._ready:
            return None
        if not shutil.which(self.command[0]):
            return f"`{self.command[0]}` isn't installed. Install Node.js 22.20 or later."
        if os.path.basename(self.command[0]) in ("npx", "npx.cmd"):
            problem = _node_problem()
            if problem:
                return problem
        try:
            self._run(["--version"], timeout=120)
        except SkillError as e:
            return f"The skills CLI doesn't start: {e}"
        self._ready = True
        return None

    def search(self, query: str) -> List[CatalogEntry]:
        query = (query or "").strip()
        if not query or len(query) > 100 or query.startswith("-"):
            raise SkillError("Type a search term")
        return parse_find(self._run(["find", query]))

    def preview(self, source: str, skill: str) -> str:
        out = self._run(["use", f"{check_source(source)}@{check_skill_name(skill)}"])
        start, end = out.find("<SKILL.md>"), out.rfind("</SKILL.md>")
        if start == -1 or end <= start:
            raise SkillError(f"Couldn't find {skill} in {source}")
        return out[start + len("<SKILL.md>") : end].strip()

    def stage(self, source: str, skill: str, folder: str) -> StagedSkill:
        source, skill = check_source(source), check_skill_name(skill)
        out = self._run(
            ["add", source, "--skill", skill, "-a", "universal", "-y", "--json"], cwd=folder
        )
        results = _json_list(out)
        item = next((r for r in results if r.get("name") == skill), results[0] if results else None)
        if not item or item.get("status") != "installed":
            reason = (item or {}).get("error") or f"{skill} wasn't found in {source}"
            raise SkillError(reason)
        path = os.path.realpath(item.get("path") or "")
        if not path.startswith(os.path.realpath(folder) + os.sep) or not os.path.isdir(path):
            raise SkillError("The skills CLI put the skill somewhere unexpected")
        return StagedSkill(
            name=os.path.basename(path), path=path, source=source, security=item.get("security") or {}
        )

    def _run(self, args: Sequence[str], cwd: Optional[str] = None, timeout: int = TIMEOUT) -> str:
        try:
            result = subprocess.run(
                [*self.command, *args],
                cwd=cwd,
                env=_cli_env(),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise SkillError(f"The skills CLI took longer than {timeout}s")
        except OSError as e:
            raise SkillError(f"The skills CLI couldn't run: {e}")
        out = ANSI_RE.sub("", result.stdout)
        if result.returncode != 0 and not out.strip():
            err = ANSI_RE.sub("", result.stderr).strip().splitlines()
            raise SkillError(err[-1] if err else f"The skills CLI exited with {result.returncode}")
        return out


def parse_find(text: str) -> List[CatalogEntry]:
    entries: List[CatalogEntry] = []
    for line in ANSI_RE.sub("", text).splitlines():
        line = line.strip()
        match = FIND_RE.match(line)
        if match:
            entries.append(CatalogEntry(**match.groupdict()))
            continue
        url = URL_RE.search(line)
        if url and entries and not entries[-1].url and line.startswith("└"):
            entries[-1].url = url.group(1)
    return entries


def _json_list(text: str) -> list:
    start = text.find("[")
    try:
        data = json.loads(text[start:]) if start != -1 else []
    except ValueError:
        raise SkillError("The skills CLI returned output Director can't read")
    return data if isinstance(data, list) else []


def _cli_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k in ENV_KEYS or k.startswith(ENV_PREFIXES)}
    env["CI"] = "1"  # no prompts or spinners
    return env


def _node_problem() -> Optional[str]:
    node = shutil.which("node")
    if not node:
        return "Node.js isn't installed. Install Node.js 22.20 or later."
    try:
        version = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10).stdout
        major, minor = (int(x) for x in version.strip().lstrip("v").split(".")[:2])
    except (OSError, ValueError, subprocess.SubprocessError):
        return None  # can't tell; let the CLI try
    if (major, minor) < MIN_NODE:
        return f"The skills CLI needs Node.js 22.20 or later; this machine has {version.strip()}."
    return None

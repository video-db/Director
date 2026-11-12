"""Skill resolver for the Director reasoning engine.

A *skill* is a self-contained, task-specific instruction package. The
reasoning engine is told each skill's name, description, and path on every
turn; it reads the full SKILL.md on demand (e.g. ``cat <location>``) and then
follows its instructions — a progressive disclosure pattern borrowed from the
Agent Skills standard (https://agentskills.io/specification).

Skills live in the user's skills folder (``SKILLS_DIR``, default
``~/.agents/skills``), managed with the ``skills`` CLI. Director never copies
or bundles them. Discovery is intentionally flat:

    <SKILLS_DIR>/<skill-name>/SKILL.md

No recursion, no nested skills, no ignore files. One directory per skill.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_SKILLS_DIR = "~/.agents/skills"

# Director's VideoDB work depends on this skill; it is checked on every turn.
VIDEODB_SKILL = "videodb"
VIDEODB_SKILL_INSTALL = "npx skills add video-db/skills --skill videodb -g -y"

SKILL_FILENAME = "SKILL.md"
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Skill:
    """A discovered skill.

    ``file_path`` and ``base_dir`` are always absolute so the model can use
    them verbatim in commands regardless of the process CWD.
    """

    name: str
    description: str
    file_path: str
    base_dir: str
    disable_model_invocation: bool = False


# --- Tiny YAML frontmatter parser -------------------------------------------
#
# Skills only carry a handful of scalar keys (``name``, ``description``,
# ``disable-model-invocation``). A small hand parser covers the real-world
# surface area without pulling in PyYAML: plain scalars plus block scalars
# (``description: >`` / ``|``), which third-party skills use for long
# descriptions.

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_KEY_VALUE_RE = re.compile(r"^([A-Za-z][\w-]*)\s*:\s*(.*?)\s*$")
_BLOCK_SCALAR_RE = re.compile(r"^([|>])[+-]?$")


def _coerce(value: str):
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        inner = value[1:-1]
        # YAML escaping: single-quoted doubles the quote, double-quoted
        # backslash-escapes.
        if value[0] == "'":
            return inner.replace("''", "'")
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return value


def _parse_frontmatter(text: str) -> Dict[str, object]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: Dict[str, object] = {}
    lines = match.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        kv = _KEY_VALUE_RE.match(line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2)
        block = _BLOCK_SCALAR_RE.match(value)
        if block:
            # Block scalar: the value is the indented lines that follow.
            # ``>`` folds lines with spaces, ``|`` keeps newlines.
            chunk = []
            while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                chunk.append(lines[i].strip())
                i += 1
            joiner = " " if block.group(1) == ">" else "\n"
            data[key] = joiner.join(c for c in chunk if c)
        else:
            data[key] = _coerce(value)
    return data


def _validate(name: str, parent_dir_name: str, description: str) -> List[str]:
    errs: List[str] = []
    if name != parent_dir_name:
        errs.append(f"name {name!r} does not match directory {parent_dir_name!r}")
    if not _NAME_RE.match(name) or len(name) > MAX_NAME_LENGTH:
        errs.append(
            f"name {name!r} is invalid "
            f"(lowercase a-z, 0-9, hyphens, ≤{MAX_NAME_LENGTH} chars, no leading/trailing/double hyphens)"
        )
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errs.append(f"description exceeds {MAX_DESCRIPTION_LENGTH} characters")
    return errs


def _load_one(skill_dir: str) -> Optional[Skill]:
    file_path = os.path.join(skill_dir, SKILL_FILENAME)
    if not os.path.isfile(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        logger.warning("Failed to read skill %s: %s", file_path, e)
        return None

    fm = _parse_frontmatter(raw)
    parent = os.path.basename(skill_dir)
    name = str(fm.get("name") or parent)
    description = str(fm.get("description") or "").strip()

    if not description:
        logger.warning("Skill %s: missing required 'description' — skipping", file_path)
        return None

    for err in _validate(name, parent, description):
        logger.warning("Skill %s: %s", file_path, err)

    return Skill(
        name=name,
        description=description,
        file_path=file_path,
        base_dir=skill_dir,
        disable_model_invocation=bool(fm.get("disable-model-invocation", False)),
    )


def get_skills_dir() -> str:
    """The configured skills folder as an absolute path (``~`` and env vars expanded)."""
    raw = os.getenv("SKILLS_DIR") or DEFAULT_SKILLS_DIR
    return os.path.abspath(os.path.expandvars(os.path.expanduser(raw)))


def load_skills(skills_dir: str = None) -> List[Skill]:
    """Discover skills in ``<skills_dir>/<name>/SKILL.md``.

    Flat discovery: only immediate subdirectories containing ``SKILL.md`` are
    loaded. No recursion. Duplicate names are skipped with a warning (first
    one wins, sorted alphabetically).
    """
    skills_dir = skills_dir or get_skills_dir()
    if not os.path.isdir(skills_dir):
        return []

    skills: List[Skill] = []
    seen: set = set()

    for entry in sorted(os.listdir(skills_dir)):
        if entry.startswith(".") or entry == "__pycache__":
            continue

        candidate = os.path.join(skills_dir, entry)
        # isdir follows symlinks, so skills linked in by the skills CLI load too.
        if not os.path.isdir(candidate):
            continue

        skill = _load_one(candidate)
        if skill is None:
            continue
        if skill.name in seen:
            logger.warning(
                "Skill name collision for %r — skipping %s", skill.name, candidate
            )
            continue

        seen.add(skill.name)
        skills.append(skill)

    return skills


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def format_skills_for_prompt(skills: List[Skill], skills_dir: str, sandbox) -> str:
    """Render the system-prompt block for the skills the model may use.

    Paths go through ``sandbox.skills_path`` so they resolve where the code
    runs. When the VideoDB skill is missing, the block tells the model to have
    the user install it instead of guessing at the SDK.
    """
    lines = []
    if not any(s.name == VIDEODB_SKILL for s in skills):
        _warn_missing_videodb_skill(skills_dir)
        lines += [
            "",
            "## VideoDB skill missing",
            "",
            f"The `{VIDEODB_SKILL}` skill is not installed in `{skills_dir}`, and you need it "
            "to work with VideoDB. Don't guess at the SDK. Tell the user to install it by "
            "running this command (it needs Node.js 22.20 or later), then ask again:",
            "",
            f"`{VIDEODB_SKILL_INSTALL}`",
        ]

    visible = [s for s in skills if not s.disable_model_invocation]
    if visible:
        lines += [
            "",
            "## Skills",
            "",
            "Skills are task-specific instructions. Each `<location>` is the path to a "
            "`SKILL.md` file where `code_executor` and `bash_executor` run.",
            "",
            "**When a task matches a skill's `<description>`:**",
            "1. Read the full SKILL.md first, with `cat <location>` in `bash_executor` or "
            "`print(open('<location>').read())` in `code_executor`.",
            "2. Follow its instructions, then complete the task.",
            "",
            "Relative paths inside a SKILL.md (helper scripts, data files) are rooted at its "
            "`<base_dir>`. Every executor call starts in an empty directory, so run helpers "
            "with `cd <base_dir> && ...` or use the full path.",
            "",
            "<available_skills>",
        ]
        for s in visible:
            location = sandbox.skills_path(s.file_path, skills_dir)
            base_dir = sandbox.skills_path(s.base_dir, skills_dir)
            lines += [
                "  <skill>",
                f"    <name>{_escape_xml(s.name)}</name>",
                f"    <description>{_escape_xml(s.description)}</description>",
                f"    <location>{_escape_xml(location)}</location>",
                f"    <base_dir>{_escape_xml(base_dir)}</base_dir>",
                "  </skill>",
            ]
        lines.append("</available_skills>")
    return "\n".join(lines)


_warned_dirs: set = set()


def _warn_missing_videodb_skill(skills_dir: str) -> None:
    """Log the install command once per folder, so the user sees it in the server log."""
    if skills_dir in _warned_dirs:
        return
    _warned_dirs.add(skills_dir)
    logger.warning(
        "The %s skill is not installed in %s. Install it with: %s",
        VIDEODB_SKILL,
        skills_dir,
        VIDEODB_SKILL_INSTALL,
    )

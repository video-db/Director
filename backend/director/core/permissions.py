"""Decides whether a tool call runs, asks the user, or is blocked.

Order: deny rules, read-only calls, the mode, deletes, "Allow for this chat",
then the judge (Auto mode only). Anything not cleared asks.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional


class Mode(str, Enum):
    ask = "ask"
    read_only = "read_only"
    auto = "auto"
    full = "full"


# Least to most permissive; DIRECTOR_MAX_MODE caps what a client can pick.
MODE_ORDER = [Mode.ask, Mode.read_only, Mode.auto, Mode.full]
DEFAULT_MODE = Mode.auto


def _parse_mode(value) -> Optional[Mode]:
    try:
        return Mode(value)
    except ValueError:
        return None


def max_mode() -> Mode:
    return _parse_mode(os.getenv("DIRECTOR_MAX_MODE")) or Mode.full


def clamp(value) -> Mode:
    """The mode a client asked for, capped by DIRECTOR_MAX_MODE."""
    mode = _parse_mode(value) or DEFAULT_MODE
    ceiling = max_mode()
    if MODE_ORDER.index(mode) > MODE_ORDER.index(ceiling):
        return ceiling
    return mode


@dataclass
class CallInfo:
    """What an agent knows about one call, before it runs."""

    preview: str
    language: str = "text"
    read_only: bool = False
    # Set when a deny rule matches; the call never runs.
    blocked: Optional[str] = None
    # Irreversible (deletes): always asks, and "Allow for this chat" isn't offered.
    destructive: Optional[str] = None
    # Worth a second look; shown to the judge and as the card's reason.
    risks: List[str] = field(default_factory=list)
    # Key for "Allow for this chat"; None when the call can't be keyed safely.
    key: Optional[str] = None


@dataclass
class Decision:
    action: str  # "allow" | "ask" | "deny"
    reason: str = ""
    source: str = ""  # "rule" | "read_only" | "mode" | "chat" | "judge" | "user"
    offer_chat: bool = True


# After this many judge denials in a row, or in total, Auto goes back to asking.
JUDGE_STREAK_LIMIT = 3
JUDGE_TOTAL_LIMIT = 20
JUDGE_PAUSED = (
    "Auto mode blocked several actions in this chat, so Director is asking you instead."
)


@dataclass
class Permissions:
    mode: Mode = DEFAULT_MODE
    allowed: List[str] = field(default_factory=list)
    judge_streak: int = 0
    judge_blocks: int = 0

    @property
    def judge_paused(self) -> bool:
        return (
            self.judge_streak >= JUDGE_STREAK_LIMIT
            or self.judge_blocks >= JUDGE_TOTAL_LIMIT
        )

    def record(self, decision: "Decision") -> None:
        """Track judge denials; an allow from the judge or the user resets the streak."""
        if decision.source == "judge" and decision.action == "deny":
            self.judge_streak += 1
            self.judge_blocks += 1
        elif decision.action == "allow" and decision.source in ("judge", "user"):
            self.judge_streak = 0

    @classmethod
    def from_metadata(cls, metadata: Optional[dict]) -> "Permissions":
        data = (metadata or {}).get("permissions") or {}
        return cls(
            mode=_parse_mode(data.get("mode")) or DEFAULT_MODE,
            allowed=list(data.get("allowed") or []),
            judge_streak=int(data.get("judge_streak") or 0),
            judge_blocks=int(data.get("judge_blocks") or 0),
        )

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "allowed": self.allowed,
            "judge_streak": self.judge_streak,
            "judge_blocks": self.judge_blocks,
        }


Judge = Callable[[str, CallInfo], Decision]


def decide(
    agent_name: str,
    info: CallInfo,
    permissions: Permissions,
    judge: Optional[Judge] = None,
) -> Decision:
    if info.blocked:
        return Decision("deny", info.blocked, source="rule")
    if info.read_only:
        return Decision("allow", source="read_only")

    mode = permissions.mode
    if mode == Mode.full:
        return Decision("allow", source="mode")
    if info.destructive:
        return Decision("ask", info.destructive, offer_chat=False)
    if info.key and info.key in permissions.allowed and not info.risks:
        return Decision("allow", source="chat")
    if mode == Mode.auto and judge is not None:
        if permissions.judge_paused:
            return Decision("ask", JUDGE_PAUSED, offer_chat=info.key is not None)
        return judge(agent_name, info)

    reason = "; ".join(info.risks) or DEFAULT_REASONS.get(
        mode, "Director wants to run this."
    )
    return Decision("ask", reason, offer_chat=info.key is not None)


DEFAULT_REASONS = {
    Mode.ask: "Ask mode: every run needs your approval.",
    Mode.read_only: "Read-only mode: this may change something.",
    Mode.auto: "Director wants to run this.",
}

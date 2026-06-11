"""Topic safety filter for pupil use.

Topics are checked against a teacher-editable blocklist (`safety_blocklist.txt`
in the project root, one term per line, `#` for comments) before any generation
runs. Blocked attempts are appended to `reports/blocked_topics.log` so the
teacher can review what pupils tried to search for.

This is defence-in-depth: the primary-school modes also carry a prompt-level
rule telling the agents to refuse unsuitable topics.
"""

import re
from datetime import datetime
from pathlib import Path

from logic.logger import get_logger

BLOCKLIST_PATH = Path("safety_blocklist.txt")
BLOCKED_LOG_PATH = Path("reports") / "blocked_topics.log"

_log = get_logger("safety")

# Fallback used only if safety_blocklist.txt is missing.
_DEFAULT_BLOCKLIST = [
    "gun", "guns", "knife", "knives", "weapon", "weapons", "bomb", "bombs",
    "kill", "killing", "murder", "war", "terrorist", "terrorism",
    "drugs", "alcohol", "beer", "wine", "vodka", "cigarette", "cigarettes",
    "vape", "vaping", "smoking", "gambling", "casino",
    "sex", "sexy", "naked", "nude", "porn",
    "suicide", "self harm", "self-harm",
    "gore", "torture",
]

_MAX_TOPIC_LEN = 120


def _load_blocklist() -> list[str]:
    if BLOCKLIST_PATH.exists():
        lines = BLOCKLIST_PATH.read_text(encoding="utf-8").splitlines()
        terms = [ln.strip().lower() for ln in lines]
        return [t for t in terms if t and not t.startswith("#")]
    return _DEFAULT_BLOCKLIST


def check_topic(topic: str) -> tuple[bool, str]:
    """Return (ok, reason). reason is "" when ok, otherwise a short code."""
    t = topic.lower().strip()
    if len(t) > _MAX_TOPIC_LEN:
        return False, "topic_too_long"
    for term in _load_blocklist():
        # Whole-word match so e.g. "grape" never trips on "rape".
        if re.search(rf"\b{re.escape(term)}\b", t):
            return False, f"blocked_term:{term}"
    return True, ""


def log_blocked(topic: str, mode: str, reason: str) -> None:
    BLOCKED_LOG_PATH.parent.mkdir(exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with BLOCKED_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\tmode={mode}\treason={reason}\ttopic={topic.strip()}\n")
    _log.warning("topic_blocked  mode=%s  reason=%s  topic=%r", mode, reason, topic.strip())

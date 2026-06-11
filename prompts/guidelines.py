"""Shared Guideline instances — the standing rules reused across modes.

These replace the loose ``_SAFETY_RULE`` / ``_UK_RULE`` string constants that are
currently copy-pasted into ``modes/*.py`` agent backstories (see modes/eyfs.py).
They are plain ``Guideline`` objects, so they carry no CrewAI/Gradio dependency.
"""

from applogics.guideline import Guideline

SAFETY_RULE = Guideline(
    name="child-safety",
    text=(
        "Everything you write will be read aloud to primary school children in the UK. "
        "If the topic is not suitable for young children, do not write about it — "
        "instead write one gentle sentence suggesting they choose a different topic with their teacher. "
    ),
)

UK_RULE = Guideline(
    name="uk-english",
    text=(
        "Always use British English spelling (colour, favourite, metre, -ise endings), "
        "metric units, and examples familiar to children in the UK. "
    ),
)

__all__ = ["SAFETY_RULE", "UK_RULE"]

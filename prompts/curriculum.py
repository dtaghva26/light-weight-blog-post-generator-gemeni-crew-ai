"""Curriculum prompt builders.

``create_curriculum_based_prompt`` is the function named directly in
``applogics/applogics.md``. It replaces the inline ``subject_note`` ternaries
duplicated across every mode (e.g. modes/eyfs.py:35-38, modes/master.py:21-24):
a National-Curriculum / EYFS framing note appended to a task description when a
subject is chosen, or an empty string when it is not.
"""

from __future__ import annotations

from typing import Optional

# Per-framework framing. ``unit`` names how that framework labels its content
# (an EYFS "area of learning" vs. a National Curriculum "programme of study").
EYFS_FRAMEWORK = ("the Early Years Foundation Stage framework", "area of learning")
NATIONAL_CURRICULUM = ("the National Curriculum for England", "programme of study")


def create_curriculum_based_prompt(
    subject: Optional[str],
    framework: tuple[str, str] = NATIONAL_CURRICULUM,
    verb: str = "Frame the facts to support",
) -> str:
    """Return a curriculum-framing note for a task description.

    Args:
        subject: The chosen National Curriculum subject (e.g. "Science"). When
            falsy, returns an empty string so callers can splice it in inline.
        framework: ``(framework_name, unit_label)`` describing the standards
            framework — use ``EYFS_FRAMEWORK`` or ``NATIONAL_CURRICULUM``.
        verb: How to introduce the framing (e.g. "Frame the analysis to support").

    Returns:
        A leading-space-prefixed sentence, or ``""`` when no subject is given.
    """
    if not subject:
        return ""
    framework_name, unit = framework
    return f" {verb} the {subject} {unit} in {framework_name}."


__all__ = ["create_curriculum_based_prompt", "EYFS_FRAMEWORK", "NATIONAL_CURRICULUM"]

"""Guideline — a reusable, named rule injected into agent backstories.

A Guideline captures a single piece of standing guidance (e.g. a child-safety
rule, a British-English requirement, a curriculum-framing note) as plain text so
it can be composed into a Persona's backstory without copy-pasting prose across
modes. Guidelines hold *no* CrewAI / Gradio dependency — they are pure data, so
the domain layer and any future frontend can share them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Guideline:
    """A single named rule.

    Args:
        name: Short identifier for the rule (e.g. ``"safety"``, ``"uk-english"``).
        text: The full guidance prose, ready to drop into a backstory.
    """

    name: str
    text: str

    def render(self) -> str:
        """Return the guidance prose for inclusion in a backstory/prompt."""
        return self.text

    @staticmethod
    def join(*guidelines: "Guideline | Iterable[Guideline]", sep: str = " ") -> str:
        """Compose several Guidelines into one backstory fragment.

        Accepts Guidelines as positional args and/or iterables of Guidelines,
        skipping any ``None`` so callers can splice in optional rules inline.
        """
        flat: list[Guideline] = []
        for item in guidelines:
            if item is None:
                continue
            if isinstance(item, Guideline):
                flat.append(item)
            else:
                flat.extend(g for g in item if g is not None)
        return sep.join(g.render() for g in flat)

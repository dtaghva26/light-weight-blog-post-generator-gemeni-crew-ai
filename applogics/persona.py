"""Persona — the domain concept of an agent (role + goal + guidelines).

A Persona is the engine-agnostic description of *who* performs work: its role,
the goal it pursues, and the Guidelines that shape its voice and constraints. It
deliberately does **not** import CrewAI — translation to a concrete
``crewai.Agent`` happens inside ``applogics.engine.crewai_engine``. This keeps the
execution engine swappable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from applogics.guideline import Guideline


@dataclass
class Persona:
    """An engine-agnostic agent description.

    Args:
        role: The persona's job title (e.g. "Early Years Fact Friend").
        goal: What this persona is trying to achieve.
        guidelines: Ordered Guidelines composed into the backstory.
        llm_config: Optional per-persona LLM overrides (model, timeout, ...).
            When ``None`` the engine supplies its default LLM configuration.
    """

    role: str
    goal: str
    guidelines: list[Guideline] = field(default_factory=list)
    llm_config: Optional[dict[str, Any]] = None

    def backstory(self) -> str:
        """Compose this persona's Guidelines into a single backstory string."""
        return Guideline.join(self.guidelines)

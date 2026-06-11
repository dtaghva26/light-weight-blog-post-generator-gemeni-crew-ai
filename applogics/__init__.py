"""applogics — the engine-agnostic OOP domain layer for the generator app.

Core concepts:
    Guideline  — a reusable named rule injected into a Persona's backstory.
    Persona    — an agent description (role + goal + guidelines), CrewAI-free.
    Task       — a unit of work owned by a Persona (modelled on task_example.py).
    Pipeline   — an ordered crew of Personas + Tasks; ``run(engine)`` executes it.
    Engine     — the abstraction that runs a Pipeline against a concrete backend.

CrewAI lives only in ``applogics.engine.crewai_engine.CrewAIEngine`` (imported
lazily), so the domain classes above never depend on it.
"""

from applogics.guideline import Guideline
from applogics.persona import Persona
from applogics.task import Task
from applogics.pipeline import Pipeline
from applogics.engine.base import Engine

__all__ = ["Guideline", "Persona", "Task", "Pipeline", "Engine"]

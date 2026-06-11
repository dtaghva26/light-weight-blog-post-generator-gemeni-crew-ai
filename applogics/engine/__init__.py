"""Execution engines for the applogics domain layer.

``Engine`` is the abstraction; ``CrewAIEngine`` is the current implementation and
the only module that imports CrewAI.
"""

from applogics.engine.base import Engine
from applogics.engine.crewai_engine import CrewAIEngine

__all__ = ["Engine", "CrewAIEngine"]

"""Engine — the abstraction that executes a Pipeline.

Engines are the *only* place a concrete framework (CrewAI today, something else
tomorrow) is allowed to appear. The domain layer (Guideline / Persona / Task /
Pipeline) talks to this ABC and never imports the backend directly, so the engine
is swappable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from applogics.pipeline import Pipeline
    from applogics.task import Task


class Engine(ABC):
    """Executes domain Pipelines/Tasks against a concrete backend."""

    @abstractmethod
    def run(self, pipeline: "Pipeline") -> dict:
        """Run an entire Pipeline and return a validated result dict.

        The result is a ``StructuredBlogPost``-shaped dict (validated against the
        final task's ``output_schema`` when one is set).
        """

    @abstractmethod
    def run_task(self, task: "Task", context: Optional[dict] = None) -> Any:
        """Run a single Task, optionally seeded with upstream ``context``."""

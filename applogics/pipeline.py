"""Pipeline — the domain concept of a crew (ordered personas + tasks).

A Pipeline bundles the Personas and the sequence of Tasks that make up one
generation run. ``run(engine)`` is the single public entry the future
``logic/crew.py`` will call: it hands the whole Pipeline to an Engine, which
executes the tasks in order and returns a validated ``StructuredBlogPost``-shaped
dict. The Pipeline itself imports no CrewAI — it only describes the work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from applogics.persona import Persona
from applogics.task import Task

if TYPE_CHECKING:
    from applogics.engine.base import Engine


@dataclass
class Pipeline:
    """An ordered set of Personas and the Tasks they run, in sequence.

    Args:
        personas: The agents participating in this run.
        tasks: The tasks to execute, in order. Each later task receives the
            preceding tasks' output as context (sequential process).
    """

    personas: list[Persona]
    tasks: list[Task]

    def run(self, engine: "Engine") -> dict:
        """Execute the full pipeline and return a validated result dict.

        The Engine is responsible for translating this Pipeline into its native
        representation, running it, and validating the output against the final
        task's ``output_schema``. Returns a ``StructuredBlogPost``-shaped dict.
        """
        return engine.run(self)

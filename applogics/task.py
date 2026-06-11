"""Task — the domain unit of work, modelled on ``applogics/task_example.py``.

The original sketch was::

    class Task():
        def __init__(self, name, description):
            ...
        def execute(self):
            print(...)

This keeps that shape (``name`` / ``description`` / ``execute``) while adding the
fields the real pipeline needs — the ``expected_output`` contract, the owning
``Persona``, and an optional Pydantic ``output_schema`` to validate against. A
Task carries no CrewAI dependency; ``execute`` simply routes through an Engine so
the underlying framework stays swappable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Type

from applogics.persona import Persona


@dataclass
class Task:
    """A single unit of work performed by a Persona.

    Args:
        name: Short identifier for the task (e.g. "research", "write").
        description: The instruction prose handed to the persona.
        expected_output: A description of what a correct result looks like.
        persona: The Persona that carries out this task.
        output_schema: Optional Pydantic model the result must validate against
            (e.g. ``StructuredBlogPost`` for the final writing task).
    """

    name: str
    description: str
    expected_output: str
    persona: Persona
    output_schema: Optional[Type[Any]] = None

    def execute(self, engine: "Engine", context: Optional[dict] = None) -> Any:  # noqa: F821
        """Run just this task through the given engine.

        Mirrors the example's ``execute()`` but delegates to the Engine rather
        than printing, so the domain layer never touches the execution backend.
        ``context`` carries any upstream task output the engine should pass in.
        """
        return engine.run_task(self, context=context)

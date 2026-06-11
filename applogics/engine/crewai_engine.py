"""CrewAIEngine — the CrewAI adapter for the domain layer.

This is the **only** module in ``applogics`` that imports ``crewai``. It
translates domain objects into CrewAI primitives
(``Persona``→``Agent``, ``Task``→``Task``, ``Pipeline``→``Crew``), runs
``kickoff()``, and validates the result with the same
``json_dict`` → ``json.loads(result.raw)`` fallback already used in
``logic/crew.py``. Swapping execution backends means writing a sibling Engine
here — the domain classes and prompts stay untouched.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from applogics.engine.base import Engine
from applogics.persona import Persona
from applogics.pipeline import Pipeline
from applogics.task import Task

# Default LLM configuration — mirrors logic/crew.py and every modes/*.py _build().
_DEFAULT_LLM = {
    "model": "gemini/gemini-3.5-flash",
    "timeout": 60,
    "max_retries": 2,
}


class CrewAIEngine(Engine):
    """Runs domain Pipelines on CrewAI + Google Gemini."""

    def __init__(self, llm_config: Optional[dict[str, Any]] = None):
        # Per-engine overrides; per-Persona overrides win at build time.
        self._llm_config = {**_DEFAULT_LLM, **(llm_config or {})}

    # ── Translation ────────────────────────────────────────────────────────────

    def _make_llm(self, overrides: Optional[dict[str, Any]] = None):
        from crewai import LLM

        cfg = {**self._llm_config, **(overrides or {})}
        api_key = cfg.pop("api_key", None) or os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY")
        return LLM(api_key=api_key, **cfg)

    def _to_agent(self, persona: Persona):
        from crewai import Agent

        return Agent(
            role=persona.role,
            goal=persona.goal,
            backstory=persona.backstory(),
            verbose=True,
            llm=self._make_llm(persona.llm_config),
        )

    def _to_task(self, task: Task, agent):
        from crewai import Task as CrewTask

        kwargs = dict(
            description=task.description,
            expected_output=task.expected_output,
            agent=agent,
        )
        if task.output_schema is not None:
            kwargs["output_json"] = task.output_schema
        return CrewTask(**kwargs)

    # ── Execution ──────────────────────────────────────────────────────────────

    def run(self, pipeline: Pipeline) -> dict:
        from crewai import Crew, Process

        agents = {id(p): self._to_agent(p) for p in pipeline.personas}
        crew_tasks = [self._to_task(t, agents[id(t.persona)]) for t in pipeline.tasks]
        crew = Crew(
            agents=list(agents.values()),
            tasks=crew_tasks,
            process=Process.sequential,
        )
        result = crew.kickoff()
        return self._validate(result, pipeline.tasks[-1] if pipeline.tasks else None)

    def run_task(self, task: Task, context: Optional[dict] = None) -> Any:
        """Run a single task as a one-step pipeline (no upstream wiring yet)."""
        return self.run(Pipeline(personas=[task.persona], tasks=[task]))

    # ── Validation ─────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(result, final_task: Optional[Task]) -> dict:
        """Extract and validate the crew result against the task's schema.

        Reuses the exact extraction order from logic/crew.py: prefer
        ``result.json_dict``, fall back to ``json.loads(result.raw)``.
        """
        blog_data = getattr(result, "json_dict", None)
        if blog_data is None:
            blog_data = json.loads(getattr(result, "raw", result))
        if final_task is not None and final_task.output_schema is not None:
            final_task.output_schema(**blog_data)  # raises ValidationError on bad shape
        return blog_data

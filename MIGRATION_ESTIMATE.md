# Migration Estimate: Mess to OOP Platform (MVC)

This document provides a detailed story point estimate and execution plan for migrating the current codebase to an organized, OOP-based platform with clear separation of concerns (MVC).

## Story Point Definition
- **1 Story Point**: A task that can be fully understood and solved by an AI (e.g., Claude 3.5 Haiku/Flash) in **one prompt** for analysis and **one prompt** for execution/code change.
- **Scale**: Fibonacci (1, 2, 3, 5, 8, 13).

---

## Epic 1: Model & Domain Refactoring (The "M" in MVC)
*Focus: Establishing the core business logic and data structures in `applogics/`.*

### Story M1: Relocate and Refine Core Models
- **Description**: Move `logic/models.py` to `applogics/models.py`. Update all imports. Ensure `StructuredBlogPost` and `ArticleSection` are ready for the new pipeline.
- **AI Instructions**:
  - `mv logic/models.py applogics/models.py`
  - Update imports in `logic/crew.py`, `logic/renderer.py`, and `modes/*.py`.
- **Estimate**: 1 SP

### Story M2: Define Domain Pipelines for EYFS
- **Description**: Convert the functional `_build` in `modes/eyfs.py` into an OOP `Pipeline` and `Persona` structure in `applogics/pipelines/eyfs.py`.
- **AI Instructions**: Use `applogics/persona.py`, `applogics/task.py`, and `applogics/pipeline.py` to define the "Fact Friend" and "Storyteller" personas.
- **Estimate**: 2 SP

### Story M3: Define Domain Pipelines for KS1/LKS2/UKS2
- **Description**: Similar to M2, migrate the primary school age-group modes to the new domain structure.
- **Estimate**: 5 SP (grouped for efficiency)

### Story M4: Define Domain Pipelines for Master Mode
- **Description**: Migrate the complex "Master Thinker" mode to the new domain structure.
- **Estimate**: 2 SP

### Story M5: Global Pipeline Registry
- **Description**: Migrate `modes/registry.py` to `applogics/registry.py`. It should now manage `Pipeline` objects instead of `ModeDefinition` dataclasses.
- **Estimate**: 2 SP

---

## Epic 2: Prompt Engineering Package
*Focus: Moving all natural language logic out of Python code and into the `prompts/` package.*

### Story P1: Extract Persona Guidelines
- **Description**: Extract all `_SAFETY_RULE`, `_UK_RULE`, and agent-specific backstories from `modes/*.py` into `prompts/guidelines.py` and `prompts/backstories.py`.
- **Estimate**: 3 SP

### Story P2: Standardize Curriculum Prompt Builders
- **Description**: Use and expand `prompts/curriculum.py` to handle all curriculum-specific notes currently scattered in `modes/*.py`.
- **Estimate**: 2 SP

---

## Epic 3: Engine & Execution Layer
*Focus: Enhancing the CrewAIEngine to handle the specific needs of the application (Streaming).*

### Story E1: Implement Streaming Support in CrewAIEngine
- **Description**: The current `logic/crew.py` handles streaming via a `QueueWriter`. Implement this logic inside `CrewAIEngine.run_streaming` so the UI can still show logs.
- **AI Instructions**: Modify `applogics/engine/crewai_engine.py` to accept a callback or return a generator for log lines.
- **Estimate**: 5 SP

### Story E2: Engine Configuration & Factory
- **Description**: Implement a factory to initialize the `CrewAIEngine` with proper API keys and default LLM settings, replacing the redundant `LLM(...)` calls in every mode file.
- **Estimate**: 2 SP

---

## Epic 4: View & Templates (The "V" in MVC)
*Focus: Moving from hardcoded Python HTML strings to Jinja2 templates in `frontend/designs/`.*

### Story V1: Base Report Template
- **Description**: Create `frontend/designs/base_report.html.j2` using Jinja2. This should contain the core HTML structure and CSS variables for light/dark mode.
- **Estimate**: 2 SP

### Story V2: Mode-Specific Style Overlays
- **Description**: Create sub-templates or CSS blocks for each mode (EYFS, Master, etc.) that the base template can include.
- **Estimate**: 3 SP

### Story V3: Template Renderer Implementation
- **Description**: Create `applogics/view/renderer.py` which uses `jinja2.Environment` to render the `StructuredBlogPost` into HTML. Replace `logic/renderer.py`.
- **Estimate**: 3 SP

---

## Epic 5: Controller & Integration (The "C" in MVC)
*Focus: Wiring the new Model and View together in the Gradio Handlers.*

### Story C1: Refactor Handlers to MVC
- **Description**: Update `frontend/gradio/handlers.py` to use `applogics.registry` to get a `Pipeline`, and `CrewAIEngine` to run it.
- **Estimate**: 5 SP

### Story C2: Cleanup and Final Decoupling
- **Description**: Delete the legacy `modes/` directory and `logic/renderer.py` once migration is verified.
- **Estimate**: 1 SP

---

## Total Estimate: 38 Story Points

### Recommended Execution Order for AI:
1. **P1, P2** (Extract Prompts)
2. **M1, M5** (Setup Core Domain & Registry)
3. **M2, M3, M4** (Migrate Logic to Pipelines)
4. **V1, V2, V3** (Setup Jinja2 View Layer)
5. **E1, E2** (Implement Execution Engine)
6. **C1, C2** (Final Integration)

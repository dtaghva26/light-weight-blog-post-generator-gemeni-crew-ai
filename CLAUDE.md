# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install dependencies
pip install crewai google-genai pydantic python-dotenv nest_asyncio gradio

# Run the Gradio web UI
python app.py
# Opens at http://127.0.0.1:7860
```

Requires a `.env` file in the project root:
```
GEMINI_API_KEY=your_google_gemini_api_key_here
```
The code also accepts `Gemeni_API_KEY` (typo fallback in `logic/crew.py`).

There are no tests and no linter configuration in this project.

## File Map

```
app.py                          # Entry point — imports and launches frontend/gradio/ui.py demo
agents.py                       # Legacy re-export shim: run_crew_streaming, create_html
utils.py                        # Legacy re-export shim: save_report, list_reports, load_report_*, blog_to_markdown
logic/models.py                 # Pydantic schema: StructuredBlogPost, ArticleSection
logic/crew.py                   # 4 crew builder functions + run_crew_streaming() generator
logic/renderer.py               # create_html(), blog_to_markdown()
logic/reports.py                # save_report(), list_reports(), load_report_json/html()
frontend/gradio/ui.py           # Gradio Blocks layout + all event wiring
frontend/gradio/handlers.py     # generate(), load_history(), rerender_dark(), update_ui()
frontend/gradio/themes.py       # Theme dicts (title/labels/placeholders) for each mode
```

`agents.py` and `utils.py` in the root are legacy re-export shims kept for backwards compatibility with `hello.ipynb`. Do not add logic there.

## Architecture

The app is a two-agent CrewAI pipeline with a Gradio frontend. The two agents always run sequentially: Researcher → Writer. The Writer receives the Researcher's output before starting. Pydantic validates the LLM's JSON output against `StructuredBlogPost` before any rendering occurs.

**LLM**: All four crews use `gemini/gemini-3.5-flash` via CrewAI's `LLM` wrapper, keyed from `GEMINI_API_KEY` (or `Gemeni_API_KEY` fallback).

## Four Critical Thinking Modes

The UI radio ("Critical Thinking Stage") maps to an internal `crew_type` string and a distinct crew builder:

| UI Label | crew_type | Crew builder | Epistemological stance |
|---|---|---|---|
| Absolutist | `absolutist` | `_build_absolutist_crew` | Facts as absolute truth, ages 4–10 |
| Multiplist | `multiplist` | `_build_multiplist_crew` | All opinions equally valid, ages 11–17 |
| Evaluativist | `evaluativist` | `_build_evaluativist_crew` | Evidence-based reasoning, adults |
| Master Thinker | `master` | `_build_master_crew` | Self-reflective, surfaces blind spots |

The mapping lives in `handlers.py:_MODE_MAP` (UI label → `crew_type` string). The `crew_type` is stored as `audience` in each report's `.json` so re-renders use the correct CSS theme.

## Pydantic Models (`logic/models.py`)

```python
class ArticleSection(BaseModel):
    heading: str
    body: str
    cognitive_load: Optional[float]   # 0.0–1.0; low=kids, high=master
    emotional_valence: Optional[str]  # one of: uplifting, neutral, cautionary, reflective, mixed
    review_prompts: Optional[List[str]]  # 2–3 spaced-repetition questions

class StructuredBlogPost(BaseModel):
    title: str
    author: str
    sections: List[ArticleSection]
    generated_at: Optional[str]   # ISO 8601, injected by reports.py (not the LLM)
```

## Key Patterns

**Streaming generation** (`logic/crew.py:run_crew_streaming()`): Runs the crew in a daemon thread. Captures stdout via a `QueueWriter` (subclass of `io.TextIOBase`) and yields items from a `queue.Queue`. Yields raw log strings during the run, then a `("RESULT", dict)` tuple on success or `("ERROR", str)` on failure.

**`generate()` in `handlers.py`**: Consumes `run_crew_streaming()`. Strips ANSI codes from log lines via `_ANSI_RE`. On success: calls `create_html()` → `save_report()` → writes `.md` file separately → yields `(log_str, preview_html, html_path, md_path, gr.update(choices=...))`. On error: yields `(log_str_with_error, None, None, None, gr.update())`. Mode-specific messages live in `_EMPTY_MSG`, `_ERROR_MSG`, `_DONE_MSG` dicts keyed by `crew_type`.

**Report persistence** (`logic/reports.py`): `save_report()` writes two files — `.html` and `.json` — under `reports/` with a `YYYYMMDD_HHMMSS_<slug>` prefix. The `.md` file is written separately by `handlers.py:generate()`. The JSON is the source of truth; HTML and Markdown are always re-renderable from it. `audience` (the `crew_type` string) and `generated_at` (ISO timestamp) are injected into the JSON by `save_report()`.

**LLM output validation** (`logic/crew.py`): The Writer task uses `output_json=StructuredBlogPost`. After `crew.kickoff()`, `result.json_dict` is tried first, falling back to `json.loads(result.raw)`. Pydantic validates — a `ValidationError` surfaces as `("ERROR", str)` in the queue.

**HTML rendering** (`logic/renderer.py:create_html()`): Renders cognitive load bars, emotional valence badges, and a 3-panel spaced repetition review schedule (Day 1, Day 7, Day 21 from `generated_at`). Per-audience CSS is injected:
- `absolutist`/`kids` → Poppins font, pink/colorful headers
- `multiplist` → Inter font, blue headers
- `master` → Crimson Text serif, gold accents
- `evaluativist` (default) → system fonts, neutral palette
Dark mode is a separate CSS variable layer toggled by the `dark` bool parameter.

**HTML preview** (`handlers.py:_wrap_preview()`): Wraps the rendered HTML string in an `<iframe srcdoc="...">` so Gradio can display it safely (sandboxed with `allow-same-origin`).

**UI theme switching** (`frontend/gradio/handlers.py:update_ui()`): Returns a flat dict of 15 keys covering label strings and a `<style>` block. The `_build_update_ui_outputs` closure in `ui.py` maps that dict to Gradio component updates for all 15 components simultaneously via `audience_selector.change`.

**History loading** (`handlers.py:load_history()`): Reads the `.json` source of truth, re-renders HTML with the stored `audience` CSS theme, regenerates the `.md`, and returns `(preview_html, html_path, md_path)`.

**Dark mode toggle** (`handlers.py:rerender_dark()`): Re-reads the `.json` for the currently displayed report and re-renders with the new `dark` value. No-ops if no report is loaded.

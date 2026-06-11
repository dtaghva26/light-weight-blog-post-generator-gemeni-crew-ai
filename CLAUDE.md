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
TEACHER_PIN=optional_pin   # defaults to 0000 (handlers.py:_teacher_pin)
```
The code also accepts `Gemeni_API_KEY` (typo fallback in `logic/crew.py`).

There are no tests and no linter configuration in this project.

## File Map

```
app.py                          # Entry point — imports and launches frontend/gradio/ui.py demo
agents.py                       # Legacy re-export shim: run_crew_streaming, create_html
utils.py                        # Legacy re-export shim: save_report, list_reports, load_report_*, blog_to_markdown
logic/models.py                 # Pydantic schema: StructuredBlogPost, ArticleSection
logic/crew.py                   # run_crew_streaming() generator (subject kwarg threads to build_crew)
logic/renderer.py               # create_html(), create_worksheet_html(), blog_to_markdown()
logic/reports.py                # save_report(), list_reports() (skips *_worksheet.html), load_report_json/html()
logic/safety.py                 # check_topic() against safety_blocklist.txt, log_blocked()
modes/                          # One plugin file per mode; eyfs/ks1/lks2/uks2 are the UK year-group modes
frontend/gradio/ui.py           # Gradio Blocks layout + all event wiring; exports APP_THEME/APP_CSS for launch()
frontend/gradio/handlers.py     # generate(), load_history(), rerender_view(), update_ui(), on_class_setup(), unlock_teacher()
frontend/gradio/themes.py       # Theme dicts (title/labels/placeholders) for each mode
safety_blocklist.txt            # Teacher-editable topic blocklist (whole-word, case-insensitive)
```

`agents.py` and `utils.py` in the root are legacy re-export shims kept for backwards compatibility with `hello.ipynb`. Do not add logic there.

## Architecture

The app is a two-agent CrewAI pipeline with a Gradio frontend. The two agents always run sequentially: Researcher → Writer. The Writer receives the Researcher's output before starting. Pydantic validates the LLM's JSON output against `StructuredBlogPost` before any rendering occurs.

**LLM**: All four crews use `gemini/gemini-3.5-flash` via CrewAI's `LLM` wrapper, keyed from `GEMINI_API_KEY` (or `Gemeni_API_KEY` fallback).

## Modes (Classroom Edition)

The UI radio ("Who is this for?") maps display names to `ModeDefinition`s via `modes/registry.py:by_display_name`. The `crew_type` is stored as `audience` in each report's `.json` so re-renders use the correct CSS theme.

| Mode | crew_type | Notes |
|---|---|---|
| Reception (ages 4–5) | `eyfs` | ≤6-word sentences, words capped at 60/section |
| Years 1–2 (ages 5–7) | `ks1` | ≤8-word sentences, capped at 100/section |
| Years 3–4 (ages 7–9) | `lks2` | Wow fact + why, capped at 180/section |
| Years 5–6 (ages 9–11) | `uks2` | Non-fiction features, capped at 250/section |
| Kids Mode | `kids_mode` | Original magical-tone mode |
| Absolutist | `absolutist` | Facts as absolute truth |
| Multiplist | `multiplist` | `teacher_only=True` |
| Evaluativist | `evaluativist` | `teacher_only=True` |
| Master Thinker | `master` | `teacher_only=True` |

**Pupil vs teacher mode**: the app starts pupil-locked — the radio shows only non-`teacher_only` modes; the settings accordion and history column are `visible=False`. `handlers.py:unlock_teacher()` (PIN from `TEACHER_PIN`, default 0000) reveals them. The first screen is a year-group class setup (`on_class_setup`, `YEAR_GROUPS` dict) — the old age gate was removed so no pupil ages are collected.

**Topic safety**: `generate()` calls `logic/safety.py:check_topic()` before running the crew; blocked topics yield a child-friendly message and are appended to `reports/blocked_topics.log`. The four year-group modes also embed a prompt-level refusal rule and British English requirements in agent backstories.

**Curriculum subject**: a `subject` dropdown ("Any topic" → `None`) threads `generate()` → `run_crew_streaming()` → `build_crew(topic, num_sections, words_per_section, subject=...)`. Every mode's `_build` must accept the `subject` kwarg.

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

**Report persistence** (`logic/reports.py`): `save_report()` writes two files — `.html` and `.json` — under `reports/` with a `YYYYMMDD_HHMMSS_<slug>` prefix. The `.md` and `_worksheet.html` files are written separately by `handlers.py:generate()`. The JSON is the source of truth; HTML, Markdown, and the worksheet are always re-renderable from it. `audience` (the `crew_type` string) and `generated_at` (ISO timestamp) are injected into the JSON by `save_report()`. `list_reports()` skips `*_worksheet.html` so worksheets never appear in history.

**LLM output validation** (`logic/crew.py`): The Writer task uses `output_json=StructuredBlogPost`. After `crew.kickoff()`, `result.json_dict` is tried first, falling back to `json.loads(result.raw)`. Pydantic validates — a `ValidationError` surfaces as `("ERROR", str)` in the queue.

**HTML rendering** (`logic/renderer.py:create_html()`): Renders cognitive load bars, emotional valence badges, and a 3-panel spaced repetition review schedule (Day 1, Day 7, Day 21 from `generated_at`). Per-audience CSS comes from each mode's `report_css`. Dark mode is a CSS variable layer toggled by the `dark` bool. Three accessibility bools (`easy_font`, `large_print`, `reduce_motion`) append an override layer after all mode CSS (`_accessibility_css()`), and `_PRINT_CSS` (`@media print`) is always included. `create_worksheet_html()` builds the A4 comprehension worksheet from each section's `review_prompts`.

**HTML preview** (`handlers.py:_wrap_preview()`): Wraps the rendered HTML string in an `<iframe srcdoc="...">` so Gradio can display it safely (sandboxed with `allow-same-origin`).

**UI theme switching** (`frontend/gradio/handlers.py:update_ui()`): Returns a flat dict of 16 keys covering label strings and a `<style>` block. The `_build_update_ui_outputs` closure in `ui.py` maps that dict to Gradio component updates for all 16 components simultaneously via `audience_selector.change`.

**History loading** (`handlers.py:load_history()`): Reads the `.json` source of truth, re-renders HTML with the stored `audience` CSS theme and current view toggles, regenerates the `.md` and worksheet, and returns `(preview_html, html_path, md_path, ws_path)`.

**View toggles** (`handlers.py:rerender_view()`): Re-reads the `.json` for the currently displayed report and re-renders with the current dark/easy-font/large-print/reduce-motion values. No-ops if no report is loaded. `on_motion_toggle()` additionally injects a `<style>` that kills animations in the live Gradio UI.

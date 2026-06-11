# Plan: Mode Registry / Plugin Architecture

## Context

Adding a new crew mode currently requires **8+ changes across 5 files** — crew builder in `logic/crew.py`, theme dict in `themes.py`, 6 separate dicts/blocks in `handlers.py`, radio list in `ui.py`, and optionally a CSS block in `renderer.py`. This scatter makes the app fragile to extend and error-prone: it's easy to forget one entry and get a silent runtime bug.

The goal is to make **adding a mode = dropping one new file**. No existing files change.

---

## Approach: Self-Contained Mode Modules + Auto-Discovery Registry

Each mode becomes a single Python file in a new `modes/` package. A `ModeDefinition` dataclass holds *everything* about a mode. A registry auto-discovers all mode files at startup using `pkgutil.iter_modules`. Every consuming file becomes a thin registry lookup.

---

## New Files to Create

### `modes/__init__.py`
Empty package marker (or re-exports from `registry.py`).

### `modes/base.py` — `ModeDefinition` dataclass
```python
@dataclass
class ModeDefinition:
    crew_type: str           # internal key e.g. "evaluativist"
    display_name: str        # Gradio radio label e.g. "Evaluativist"
    min_age: int             # age gate lower bound (age_to_mode uses sorted lookup)
    order: int               # radio widget sort position
    build_crew: Callable     # (topic, num_sections, words_per_section) -> Crew
    # theme strings (replaces themes.py dicts)
    title: str
    topic_label: str
    topic_placeholder: str
    gen_btn: str
    log_label: str
    log_placeholder: str
    preview_label: str
    # UI labels (replaces inline dicts in update_ui())
    settings_label: str
    num_sections_label: str
    words_per_section_label: str
    dark_toggle_label: str
    history_title: str
    history_dd_label: str
    load_btn_label: str
    dl_html_label: str
    dl_md_label: str
    # CSS (replaces elif blocks in handlers.py + renderer.py)
    gradio_css: str          # injected into Gradio live DOM
    report_css: str          # injected into standalone HTML report
    # messages (replaces _EMPTY_MSG, _ERROR_MSG, _DONE_MSG dicts)
    empty_msg: str
    error_msg: Callable[[str], str]
    done_msg: str
```

### `modes/registry.py` — auto-discovery registry
```python
def _load_all():   # pkgutil.iter_modules, imports every modes/*.py except base+registry
def register(mode: ModeDefinition): ...
def get(crew_type: str) -> ModeDefinition: ...
def all_modes() -> List[ModeDefinition]: ...        # sorted by order
def by_display_name(name: str) -> ModeDefinition: ...
```

### `modes/kids_mode.py`, `absolutist.py`, `multiplist.py`, `evaluativist.py`, `master.py`
One file per existing mode. Each file:
1. Defines `_build(topic, num_sections, words_per_section) -> Crew` — **verbatim copy** of the matching `_build_*_crew()` from `crew.py`
2. Calls `register(ModeDefinition(...))` with all strings from `themes.py`, `handlers.py` dicts, and `renderer.py` CSS blocks

---

## Files to Modify

### `logic/crew.py`
- **Delete** the 5 `_build_*_crew()` functions (moved to `modes/*.py`)
- **Replace** the 10-line `if/elif` dispatch in `_run()` with:
  ```python
  from modes.registry import get as get_mode
  crew = get_mode(crew_type).build_crew(topic, num_sections, words_per_section)
  ```

### `frontend/gradio/handlers.py`
- **Delete** `_MODE_MAP`, `_EMPTY_MSG`, `_ERROR_MSG`, `_DONE_MSG` (~30 lines)
- **Simplify** `age_to_mode()`: replace elif chain with `sorted(all_modes(), key=lambda m: m.min_age)` lookup
- **Simplify** `update_ui()`: replace ~200 lines of CSS/label dicts with single `by_display_name(audience)` lookup
- **Simplify** `generate()`: replace `_MODE_MAP[audience]` + message dicts with `mode = by_display_name(audience)`

### `frontend/gradio/ui.py`
- Replace hardcoded radio choices list + `ADULT_THEME` default references with:
  ```python
  from modes.registry import all_modes
  _modes = all_modes()
  _mode_names = [m.display_name for m in _modes]
  _default = next(m for m in _modes if m.crew_type == "evaluativist")
  ```

### `logic/renderer.py`
- Replace the 120-line `if/elif audience` CSS block with:
  ```python
  from modes.registry import get as get_mode
  extra_css = get_mode(audience).report_css
  ```

### `frontend/gradio/themes.py`
- Mark deprecated (add comment at top). Keep the file for now to avoid breaking `hello.ipynb`. Delete after verifying no external imports.

---

## Migration Order (each step independently verifiable)

1. **Create scaffolding** — `modes/__init__.py`, `base.py`, `registry.py`. Run app. Nothing changes.
2. **Migrate one mode** (`evaluativist`) — create `modes/evaluativist.py`, update only the `evaluativist` branch in `crew.py` dispatch to use registry. Test evaluativist mode.
3. **Migrate remaining 4 modes** one at a time — same pattern, remove each `elif` branch after migrating.
4. **Thin consuming files** — simplify `handlers.py`, `ui.py`, `renderer.py` once all 5 modes route through registry.

---

## Adding a New Mode After Refactor

Create `modes/socratic.py` (or any name). Define `_build()` and call `register(ModeDefinition(...))`. On next startup, `pkgutil` discovers it, it appears in the radio automatically. **Zero changes to existing files.**

---

## Verification

1. `python app.py` — app opens at `http://127.0.0.1:7860`
2. Switch through all 5 modes in the radio — UI labels, CSS, and placeholder text update correctly for each
3. Generate a report in each mode — crew runs, output validates, HTML/JSON/MD saved in `reports/`
4. Toggle dark mode — re-renders correctly
5. Load from history — re-renders with original mode's CSS
6. Create `modes/test_mode.py` with a trivial `_build()` and `register()` — verify it appears in the radio without touching any other file

---

## Critical Files

| File | Status | Key Change |
|------|--------|-----------|
| `modes/base.py` | NEW | `ModeDefinition` dataclass |
| `modes/registry.py` | NEW | `register`, `get`, `all_modes`, `by_display_name` |
| `modes/kids_mode.py` … `master.py` | NEW (×5) | Mode definitions + crew builders |
| `logic/crew.py:367-376` | MODIFY | 10-line elif → 1 registry lookup |
| `frontend/gradio/handlers.py:13-43` | MODIFY | Delete dicts; simplify `update_ui` + `age_to_mode` |
| `frontend/gradio/ui.py:79-81` | MODIFY | 2 lines: radio list from registry |
| `logic/renderer.py:15-120` | MODIFY | 120-line elif → 5-line registry lookup |
| `frontend/gradio/themes.py` | DEPRECATE | Add deprecation comment; delete after verification |

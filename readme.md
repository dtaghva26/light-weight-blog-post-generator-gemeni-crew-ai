# Multi-Agent AI Blog & Story Generator

A multi-agent pipeline powered by **CrewAI** and **Google Gemini** that researches any topic and writes a structured, styled article — with five distinct thinking modes tailored to different age groups and epistemological stances.

## What It Does

1. A **Researcher agent** investigates the topic based on the active mode's personality.
2. A **Writer agent** turns the research into a structured article (validated via Pydantic).
3. The output is rendered into a polished **HTML report** with cognitive load bars, emotional valence badges, and a spaced repetition review schedule.

## Thinking Modes

Each mode changes the agents' personalities, writing style, UI labels, and visual theme:

| Mode | Audience | Epistemological stance |
|---|---|---|
| Kids Mode | Ages 0+ | Short sentences, simple words, magical tone |
| Absolutist | Ages 8+ | Facts presented as clear truth |
| Multiplist | Ages 11+ | All perspectives treated as equally valid |
| Evaluativist | Ages 18+ | Evidence-based reasoning |
| Master Thinker | Ages 40+ | Self-reflective, surfaces blind spots |

The app selects a default mode from the user's age at the age gate. The user can switch modes freely in the radio selector.

## Stack

| Tool | Role |
|---|---|
| [CrewAI](https://crewai.com) | Multi-agent orchestration |
| [Google Gemini 1.5 Flash](https://ai.google.dev) | LLM powering both agents |
| [Gradio](https://gradio.app) | Web UI |
| [Pydantic](https://docs.pydantic.dev) | Structured JSON output validation |
| `python-dotenv` | Environment variable management |

## Setup

### 1. Install dependencies

```bash
pip install crewai google-genai pydantic python-dotenv nest_asyncio gradio
```

### 2. Configure your API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run the app

```bash
python app.py
```

Opens at `http://127.0.0.1:7860`.

## Features

- **Age gate** — routes the user to the appropriate mode on first load
- **Five thinking modes** — distinct agent personas, UI themes, and CSS per mode
- **Live agent log** — agent stdout streams to the UI while generation runs
- **Configurable output** — 2–5 sections and 100–400 words per section via sliders
- **Dark mode** — re-renders the report theme on the fly
- **Cognitive load bars** — per-section visual indicator of reading complexity
- **Emotional valence badges** — per-section tone label (uplifting / neutral / cautionary / reflective / mixed)
- **Spaced repetition schedule** — review questions rendered at Day 1, Day 7, Day 21
- **Download** — saves HTML, JSON (source of truth), and Markdown per report
- **History** — dropdown to reload and re-render any previously generated report

## How It Saves Reports

Each run writes three files under `reports/`:

```
reports/
└── YYYYMMDD_HHMMSS_<slug>.html   # styled HTML report
    YYYYMMDD_HHMMSS_<slug>.json   # raw structured data — source of truth
    YYYYMMDD_HHMMSS_<slug>.md     # Markdown export
```

The JSON is the source of truth. The HTML and Markdown are always re-renderable from it.

## Project Structure

```
app.py                          # Entry point — launches the Gradio UI

modes/                          # One file per thinking mode (plugin architecture)
├── __init__.py
├── base.py                     # ModeDefinition dataclass
├── registry.py                 # Auto-discovery registry (pkgutil)
├── kids_mode.py
├── absolutist.py
├── multiplist.py
├── evaluativist.py
└── master.py

logic/
├── models.py                   # Pydantic schema: StructuredBlogPost, ArticleSection
├── crew.py                     # run_crew_streaming() generator
├── renderer.py                 # create_html(), blog_to_markdown()
└── reports.py                  # save_report(), list_reports(), load_report_*()

frontend/gradio/
├── ui.py                       # Gradio Blocks layout + event wiring
├── handlers.py                 # generate(), load_history(), rerender_dark(), update_ui()
└── themes.py                   # Deprecated — kept for hello.ipynb backwards compatibility

agents.py                       # Legacy re-export shim (kept for hello.ipynb)
utils.py                        # Legacy re-export shim (kept for hello.ipynb)
help/
└── expand.md                   # Guide for adding new modes
```

## How the Pipeline Works

```
User clicks Generate
        │
        ▼
run_crew_streaming(topic, num_sections, words_per_section, crew_type)
        │
        ├── Thread: mode._build() → Crew([researcher, writer], sequential)
        │       │
        │       ├── Task 1 → Researcher agent  (research / questions / facts)
        │       │       ↓  output passed automatically
        │       └── Task 2 → Writer agent  (structured article, JSON output)
        │
        ├── Stdout captured → streamed to UI log in real time
        │
        └── On finish: Pydantic validates → create_html() → save_report()
                                                  ↓
                                         HTML / JSON / MD written to reports/
```

## Adding a New Mode

Every mode is a single self-contained file in `modes/`. The app auto-discovers all files there at startup — no existing files need to change.

Full walkthrough, field reference, worked example, and common mistakes: **[help/expand.md](help/expand.md)**

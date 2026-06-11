# Multi-Agent AI Blog & Story Generator — Classroom Edition

A multi-agent pipeline powered by **CrewAI** and **Google Gemini** that researches any topic and writes a structured, styled article — adapted for direct pupil use in a UK primary classroom, with year-group writing modes, a topic safety filter, a teacher PIN, National Curriculum subject alignment, printable worksheets, and accessibility options.

## What It Does

1. A **Researcher agent** investigates the topic based on the active mode's personality.
2. A **Writer agent** turns the research into a structured article (validated via Pydantic).
3. The output is rendered into a polished **HTML report** with cognitive load bars, emotional valence badges, and a spaced repetition review schedule.

## Modes

Each mode changes the agents' personalities, writing style, UI labels, and visual theme. The four UK year-group modes write in British English, cap section lengths to age-appropriate sizes, and carry a prompt-level safety rule.

| Mode | Audience | Writing style | Visibility |
|---|---|---|---|
| Reception (ages 4–5) | EYFS | ≤6-word sentences, repetition, read-aloud rhythm | Pupils |
| Years 1–2 (ages 5–7) | KS1 | ≤8-word sentences, simple decodable vocabulary | Pupils |
| Years 3–4 (ages 7–9) | Lower KS2 | Wow fact + why, simple subordinate clauses | Pupils |
| Years 5–6 (ages 9–11) | Upper KS2 | Non-fiction features, technical vocab explained, discussion questions | Pupils |
| Kids Mode | Ages 0+ | Short sentences, simple words, magical tone | Pupils |
| Absolutist | Ages 8+ | Facts presented as clear truth | Pupils |
| Multiplist | Ages 11+ | All perspectives treated as equally valid | Teacher PIN |
| Evaluativist | Ages 18+ | Evidence-based reasoning | Teacher PIN |
| Master Thinker | Ages 40+ | Self-reflective, surfaces blind spots | Teacher PIN |

On first load the app asks for the **year group** (no pupil ages are collected) and routes to the matching mode. Pupils can switch freely between the pupil-visible modes.

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
TEACHER_PIN=your_four_digit_pin   # optional — defaults to 0000
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run the app

```bash
python app.py
```

Opens at `http://127.0.0.1:7860`.

## Features

- **Class setup screen** — the teacher picks the year group on first load; no pupil ages or personal data are collected
- **Nine modes** — four UK year-group modes plus the original five, each with distinct agent personas, UI themes, and CSS
- **Topic safety filter** — pupil topics are checked against the teacher-editable `safety_blocklist.txt` (whole-word matching) before any generation runs; blocked attempts are logged to `reports/blocked_topics.log` for teacher review, and the primary modes carry a prompt-level safety rule as a second layer
- **Teacher PIN** — the app starts in pupil mode (adult modes, sliders, and history hidden); entering the PIN in the "Teacher unlock" panel reveals everything
- **Curriculum subject alignment** — an optional subject dropdown (Science, History, Geography…) steers the Researcher toward the National Curriculum programme of study for the chosen key stage
- **Printable worksheet** — every report also saves an A4 comprehension worksheet (name/date line, numbered questions from the review prompts, ruled answer lines)
- **Accessibility options** — easy-read font, large print, and a calm-screen toggle that removes all animations from both the UI and the report
- **Live agent log** — agent stdout streams to the UI while generation runs
- **Configurable output** — 2–5 sections and 50–400 words per section via sliders (teacher mode); year-group modes also cap section length to age-appropriate sizes
- **Dark mode** — re-renders the report theme on the fly
- **Cognitive load bars** — per-section visual indicator of reading complexity
- **Emotional valence badges** — per-section tone label (uplifting / neutral / cautionary / reflective / mixed)
- **Spaced repetition schedule** — review questions rendered at Day 1, Day 7, Day 21
- **Download** — saves HTML, JSON (source of truth), Markdown, and worksheet HTML per report
- **History** — dropdown (teacher mode) to reload and re-render any previously generated report

## How It Saves Reports

Each run writes four files under `reports/`:

```
reports/
└── YYYYMMDD_HHMMSS_<slug>.html             # styled HTML report
    YYYYMMDD_HHMMSS_<slug>.json             # raw structured data — source of truth
    YYYYMMDD_HHMMSS_<slug>.md               # Markdown export
    YYYYMMDD_HHMMSS_<slug>_worksheet.html   # printable A4 comprehension worksheet
```

The JSON is the source of truth. The HTML and Markdown are always re-renderable from it.

## Project Structure

```
app.py                          # Entry point — launches the Gradio UI

modes/                          # One file per mode (plugin architecture)
├── __init__.py
├── base.py                     # ModeDefinition dataclass (incl. teacher_only flag)
├── registry.py                 # Auto-discovery registry (pkgutil)
├── eyfs.py                     # Reception (ages 4–5)
├── ks1.py                      # Years 1–2 (ages 5–7)
├── lks2.py                     # Years 3–4 (ages 7–9)
├── uks2.py                     # Years 5–6 (ages 9–11)
├── kids_mode.py
├── absolutist.py
├── multiplist.py               # teacher-only
├── evaluativist.py             # teacher-only
└── master.py                   # teacher-only

logic/
├── models.py                   # Pydantic schema: StructuredBlogPost, ArticleSection
├── crew.py                     # run_crew_streaming() generator
├── renderer.py                 # create_html(), create_worksheet_html(), blog_to_markdown()
├── reports.py                  # save_report(), list_reports(), load_report_*()
└── safety.py                   # check_topic(), log_blocked()

safety_blocklist.txt            # Teacher-editable topic blocklist (one term per line)

frontend/gradio/
├── ui.py                       # Gradio Blocks layout + event wiring
├── handlers.py                 # generate(), load_history(), rerender_view(), update_ui(), unlock_teacher()
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
run_crew_streaming(topic, num_sections, words_per_section, crew_type, subject)
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

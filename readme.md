# Multi-Agent AI Blog Generator

A multi-agent pipeline that uses **CrewAI** and **Google Gemini** to autonomously research AI trends, write a structured blog post, and export it as a polished HTML report.

## What It Does

1. A **Researcher agent** identifies the top AI trends for 2026.
2. A **Writer agent** turns those findings into a structured, database-ready blog post (validated via Pydantic).
3. The output is rendered into a standalone, styled **HTML file** (`ai_trends_report.html`).

## Stack

| Tool | Role |
|------|------|
| [CrewAI](https://crewai.com) | Multi-agent orchestration |
| [Google Gemini 2.5 Flash](https://ai.google.dev) | LLM powering both agents |
| [Pydantic](https://docs.pydantic.dev) | Structured JSON output validation |
| `google-genai` | Direct Gemini API client (sanity test) |
| `python-dotenv` | Environment variable management |

## Setup

### 1. Install dependencies

```bash
pip install crewai google-genai pydantic python-dotenv nest_asyncio
```

### 2. Configure your API key

Create a `.env` file in the project root:

```env
Gemeni_API_KEY=your_google_gemini_api_key_here
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run the notebook

Open `hello.ipynb` and run all cells. The final cell writes `ai_trends_report.html` to the project directory.

## Output

The generated `ai_trends_report.html` is a self-contained, responsive page with:

- A styled article header (title + author)
- One section per AI trend (heading + body paragraph)
- Mobile-friendly layout using CSS variables

## Project Structure

```
multi-agent/
├── hello.ipynb           # Main notebook — agents, tasks, HTML export
├── ai_trends_report.html # Generated output (created at runtime)
├── .env                  # API key (not committed)
└── readme.md
```

## How the Agents Work

```
Task 1 → Researcher: "List 3 major AI trends for 2026"
              ↓
Task 2 → Writer: "Write a 200-word blog post from those trends"
              ↓
        Pydantic-validated JSON (title, author, sections[])
              ↓
        create_html() → ai_trends_report.html
```

The crew runs `Process.sequential` — the writer receives the researcher's output before it begins.

# How to Add a New Mode to This App

This guide is for first-year CS students. No prior experience with this codebase required.

---

## What is a "mode"?

When you open the app, there is a row of radio buttons at the top: **Kids Mode, Absolutist, Multiplist, Evaluativist, Master Thinker**. Each one is a *mode* — it controls:

- The personality of the two AI agents that write the article
- The words and labels shown in the UI
- The visual style (colours, fonts, animations)
- Which age group sees it by default

**The key insight:** every mode is completely described by one Python file in the `modes/` folder. When the app starts, it automatically finds and loads every file in that folder. To add a new mode, you create one file. You do not touch anything else.

---

## The two things every mode file must do

Open any existing file — for example [modes/evaluativist.py](../modes/evaluativist.py). Every mode file does exactly two things:

1. **Define a `_build()` function** — this creates the two AI agents and tells them what to do
2. **Call `register(ModeDefinition(...))`** — this tells the app "I exist, here is everything about me"

That is it. The app takes care of the rest.

---

## Step-by-step: create a new mode

We will create a "Socratic" mode — an AI that asks questions instead of giving answers.

### Step 1 — Create the file

Create a new file: `modes/socratic.py`

Copy this skeleton into it:

```python
import os

from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

from logic.models import StructuredBlogPost
from modes.base import ModeDefinition
from modes.registry import register

load_dotenv()


def _build(topic: str, num_sections: int, words_per_section: int) -> Crew:
    gemini_llm = LLM(
        model="gemini/gemini-3.5-flash",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY"),
    )

    # --- Define your two agents here ---

    researcher = Agent(
        role="Socratic Questioner",
        goal=f"Generate thought-provoking questions about {topic} that challenge assumptions.",
        backstory=(
            "You are a Socratic philosopher. You never state facts directly. "
            "Instead, you ask questions that lead people to discover truth for themselves. "
            "You always respond with questions, not answers."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Dialectic Writer",
        goal="Turn philosophical questions into an article that makes the reader think deeply.",
        backstory=(
            "You write in the Socratic tradition. Each section poses a central question, "
            "then explores it through further questions rather than conclusions. "
            "You trust the reader to arrive at their own understanding."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    # --- Define what each agent must do ---

    task1 = Task(
        description=(
            f"Generate {num_sections} deep, open-ended questions about '{topic}' "
            f"that challenge common assumptions. Each question should be unsettling in a productive way."
        ),
        expected_output=f"A list of {num_sections} Socratic questions about {topic}.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Write an article with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Each section should be structured as a question followed by deeper sub-questions. "
            f"Do not give definitive answers — leave the reader thinking. "
            f"For each section, include: "
            f"'cognitive_load': a float 0.0–1.0 (Socratic articles are demanding, use 0.6–0.85). "
            f"'emotional_valence': one of: uplifting, neutral, cautionary, reflective, mixed. "
            f"'review_prompts': 2–3 questions the reader should sit with for a week."
        ),
        expected_output=(
            "A structured payload matching the StructuredBlogPost schema. "
            "Sections written as Socratic dialogues with cognitive_load, emotional_valence, and review_prompts."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="socratic",          # internal key — must be unique, no spaces
    display_name="Socratic",       # what appears in the radio button
    min_age=16,                    # minimum age to be routed here automatically
    order=5,                       # position in the radio (existing modes are 0–4)
    build_crew=_build,

    # --- UI text ---
    title="# Socratic Inquiry Engine\nQuestions that make you think",
    topic_label="What topic should we question?",
    topic_placeholder="e.g. free will, democracy, social media, memory...",
    gen_btn="Begin Inquiry",
    log_label="Inquiry in progress",
    log_placeholder="The agents will begin questioning once you click Begin Inquiry...",
    preview_label="Inquiry Report",

    # --- Sidebar labels ---
    settings_label="Inquiry settings",
    num_sections_label="Number of questions",
    words_per_section_label="Depth per question (words)",
    dark_toggle_label="Dark mode (report)",
    history_title="### Past Inquiries",
    history_dd_label="Load a past inquiry",
    load_btn_label="Load",
    dl_html_label="Download HTML",
    dl_md_label="Download Markdown",

    # --- Visual style ---
    gradio_css="<style></style>",  # no special Gradio styling — see below for how to add some
    report_css="",                 # no special report styling — see below for how to add some

    # --- Status messages ---
    empty_msg="Please enter a topic to question.",
    error_msg=lambda e: f"\n\nError: {e}",
    done_msg="\n\nInquiry complete.",
))
```

### Step 2 — Run the app

```bash
python app.py
```

Open `http://127.0.0.1:7860`. You will see **Socratic** appear in the radio automatically. No other files changed.

---

## Understanding the `_build()` function

This is where you define the AI behaviour. The function receives three arguments every time a user clicks Generate:

| Argument | Type | Meaning |
|---|---|---|
| `topic` | `str` | Whatever the user typed in the text box |
| `num_sections` | `int` | How many sections the article should have (from the slider) |
| `words_per_section` | `int` | How long each section should be (from the slider) |

Inside `_build()` you create:

**Two agents** — think of these as two employees you are hiring:
- `researcher` — finds information or asks questions first
- `writer` — takes the researcher's output and writes the article

Each agent has:
- `role` — their job title
- `goal` — what they are trying to accomplish for this specific topic
- `backstory` — their personality and constraints (this is the most important field — the LLM reads this to decide *how* to write)

**Two tasks** — the actual work orders:
- `task1` — assigned to the researcher, runs first
- `task2` — assigned to the writer, runs second and automatically receives task1's output

The `description` in `task2` is where you give the most detailed instructions. Notice how it uses f-strings to include `{topic}`, `{num_sections}`, and `{words_per_section}` — this is how user input reaches the AI.

The line `output_json=StructuredBlogPost` in `task2` is required — it tells CrewAI to return structured JSON that the app can render.

**One Crew** — packages everything together and runs it:
```python
return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)
```
`Process.sequential` means researcher runs first, then writer. Do not change this.

---

## Understanding the `register()` call

After `_build()`, you call `register(ModeDefinition(...))` with a flat list of fields. Here is what each field does:

### Identity fields

| Field | Example | What it does |
|---|---|---|
| `crew_type` | `"socratic"` | Internal key used in filenames and CSS. Must be unique. Lowercase, no spaces. |
| `display_name` | `"Socratic"` | The label shown in the radio button. |
| `min_age` | `16` | When the user enters their age, the app picks the highest mode whose `min_age` is <= their age. |
| `order` | `5` | Where this mode appears in the radio (0 = leftmost). |
| `build_crew` | `_build` | Pass your `_build` function here — just the name, no parentheses. |

### UI text fields

These control what the user reads in the interface. They are just strings — change them to fit your mode's personality.

| Field | Shows up where |
|---|---|
| `title` | The big heading at the top of the app. Supports Markdown (`**bold**`, `# Heading`). |
| `topic_label` | The label above the text input box. |
| `topic_placeholder` | The grey hint text inside the box before the user types. |
| `gen_btn` | The label on the Generate button. |
| `log_label` | The label above the streaming log panel. |
| `log_placeholder` | The hint text in the log panel before anything runs. |
| `preview_label` | The label above the rendered report. |
| `settings_label` | The label on the collapsible settings accordion. |
| `num_sections_label` | Label for the sections slider. |
| `words_per_section_label` | Label for the words-per-section slider. |
| `dark_toggle_label` | Label for the dark mode checkbox. |
| `history_title` | Markdown heading above the history dropdown. |
| `history_dd_label` | Label for the history dropdown. |
| `load_btn_label` | Label on the Load button. |
| `dl_html_label` | Label on the HTML download button. |
| `dl_md_label` | Label on the Markdown download button. |

### CSS fields

These control visual styling. If you do not want custom styling, use the empty defaults shown in the skeleton above.

**`gradio_css`** — HTML `<style>` block injected into the live Gradio UI when your mode is selected. Use this to change colours, fonts, or animations in the app itself. Example:

```python
gradio_css="""
<style>
.gradio-container { background: #f0f4ff !important; }
.gradio-container h1 { color: #1a237e !important; }
button.primary { background: #3949ab !important; border-radius: 4px !important; }
</style>
""",
```

**`report_css`** — Raw CSS (no `<style>` tags) injected into the standalone HTML report file. Use this to style the saved report. Example:

```python
report_css="""
body { font-family: 'Georgia', serif !important; }
h1 { color: #1a237e !important; border-bottom: 3px solid #3949ab; }
h2 { color: #283593 !important; }
""",
```

### Message fields

These are the short strings shown in the log when things happen.

| Field | When shown |
|---|---|
| `empty_msg` | User clicks Generate without typing a topic. |
| `error_msg` | The AI fails or returns invalid output. Takes the error text `e` as an argument. |
| `done_msg` | Generation succeeded. Appended to the log. |

`error_msg` is a lambda (a one-line function). The `e` parameter is the error message from the AI or the system:
```python
error_msg=lambda e: f"\n\nSomething went wrong: {e}",
```

---

## How the app finds your file automatically

You do not need to register your file anywhere. When the app starts, [modes/registry.py](../modes/registry.py) runs this code:

```python
for _finder, name, _ispkg in pkgutil.iter_modules(_pkg.__path__):
    if name not in ("base", "registry"):
        importlib.import_module(f"modes.{name}")
```

`pkgutil.iter_modules` lists every `.py` file in the `modes/` folder. It imports each one. When your file is imported, the line at the bottom — `register(ModeDefinition(...))` — runs automatically, adding your mode to the registry. From that point, every other part of the app (the radio button list, the routing, the CSS injection, the age gate) pulls from the registry, so your mode appears everywhere.

---

## The cognitive load and review_prompts fields

These are metadata the AI fills in for each section — you instruct it to in `task2`'s description.

**`cognitive_load`** — a number between 0.0 and 1.0. Low = easy (kids mode uses 0.05–0.15). High = demanding (master mode uses 0.7–0.95). The app renders this as a coloured progress bar under each section heading. Guide the AI to use values appropriate for your mode's audience.

**`review_prompts`** — a list of 2–3 questions. The app renders these in a three-panel "Spaced Repetition Review Schedule" at the bottom of the report (Day 1, Day 7, Day 21). Write your task2 description to ask the AI for questions that match your mode's tone.

---

## Common mistakes

**Duplicate `crew_type`** — if two files use the same `crew_type` string, the second one silently overwrites the first. Use a unique lowercase key.

**Skipping `output_json=StructuredBlogPost` in task2** — the app will crash with a validation error because it cannot parse the AI's output. Always include this line on task2.

**Forgetting `process=Process.sequential` in the Crew** — the researcher and writer will run in parallel, which breaks the pipeline because the writer needs the researcher's output.

**Using the wrong Python** — if you see `ModuleNotFoundError: No module named 'crewai'`, you are running the wrong Python. Use the conda environment:
```
C:\Users\admin\anaconda3\envs\multiagent-env\python.exe app.py
```

**Leaving `output_json` off the researcher's task** — only task2 (the writer) needs `output_json`. Putting it on task1 causes issues.

---

## Quick reference: minimum viable mode file

If you want the smallest possible new mode with no custom styling:

```python
import os
from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv
from logic.models import StructuredBlogPost
from modes.base import ModeDefinition
from modes.registry import register

load_dotenv()

def _build(topic, num_sections, words_per_section):
    llm = LLM(model="gemini/gemini-3.5-flash",
              api_key=os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY"))

    researcher = Agent(role="Researcher", goal=f"Research {topic}.", backstory="You are thorough.", verbose=True, llm=llm)
    writer     = Agent(role="Writer",     goal=f"Write about {topic}.", backstory="You are clear.", verbose=True, llm=llm)

    task1 = Task(description=f"Find {num_sections} key points about {topic}.",
                 expected_output=f"{num_sections} bullet points about {topic}.", agent=researcher)
    task2 = Task(description=(f"Write {num_sections} sections of ~{words_per_section} words each about {topic}. "
                               f"Include cognitive_load (0.0–1.0), emotional_valence (uplifting/neutral/cautionary/reflective/mixed), "
                               f"and review_prompts (2–3 questions) per section."),
                 expected_output="A StructuredBlogPost JSON payload.", agent=writer, output_json=StructuredBlogPost)

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)

register(ModeDefinition(
    crew_type="my_mode", display_name="My Mode", min_age=18, order=6, build_crew=_build,
    title="# My Mode", topic_label="Topic", topic_placeholder="Enter a topic...",
    gen_btn="Generate", log_label="Log", log_placeholder="Log will appear here...", preview_label="Preview",
    settings_label="Settings", num_sections_label="Sections", words_per_section_label="Words per section",
    dark_toggle_label="Dark mode", history_title="### History", history_dd_label="Past reports",
    load_btn_label="Load", dl_html_label="Download HTML", dl_md_label="Download Markdown",
    gradio_css="<style></style>", report_css="",
    empty_msg="Please enter a topic.", error_msg=lambda e: f"\n\nError: {e}", done_msg="\n\nDone.",
))
```

Save this as `modes/my_mode.py`, run the app, and your mode appears in the radio.

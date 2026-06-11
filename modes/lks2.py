import os

from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

from logic.models import StructuredBlogPost
from modes.base import ModeDefinition
from modes.registry import register

load_dotenv()

_SAFETY_RULE = (
    "Everything you write will be read by primary school children in the UK. "
    "If the topic is not suitable for children, do not write about it — "
    "instead write one gentle sentence suggesting they choose a different topic with their teacher. "
)

_UK_RULE = (
    "Always use British English spelling (colour, favourite, metre, -ise endings), "
    "metric units, and examples familiar to children in the UK. "
)


def _build(topic: str, num_sections: int, words_per_section: int, subject: str = None) -> Crew:
    gemini_llm = LLM(
        model="gemini/gemini-3.5-flash",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY"),
        timeout=60,
        max_retries=2,
    )

    words = min(words_per_section, 180)

    subject_note = (
        f" Frame the facts to support the lower Key Stage 2 {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="Lower KS2 Discovery Researcher",
        goal=f"Find {num_sections} fascinating facts about {topic} for children in Years 3 and 4, each with a 'why' behind it.",
        backstory=(
            "You are an enthusiastic lower Key Stage 2 teacher in a UK primary school, teaching ages 7 to 9. "
            + _SAFETY_RULE + _UK_RULE +
            "You find facts that make children say 'wow' — and you always explain WHY they happen, "
            "because Years 3 and 4 love knowing the reason behind things. "
            "You use clear, friendly language with the occasional new word explained simply."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Lower KS2 Explainer",
        goal="Turn fascinating facts into clear, lively paragraphs Years 3 and 4 children can read independently.",
        backstory=(
            "You write for children aged 7 to 9 who are becoming confident readers. "
            + _SAFETY_RULE + _UK_RULE +
            "You write in short paragraphs with varied sentences, including simple subordinate clauses "
            "(because, when, if, although). "
            "Each section gives a wow fact and then explains why it is true. "
            "When you use a new or tricky word, you explain it in brackets straight after."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} fascinating facts about '{topic}' for children aged 7 to 9. "
            f"For each fact, also note the reason WHY it is true, in child-friendly language."
            f"{subject_note}"
        ),
        expected_output=f"A list of {num_sections} wow facts about {topic}, each with a child-friendly 'why'.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the facts, write an article with exactly {num_sections} sections, "
            f"roughly {words} words each. Topic: {topic}. "
            f"Each section: a wow fact, then a clear explanation of why it happens. "
            f"Use short paragraphs and varied sentences with simple subordinate clauses "
            f"(because, when, if). Explain any tricky word in brackets straight after it. "
            f"British English spelling only. "
            f"For each section add: "
            f"'cognitive_load' — between 0.2 and 0.35. "
            f"'emotional_valence' — exactly one of: uplifting, neutral, cautionary, reflective, mixed. "
            f"'review_prompts' — exactly 2 questions for ages 7-9, one recall ('What did you learn about...?') "
            f"and one explain ('Why does... happen?')."
        ),
        expected_output=(
            "A structured payload matching StructuredBlogPost, written for ages 7-9: "
            "wow fact + why structure, simple subordinate clauses, tricky words explained, British English, "
            "cognitive_load 0.2-0.35, emotional_valence one of the 5 allowed values, review_prompts 2 questions."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="lks2",
    display_name="Years 3–4 (ages 7–9)",
    min_age=7,
    order=-2,
    build_crew=_build,
    dl_worksheet_label="🖨️ Print Comprehension Sheet",

    # theme
    title="# 🔍 Discovery Machine 🔍\n### Pick a topic and find out the amazing WHY behind it!",
    topic_label="🔭 What shall we discover today?",
    topic_placeholder="e.g. volcanoes, Romans, rainforests, electricity, Egyptians...",
    gen_btn="🔍 Start Discovering!",
    log_label="🤖 The research robots are investigating...",
    log_placeholder="Click Start Discovering and watch the robots investigate your topic!",
    preview_label="🌟 Your Discovery Report!",

    # labels
    settings_label="⚙️ Teacher options",
    num_sections_label="📖 Number of discoveries",
    words_per_section_label="📝 Length of each discovery",
    dark_toggle_label="🌙 Night Mode",
    history_title="### 📚 Look back at past discoveries",
    history_dd_label="Pick a past discovery 👇",
    load_btn_label="📖 Open",
    dl_html_label="💾 Save Report",
    dl_md_label="📄 Save as Text",

    # Gradio CSS — fresh greens
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
    body, .gradio-container {
        background: linear-gradient(135deg, #E8FFF0 0%, #E0F7FA 100%) !important;
    }
    .gradio-container * { font-family: 'Nunito', sans-serif !important; }
    .gradio-container h1 {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        color: #00897B !important;
    }
    button.primary {
        background: linear-gradient(135deg, #26A69A, #66BB6A) !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
    }
    </style>
    """,

    # Report CSS
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
        body { font-family: 'Nunito', sans-serif !important; background: #F0FFF6 !important; }
        h1 { font-size: 2.3rem; font-weight: 800; color: #00897B !important; }
        h2 { font-size: 1.5rem; font-weight: 800; color: #2E7D32 !important; border-left: 6px solid #66BB6A !important; padding-left: 12px !important; }
        p  { font-size: 1.2rem !important; line-height: 1.9 !important; text-align: left !important; }
        .section-block { border: 2px solid #C8F5D8 !important; border-radius: 16px !important; padding: 22px !important; background: #FCFFFD !important; }
        """,

    # messages
    empty_msg="Type a topic to discover first! 🔍",
    error_msg=lambda e: f"\n\n😕 The robots hit a snag — give it another go! ({e})",
    done_msg="\n\n🌟 Discovery complete! Brilliant work!",
))

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

    words = min(words_per_section, 250)

    subject_note = (
        f" Frame the facts to support the upper Key Stage 2 {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="Upper KS2 Research Reporter",
        goal=f"Research {num_sections} key ideas about {topic} for children in Years 5 and 6, with accurate detail.",
        backstory=(
            "You are an upper Key Stage 2 teacher in a UK primary school, teaching ages 9 to 11. "
            + _SAFETY_RULE + _UK_RULE +
            "You gather accurate, interesting information with real detail — Years 5 and 6 can handle "
            "proper technical vocabulary as long as it is explained in context. "
            "You prefer facts that invite a question or a debate."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Upper KS2 Non-Fiction Author",
        goal="Write engaging non-fiction Years 5 and 6 children can read independently and discuss.",
        backstory=(
            "You write non-fiction for children aged 9 to 11, in the style of a great children's reference book. "
            + _SAFETY_RULE + _UK_RULE +
            "You use proper non-fiction features: clear headings, well-organised paragraphs, "
            "and technical vocabulary explained in context the first time it appears. "
            "You end each section with one short 'What do you think?' question to spark class discussion."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Research {num_sections} key ideas about '{topic}' for children aged 9 to 11. "
            f"Include accurate detail and correct technical vocabulary, noting child-friendly explanations "
            f"for each technical term. Prefer ideas that invite discussion."
            f"{subject_note}"
        ),
        expected_output=f"A list of {num_sections} well-researched ideas about {topic} with explained technical terms.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the research, write a non-fiction article with exactly {num_sections} sections, "
            f"roughly {words} words each. Topic: {topic}. "
            f"Use non-fiction features: informative headings and well-organised paragraphs. "
            f"Introduce technical vocabulary and explain it in context the first time it appears. "
            f"End each section with one short 'What do you think?' discussion question. "
            f"British English spelling only. "
            f"For each section add: "
            f"'cognitive_load' — between 0.3 and 0.5. "
            f"'emotional_valence' — exactly one of: uplifting, neutral, cautionary, reflective, mixed. "
            f"'review_prompts' — exactly 3 questions for ages 9-11: one recall, one explain, "
            f"and one opinion question that asks the reader what they think and why."
        ),
        expected_output=(
            "A structured payload matching StructuredBlogPost, written for ages 9-11: "
            "non-fiction features, technical vocabulary explained in context, a discussion question per section, "
            "British English, cognitive_load 0.3-0.5, emotional_valence one of the 5 allowed values, "
            "review_prompts 3 questions (recall, explain, opinion)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="uks2",
    display_name="Years 5–6 (ages 9–11)",
    min_age=9,
    order=-1,
    build_crew=_build,
    dl_worksheet_label="🖨️ Print Comprehension Sheet",

    # theme
    title="# 📰 Junior Journalist 📰\n### Research any topic and get a proper non-fiction report — then debate it!",
    topic_label="🗞️ What's your topic?",
    topic_placeholder="e.g. space exploration, climate change, Ancient Greece, the human body...",
    gen_btn="📰 Research It!",
    log_label="🤖 The newsroom robots are researching...",
    log_placeholder="Click Research It and follow the robots' investigation here...",
    preview_label="📰 Your Report",

    # labels
    settings_label="⚙️ Teacher options",
    num_sections_label="📖 Number of sections",
    words_per_section_label="📝 Words per section",
    dark_toggle_label="🌙 Night Mode",
    history_title="### 📚 Past reports",
    history_dd_label="Open a past report 👇",
    load_btn_label="📖 Open",
    dl_html_label="💾 Save Report",
    dl_md_label="📄 Save as Text",

    # Gradio CSS — crisp newsroom blues
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
    body, .gradio-container {
        background: linear-gradient(135deg, #EDF4FF 0%, #E8EEFF 100%) !important;
    }
    .gradio-container * { font-family: 'Nunito', sans-serif !important; }
    .gradio-container h1 {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        color: #1A4FBF !important;
    }
    button.primary {
        background: linear-gradient(135deg, #1E5BD6, #3D8EBF) !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
    }
    </style>
    """,

    # Report CSS
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
        body { font-family: 'Nunito', sans-serif !important; }
        h1 { font-size: 2.2rem; font-weight: 800; color: #1A4FBF !important; }
        h2 { font-size: 1.4rem; font-weight: 700; color: #15397F !important; border-bottom: 3px solid #B8C7FF !important; padding-bottom: 6px !important; }
        p  { font-size: 1.1rem !important; line-height: 1.85 !important; text-align: left !important; }
        .section-block { border: 2px solid #D6E0FF !important; border-radius: 12px !important; padding: 22px !important; }
        """,

    # messages
    empty_msg="Enter a topic to research first. 🗞️",
    error_msg=lambda e: f"\n\n⚠️ The newsroom hit a problem — try again! ({e})",
    done_msg="\n\n📰 Report filed! Excellent journalism!",
))

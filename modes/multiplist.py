import os

from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

from logic.models import StructuredBlogPost
from modes.base import ModeDefinition
from modes.registry import register

load_dotenv()


def _build(topic: str, num_sections: int, words_per_section: int, subject: str = None) -> Crew:
    gemini_llm = LLM(
        model="gemini/gemini-3.5-flash",
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY"),
    )

    subject_note = (
        f" Frame the perspectives to support the {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="Perspective Collector",
        goal=f"Gather {num_sections} different viewpoints that people hold about {topic}, without judging which is best.",
        backstory=(
            "You are an open-minded explorer who believes everyone's opinion deserves to be heard. "
            "You collect perspectives from all sides without deciding who is right. "
            "You present each viewpoint fairly and equally, because you know truth is subjective "
            "and different people see things differently. You never conclude one view is better than another."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Opinion Journalist",
        goal="Present multiple perspectives on a topic in a conversational way, without picking a winner.",
        backstory=(
            "You are a conversational writer who speaks to teenagers and young adults. "
            "You use casual, engaging language and present all sides of a debate equally. "
            "You never conclude which view is correct — you say things like 'some people think', "
            "'others argue', 'it depends on your perspective'. "
            "Your readers should feel that all opinions are valid and worth considering."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Collect {num_sections} distinct viewpoints or perspectives that people hold about '{topic}'. "
            f"For each perspective, describe who holds it and why they believe it. "
            f"Do NOT evaluate which perspective is better — just present them all fairly."
            f"{subject_note}"
        ),
        expected_output=f"A bulleted list of {num_sections} different perspectives on {topic}, each described without judgment.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the perspectives provided, write a blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Each section presents a different viewpoint in a casual, conversational tone. "
            f"Never conclude which view is correct. Use phrases like 'some people believe', "
            f"'others feel', 'it really depends on your own experience'. "
            f"The tone should feel like a thoughtful teen exploring different ideas. "
            f"For each section, include three extra fields. "
            f"'cognitive_load': a decimal 0.0–1.0 showing how mentally demanding the section is — conversational sections should be around 0.3–0.5. "
            f"'emotional_valence': exactly one of uplifting, neutral, cautionary, reflective, mixed based on the overall vibe. "
            f"'review_prompts': a list of 2–3 casual questions someone could ask themselves after reading, like 'What perspective surprised you most?'"
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema, presenting multiple equal perspectives without evaluation. "
            "Each section includes cognitive_load (float roughly 0.3–0.5), emotional_valence (one of the 5 allowed values), and review_prompts (2–3 casual recall questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="multiplist",
    display_name="Multiplist",
    min_age=11,
    order=2,
    build_crew=_build,
    teacher_only=True,

    # theme
    title="# 🔍 Perspectives Explorer\nDiscover what different people think about any topic",
    topic_label="What topic should we explore different views on?",
    topic_placeholder="e.g. social media, climate change, AI, school uniforms...",
    gen_btn="🔍 Explore Views",
    log_label="🤔 Exploring perspectives...",
    log_placeholder="The agents will collect different viewpoints once you click Explore Views...",
    preview_label="🗣️ Perspectives",

    # labels
    settings_label="More options",
    num_sections_label="How many perspectives?",
    words_per_section_label="Length per perspective",
    dark_toggle_label="Dark mode",
    history_title="### Past Explorations",
    history_dd_label="Load a past exploration",
    load_btn_label="Open",
    dl_html_label="Download HTML",
    dl_md_label="Download Markdown",

    # Gradio CSS
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    body, .gradio-container {
        background: linear-gradient(135deg, #F0F7FF 0%, #F5F0FF 100%) !important;
    }
    .gradio-container * { font-family: 'Inter', sans-serif !important; }
    .gradio-container h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #5B6EF5 !important;
    }
    </style>
    """,

    # Report CSS
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif !important; }
        h1 { font-size: 2rem; font-weight: 700; color: #5B6EF5 !important; }
        h2 { font-size: 1.35rem; font-weight: 600; color: #3D8EBF !important; border-left: 4px solid #B8C7FF; padding-left: 12px; margin-top: 1.8rem; }
        p  { font-size: 1.05rem; line-height: 1.85; }
        .author { color: #5B6EF5; font-weight: 500; font-size: 1rem; }
        """,

    # messages
    empty_msg="Please enter a topic to explore.",
    error_msg=lambda e: f"\n\n⚠️ Couldn't collect perspectives: {e}",
    done_msg="\n\n✅ Perspectives collected!",
))

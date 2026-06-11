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
        f" Frame the findings to support the {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Uncover cutting-edge developments and trends in {topic}, evaluating evidence quality.",
        backstory=(
            "You are an expert researcher who evaluates claims based on evidence and logic. "
            "You understand that not all opinions are equal — some are better supported than others. "
            "You identify the strongest evidence, weigh conflicting data, and focus on what reasoning supports."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Tech Content Writer",
        goal="Create evidence-based blog posts that help readers evaluate claims for themselves.",
        backstory=(
            "You are a skilled analytical writer who presents arguments with supporting evidence. "
            "You help readers understand WHY certain conclusions are better supported than others. "
            "You use clarity, accuracy, and logic as your standards. You distinguish strong evidence from weak."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=f"List {num_sections} major trends or developments in {topic}, noting the evidence supporting each.{subject_note}",
        expected_output=f"A bulleted list of {num_sections} evidence-backed trends in {topic}.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Write a blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each, based on the trends provided. "
            f"Topic: {topic}. Each section should present evidence, evaluate its strength, "
            f"and help the reader understand why certain conclusions are better supported. "
            f"For each section, populate three analytical metadata fields. "
            f"'cognitive_load': a float 0.0–1.0 estimating working memory demand — analytical sections with dense evidence should score 0.5–0.75. "
            f"'emotional_valence': exactly one value from [uplifting, neutral, cautionary, reflective, mixed] based on the section's rhetorical register. "
            f"'review_prompts': 2–3 evidence-focused recall questions that test whether the reader understood the reasoning, not just the conclusion."
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema. "
            "Each section includes cognitive_load (float 0.0–1.0), emotional_valence (one of 5 allowed values), and review_prompts (2–3 analytical recall questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="evaluativist",
    display_name="Evaluativist",
    min_age=18,
    order=3,
    build_crew=_build,
    teacher_only=True,

    # theme
    title="# Multi-Agent Blog Generator\nPowered by **CrewAI** + **Google Gemini**",
    topic_label="Blog Topic",
    topic_placeholder="e.g. quantum computing, climate tech, Web3...",
    gen_btn="Generate",
    log_label="Agent Activity",
    log_placeholder="Agent log will appear here once you click Generate...",
    preview_label="Report Preview",

    # labels
    settings_label="Advanced settings",
    num_sections_label="Number of sections",
    words_per_section_label="Words per section",
    dark_toggle_label="Dark mode (report)",
    history_title="### Past Reports",
    history_dd_label="Load a past report",
    load_btn_label="Load",
    dl_html_label="Download HTML",
    dl_md_label="Download Markdown",

    # Gradio CSS (no special styling for evaluativist — default Gradio theme)
    gradio_css="<style></style>",

    # Report CSS
    report_css="",

    # messages
    empty_msg="Please enter a topic.",
    error_msg=lambda e: f"\n\n⚠ ERROR: {e}",
    done_msg="\n\n✅ Done!",
))

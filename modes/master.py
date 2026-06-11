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
        timeout=60,
        max_retries=2,
    )

    subject_note = (
        f" Frame the analysis to support the {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="Epistemic Analyst",
        goal=(
            f"Analyze {num_sections} key claims about {topic}, explicitly surfacing assumptions, "
            f"blind spots, and genuine uncertainty in each."
        ),
        backstory=(
            "You are a master thinker who has spent decades examining not just what people know, "
            "but HOW they know it and what they might be missing. "
            "For every claim, you automatically ask: What assumptions underlie this? "
            "Where is the evidence thin? What would change this conclusion? "
            "What cognitive biases might be distorting the picture? "
            "You treat intellectual humility as a strength, not a weakness."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Reflective Scholar",
        goal="Synthesize complex ideas across frameworks while openly acknowledging limits and inviting critical reader engagement.",
        backstory=(
            "You are a distinguished scholar whose writing models the highest form of critical thinking. "
            "You use hedged, precise language ('the evidence suggests', 'one must be cautious', "
            "'this conclusion rests on the assumption that'). "
            "You synthesize across multiple frameworks and disciplines. "
            "You explicitly acknowledge what remains unknown or contested. "
            "You invite readers to examine their own priors and challenge your conclusions. "
            "Your writing does not perform certainty — it demonstrates intellectual integrity."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Analyze {num_sections} key claims, arguments, or developments related to '{topic}'. "
            f"For each, explicitly identify: the underlying assumptions, the quality and limits of supporting evidence, "
            f"where expert consensus is genuinely weak or contested, and what a thoughtful critic would challenge. "
            f"Flag your own potential blind spots in this analysis."
            f"{subject_note}"
        ),
        expected_output=(
            f"A structured list of {num_sections} epistemic analyses of claims about {topic}, "
            f"each including assumptions, evidence assessment, points of genuine uncertainty, and potential blind spots."
        ),
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the epistemic analyses provided, write a scholarly blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Use precise, hedged language. Synthesize across frameworks. "
            f"Explicitly acknowledge what remains uncertain or unknown. "
            f"Invite readers to question both your conclusions and their own assumptions. "
            f"The tone should model habitual critical self-reflection — confident in its reasoning process, "
            f"humble about the limits of its conclusions. "
            f"For each section, assign three epistemic-metadata fields. "
            f"'cognitive_load': a float 0.0–1.0 reflecting working-memory burden from nested qualifications and multi-framework synthesis — expect values in the 0.65–0.95 range. "
            f"'emotional_valence': one of exactly five values — uplifting, neutral, cautionary, reflective, mixed — representing the dominant epistemic-emotional register of the section. "
            f"'review_prompts': precisely 2–3 questions requiring the reader to reconstruct the core argument, identify a key assumption, and articulate one remaining point of genuine uncertainty."
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema, "
            "written with master-thinker epistemic standards: hedged, self-reflective, synthesizing, and intellectually honest. "
            "Each section includes cognitive_load (float expected 0.65–0.95), emotional_valence (one of 5 allowed values), and review_prompts (2–3 deep reflective questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="master",
    display_name="Master Thinker",
    min_age=40,
    order=4,
    build_crew=_build,
    teacher_only=True,

    # theme
    title="# Deep Analysis Engine\nEpistemic synthesis powered by **CrewAI** + **Google Gemini**",
    topic_label="Subject for deep analysis",
    topic_placeholder="e.g. consciousness, democracy, scientific consensus, free will...",
    gen_btn="Analyze & Synthesize",
    log_label="Reasoning trace",
    log_placeholder="The epistemic analysis will stream here once you begin...",
    preview_label="Synthesis",

    # labels
    settings_label="Analysis parameters",
    num_sections_label="Number of sections",
    words_per_section_label="Words per section",
    dark_toggle_label="Dark mode",
    history_title="### Prior Analyses",
    history_dd_label="Load a prior analysis",
    load_btn_label="Load",
    dl_html_label="Export HTML",
    dl_md_label="Export Markdown",

    # Gradio CSS
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
    body, .gradio-container {
        background: #F9F6F0 !important;
    }
    .gradio-container * { font-family: 'Crimson Text', Georgia, serif !important; }
    .gradio-container h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #2C2416 !important;
        letter-spacing: 0.01em !important;
    }
    </style>
    """,

    # Report CSS
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
        body { font-family: 'Crimson Text', Georgia, serif !important; }
        h1 { font-size: 2.1rem; font-weight: 600; color: #2C2416 !important; letter-spacing: 0.01em; }
        h2 { font-size: 1.4rem; font-weight: 600; color: #5C4A1E !important; border-left: 3px solid #C8A96E; padding-left: 14px; margin-top: 2rem; font-style: italic; }
        p  { font-size: 1.1rem; line-height: 1.95; text-align: justify; }
        blockquote { border-left: 3px solid #C8A96E; padding-left: 1rem; color: #5C4A1E; font-style: italic; }
        .author { color: #5C4A1E; font-weight: 600; font-size: 1rem; letter-spacing: 0.02em; }
        """,

    # messages
    empty_msg="Please provide a subject for analysis.",
    error_msg=lambda e: f"\n\n⚠ Analysis failed: {e}",
    done_msg="\n\n✅ Analysis complete.",
))

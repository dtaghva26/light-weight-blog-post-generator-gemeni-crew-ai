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
        f" Frame the facts to support the {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="Fact Finder",
        goal=f"Find {num_sections} clear, definitive facts about {topic} that a 6-year-old can understand.",
        backstory=(
            "You are a trusted teacher who knows everything. You present facts as simple, absolute truths. "
            "Everything you say is definitely right. You use very short sentences and only the simplest words. "
            "You never say 'maybe' or 'some people think' — you state what IS, clearly and confidently."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Simple Storyteller",
        goal="Turn facts into a clear, definitive story a young child can follow easily.",
        backstory=(
            "You are a trusted author who writes for children aged 6 to 10. "
            "You use only simple vocabulary, very short sentences, and declare facts confidently. "
            "There is no ambiguity in your writing — things are simply true or not true. "
            "You never hedge. Every sentence ends with certainty."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} clear, definitive facts about '{topic}' that a 6-year-old can understand. "
            f"Write each fact as a simple, confident statement. No maybes. No 'some experts say'. "
            f"Use only words a young child knows."
            f"{subject_note}"
        ),
        expected_output=f"A bulleted list of {num_sections} simple, definitive facts about {topic} for young children.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the facts provided, write a simple blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Use very short sentences. Declare everything as clear fact. "
            f"Use only vocabulary a 6-year-old knows. No hedging, no 'maybe', no complexity. "
            f"For each section, add three special helper fields. "
            f"'cognitive_load' is a number from 0.0 to 1.0 — use low numbers like 0.1 or 0.2 because this is simple writing for children. "
            f"'emotional_valence' must be exactly one word chosen from: uplifting, neutral, cautionary, reflective, mixed — pick the one that matches how the section feels. "
            f"'review_prompts' is a list of exactly 2 simple questions a young child can answer after reading, like 'What is the main thing you learned?'"
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema, written for young children as clear absolute facts. "
            "Each section includes cognitive_load (a low float near 0.1–0.3), emotional_valence (one of the 5 allowed values), and review_prompts (2 simple recall questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="absolutist",
    display_name="Absolutist",
    min_age=8,
    order=1,
    build_crew=_build,

    # theme
    title="# 🌟 My Story Maker 🌟\nTell me a topic and I'll write a story for you! ✨",
    topic_label="✏️ What do you want to learn about?",
    topic_placeholder="e.g. space, animals, dinosaurs, robots...",
    gen_btn="🚀 Make My Story!",
    log_label="🤖 What's happening...",
    log_placeholder="The helper robots will show their work here once you click Make My Story!",
    preview_label="🎉 Your Story!",

    # labels
    settings_label="⚙️ More options (for curious kids!)",
    num_sections_label="📖 How many chapters?",
    words_per_section_label="📝 How long each chapter?",
    dark_toggle_label="🌙 Night Mode",
    history_title="### 📚 Read an old story",
    history_dd_label="Pick a story you made before",
    load_btn_label="📖 Open!",
    dl_html_label="💾 Save as Web Page",
    dl_md_label="📄 Save as Text File",

    # Gradio CSS
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
    body, .gradio-container {
        background: linear-gradient(135deg, #FFF0F5 0%, #EEF4FF 50%, #F0FFF8 100%) !important;
    }
    .gradio-container * { font-family: 'Poppins', sans-serif !important; }
    .gradio-container h1 {
        font-size: 2.6rem !important;
        font-weight: 800 !important;
        color: #FF6B9D !important;
    }
    </style>
    """,

    # Report CSS
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
        body { font-family: 'Poppins', sans-serif !important; }
        h1 { font-size: 2.4rem; font-weight: 800; color: #FF6B9D !important; }
        h2 { font-size: 1.6rem; font-weight: 700; color: #7888BF !important; border-left: 6px solid #FFE87C; padding-left: 12px; margin-top: 2rem; }
        p  { font-size: 1.1rem; line-height: 1.8; }
        .author { color: #FF6B9D; font-weight: 600; font-size: 1.1rem; }
        """,

    # messages
    empty_msg="Please type something! 🐣",
    error_msg=lambda e: f"\n\n⚠️ Uh-oh! Something went wrong: {e}",
    done_msg="\n\n🎉 Your story is ready! Great job! 🌟",
))

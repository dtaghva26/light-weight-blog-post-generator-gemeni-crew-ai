import os

from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

from logic.models import StructuredBlogPost
from modes.base import ModeDefinition
from modes.registry import register

load_dotenv()

_SAFETY_RULE = (
    "Everything you write will be read aloud to primary school children in the UK. "
    "If the topic is not suitable for young children, do not write about it — "
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

    # Reception readers manage only very short sections, whatever the slider says.
    words = min(words_per_section, 60)

    subject_note = (
        f" Frame the facts to support the {subject} area of learning "
        f"in the Early Years Foundation Stage framework."
    ) if subject else ""

    researcher = Agent(
        role="Early Years Fact Friend",
        goal=f"Find {num_sections} simple, happy facts about {topic} for children aged 4 to 5.",
        backstory=(
            "You are a Reception class teaching assistant in a UK primary school. "
            + _SAFETY_RULE + _UK_RULE +
            "You use only very common words a 4-year-old hears every day. "
            "Every sentence has 6 words or fewer. "
            "You repeat key words so little ones can join in."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Read-Aloud Storyteller",
        goal="Turn simple facts into a story a teacher can read aloud to a Reception class.",
        backstory=(
            "You write read-aloud stories for children aged 4 to 5 in Reception. "
            + _SAFETY_RULE + _UK_RULE +
            "Sentences have 6 words or fewer. "
            "You use repetition and rhythm so children can join in. "
            "You use only short, common, easy-to-sound-out words. "
            "Every section ends on a happy, calm note."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} simple, happy facts about '{topic}' for children aged 4 to 5. "
            f"One short sentence per fact, 6 words or fewer. "
            f"Use only words a 4-year-old knows."
            f"{subject_note}"
        ),
        expected_output=f"A list of {num_sections} very simple facts about {topic} for Reception children.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the facts, write a read-aloud story with exactly {num_sections} sections, "
            f"roughly {words} words each. Topic: {topic}. "
            f"Rules: sentences of 6 words or fewer. Only very common words. "
            f"Use repetition so children can join in. British English spelling only. "
            f"For each section add: "
            f"'cognitive_load' — always 0.05 (this is the very easiest writing). "
            f"'emotional_valence' — exactly one of: uplifting, neutral, cautionary, reflective, mixed. "
            f"'review_prompts' — exactly 2 talk-about questions a 4-year-old can answer out loud, "
            f"like 'Can you point to something red?' or 'What noise does it make?'"
        ),
        expected_output=(
            "A structured payload matching StructuredBlogPost, written for ages 4-5: "
            "6-word-max sentences, repetition, British English, cognitive_load 0.05, "
            "emotional_valence one of the 5 allowed values, review_prompts 2 talk-about questions."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="eyfs",
    display_name="Reception (ages 4–5)",
    min_age=4,
    order=-4,
    build_crew=_build,
    dl_worksheet_label="🖨️ Print Talk-About Sheet",

    # theme
    title="# 🌞 Story Time! 🌞\n### Tell me something you like and we will make a story to read together! 📖",
    topic_label="🧸 What do you like?",
    topic_placeholder="🐶 dogs   🚜 tractors   🌻 flowers   🦆 ducks...",
    gen_btn="📖 Make Our Story!",
    log_label="🤖 The story helpers are busy...",
    log_placeholder="Press the big button and watch!",
    preview_label="📖 Our Story!",

    # labels
    settings_label="⚙️ Teacher options",
    num_sections_label="📖 How many parts?",
    words_per_section_label="📝 How long each part?",
    dark_toggle_label="🌙 Night colours",
    history_title="### 📚 Read an old story",
    history_dd_label="Pick a story 👇",
    load_btn_label="📖 Open it!",
    dl_html_label="💾 Save Story",
    dl_md_label="📄 Save as Text",

    # Gradio CSS — warm, calm, no animation (Reception-friendly)
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
    body, .gradio-container {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECC7 100%) !important;
    }
    .gradio-container * { font-family: 'Nunito', sans-serif !important; }
    .gradio-container h1 {
        font-size: 3rem !important;
        font-weight: 900 !important;
        color: #E8871E !important;
    }
    button.primary {
        background: #FFB703 !important;
        color: #5C3A00 !important;
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        border-radius: 999px !important;
        padding: 16px 32px !important;
    }
    </style>
    """,

    # Report CSS — very large print for shared reading
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
        body { font-family: 'Nunito', sans-serif !important; background: #FFF8E1 !important; }
        h1 { font-size: 3rem; font-weight: 900; color: #E8871E !important; }
        h2 { font-size: 2rem; font-weight: 800; color: #BC6C25 !important; }
        p  { font-size: 1.6rem !important; line-height: 2.2 !important; font-weight: 700 !important; text-align: left !important; }
        .section-block { border: 3px solid #FFD89C !important; border-radius: 20px !important; padding: 24px !important; background: #FFFDF5 !important; }
        """,

    # messages
    empty_msg="Type something you like first! 🌻",
    error_msg=lambda e: f"\n\n🙈 Oh dear! Let's try again! ({e})",
    done_msg="\n\n🌟 Our story is ready! Well done! 🌟",
))

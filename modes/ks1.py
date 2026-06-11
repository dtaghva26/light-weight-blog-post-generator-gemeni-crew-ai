import os

from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

from logic.models import StructuredBlogPost
from modes.base import ModeDefinition
from modes.registry import register

load_dotenv()

_SAFETY_RULE = (
    "Everything you write will be read by primary school children in the UK. "
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

    words = min(words_per_section, 100)

    subject_note = (
        f" Frame the facts to support the Key Stage 1 {subject} programme of study "
        f"in the National Curriculum for England."
    ) if subject else ""

    researcher = Agent(
        role="KS1 Wow-Fact Finder",
        goal=f"Find {num_sections} wow-worthy facts about {topic} for children in Years 1 and 2.",
        backstory=(
            "You are a brilliant Key Stage 1 teacher in a UK primary school, teaching ages 5 to 7. "
            + _SAFETY_RULE + _UK_RULE +
            "You use simple words children are learning to read. "
            "Every sentence has 8 words or fewer. "
            "You make everything sound exciting and magical."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="KS1 Story Writer",
        goal="Turn wow facts into an exciting mini-story Years 1 and 2 children can read themselves.",
        backstory=(
            "You write for children aged 5 to 7 who are learning to read. "
            + _SAFETY_RULE + _UK_RULE +
            "Sentences have 8 words or fewer. "
            "You use mostly simple, decodable words, plus common exception words children learn in Years 1-2. "
            "You start sections with hooks like 'Did you know?' or 'Guess what!'. "
            "Every section feels like a little adventure."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} amazing facts about '{topic}' for children aged 5 to 7. "
            f"One short sentence per fact, 8 words or fewer, simple words only. "
            f"Start each fact with 'Did you know' or 'Guess what'."
            f"{subject_note}"
        ),
        expected_output=f"A list of {num_sections} short, exciting facts about {topic} for Years 1-2.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the facts, write an exciting story with exactly {num_sections} sections, "
            f"roughly {words} words each. Topic: {topic}. "
            f"Rules: sentences of 8 words or fewer. Simple words children aged 5-7 can read. "
            f"British English spelling only. Start each section with a hook like 'Did you know?'. "
            f"For each section add: "
            f"'cognitive_load' — a small number between 0.05 and 0.15. "
            f"'emotional_valence' — exactly one of: uplifting, neutral, cautionary, reflective, mixed. "
            f"'review_prompts' — exactly 2 simple questions a 6-year-old can answer, "
            f"like 'What was your favourite fact?'"
        ),
        expected_output=(
            "A structured payload matching StructuredBlogPost, written for ages 5-7: "
            "8-word-max sentences, simple vocabulary, British English, cognitive_load 0.05-0.15, "
            "emotional_valence one of the 5 allowed values, review_prompts 2 simple questions."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="ks1",
    display_name="Years 1–2 (ages 5–7)",
    min_age=5,
    order=-3,
    build_crew=_build,
    dl_worksheet_label="🖨️ Print Question Sheet",

    # theme
    title="# 🌈 Super Story Maker 🌈\n### Type what you love and I will make a story just for you! ✨",
    topic_label="✏️ What do you love?",
    topic_placeholder="🦕 dinosaurs   🚀 rockets   🐬 dolphins   🏰 castles...",
    gen_btn="✨ Make My Story!",
    log_label="🤖 The story robots are working...",
    log_placeholder="Click the button and watch the robots write your story!",
    preview_label="🎉 Your Story!",

    # labels
    settings_label="⚙️ Teacher options",
    num_sections_label="📖 How many parts?",
    words_per_section_label="📝 How long each part?",
    dark_toggle_label="🌙 Night Mode",
    history_title="### 📚 Read one of our old stories",
    history_dd_label="Pick a story 👇",
    load_btn_label="📖 Open it!",
    dl_html_label="💾 Save Story",
    dl_md_label="📄 Save as Text",

    # Gradio CSS — bright and playful, no constant animation
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
    body, .gradio-container {
        background: linear-gradient(135deg, #FFE0F5 0%, #E0F0FF 100%) !important;
    }
    .gradio-container * { font-family: 'Nunito', sans-serif !important; }
    .gradio-container h1 {
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        color: #FF4D8D !important;
        text-shadow: 2px 2px 0 #FFD700 !important;
    }
    button.primary {
        background: linear-gradient(135deg, #FF6B9D, #FF8E53) !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        border-radius: 999px !important;
        padding: 14px 28px !important;
    }
    </style>
    """,

    # Report CSS — large friendly print
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
        body { font-family: 'Nunito', sans-serif !important; background: #FFF5FB !important; }
        h1 { font-size: 2.6rem; font-weight: 900; color: #FF4D8D !important; }
        h2 { font-size: 1.8rem; font-weight: 800; color: #7C3AED !important; border-left: 8px solid #FFD700 !important; padding-left: 12px !important; }
        p  { font-size: 1.35rem !important; line-height: 2.0 !important; font-weight: 600 !important; text-align: left !important; }
        .section-block { border: 3px solid #FFD0EA !important; border-radius: 20px !important; padding: 24px !important; background: #FFFDF8 !important; }
        """,

    # messages
    empty_msg="Oops! Type something you love first! 🌈",
    error_msg=lambda e: f"\n\n😢 Uh-oh! The robot got muddled! Try again! ({e})",
    done_msg="\n\n🎉 Hooray! Your story is ready! 🌟",
))

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

    researcher = Agent(
        role="Fun Fact Finder",
        goal=f"Find {num_sections} WOW-worthy facts about {topic} that a 5-year-old will find magical.",
        backstory=(
            "You are a super-fun teacher who LOVES teaching little kids aged 5 to 7. "
            "You only use tiny, easy words — nothing longer than 2 syllables if you can help it. "
            "Every sentence is SHORT. MAX 8 words per sentence. "
            "You make everything sound exciting with lots of exclamation marks and 'WOW!' moments. "
            "You never say hard words. You always say things like 'really big', 'super fast', 'so cool'."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Magical Story Writer",
        goal="Turn fun facts into a magical, exciting mini-story a 5-year-old will love reading aloud.",
        backstory=(
            "You write stories for children aged 5 to 7. "
            "Your sentences are VERY short — never more than 8 words. "
            "You use only easy words a kindergartener knows. "
            "You make every section feel like an adventure. "
            "You start sections with exciting hooks like 'Did you know?' or 'Guess what!' or 'WOW!'. "
            "You use LOTS of exclamation marks because kids love excitement. "
            "No hard words. No long sentences. Only magic and fun!"
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} amazing, WOW-worthy facts about '{topic}' that a 5-year-old will love. "
            f"Use only tiny, easy words. Write each fact in ONE short sentence (max 8 words). "
            f"Start each fact with 'Did you know' or 'WOW' or 'Guess what'. Make it feel magical!"
        ),
        expected_output=f"A list of {num_sections} short, exciting, kid-friendly WOW facts about {topic}.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the fun facts, write a magical story with exactly {num_sections} sections, "
            f"roughly {words_per_section} words each. Topic: {topic}. "
            f"Rules: ONLY easy words. ONLY short sentences (max 8 words). "
            f"Start each section with 'WOW!', 'Did you know?', or 'Guess what!'. "
            f"Make every sentence sound exciting. Use exclamation marks often. "
            f"For each section add: "
            f"'cognitive_load' — always a very small number between 0.05 and 0.15 (this is easy-peasy writing!). "
            f"'emotional_valence' — exactly one of: uplifting, neutral, cautionary, reflective, mixed. "
            f"'review_prompts' — exactly 2 super simple questions a 5-year-old can answer, like 'What was your favourite part?'"
        ),
        expected_output=(
            "A structured payload matching StructuredBlogPost, written for ages 5-7 with only simple words, "
            "very short sentences, and exciting tone. "
            "cognitive_load between 0.05–0.15, emotional_valence one of the 5 allowed values, "
            "review_prompts 2 very simple kid-friendly questions."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


register(ModeDefinition(
    crew_type="kids_mode",
    display_name="Kids Mode",
    min_age=0,
    order=0,
    build_crew=_build,

    # theme
    title="# 🦄✨ STORY MAGIC MACHINE ✨🦄\n### Tell me what you LOVE and I'll make an AMAZING story JUST FOR YOU! 🎉🎈🌈",
    topic_label="🌈 What do you love? Type it here! 👇",
    topic_placeholder="🦕 dinosaurs   🚀 rockets   🐬 dolphins   🦁 lions   🌈 rainbows   🍕 pizza...",
    gen_btn="🪄✨ MAKE MY STORY! ✨🪄",
    log_label="🤖💫 The story robots are working RIGHT NOW...",
    log_placeholder="🌟 Click the magic button and watch the robots make your story! 🌟",
    preview_label="🎉🥳 YOUR SUPER AMAZING STORY IS HERE! 🥳🎉",

    # labels
    settings_label="⚙️ More fun options!",
    num_sections_label="📖 How many parts in your story?",
    words_per_section_label="📝 How long each part?",
    dark_toggle_label="🌙 Night Mode",
    history_title="### 📚 Read one of your old stories!",
    history_dd_label="Pick an old story 👇",
    load_btn_label="📖 Open it!",
    dl_html_label="💾 Save Story",
    dl_md_label="📄 Save as Text",

    # Gradio CSS
    gradio_css="""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap');
    @keyframes floatBg {
      0%, 100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }
    @keyframes wobble {
      0%, 100% { transform: rotate(-1deg) scale(1); }
      50% { transform: rotate(1deg) scale(1.015); }
    }
    body, .gradio-container {
        background: linear-gradient(-45deg, #FFE0F5, #E0F0FF, #E8FFE0, #FFF5D6, #F5E0FF) !important;
        background-size: 400% 400% !important;
        animation: floatBg 10s ease infinite !important;
    }
    .gradio-container * { font-family: 'Nunito', sans-serif !important; }
    .gradio-container h1 {
        font-size: 2.8rem !important;
        font-weight: 900 !important;
        color: #FF4D8D !important;
        text-shadow: 3px 3px 0 #FFD700 !important;
        animation: wobble 2.5s ease-in-out infinite !important;
        display: inline-block !important;
    }
    .gradio-container h3 {
        font-weight: 900 !important;
        color: #7C3AED !important;
        font-size: 1.3rem !important;
    }
    button.primary {
        background: linear-gradient(135deg, #FF6B9D, #FF8E53) !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        border-radius: 999px !important;
        padding: 14px 28px !important;
        border: 3px solid #FFD700 !important;
        box-shadow: 0 6px 20px rgba(255,107,157,0.4) !important;
        letter-spacing: 0.02em !important;
        animation: wobble 3s ease-in-out infinite !important;
    }
    </style>
    """,

    # Report CSS
    report_css="""
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap');
        @keyframes floatBg {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0px) rotate(-1deg); }
            50% { transform: translateY(-8px) rotate(1deg); }
        }
        body {
            font-family: 'Nunito', sans-serif !important;
            background: linear-gradient(-45deg, #FFE0F5, #E0F0FF, #E8FFE0, #FFF5D6, #F5E0FF) !important;
            background-size: 400% 400% !important;
            animation: floatBg 10s ease infinite !important;
        }
        .container {
            border-radius: 28px !important;
            box-shadow: 0 0 0 4px #FF8AC8, 0 20px 60px rgba(255,107,157,0.18) !important;
            background: rgba(255,255,255,0.94) !important;
        }
        header { border-bottom: 3px dashed #FFD0EA !important; }
        h1 {
            font-family: 'Nunito', sans-serif !important;
            font-size: 2.8rem !important;
            font-weight: 900 !important;
            color: #FF4D8D !important;
            text-shadow: 3px 3px 0 #FFD700, 5px 5px 0 rgba(255,107,157,0.2) !important;
            animation: bounce 2.2s ease-in-out infinite !important;
            display: inline-block !important;
        }
        h2 {
            font-family: 'Nunito', sans-serif !important;
            font-size: 1.7rem !important;
            font-weight: 800 !important;
            color: #7C3AED !important;
            border-left: 8px solid #FFD700 !important;
            padding: 6px 14px !important;
            border-radius: 0 12px 12px 0 !important;
            background: linear-gradient(90deg, rgba(255,215,0,0.18) 0%, transparent 100%) !important;
        }
        p {
            font-family: 'Nunito', sans-serif !important;
            font-size: 1.25rem !important;
            line-height: 2.0 !important;
            font-weight: 600 !important;
            text-align: left !important;
        }
        .author { font-family: 'Nunito', sans-serif !important; color: #FF6B9D !important; font-weight: 900 !important; font-size: 1.15rem !important; }
        .section-block {
            border-radius: 22px !important;
            border: 3px solid #FFD0EA !important;
            background: linear-gradient(135deg, #FFFBF0 0%, #F9F0FF 100%) !important;
            box-shadow: 0 6px 18px rgba(124,58,237,0.08) !important;
            padding: 24px !important;
            transition: transform 0.25s ease, box-shadow 0.25s ease !important;
        }
        .section-block:hover { transform: translateY(-4px) scale(1.01) !important; box-shadow: 0 12px 30px rgba(255,107,157,0.18) !important; }
        .section-block:nth-child(1) { border-color: #FFD0EA !important; background: linear-gradient(135deg, #FFF5FB, #FFF0FF) !important; }
        .section-block:nth-child(2) { border-color: #C7E8FF !important; background: linear-gradient(135deg, #F0F8FF, #EDF5FF) !important; }
        .section-block:nth-child(3) { border-color: #C8F5D8 !important; background: linear-gradient(135deg, #F0FFF6, #EDFFF6) !important; }
        .section-block:nth-child(4) { border-color: #FFE8C0 !important; background: linear-gradient(135deg, #FFFBF0, #FFFAF0) !important; }
        .section-block:nth-child(5) { border-color: #E0CCFF !important; background: linear-gradient(135deg, #F8F0FF, #F5EDFF) !important; }
        .cog-load-label { font-family: 'Nunito', sans-serif !important; font-size: 0.82rem !important; font-weight: 800 !important; color: #7C3AED !important; text-transform: none !important; letter-spacing: 0 !important; }
        .cog-load-track { height: 10px !important; border-radius: 5px !important; }
        .cog-load-fill { background: linear-gradient(90deg, #6BCB77 0%, #FFD700 55%, #FF6B9D 100%) !important; }
        .valence-badge { font-family: 'Nunito', sans-serif !important; font-size: 0.85rem !important; font-weight: 800 !important; padding: 4px 14px !important; border-radius: 999px !important; }
        .review-schedule { border-top: 4px dashed #FFD700 !important; padding-top: 36px !important; margin-top: 52px !important; }
        .review-schedule h3 { font-family: 'Nunito', sans-serif !important; font-size: 1.6rem !important; font-weight: 900 !important; color: #FF4D8D !important; }
        .review-panel { border: 3px solid #FFD0EA !important; border-radius: 18px !important; background: linear-gradient(135deg, #FFFDE7, #FFF9F0) !important; box-shadow: 0 4px 12px rgba(255,215,0,0.15) !important; }
        .review-panel-title { font-family: 'Nunito', sans-serif !important; font-size: 0.9rem !important; font-weight: 900 !important; color: #7C3AED !important; }
        .review-panel-date { font-family: 'Nunito', sans-serif !important; font-weight: 700 !important; }
        .review-panel li { font-family: 'Nunito', sans-serif !important; font-size: 1rem !important; font-weight: 700 !important; line-height: 1.6 !important; }
        .review-section-label { font-family: 'Nunito', sans-serif !important; font-weight: 800 !important; color: #FF6B9D !important; text-transform: none !important; letter-spacing: 0 !important; font-size: 0.8rem !important; }
        """,

    # messages
    empty_msg="Oops! 🙈 Type something you love first! 🌈",
    error_msg=lambda e: f"\n\n😢 Uh-oh! The robot got confused! Try again! 🔄 ({e})",
    done_msg="\n\n🎉🥳 YAY! Your AMAZING story is ready! You're so awesome! 🌟⭐🦄",
))

import html
import re
from pathlib import Path
import gradio as gr

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

from logic.crew import run_crew_streaming
from logic.renderer import create_html, blog_to_markdown
from logic.reports import save_report, list_reports, load_report_html, load_report_json


_MODE_MAP = {
    "Absolutist": "absolutist",
    "Multiplist": "multiplist",
    "Evaluativist": "evaluativist",
    "Master Thinker": "master",
}

_EMPTY_MSG = {
    "absolutist": "Please type something! 🐣",
    "multiplist": "Please enter a topic to explore.",
    "evaluativist": "Please enter a topic.",
    "master": "Please provide a subject for analysis.",
}

_ERROR_MSG = {
    "absolutist": lambda e: f"\n\n⚠️ Uh-oh! Something went wrong: {e}",
    "multiplist": lambda e: f"\n\n⚠️ Couldn't collect perspectives: {e}",
    "evaluativist": lambda e: f"\n\n⚠ ERROR: {e}",
    "master": lambda e: f"\n\n⚠ Analysis failed: {e}",
}

_DONE_MSG = {
    "absolutist": "\n\n🎉 Your story is ready! Great job! 🌟",
    "multiplist": "\n\n✅ Perspectives collected!",
    "evaluativist": "\n\n✅ Done!",
    "master": "\n\n✅ Analysis complete.",
}


def _wrap_preview(html_str: str) -> str:
    escaped = html.escape(html_str, quote=True)
    return (
        f'<iframe srcdoc="{escaped}" '
        f'style="width:100%;height:600px;border:none;border-radius:8px;" '
        f'sandbox="allow-same-origin"></iframe>'
    )


def _report_choices() -> list[str]:
    reports = list_reports()
    return [f"{r['timestamp']} — {r['title'][:60]}" for r in reports]


def _choice_to_path(choice: str) -> str | None:
    reports = list_reports()
    choices = _report_choices()
    if choice in choices:
        idx = choices.index(choice)
        return reports[idx]["path"]
    return None


def generate(audience: str, topic: str, num_sections: int, words_per_section: int, dark_mode: bool):
    crew_type = _MODE_MAP.get(audience, "evaluativist")

    if not topic.strip():
        yield _EMPTY_MSG[crew_type], None, None, None, gr.update()
        return

    log_lines: list[str] = []
    blog_data = None

    for item in run_crew_streaming(topic.strip(), int(num_sections), int(words_per_section), crew_type=crew_type):
        if isinstance(item, tuple) and item[0] == "RESULT":
            blog_data = item[1]
        elif isinstance(item, tuple) and item[0] == "ERROR":
            err_msg = "\n".join(log_lines) + _ERROR_MSG[crew_type](item[1])
            yield err_msg, None, None, None, gr.update()
            return
        else:
            clean = _ANSI_RE.sub("", str(item)).strip()
            if clean:
                log_lines.append(clean)
            yield "\n".join(log_lines), None, None, None, gr.update()

    if blog_data:
        html_str = create_html(blog_data, dark=dark_mode, audience=crew_type)
        html_path = save_report(blog_data, html_str, audience=crew_type)

        md_str = blog_to_markdown(blog_data)
        md_path = str(html_path).replace(".html", ".md")
        Path(md_path).write_text(md_str, encoding="utf-8")

        preview_html = _wrap_preview(html_str)
        updated_choices = _report_choices()

        done_msg = "\n".join(log_lines) + _DONE_MSG[crew_type]
        yield done_msg, preview_html, str(html_path), md_path, gr.update(choices=updated_choices)


def load_history(choice: str, dark_mode: bool):
    if not choice:
        return None, None, None
    path = _choice_to_path(choice)
    if not path:
        return None, None, None
    blog_data = load_report_json(path)
    audience = blog_data.get("audience", "evaluativist")
    html_str = create_html(blog_data, dark=dark_mode, audience=audience) if blog_data else load_report_html(path)
    md_path = path.replace(".html", ".md")
    if blog_data:
        md_str = blog_to_markdown(blog_data)
        Path(md_path).write_text(md_str, encoding="utf-8")
    return _wrap_preview(html_str), path, md_path if Path(md_path).exists() else None


def rerender_dark(dl_html_path, dark_mode: bool):
    if not dl_html_path:
        return None
    path = dl_html_path if isinstance(dl_html_path, str) else dl_html_path.name
    blog_data = load_report_json(path)
    if not blog_data:
        return _wrap_preview(load_report_html(path))
    audience = blog_data.get("audience", "evaluativist")
    return _wrap_preview(create_html(blog_data, dark=dark_mode, audience=audience))


def update_ui(audience: str) -> dict:
    from frontend.gradio.themes import ABSOLUTIST_THEME, MULTIPLIST_THEME, EVALUATIVIST_THEME, MASTER_THEME

    theme_map = {
        "Absolutist": ABSOLUTIST_THEME,
        "Multiplist": MULTIPLIST_THEME,
        "Evaluativist": EVALUATIVIST_THEME,
        "Master Thinker": MASTER_THEME,
    }
    theme = theme_map.get(audience, EVALUATIVIST_THEME)

    if audience == "Absolutist":
        style = """
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
    """
    elif audience == "Multiplist":
        style = """
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
    """
    elif audience == "Master Thinker":
        style = """
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
    """
    else:
        style = "<style></style>"

    labels = {
        "Absolutist": {
            "settings_label": "⚙️ More options (for curious kids!)",
            "num_sections_label": "📖 How many chapters?",
            "words_per_section_label": "📝 How long each chapter?",
            "dark_toggle_label": "🌙 Night Mode",
            "history_title": "### 📚 Read an old story",
            "history_dd_label": "Pick a story you made before",
            "load_btn_label": "📖 Open!",
            "dl_html_label": "💾 Save as Web Page",
            "dl_md_label": "📄 Save as Text File",
        },
        "Multiplist": {
            "settings_label": "More options",
            "num_sections_label": "How many perspectives?",
            "words_per_section_label": "Length per perspective",
            "dark_toggle_label": "Dark mode",
            "history_title": "### Past Explorations",
            "history_dd_label": "Load a past exploration",
            "load_btn_label": "Open",
            "dl_html_label": "Download HTML",
            "dl_md_label": "Download Markdown",
        },
        "Evaluativist": {
            "settings_label": "Advanced settings",
            "num_sections_label": "Number of sections",
            "words_per_section_label": "Words per section",
            "dark_toggle_label": "Dark mode (report)",
            "history_title": "### Past Reports",
            "history_dd_label": "Load a past report",
            "load_btn_label": "Load",
            "dl_html_label": "Download HTML",
            "dl_md_label": "Download Markdown",
        },
        "Master Thinker": {
            "settings_label": "Analysis parameters",
            "num_sections_label": "Number of sections",
            "words_per_section_label": "Words per section",
            "dark_toggle_label": "Dark mode",
            "history_title": "### Prior Analyses",
            "history_dd_label": "Load a prior analysis",
            "load_btn_label": "Load",
            "dl_html_label": "Export HTML",
            "dl_md_label": "Export Markdown",
        },
    }
    lbl = labels.get(audience, labels["Evaluativist"])

    return {
        "kids_style": style,
        "title": theme["title"],
        "topic_label": theme["topic_label"],
        "topic_placeholder": theme["topic_placeholder"],
        "gen_btn": theme["gen_btn"],
        "log_label": theme["log_label"],
        "log_placeholder": theme["log_placeholder"],
        "preview_label": theme["preview_label"],
        "settings_label": lbl["settings_label"],
        "num_sections_label": lbl["num_sections_label"],
        "words_per_section_label": lbl["words_per_section_label"],
        "dark_toggle_label": lbl["dark_toggle_label"],
        "history_title": lbl["history_title"],
        "history_dd_label": lbl["history_dd_label"],
        "load_btn_label": lbl["load_btn_label"],
        "dl_html_label": lbl["dl_html_label"],
        "dl_md_label": lbl["dl_md_label"],
    }

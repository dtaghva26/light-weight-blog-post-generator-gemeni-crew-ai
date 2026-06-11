import html
import os
import re
from pathlib import Path
import gradio as gr

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

from logic.crew import run_crew_streaming
from logic.renderer import create_html, blog_to_markdown, create_worksheet_html
from logic.reports import save_report, list_reports, load_report_html, load_report_json
from logic.safety import check_topic, log_blocked
from logic.logger import get_logger

_log = get_logger("handlers")

# ── Classroom configuration ────────────────────────────────────────────────────

YEAR_GROUPS = {
    "Reception (ages 4–5)": "eyfs",
    "Years 1–2 (ages 5–7)": "ks1",
    "Years 3–4 (ages 7–9)": "lks2",
    "Years 5–6 (ages 9–11)": "uks2",
}

SUBJECTS = [
    "Any topic", "Science", "History", "Geography", "English",
    "Computing", "Art & Design", "PSHE",
]

_BLOCKED_MSG = (
    "That's not a topic for our stories — let's pick a different one! 🌈\n"
    "Ask your teacher if you're not sure what to choose."
)

_REDUCE_MOTION_STYLE = (
    "<style>*, *::before, *::after { animation: none !important; transition: none !important; }</style>"
)


def _teacher_pin() -> str:
    # Documented in readme.md — set TEACHER_PIN in .env; defaults to 0000.
    return os.getenv("TEACHER_PIN", "0000")


def pupil_mode_names() -> list[str]:
    from modes.registry import all_modes
    return [m.display_name for m in all_modes() if not m.teacher_only]


def all_mode_names() -> list[str]:
    from modes.registry import all_modes
    return [m.display_name for m in all_modes()]


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _write_worksheet(blog_data: dict, html_path: str) -> str:
    ws_path = str(html_path).replace(".html", "_worksheet.html")
    Path(ws_path).write_text(create_worksheet_html(blog_data), encoding="utf-8")
    return ws_path


# ── Generation ────────────────────────────────────────────────────────────────

def generate(audience: str, topic: str, subject: str, num_sections: int,
             words_per_section: int, dark_mode: bool, easy_font: bool,
             large_print: bool, reduce_motion: bool):
    from modes.registry import by_display_name
    mode = by_display_name(audience)

    if not topic.strip():
        _log.debug("generate_skipped  audience=%s  reason=empty_topic", audience)
        yield mode.empty_msg, None, None, None, None, gr.update()
        return

    ok, reason = check_topic(topic)
    if not ok:
        log_blocked(topic, mode.crew_type, reason)
        yield _BLOCKED_MSG, None, None, None, None, gr.update()
        return

    subject_arg = subject if subject and subject != "Any topic" else None

    _log.info("generate_requested  audience=%s  topic=%r  subject=%s  sections=%d  words=%d",
              audience, topic.strip(), subject_arg, int(num_sections), int(words_per_section))

    log_lines: list[str] = []
    blog_data = None

    for item in run_crew_streaming(topic.strip(), int(num_sections), int(words_per_section),
                                   crew_type=mode.crew_type, subject=subject_arg):
        if isinstance(item, tuple) and item[0] == "RESULT":
            blog_data = item[1]
        elif isinstance(item, tuple) and item[0] == "ERROR":
            err_msg = "\n".join(log_lines) + mode.error_msg(item[1])
            yield err_msg, None, None, None, None, gr.update()
            return
        else:
            clean = _ANSI_RE.sub("", str(item)).strip()
            if clean:
                log_lines.append(clean)
            yield "\n".join(log_lines), None, None, None, None, gr.update()

    if blog_data:
        html_str = create_html(blog_data, dark=dark_mode, audience=mode.crew_type,
                               easy_font=easy_font, large_print=large_print,
                               reduce_motion=reduce_motion)
        html_path = save_report(blog_data, html_str, audience=mode.crew_type)

        md_str = blog_to_markdown(blog_data)
        md_path = str(html_path).replace(".html", ".md")
        Path(md_path).write_text(md_str, encoding="utf-8")

        ws_path = _write_worksheet(blog_data, html_path)

        preview_html = _wrap_preview(html_str)
        updated_choices = _report_choices()

        done_msg = "\n".join(log_lines) + mode.done_msg
        yield done_msg, preview_html, str(html_path), md_path, ws_path, gr.update(choices=updated_choices)


# ── History / re-rendering ────────────────────────────────────────────────────

def load_history(choice: str, dark_mode: bool, easy_font: bool,
                 large_print: bool, reduce_motion: bool):
    if not choice:
        return None, None, None, None
    _log.info("history_load  choice=%r  dark=%s", choice, dark_mode)
    path = _choice_to_path(choice)
    if not path:
        return None, None, None, None
    blog_data = load_report_json(path)
    audience = blog_data.get("audience", "evaluativist")
    if blog_data:
        html_str = create_html(blog_data, dark=dark_mode, audience=audience,
                               easy_font=easy_font, large_print=large_print,
                               reduce_motion=reduce_motion)
    else:
        html_str = load_report_html(path)
    md_path = path.replace(".html", ".md")
    ws_path = None
    if blog_data:
        md_str = blog_to_markdown(blog_data)
        Path(md_path).write_text(md_str, encoding="utf-8")
        ws_path = _write_worksheet(blog_data, path)
    return _wrap_preview(html_str), path, md_path if Path(md_path).exists() else None, ws_path


def rerender_view(dl_html_path, dark_mode: bool, easy_font: bool,
                  large_print: bool, reduce_motion: bool):
    """Re-render the currently displayed report when any view toggle changes."""
    if not dl_html_path:
        return None
    path = dl_html_path if isinstance(dl_html_path, str) else dl_html_path.name
    blog_data = load_report_json(path)
    if not blog_data:
        return _wrap_preview(load_report_html(path))
    audience = blog_data.get("audience", "evaluativist")
    return _wrap_preview(create_html(blog_data, dark=dark_mode, audience=audience,
                                     easy_font=easy_font, large_print=large_print,
                                     reduce_motion=reduce_motion))


def on_motion_toggle(dl_html_path, dark_mode: bool, easy_font: bool,
                     large_print: bool, reduce_motion: bool):
    """Reduce motion affects both the live Gradio UI and the rendered report."""
    motion_style = _REDUCE_MOTION_STYLE if reduce_motion else "<style></style>"
    return motion_style, rerender_view(dl_html_path, dark_mode, easy_font, large_print, reduce_motion)


# ── Class setup (replaces the age gate) ───────────────────────────────────────

def on_class_setup(year_group):
    from modes.registry import get as get_mode
    crew_type = YEAR_GROUPS.get(year_group, "lks2")
    mode_name = get_mode(crew_type).display_name
    _log.info("class_setup  year_group=%r  routed_to=%s", year_group, mode_name)
    ui = update_ui(mode_name)
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(value=mode_name),
        ui["kids_style"],
        ui["title"],
        gr.update(label=ui["topic_label"], placeholder=ui["topic_placeholder"]),
        gr.update(value=ui["gen_btn"]),
        gr.update(label=ui["log_label"], placeholder=ui["log_placeholder"]),
        gr.update(label=ui["preview_label"]),
        gr.update(label=ui["settings_label"]),
        gr.update(label=ui["num_sections_label"]),
        gr.update(label=ui["words_per_section_label"]),
        gr.update(label=ui["dark_toggle_label"]),
        ui["history_title"],
        gr.update(label=ui["history_dd_label"]),
        gr.update(value=ui["load_btn_label"]),
        gr.update(label=ui["dl_html_label"]),
        gr.update(label=ui["dl_md_label"]),
        gr.update(label=ui["dl_worksheet_label"]),
    )


# ── Teacher unlock ────────────────────────────────────────────────────────────

def unlock_teacher(pin: str):
    """Correct PIN reveals the adult modes, advanced settings and history."""
    if (pin or "").strip() == _teacher_pin():
        _log.info("teacher_unlocked")
        return (
            gr.update(choices=all_mode_names()),
            gr.update(visible=True),
            gr.update(visible=True),
            "✅ Teacher mode unlocked.",
            gr.update(value=""),
        )
    _log.warning("teacher_unlock_failed")
    return (
        gr.update(),
        gr.update(),
        gr.update(),
        "❌ Incorrect PIN.",
        gr.update(value=""),
    )


# ── Per-mode UI labels ────────────────────────────────────────────────────────

def update_ui(audience: str) -> dict:
    from modes.registry import by_display_name
    mode = by_display_name(audience)
    return {
        "kids_style":              mode.gradio_css,
        "title":                   mode.title,
        "topic_label":             mode.topic_label,
        "topic_placeholder":       mode.topic_placeholder,
        "gen_btn":                 mode.gen_btn,
        "log_label":               mode.log_label,
        "log_placeholder":         mode.log_placeholder,
        "preview_label":           mode.preview_label,
        "settings_label":          mode.settings_label,
        "num_sections_label":      mode.num_sections_label,
        "words_per_section_label": mode.words_per_section_label,
        "dark_toggle_label":       mode.dark_toggle_label,
        "history_title":           mode.history_title,
        "history_dd_label":        mode.history_dd_label,
        "load_btn_label":          mode.load_btn_label,
        "dl_html_label":           mode.dl_html_label,
        "dl_md_label":             mode.dl_md_label,
        "dl_worksheet_label":      mode.dl_worksheet_label,
    }

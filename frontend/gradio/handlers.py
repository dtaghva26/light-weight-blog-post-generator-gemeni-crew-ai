import html
import re
from pathlib import Path
import gradio as gr

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

from logic.crew import run_crew_streaming
from logic.renderer import create_html, blog_to_markdown
from logic.reports import save_report, list_reports, load_report_html, load_report_json


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
    from modes.registry import by_display_name
    mode = by_display_name(audience)

    if not topic.strip():
        yield mode.empty_msg, None, None, None, gr.update()
        return

    log_lines: list[str] = []
    blog_data = None

    for item in run_crew_streaming(topic.strip(), int(num_sections), int(words_per_section), crew_type=mode.crew_type):
        if isinstance(item, tuple) and item[0] == "RESULT":
            blog_data = item[1]
        elif isinstance(item, tuple) and item[0] == "ERROR":
            err_msg = "\n".join(log_lines) + mode.error_msg(item[1])
            yield err_msg, None, None, None, gr.update()
            return
        else:
            clean = _ANSI_RE.sub("", str(item)).strip()
            if clean:
                log_lines.append(clean)
            yield "\n".join(log_lines), None, None, None, gr.update()

    if blog_data:
        html_str = create_html(blog_data, dark=dark_mode, audience=mode.crew_type)
        html_path = save_report(blog_data, html_str, audience=mode.crew_type)

        md_str = blog_to_markdown(blog_data)
        md_path = str(html_path).replace(".html", ".md")
        Path(md_path).write_text(md_str, encoding="utf-8")

        preview_html = _wrap_preview(html_str)
        updated_choices = _report_choices()

        done_msg = "\n".join(log_lines) + mode.done_msg
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


def age_to_mode(age: int) -> str:
    from modes.registry import all_modes
    candidates = [m for m in all_modes() if m.min_age <= age]
    return candidates[-1].display_name if candidates else all_modes()[0].display_name


def on_age_submit(age):
    mode_name = age_to_mode(int(age) if age else 18)
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
    )


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
    }

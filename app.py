import html
import time
from pathlib import Path

import gradio as gr

import agents
import utils


# ---------------------------------------------------------------------------
# Core generate function (streaming generator)
# ---------------------------------------------------------------------------

def generate(topic: str, num_sections: int, words_per_section: int, dark_mode: bool):
    if not topic.strip():
        yield "Please enter a topic.", None, None, None, gr.update()
        return

    log_lines: list[str] = []
    blog_data = None

    for item in agents.run_crew_streaming(topic.strip(), int(num_sections), int(words_per_section)):
        if isinstance(item, tuple) and item[0] == "RESULT":
            blog_data = item[1]
        elif isinstance(item, tuple) and item[0] == "ERROR":
            err_msg = "\n".join(log_lines) + f"\n\n⚠ ERROR: {item[1]}"
            yield err_msg, None, None, None, gr.update()
            return
        else:
            log_lines.append(str(item))
            yield "\n".join(log_lines), None, None, None, gr.update()

    if blog_data:
        html_str = agents.create_html(blog_data, dark=dark_mode)
        html_path = utils.save_report(blog_data, html_str)

        md_str = utils.blog_to_markdown(blog_data)
        md_path = str(html_path).replace(".html", ".md")
        Path(md_path).write_text(md_str, encoding="utf-8")

        preview_html = _wrap_preview(html_str)
        updated_choices = _report_choices()

        yield (
            "\n".join(log_lines) + "\n\n✅ Done!",
            preview_html,
            str(html_path),
            md_path,
            gr.update(choices=updated_choices),
        )


def _wrap_preview(html_str: str) -> str:
    escaped = html.escape(html_str, quote=True)
    return (
        f'<iframe srcdoc="{escaped}" '
        f'style="width:100%;height:600px;border:none;border-radius:8px;" '
        f'sandbox="allow-same-origin"></iframe>'
    )


def _report_choices() -> list[str]:
    reports = utils.list_reports()
    return [f"{r['timestamp']} — {r['title'][:60]}" for r in reports]


def _choice_to_path(choice: str) -> str | None:
    reports = utils.list_reports()
    choices = _report_choices()
    if choice in choices:
        idx = choices.index(choice)
        return reports[idx]["path"]
    return None


# ---------------------------------------------------------------------------
# History loader
# ---------------------------------------------------------------------------

def load_history(choice: str, dark_mode: bool):
    if not choice:
        return None, None, None
    path = _choice_to_path(choice)
    if not path:
        return None, None, None
    blog_data = utils.load_report_json(path)
    html_str = agents.create_html(blog_data, dark=dark_mode) if blog_data else utils.load_report_html(path)
    md_path = path.replace(".html", ".md")
    if blog_data:
        md_str = utils.blog_to_markdown(blog_data)
        Path(md_path).write_text(md_str, encoding="utf-8")
    return _wrap_preview(html_str), path, md_path if Path(md_path).exists() else None


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    theme=gr.themes.Soft(),
    title="Multi-Agent Blog Generator",
    css="""
    .generate-btn { font-size: 1rem !important; }
    #log-box textarea { font-family: monospace; font-size: 0.8rem; }
    """,
) as demo:

    gr.Markdown("# Multi-Agent Blog Generator\nPowered by **CrewAI** + **Google Gemini**")

    with gr.Row():
        with gr.Column(scale=3):
            topic_input = gr.Textbox(
                label="Blog Topic",
                value="AI",
                placeholder="e.g. quantum computing, climate tech, Web3...",
                lines=1,
            )
        with gr.Column(scale=1):
            gen_btn = gr.Button("Generate", variant="primary", elem_classes="generate-btn")

    with gr.Accordion("Advanced settings", open=False):
        with gr.Row():
            num_sections = gr.Slider(2, 5, value=3, step=1, label="Number of sections")
            words_per_section = gr.Slider(100, 400, value=200, step=50, label="Words per section")

    dark_toggle = gr.Checkbox(label="Dark mode (report)", value=False)

    with gr.Row():
        with gr.Column(scale=1):
            log_box = gr.Textbox(
                label="Agent Activity",
                lines=20,
                interactive=False,
                elem_id="log-box",
                autoscroll=True,
                placeholder="Agent log will appear here once you click Generate...",
            )
        with gr.Column(scale=2):
            html_preview = gr.HTML(label="Report Preview")

    with gr.Row():
        dl_html = gr.File(label="Download HTML", interactive=False)
        dl_md = gr.File(label="Download Markdown", interactive=False)

    gr.Markdown("---")
    gr.Markdown("### Past Reports")
    with gr.Row():
        history_dd = gr.Dropdown(
            label="Load a past report",
            choices=_report_choices(),
            interactive=True,
            scale=4,
        )
        load_btn = gr.Button("Load", scale=1)

    # -----------------------------------------------------------------------
    # Event wiring
    # -----------------------------------------------------------------------

    gen_btn.click(
        fn=generate,
        inputs=[topic_input, num_sections, words_per_section, dark_toggle],
        outputs=[log_box, html_preview, dl_html, dl_md, history_dd],
    )

    load_btn.click(
        fn=load_history,
        inputs=[history_dd, dark_toggle],
        outputs=[html_preview, dl_html, dl_md],
    )

    # Re-render preview when dark mode is toggled (if a report is already loaded)
    def rerender_dark(dl_html_path, dark_mode):
        if not dl_html_path:
            return None
        path = dl_html_path if isinstance(dl_html_path, str) else dl_html_path.name
        blog_data = utils.load_report_json(path)
        if not blog_data:
            return _wrap_preview(utils.load_report_html(path))
        return _wrap_preview(agents.create_html(blog_data, dark=dark_mode))

    dark_toggle.change(
        fn=rerender_dark,
        inputs=[dl_html, dark_toggle],
        outputs=[html_preview],
    )


if __name__ == "__main__":
    demo.launch()
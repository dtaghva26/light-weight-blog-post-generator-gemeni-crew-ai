import html
from pathlib import Path

import gradio as gr

import agents
import utils


# ---------------------------------------------------------------------------
# Kid-friendly HTML report wrapper
# ---------------------------------------------------------------------------

_KID_FONT_INJECT = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
body { font-family: 'Poppins', sans-serif !important; }
h1 { font-size: 2.4rem; font-weight: 800; color: #FF6B9D; }
h2 { font-size: 1.6rem; font-weight: 700; color: #7888BF; border-left: 6px solid #FFE87C; padding-left: 12px; margin-top: 2rem; }
p  { font-size: 1.05rem; line-height: 1.8; }
.author { color: #C5EADD; font-weight: 600; font-size: 1rem; }
</style>
"""


def _kid_html(blog_data: dict, dark: bool) -> str:
    base = agents.create_html(blog_data, dark=dark)
    return base.replace("</head>", _KID_FONT_INJECT + "</head>", 1)


# ---------------------------------------------------------------------------
# Core generate function (streaming generator)
# ---------------------------------------------------------------------------

def generate(topic: str, num_sections: int, words_per_section: int, dark_mode: bool):
    if not topic.strip():
        yield "Please type something! 🐣", None, None, None, gr.update()
        return

    log_lines: list[str] = []
    blog_data = None

    for item in agents.run_crew_streaming(topic.strip(), int(num_sections), int(words_per_section)):
        if isinstance(item, tuple) and item[0] == "RESULT":
            blog_data = item[1]
        elif isinstance(item, tuple) and item[0] == "ERROR":
            err_msg = "\n".join(log_lines) + f"\n\n⚠️ Uh-oh! Something went wrong: {item[1]}"
            yield err_msg, None, None, None, gr.update()
            return
        else:
            log_lines.append(str(item))
            yield "\n".join(log_lines), None, None, None, gr.update()

    if blog_data:
        html_str = _kid_html(blog_data, dark=dark_mode)
        html_path = utils.save_report(blog_data, html_str)

        md_str = utils.blog_to_markdown(blog_data)
        md_path = str(html_path).replace(".html", ".md")
        Path(md_path).write_text(md_str, encoding="utf-8")

        preview_html = _wrap_preview(html_str)
        updated_choices = _report_choices()

        yield (
            "\n".join(log_lines) + "\n\n🎉 Your story is ready! Great job! 🌟",
            preview_html,
            str(html_path),
            md_path,
            gr.update(choices=updated_choices),
        )


def _wrap_preview(html_str: str) -> str:
    escaped = html.escape(html_str, quote=True)
    return (
        f'<iframe srcdoc="{escaped}" '
        f'style="width:100%;height:600px;border:none;border-radius:16px;" '
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
    html_str = _kid_html(blog_data, dark=dark_mode) if blog_data else utils.load_report_html(path)
    md_path = path.replace(".html", ".md")
    if blog_data:
        md_str = utils.blog_to_markdown(blog_data)
        Path(md_path).write_text(md_str, encoding="utf-8")
    return _wrap_preview(html_str), path, md_path if Path(md_path).exists() else None


# ---------------------------------------------------------------------------
# Gradio UI — Kid Edition
# ---------------------------------------------------------------------------

KID_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

* { font-family: 'Poppins', sans-serif !important; }

/* Gradient background */
.gradio-container {
    background: linear-gradient(135deg, #FFF0F5 0%, #EEF4FF 50%, #F0FFF8 100%) !important;
}

/* Big title */
.kid-title { text-align: center; }
.kid-title h1 {
    font-size: 2.6rem !important;
    font-weight: 800 !important;
    color: #FF6B9D !important;
    letter-spacing: -0.5px;
    margin-bottom: 0 !important;
}
.kid-title p {
    font-size: 1.1rem;
    color: #7888BF;
    font-weight: 600;
    margin-top: 4px !important;
}

/* Generate button */
.make-story-btn button {
    background: linear-gradient(135deg, #4CAF50, #8BC34A) !important;
    color: white !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    border-radius: 999px !important;
    padding: 14px 28px !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(76,175,80,0.4) !important;
    transition: transform 0.15s !important;
}
.make-story-btn button:hover { transform: scale(1.04) !important; }

/* Load button */
.load-btn button {
    background: linear-gradient(135deg, #FF9800, #FFB74D) !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 999px !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(255,152,0,0.35) !important;
}

/* Log box */
#log-box textarea {
    font-family: 'Poppins', monospace !important;
    font-size: 0.82rem !important;
    background: #F3F0FF !important;
    border-radius: 12px !important;
    border: 2px solid #C5B8FF !important;
}

/* Textbox input */
.topic-input input, .topic-input textarea {
    font-size: 1rem !important;
    border-radius: 12px !important;
    border: 2px solid #FFB3C8 !important;
    padding: 10px 14px !important;
}
.topic-input input:focus, .topic-input textarea:focus {
    border-color: #FF6B9D !important;
    box-shadow: 0 0 0 3px rgba(255,107,157,0.2) !important;
}

/* Sliders */
input[type=range]::-webkit-slider-thumb { background: #FF6B9D !important; }

/* Accordion */
.accordion-header { border-radius: 12px !important; }

/* Dropdown */
.history-dd select, .history-dd input {
    border-radius: 12px !important;
    border: 2px solid #FFE87C !important;
}

/* Download file boxes */
.download-box { border-radius: 12px !important; }

/* Section dividers */
hr { border-color: #FFB3C8 !important; opacity: 0.5; }
"""


with gr.Blocks(
    theme=gr.themes.Soft(),
    title="🌟 My Story Maker",
    css=KID_CSS,
) as demo:

    with gr.Column(elem_classes="kid-title"):
        gr.Markdown("# 🌟 My Story Maker 🌟\nTell me a topic and I'll write a blog post for you! ✨")

    with gr.Row():
        with gr.Column(scale=3):
            topic_input = gr.Textbox(
                label="✏️ What do you want to write about?",
                value="Dinosaurs 🦕",
                placeholder="e.g. space, animals, robots, magic...",
                lines=1,
                elem_classes="topic-input",
            )
        with gr.Column(scale=1):
            gen_btn = gr.Button("🚀 Make My Story!", variant="primary", elem_classes="make-story-btn")

    with gr.Accordion("⚙️ More options (for curious kids!)", open=False):
        with gr.Row():
            num_sections = gr.Slider(2, 5, value=3, step=1, label="📖 How many chapters?")
            words_per_section = gr.Slider(100, 400, value=200, step=50, label="📝 How long each chapter?")

    dark_toggle = gr.Checkbox(label="🌙 Night Mode", value=False)

    with gr.Row():
        with gr.Column(scale=1):
            log_box = gr.Textbox(
                label="🤖 What's happening...",
                lines=20,
                interactive=False,
                elem_id="log-box",
                autoscroll=True,
                placeholder="The helper robots will show their work here once you click Make My Story!",
            )
        with gr.Column(scale=2):
            html_preview = gr.HTML(label="🎉 Your Story!")

    with gr.Row():
        dl_html = gr.File(label="💾 Save as Web Page", interactive=False, elem_classes="download-box")
        dl_md = gr.File(label="📄 Save as Text File", interactive=False, elem_classes="download-box")

    gr.Markdown("---")
    gr.Markdown("### 📚 Read an old story")
    with gr.Row():
        history_dd = gr.Dropdown(
            label="Pick a story you made before",
            choices=_report_choices(),
            interactive=True,
            scale=4,
            elem_classes="history-dd",
        )
        load_btn = gr.Button("📖 Open!", scale=1, elem_classes="load-btn")

    # -----------------------------------------------------------------------
    # Event wiring (identical logic to app.py)
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

    def rerender_dark(dl_html_path, dark_mode):
        if not dl_html_path:
            return None
        path = dl_html_path if isinstance(dl_html_path, str) else dl_html_path.name
        blog_data = utils.load_report_json(path)
        if not blog_data:
            return _wrap_preview(utils.load_report_html(path))
        return _wrap_preview(_kid_html(blog_data, dark=dark_mode))

    dark_toggle.change(
        fn=rerender_dark,
        inputs=[dl_html, dark_toggle],
        outputs=[html_preview],
    )


if __name__ == "__main__":
    demo.launch(server_port=7861)

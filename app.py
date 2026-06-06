import html
from pathlib import Path
import gradio as gr
import agents
import utils

# ---------------------------------------------------------------------------
# UI Constants and Helpers
# ---------------------------------------------------------------------------

ADULT_THEME = {
    "title": "# Multi-Agent Blog Generator\nPowered by **CrewAI** + **Google Gemini**",
    "topic_label": "Blog Topic",
    "topic_placeholder": "e.g. quantum computing, climate tech, Web3...",
    "gen_btn": "Generate",
    "log_label": "Agent Activity",
    "log_placeholder": "Agent log will appear here once you click Generate...",
    "preview_label": "Report Preview",
}

KIDS_THEME = {
    "title": "# 🌟 My Story Maker 🌟\nTell me a topic and I'll write a blog post for you! ✨",
    "topic_label": "✏️ What do you want to write about?",
    "topic_placeholder": "e.g. space, animals, robots, magic...",
    "gen_btn": "🚀 Make My Story!",
    "log_label": "🤖 What's happening...",
    "log_placeholder": "The helper robots will show their work here once you click Make My Story!",
    "preview_label": "🎉 Your Story!",
}

# ---------------------------------------------------------------------------
# Core generate function (streaming generator)
# ---------------------------------------------------------------------------

def generate(audience: str, topic: str, num_sections: int, words_per_section: int, dark_mode: bool):
    if not topic.strip():
        yield ("Please enter a topic." if audience == "Adult" else "Please type something! 🐣"), None, None, None, gr.update()
        return

    log_lines: list[str] = []
    blog_data = None
    crew_type = "adult" if audience == "Adult" else "kids"

    for item in agents.run_crew_streaming(topic.strip(), int(num_sections), int(words_per_section), crew_type=crew_type):
        if isinstance(item, tuple) and item[0] == "RESULT":
            blog_data = item[1]
        elif isinstance(item, tuple) and item[0] == "ERROR":
            err_msg = "\n".join(log_lines) + (f"\n\n⚠ ERROR: {item[1]}" if audience == "Adult" else f"\n\n⚠️ Uh-oh! Something went wrong: {item[1]}")
            yield err_msg, None, None, None, gr.update()
            return
        else:
            log_lines.append(str(item))
            yield "\n".join(log_lines), None, None, None, gr.update()

    if blog_data:
        html_str = agents.create_html(blog_data, dark=dark_mode, audience=crew_type)
        html_path = utils.save_report(blog_data, html_str, audience=crew_type)

        md_str = utils.blog_to_markdown(blog_data)
        md_path = str(html_path).replace(".html", ".md")
        Path(md_path).write_text(md_str, encoding="utf-8")

        preview_html = _wrap_preview(html_str)
        updated_choices = _report_choices()

        done_msg = "\n".join(log_lines) + ("\n\n✅ Done!" if audience == "Adult" else "\n\n🎉 Your story is ready! Great job! 🌟")
        yield (
            done_msg,
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
    audience = blog_data.get("audience", "adult")
    html_str = agents.create_html(blog_data, dark=dark_mode, audience=audience) if blog_data else utils.load_report_html(path)
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
    title="AI Blog & Story Generator",
    css="""
    .generate-btn { font-size: 1rem !important; }
    #log-box textarea { font-family: monospace; font-size: 0.8rem; }
    """,
) as demo:

    with gr.Row():
        audience_selector = gr.Radio(["Adult", "Kids"], label="Who are you?", value="Adult")

    # Injected style for kids mode
    style_tag = gr.HTML("", visible=True)

    title_markdown = gr.Markdown(ADULT_THEME["title"])

    with gr.Row():
        with gr.Column(scale=3):
            topic_input = gr.Textbox(
                label=ADULT_THEME["topic_label"],
                value="AI",
                placeholder=ADULT_THEME["topic_placeholder"],
                lines=1,
            )
        with gr.Column(scale=1):
            gen_btn = gr.Button(ADULT_THEME["gen_btn"], variant="primary", elem_classes="generate-btn")

    with gr.Accordion("Advanced settings", open=False) as settings_accordion:
        with gr.Row():
            num_sections = gr.Slider(2, 5, value=3, step=1, label="Number of sections")
            words_per_section = gr.Slider(100, 400, value=200, step=50, label="Words per section")

    dark_toggle = gr.Checkbox(label="Dark mode (report)", value=False)

    with gr.Row():
        with gr.Column(scale=1):
            log_box = gr.Textbox(
                label=ADULT_THEME["log_label"],
                lines=20,
                interactive=False,
                elem_id="log-box",
                autoscroll=True,
                placeholder=ADULT_THEME["log_placeholder"],
            )
        with gr.Column(scale=2):
            html_preview = gr.HTML(label=ADULT_THEME["preview_label"])

    with gr.Row():
        dl_html = gr.File(label="Download HTML", interactive=False)
        dl_md = gr.File(label="Download Markdown", interactive=False)

    gr.Markdown("---")
    history_title = gr.Markdown("### Past Reports")
    with gr.Row():
        history_dd = gr.Dropdown(
            label="Load a past report",
            choices=_report_choices(),
            interactive=True,
            scale=4,
        )
        load_btn = gr.Button("Load", scale=1)

    # -----------------------------------------------------------------------
    # Dynamic UI Logic
    # -----------------------------------------------------------------------

    def update_ui(audience):
        theme = ADULT_THEME if audience == "Adult" else KIDS_THEME

        kids_style = """
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
        """ if audience == "Kids" else "<style></style>"

        return {
            style_tag: kids_style,
            title_markdown: theme["title"],
            topic_input: gr.update(label=theme["topic_label"], placeholder=theme["topic_placeholder"]),
            gen_btn: gr.update(value=theme["gen_btn"]),
            log_box: gr.update(label=theme["log_label"], placeholder=theme["log_placeholder"]),
            html_preview: gr.update(label=theme["preview_label"]),
            settings_accordion: gr.update(label="Advanced settings" if audience == "Adult" else "⚙️ More options (for curious kids!)"),
            num_sections: gr.update(label="Number of sections" if audience == "Adult" else "📖 How many chapters?"),
            words_per_section: gr.update(label="Words per section" if audience == "Adult" else "📝 How long each chapter?"),
            dark_toggle: gr.update(label="Dark mode (report)" if audience == "Adult" else "🌙 Night Mode"),
            history_title: "### Past Reports" if audience == "Adult" else "### 📚 Read an old story",
            history_dd: gr.update(label="Load a past report" if audience == "Adult" else "Pick a story you made before"),
            load_btn: gr.update(value="Load" if audience == "Adult" else "📖 Open!"),
            dl_html: gr.update(label="Download HTML" if audience == "Adult" else "💾 Save as Web Page"),
            dl_md: gr.update(label="Download Markdown" if audience == "Adult" else "📄 Save as Text File"),
        }

    audience_selector.change(
        fn=update_ui,
        inputs=[audience_selector],
        outputs=[
            style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
            settings_accordion, num_sections, words_per_section, dark_toggle,
            history_title, history_dd, load_btn, dl_html, dl_md
        ],
    )

    # -----------------------------------------------------------------------
    # Event wiring
    # -----------------------------------------------------------------------

    gen_btn.click(
        fn=generate,
        inputs=[audience_selector, topic_input, num_sections, words_per_section, dark_toggle],
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
        audience = blog_data.get("audience", "adult")
        return _wrap_preview(agents.create_html(blog_data, dark=dark_mode, audience=audience))

    dark_toggle.change(
        fn=rerender_dark,
        inputs=[dl_html, dark_toggle],
        outputs=[html_preview],
    )


if __name__ == "__main__":
    demo.launch()

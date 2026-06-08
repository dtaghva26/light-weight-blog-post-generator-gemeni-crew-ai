import gradio as gr

from frontend.gradio.themes import EVALUATIVIST_THEME as ADULT_THEME
from frontend.gradio.handlers import (
    generate,
    load_history,
    rerender_dark,
    update_ui,
    _report_choices,
)


def _build_update_ui_outputs(
    style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
    settings_accordion, num_sections, words_per_section, dark_toggle,
    history_title, history_dd, load_btn, dl_html, dl_md,
):
    def _fn(audience):
        ui = update_ui(audience)
        return {
            style_tag: ui["kids_style"],
            title_markdown: ui["title"],
            topic_input: gr.update(label=ui["topic_label"], placeholder=ui["topic_placeholder"]),
            gen_btn: gr.update(value=ui["gen_btn"]),
            log_box: gr.update(label=ui["log_label"], placeholder=ui["log_placeholder"]),
            html_preview: gr.update(label=ui["preview_label"]),
            settings_accordion: gr.update(label=ui["settings_label"]),
            num_sections: gr.update(label=ui["num_sections_label"]),
            words_per_section: gr.update(label=ui["words_per_section_label"]),
            dark_toggle: gr.update(label=ui["dark_toggle_label"]),
            history_title: ui["history_title"],
            history_dd: gr.update(label=ui["history_dd_label"]),
            load_btn: gr.update(value=ui["load_btn_label"]),
            dl_html: gr.update(label=ui["dl_html_label"]),
            dl_md: gr.update(label=ui["dl_md_label"]),
        }

    return _fn


with gr.Blocks(
    theme=gr.themes.Soft(),
    title="AI Blog & Story Generator",
    css="""
    .generate-btn { font-size: 1rem !important; }
    #log-box textarea { font-family: monospace; font-size: 0.8rem; }
    """,
) as demo:

    with gr.Row():
        audience_selector = gr.Radio(
            ["Absolutist", "Multiplist", "Evaluativist", "Master Thinker"],
            label="Critical Thinking Stage",
            value="Evaluativist",
        )

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

    # Event wiring
    audience_selector.change(
        fn=_build_update_ui_outputs(
            style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
            settings_accordion, num_sections, words_per_section, dark_toggle,
            history_title, history_dd, load_btn, dl_html, dl_md,
        ),
        inputs=[audience_selector],
        outputs=[
            style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
            settings_accordion, num_sections, words_per_section, dark_toggle,
            history_title, history_dd, load_btn, dl_html, dl_md,
        ],
    )

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

    dark_toggle.change(
        fn=rerender_dark,
        inputs=[dl_html, dark_toggle],
        outputs=[html_preview],
    )

import gradio as gr

from modes.registry import all_modes as _all_modes

_modes = _all_modes()
_mode_names = [m.display_name for m in _modes]
_default_mode = next(m for m in _modes if m.crew_type == "evaluativist")

from frontend.gradio.handlers import (
    generate,
    load_history,
    rerender_dark,
    update_ui,
    on_age_submit,
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
    .age-gate-wrap {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 60vh;
        text-align: center;
        padding: 2rem;
    }
    .age-gate-inner { max-width: 320px; width: 100%; margin: 0 auto; }
    """,
) as demo:

    # ── Age gate (shown on load) ──────────────────────────────────────────────
    with gr.Column(visible=True, elem_classes="age-gate-wrap") as age_gate:
        gr.Markdown("## How old are you?\n\nWe'll tailor the experience just for you.")
        with gr.Column(elem_classes="age-gate-inner"):
            age_input = gr.Number(
                label="Your age",
                minimum=1,
                maximum=120,
                precision=0,
                value=None,
            )
            age_btn = gr.Button("Get Started", variant="primary", size="lg")

    # ── Main app (hidden until age is entered) ────────────────────────────────
    with gr.Column(visible=False) as main_ui:

        with gr.Row():
            audience_selector = gr.Radio(
                _mode_names,
                label="Critical Thinking Stage",
                value=_default_mode.display_name,
            )

        style_tag = gr.HTML("", visible=True)
        title_markdown = gr.Markdown(_default_mode.title)

        with gr.Row():
            with gr.Column(scale=3):
                topic_input = gr.Textbox(
                    label=_default_mode.topic_label,
                    value="AI",
                    placeholder=_default_mode.topic_placeholder,
                    lines=1,
                )
            with gr.Column(scale=1):
                gen_btn = gr.Button(_default_mode.gen_btn, variant="primary", elem_classes="generate-btn")

        with gr.Accordion(_default_mode.settings_label, open=False) as settings_accordion:
            with gr.Row():
                num_sections = gr.Slider(2, 5, value=3, step=1, label=_default_mode.num_sections_label)
                words_per_section = gr.Slider(100, 400, value=200, step=50, label=_default_mode.words_per_section_label)

        dark_toggle = gr.Checkbox(label=_default_mode.dark_toggle_label, value=False)

        with gr.Row():
            with gr.Column(scale=1):
                log_box = gr.Textbox(
                    label=_default_mode.log_label,
                    lines=20,
                    interactive=False,
                    elem_id="log-box",
                    autoscroll=True,
                    placeholder=_default_mode.log_placeholder,
                )
            with gr.Column(scale=2):
                html_preview = gr.HTML(label=_default_mode.preview_label)

        with gr.Row():
            dl_html = gr.File(label=_default_mode.dl_html_label, interactive=False)
            dl_md = gr.File(label=_default_mode.dl_md_label, interactive=False)

        gr.Markdown("---")
        history_title = gr.Markdown(_default_mode.history_title)
        with gr.Row():
            history_dd = gr.Dropdown(
                label=_default_mode.history_dd_label,
                choices=_report_choices(),
                interactive=True,
                scale=4,
            )
            load_btn = gr.Button(_default_mode.load_btn_label, scale=1)

    # ── Event wiring ──────────────────────────────────────────────────────────
    _age_outputs = [
        age_gate, main_ui, audience_selector,
        style_tag, title_markdown, topic_input, gen_btn, log_box,
        html_preview, settings_accordion, num_sections,
        words_per_section, dark_toggle, history_title,
        history_dd, load_btn, dl_html, dl_md,
    ]

    age_btn.click(fn=on_age_submit, inputs=[age_input], outputs=_age_outputs)
    age_input.submit(fn=on_age_submit, inputs=[age_input], outputs=_age_outputs)

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

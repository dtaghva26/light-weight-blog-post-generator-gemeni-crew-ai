import gradio as gr

from modes.registry import all_modes as _all_modes

_modes = _all_modes()
_default_mode = next(m for m in _modes if m.crew_type == "lks2")

from frontend.gradio.handlers import (
    YEAR_GROUPS,
    SUBJECTS,
    generate,
    load_history,
    rerender_view,
    on_motion_toggle,
    update_ui,
    on_class_setup,
    unlock_teacher,
    pupil_mode_names,
    _report_choices,
)

_pupil_names = pupil_mode_names()


def _build_update_ui_outputs(
    style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
    settings_accordion, num_sections, words_per_section, dark_toggle,
    history_title, history_dd, load_btn, dl_html, dl_md, dl_worksheet,
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
            dl_worksheet: gr.update(label=ui["dl_worksheet_label"]),
        }

    return _fn


# Gradio 6 moved theme/css from the Blocks constructor to launch() — app.py passes these.
APP_THEME = gr.themes.Soft()
APP_CSS = """
    .generate-btn { font-size: 1rem !important; }
    #log-box textarea { font-family: monospace; font-size: 0.8rem; }
    .setup-wrap {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 60vh;
        text-align: center;
        padding: 2rem;
    }
    .setup-inner { max-width: 360px; width: 100%; margin: 0 auto; }
"""

with gr.Blocks(title="Classroom Story & Report Maker") as demo:

    # ── Class setup (shown on load — replaces the old age gate) ───────────────
    with gr.Column(visible=True, elem_classes="setup-wrap") as setup_col:
        gr.Markdown("## 🏫 Welcome to our Story & Report Maker!\n\nChoose your class to get started.")
        with gr.Column(elem_classes="setup-inner"):
            year_dd = gr.Dropdown(
                label="Year group",
                choices=list(YEAR_GROUPS.keys()),
                value="Years 3–4 (ages 7–9)",
            )
            setup_btn = gr.Button("Let's Go!", variant="primary", size="lg")

    # ── Main app (hidden until a class is chosen) ─────────────────────────────
    with gr.Column(visible=False) as main_ui:

        with gr.Row():
            audience_selector = gr.Radio(
                _pupil_names,
                label="Who is this for?",
                value=_default_mode.display_name,
            )

        style_tag = gr.HTML("", visible=True)
        motion_style = gr.HTML("<style></style>", visible=True)
        title_markdown = gr.Markdown(_default_mode.title)

        with gr.Row():
            with gr.Column(scale=3):
                topic_input = gr.Textbox(
                    label=_default_mode.topic_label,
                    value="",
                    placeholder=_default_mode.topic_placeholder,
                    lines=1,
                )
            with gr.Column(scale=1):
                subject_dd = gr.Dropdown(
                    label="School subject",
                    choices=SUBJECTS,
                    value="Any topic",
                )
            with gr.Column(scale=1):
                gen_btn = gr.Button(_default_mode.gen_btn, variant="primary", elem_classes="generate-btn")

        with gr.Row():
            dark_toggle = gr.Checkbox(label=_default_mode.dark_toggle_label, value=False)
            easy_font = gr.Checkbox(label="🔤 Easy-read font", value=False)
            large_print = gr.Checkbox(label="🔎 Large print", value=False)
            reduce_motion = gr.Checkbox(label="🦋 Calm screen (no animations)", value=False)

        # Hidden in pupil mode — revealed by the teacher PIN
        with gr.Accordion(_default_mode.settings_label, open=False, visible=False) as settings_accordion:
            with gr.Row():
                num_sections = gr.Slider(2, 5, value=3, step=1, label=_default_mode.num_sections_label)
                words_per_section = gr.Slider(50, 400, value=150, step=50, label=_default_mode.words_per_section_label)

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
            dl_worksheet = gr.File(label=_default_mode.dl_worksheet_label, interactive=False)

        # Hidden in pupil mode — revealed by the teacher PIN
        with gr.Column(visible=False) as history_col:
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

        gr.Markdown("---")
        with gr.Accordion("🔑 Teacher unlock", open=False):
            with gr.Row():
                pin_box = gr.Textbox(label="Teacher PIN", type="password", scale=3)
                unlock_btn = gr.Button("Unlock", scale=1)
            teacher_status = gr.Markdown("")

    # ── Event wiring ──────────────────────────────────────────────────────────
    _setup_outputs = [
        setup_col, main_ui, audience_selector,
        style_tag, title_markdown, topic_input, gen_btn, log_box,
        html_preview, settings_accordion, num_sections,
        words_per_section, dark_toggle, history_title,
        history_dd, load_btn, dl_html, dl_md, dl_worksheet,
    ]

    setup_btn.click(fn=on_class_setup, inputs=[year_dd], outputs=_setup_outputs)

    audience_selector.change(
        fn=_build_update_ui_outputs(
            style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
            settings_accordion, num_sections, words_per_section, dark_toggle,
            history_title, history_dd, load_btn, dl_html, dl_md, dl_worksheet,
        ),
        inputs=[audience_selector],
        outputs=[
            style_tag, title_markdown, topic_input, gen_btn, log_box, html_preview,
            settings_accordion, num_sections, words_per_section, dark_toggle,
            history_title, history_dd, load_btn, dl_html, dl_md, dl_worksheet,
        ],
    )

    gen_btn.click(
        fn=generate,
        inputs=[audience_selector, topic_input, subject_dd, num_sections,
                words_per_section, dark_toggle, easy_font, large_print, reduce_motion],
        outputs=[log_box, html_preview, dl_html, dl_md, dl_worksheet, history_dd],
    )

    load_btn.click(
        fn=load_history,
        inputs=[history_dd, dark_toggle, easy_font, large_print, reduce_motion],
        outputs=[html_preview, dl_html, dl_md, dl_worksheet],
    )

    _view_inputs = [dl_html, dark_toggle, easy_font, large_print, reduce_motion]
    dark_toggle.change(fn=rerender_view, inputs=_view_inputs, outputs=[html_preview])
    easy_font.change(fn=rerender_view, inputs=_view_inputs, outputs=[html_preview])
    large_print.change(fn=rerender_view, inputs=_view_inputs, outputs=[html_preview])
    reduce_motion.change(fn=on_motion_toggle, inputs=_view_inputs, outputs=[motion_style, html_preview])

    unlock_btn.click(
        fn=unlock_teacher,
        inputs=[pin_box],
        outputs=[audience_selector, settings_accordion, history_col, teacher_status, pin_box],
    )

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ModeDefinition:
    # ── Identity ──────────────────────────────────────────────────────────────
    crew_type: str
    display_name: str

    # ── Age gate ──────────────────────────────────────────────────────────────
    min_age: int

    # ── Radio widget ordering ─────────────────────────────────────────────────
    order: int

    # ── Crew factory ──────────────────────────────────────────────────────────
    # signature: (topic: str, num_sections: int, words_per_section: int) -> Crew
    build_crew: Callable

    # ── Theme strings (replaces themes.py dicts) ──────────────────────────────
    title: str
    topic_label: str
    topic_placeholder: str
    gen_btn: str
    log_label: str
    log_placeholder: str
    preview_label: str

    # ── UI labels (replaces inline dicts in update_ui()) ─────────────────────
    settings_label: str
    num_sections_label: str
    words_per_section_label: str
    dark_toggle_label: str
    history_title: str
    history_dd_label: str
    load_btn_label: str
    dl_html_label: str
    dl_md_label: str

    # ── CSS ──────────────────────────────────────────────────────────────────
    gradio_css: str   # injected into Gradio live DOM via update_ui()
    report_css: str   # injected into standalone HTML report by renderer.py

    # ── User-facing messages ──────────────────────────────────────────────────
    empty_msg: str
    error_msg: Callable  # (e: str) -> str
    done_msg: str

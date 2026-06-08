# Re-export shim — logic has moved to logic/reports.py and logic/renderer.py
from logic.reports import (
    save_report,
    list_reports,
    load_report_html,
    load_report_json,
)
from logic.renderer import blog_to_markdown

__all__ = [
    "save_report",
    "list_reports",
    "load_report_html",
    "load_report_json",
    "blog_to_markdown",
]
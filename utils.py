import json
import re
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("reports")


def _ensure_reports_dir():
    REPORTS_DIR.mkdir(exist_ok=True)


def _slug(text: str, max_len: int = 40) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:max_len].rstrip("-")


def save_report(blog_data: dict, html_string: str, audience: str = "adult") -> Path:
    _ensure_reports_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = blog_data.get("title", "report")
    slug = _slug(title)
    base = REPORTS_DIR / f"{ts}_{slug}"
    html_path = base.with_suffix(".html")
    json_path = base.with_suffix(".json")

    # Store audience in blog_data if not already present
    if "audience" not in blog_data:
        blog_data["audience"] = audience

    html_path.write_text(html_string, encoding="utf-8")
    json_path.write_text(json.dumps(blog_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return html_path


def list_reports() -> list:
    _ensure_reports_dir()
    html_files = sorted(REPORTS_DIR.glob("*.html"), reverse=True)
    reports = []
    for html_path in html_files:
        json_path = html_path.with_suffix(".json")
        title = html_path.stem  # fallback
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                title = data.get("title", title)
            except Exception:
                pass
        ts_str = html_path.stem[:15]  # "20260606_143022"
        try:
            ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S").strftime("%b %d, %Y %H:%M")
        except ValueError:
            ts = ts_str
        reports.append({"path": str(html_path), "title": title, "timestamp": ts})
    return reports


def load_report_html(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_report_json(path: str) -> dict:
    json_path = Path(path).with_suffix(".json")
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    return {}


def blog_to_markdown(blog_data: dict) -> str:
    title = blog_data.get("title", "Untitled")
    author = blog_data.get("author", "Unknown")
    sections = blog_data.get("sections", [])

    lines = [f"# {title}", f"", f"*By {author}*", ""]

    for section in sections:
        if isinstance(section, dict):
            heading = section.get("heading", "")
            body = section.get("body", "")
        else:
            heading = section.heading
            body = section.body
        lines += [f"## {heading}", "", body, ""]

    return "\n".join(lines)
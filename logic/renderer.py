from datetime import datetime, timedelta

_ALLOWED_VALENCE = {"uplifting", "neutral", "cautionary", "reflective", "mixed"}


def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%B %d, %Y").replace(" 0", " ")


def _accessibility_css(easy_font: bool, large_print: bool, reduce_motion: bool) -> str:
    """Override layer appended after all mode CSS so it always wins."""
    css = ""
    if easy_font:
        css += """
        /* Easy-read font (dyslexia-friendly stack, no remote fonts needed) */
        body, body * {
            font-family: 'OpenDyslexic', 'Comic Sans MS', 'Comic Neue', Verdana, sans-serif !important;
            letter-spacing: 0.03em !important;
        }"""
    if large_print:
        css += """
        /* Large print */
        p, li { font-size: 1.5rem !important; line-height: 2.1 !important; }
        h1 { font-size: 3rem !important; }
        h2 { font-size: 2rem !important; }"""
    if reduce_motion:
        css += """
        /* Reduce motion */
        *, *::before, *::after { animation: none !important; transition: none !important; }"""
    return css


_PRINT_CSS = """
        @media print {
            body { background: #fff !important; padding: 0 !important; }
            body *, body *::before, body *::after { animation: none !important; transition: none !important; }
            .container { box-shadow: none !important; border: none !important; max-width: 100% !important; padding: 0 !important; border-radius: 0 !important; }
            .section-block { page-break-inside: avoid; box-shadow: none !important; }
            .review-schedule { page-break-inside: avoid; }
        }"""


def create_html(blog_data: dict, dark: bool = False, audience: str = "adult",
                easy_font: bool = False, large_print: bool = False,
                reduce_motion: bool = False) -> str:
    title = blog_data["title"]
    author = blog_data["author"]
    sections = blog_data["sections"]

    try:
        from modes.registry import get as get_mode
        extra_css = get_mode(audience).report_css
    except KeyError:
        extra_css = ""

    if dark:
        css_vars = """
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --accent-color: #60a5fa;
            --heading-color: #f1f5f9;
            --border-color: #334155;"""
    else:
        css_vars = """
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --accent-color: #2563eb;
            --heading-color: #0f172a;
            --border-color: #e2e8f0;"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{{css_vars}
        }}
        {extra_css}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.75;
            color: var(--text-main);
            background-color: var(--bg-color);
            margin: 0;
            padding: 40px 20px;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 760px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 48px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
        }}
        header {{
            margin-bottom: 40px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 24px;
        }}
        h1 {{
            font-size: 2.25rem;
            color: var(--heading-color);
            line-height: 1.25;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin: 0 0 16px 0;
        }}
        .meta {{
            font-size: 0.95rem;
            color: var(--text-muted);
            font-weight: 500;
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .meta .author {{
            color: var(--heading-color);
            font-weight: 600;
        }}
        article {{
            display: flex;
            flex-direction: column;
            gap: 32px;
        }}
        h2 {{
            font-size: 1.45rem;
            color: var(--accent-color);
            font-weight: 700;
            letter-spacing: -0.015em;
            margin: 0 0 12px 0;
            line-height: 1.3;
        }}
        p {{
            font-size: 1.05rem;
            margin: 0;
            color: var(--text-main);
            text-align: justify;
        }}
        /* Cognitive Load Bar */
        .cog-load-wrapper {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 4px 0 12px 0;
        }}
        .cog-load-label {{
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-muted);
            white-space: nowrap;
            min-width: 105px;
        }}
        .cog-load-track {{
            flex: 1;
            height: 6px;
            border-radius: 3px;
            background: var(--border-color);
            overflow: hidden;
        }}
        .cog-load-fill {{
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, #22c55e 0%, #f59e0b 55%, #ef4444 100%);
        }}
        .cog-load-value {{
            font-size: 0.7rem;
            color: var(--text-muted);
            min-width: 28px;
            text-align: right;
        }}
        /* Emotional Valence Badge */
        .valence-badge {{
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            padding: 2px 9px;
            border-radius: 999px;
            margin-left: 10px;
            vertical-align: middle;
            flex-shrink: 0;
        }}
        .valence-uplifting  {{ background: #dcfce7; color: #166534; }}
        .valence-neutral    {{ background: #f1f5f9; color: #475569; }}
        .valence-cautionary {{ background: #fef3c7; color: #92400e; }}
        .valence-reflective {{ background: #ede9fe; color: #5b21b6; }}
        .valence-mixed      {{ background: #e0f2fe; color: #0c4a6e; }}
        /* Section heading row */
        .section-heading-row {{
            display: flex;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 0;
            margin: 0 0 4px 0;
        }}
        .section-heading-row h2 {{
            margin: 0;
        }}
        /* Review Schedule */
        .review-schedule {{
            margin-top: 48px;
            border-top: 2px solid var(--border-color);
            padding-top: 32px;
        }}
        .review-schedule h3 {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--heading-color);
            margin: 0 0 20px 0;
            letter-spacing: -0.01em;
        }}
        .review-panels {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        .review-panel {{
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 16px;
            background: var(--card-bg);
        }}
        .review-panel-title {{
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: var(--accent-color);
            margin: 0 0 3px 0;
        }}
        .review-panel-date {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin: 0 0 12px 0;
        }}
        .review-panel ol {{
            margin: 0;
            padding-left: 18px;
        }}
        .review-panel li {{
            font-size: 0.85rem;
            color: var(--text-main);
            margin-bottom: 6px;
            line-height: 1.5;
            text-align: left;
        }}
        .review-section-label {{
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin: 10px 0 3px 0;
        }}
        @media (max-width: 640px) {{
            body {{ padding: 16px 12px; }}
            .container {{ padding: 24px; border-radius: 8px; }}
            h1 {{ font-size: 1.75rem; }}
            h2 {{ font-size: 1.25rem; }}
            .review-panels {{ grid-template-columns: 1fr; }}
        }}
        {_accessibility_css(easy_font, large_print, reduce_motion)}
        {_PRINT_CSS}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="meta">
                <span>Published by</span>
                <span class="author">{author}</span>
            </div>
        </header>
        <article>
"""

    for section in sections:
        if isinstance(section, dict):
            heading   = section.get("heading", "Untitled Section")
            body      = section.get("body", "")
            cog_load  = section.get("cognitive_load")
            valence   = section.get("emotional_valence")
        else:
            heading   = section.heading
            body      = section.body
            cog_load  = section.cognitive_load
            valence   = section.emotional_valence

        # Cognitive load bar
        if cog_load is not None:
            try:
                pct = int(round(float(cog_load) * 100))
                cog_html = f"""
            <div class="cog-load-wrapper">
                <span class="cog-load-label">Cognitive Load</span>
                <div class="cog-load-track">
                    <div class="cog-load-fill" style="width:{pct}%"></div>
                </div>
                <span class="cog-load-value">{float(cog_load):.2f}</span>
            </div>"""
            except (TypeError, ValueError):
                cog_html = ""
        else:
            cog_html = ""

        # Valence badge
        if valence and isinstance(valence, str) and valence.lower() in _ALLOWED_VALENCE:
            valence_html = f'<span class="valence-badge valence-{valence.lower()}">{valence}</span>'
        else:
            valence_html = ""

        html += f"""
            <div class="section-block">
                <div class="section-heading-row">
                    <h2>{heading}</h2>{valence_html}
                </div>{cog_html}
                <p>{body}</p>
            </div>"""

    # Spaced repetition review schedule
    has_any_prompts = any(
        (s.get("review_prompts") if isinstance(s, dict) else s.review_prompts)
        for s in sections
    )

    if has_any_prompts:
        generated_at_str = blog_data.get("generated_at")
        try:
            base_dt = datetime.fromisoformat(generated_at_str) if generated_at_str else datetime.now()
        except (ValueError, TypeError):
            base_dt = datetime.now()

        panels = [
            ("Day 1 — Initial Review",      base_dt),
            ("Day 7 — First Recall",         base_dt + timedelta(days=6)),
            ("Day 21 — Long-term Retention", base_dt + timedelta(days=20)),
        ]

        panels_html = ""
        for panel_label, panel_dt in panels:
            items_html = ""
            for s in sections:
                if isinstance(s, dict):
                    sec_heading = s.get("heading", "")
                    prompts = s.get("review_prompts") or []
                else:
                    sec_heading = s.heading
                    prompts = s.review_prompts or []
                if prompts:
                    items_html += f'<p class="review-section-label">{sec_heading}</p><ol>'
                    for q in prompts:
                        items_html += f"<li>{q}</li>"
                    items_html += "</ol>"

            panels_html += f"""
                <div class="review-panel">
                    <p class="review-panel-title">{panel_label}</p>
                    <p class="review-panel-date">{_fmt_date(panel_dt)}</p>
                    {items_html}
                </div>"""

        html += f"""
            <div class="review-schedule">
                <h3>Spaced Repetition Review Schedule</h3>
                <div class="review-panels">
                    {panels_html}
                </div>
            </div>"""

    html += """
        </article>
    </div>
</body>
</html>
"""
    return html


def create_worksheet_html(blog_data: dict) -> str:
    """A4 print-ready comprehension worksheet built from each section's review_prompts."""
    title = blog_data.get("title", "Untitled")

    questions_html = ""
    q_num = 0
    for section in blog_data.get("sections", []):
        if isinstance(section, dict):
            heading = section.get("heading", "")
            prompts = section.get("review_prompts") or []
        else:
            heading = section.heading
            prompts = section.review_prompts or []
        if not prompts:
            continue
        questions_html += f'<h2>{heading}</h2>'
        for q in prompts:
            q_num += 1
            questions_html += f"""
        <div class="question">
            <p class="q-text">{q_num}. {q}</p>
            <div class="answer-line"></div>
            <div class="answer-line"></div>
        </div>"""

    if q_num == 0:
        questions_html = "<p>No questions were generated for this story.</p>"

    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <title>Worksheet — {title}</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{
            font-family: 'Comic Sans MS', 'Comic Neue', Verdana, sans-serif;
            color: #1e293b;
            max-width: 17cm;
            margin: 0 auto;
            padding: 24px;
            line-height: 1.6;
        }}
        .name-date {{
            display: flex;
            justify-content: space-between;
            gap: 24px;
            margin-bottom: 20px;
            font-size: 1rem;
        }}
        .name-date span {{ flex: 1; border-bottom: 2px solid #1e293b; padding-bottom: 2px; }}
        h1 {{ font-size: 1.6rem; text-align: center; margin: 8px 0 4px 0; }}
        .subtitle {{ text-align: center; font-size: 0.95rem; color: #475569; margin: 0 0 24px 0; }}
        h2 {{ font-size: 1.1rem; margin: 24px 0 4px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; }}
        .question {{ page-break-inside: avoid; margin: 14px 0; }}
        .q-text {{ margin: 0 0 10px 0; font-size: 1.05rem; }}
        .answer-line {{ border-bottom: 1.5px solid #94a3b8; height: 28px; }}
        @media print {{
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="name-date">
        <span>Name:&nbsp;</span>
        <span>Date:&nbsp;</span>
    </div>
    <h1>{title}</h1>
    <p class="subtitle">Read the story, then answer the questions in full sentences.</p>
    {questions_html}
</body>
</html>
"""


def blog_to_markdown(blog_data: dict) -> str:
    title = blog_data.get("title", "Untitled")
    author = blog_data.get("author", "Unknown")
    sections = blog_data.get("sections", [])

    lines = [f"# {title}", "", f"*By {author}*", ""]

    for section in sections:
        if isinstance(section, dict):
            heading = section.get("heading", "")
            body = section.get("body", "")
            prompts = section.get("review_prompts") or []
        else:
            heading = section.heading
            body = section.body
            prompts = section.review_prompts or []
        lines += [f"## {heading}", "", body, ""]
        if prompts:
            lines += ["**Review prompts:**", ""]
            for q in prompts:
                lines.append(f"- {q}")
            lines.append("")

    return "\n".join(lines)

import sys
import io
import json
import queue
import threading
import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from pydantic import BaseModel, Field, ValidationError
from typing import List

load_dotenv()

# Support both the typoed and correct environment variable names
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY")


class ArticleSection(BaseModel):
    heading: str = Field(description="The subtitle or trend title.")
    body: str = Field(description="The paragraphs explaining this specific trend.")


class StructuredBlogPost(BaseModel):
    title: str = Field(description="An attention-grabbing title for the article.")
    author: str = Field(description="The author of the article.")
    sections: List[ArticleSection] = Field(description="The structured breakdowns of the article.")


def _build_crew(topic: str, num_sections: int, words_per_section: int) -> Crew:
    # Use a valid Gemini model name
    gemini_llm = LLM(model="gemini/gemini-1.5-flash", api_key=API_KEY)

    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Uncover cutting-edge developments and trends in {topic}.",
        backstory="You are an expert researcher focused on technology trends.",
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Tech Content Writer",
        goal="Create engaging blog posts about technology.",
        backstory="You are a skilled writer who simplifies complex tech topics.",
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=f"List {num_sections} major trends in {topic}.",
        expected_output=f"A bulleted list of {num_sections} trends.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Write a blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each, based on the trends provided. "
            f"Topic: {topic}."
        ),
        expected_output="A structured database-ready payload matching the StructuredBlogPost schema.",
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


def _build_kids_crew(topic: str, num_sections: int, words_per_section: int) -> Crew:
    # Use a valid Gemini model name
    gemini_llm = LLM(model="gemini/gemini-1.5-flash", api_key=API_KEY)

    researcher = Agent(
        role="Curious Kid Explorer",
        goal=f"Find {num_sections} fun and amazing facts about {topic} that kids aged 6–12 will love.",
        backstory=(
            "You are an enthusiastic, friendly explorer who loves discovering cool things about the world. "
            "You explain everything in simple words a child can understand, using short sentences, "
            "fun comparisons, and lots of excitement. You never use jargon or complicated language."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Kids Story Writer",
        goal="Turn fun facts into a cheerful, easy-to-read story for kids.",
        backstory=(
            "You are a beloved children's book author who writes in a warm, playful, encouraging style. "
            "You use simple words (no big technical terms), short paragraphs, vivid comparisons, "
            "and occasional exclamations like 'Wow!' or 'Did you know?'. "
            "Your stories make kids curious and excited to learn more."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} fun, surprising, and age-appropriate facts or ideas about '{topic}'. "
            f"Write them as simple bullet points a 8-year-old can understand. No technical jargon."
        ),
        expected_output=f"A bulleted list of {num_sections} fun facts about {topic}, written simply for kids.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the fun facts provided, write a cheerful kids blog post with exactly {num_sections} chapters. "
            f"Each chapter should be about {words_per_section} words, use simple language, "
            f"short sentences, and a fun enthusiastic tone. Topic: {topic}. "
            f"Make it feel like a story, not a textbook."
        ),
        expected_output="A structured database-ready payload matching the StructuredBlogPost schema, written for children.",
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


def run_crew_streaming(topic: str, num_sections: int, words_per_section: int, crew_type: str = "adult"):
    """
    Generator that yields stdout log lines from the crew run, then a
    ("RESULT", dict) tuple on success or ("ERROR", str) on failure.
    """
    log_q: queue.Queue = queue.Queue()

    class QueueWriter(io.TextIOBase):
        def write(self, msg: str) -> int:
            if msg.strip():
                log_q.put(msg)
            return len(msg)

        def flush(self):
            pass

    def _run():
        old_stdout = sys.stdout
        sys.stdout = QueueWriter()
        try:
            if crew_type == "kids":
                crew = _build_kids_crew(topic, num_sections, words_per_section)
            else:
                crew = _build_crew(topic, num_sections, words_per_section)
            result = crew.kickoff()
            blog_data = result.json_dict
            if blog_data is None:
                blog_data = json.loads(result.raw)
            StructuredBlogPost(**blog_data)  # validate structure
            log_q.put(("RESULT", blog_data))
        except ValidationError as e:
            log_q.put(("ERROR", f"LLM returned invalid structure: {e}"))
        except Exception as e:
            log_q.put(("ERROR", str(e)))
        finally:
            sys.stdout = old_stdout

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    while t.is_alive() or not log_q.empty():
        try:
            item = log_q.get(timeout=0.3)
            yield item
        except queue.Empty:
            continue


def create_html(blog_data: dict, dark: bool = False, audience: str = "adult") -> str:
    title = blog_data["title"]
    author = blog_data["author"]
    sections = blog_data["sections"]

    # Audience-specific CSS overrides
    extra_css = ""
    if audience == "kids":
        extra_css = """
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
        body { font-family: 'Poppins', sans-serif !important; }
        h1 { font-size: 2.4rem; font-weight: 800; color: #FF6B9D !important; }
        h2 { font-size: 1.6rem; font-weight: 700; color: #7888BF !important; border-left: 6px solid #FFE87C; padding-left: 12px; margin-top: 2rem; }
        p  { font-size: 1.1rem; line-height: 1.8; }
        .author { color: #FF6B9D; font-weight: 600; font-size: 1.1rem; }
        """

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
        @media (max-width: 640px) {{
            body {{ padding: 16px 12px; }}
            .container {{ padding: 24px; border-radius: 8px; }}
            h1 {{ font-size: 1.75rem; }}
            h2 {{ font-size: 1.25rem; }}
        }}
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
        heading = section.get("heading", "Untitled Section") if isinstance(section, dict) else section.heading
        body = section.get("body", "") if isinstance(section, dict) else section.body
        html += f"""
            <div class="section-block">
                <h2>{heading}</h2>
                <p>{body}</p>
            </div>"""

    html += """
        </article>
    </div>
</body>
</html>
"""
    return html
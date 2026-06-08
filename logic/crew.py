import sys
import io
import json
import queue
import threading
import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from pydantic import ValidationError

from logic.models import StructuredBlogPost

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("Gemeni_API_KEY")


def _build_absolutist_crew(topic: str, num_sections: int, words_per_section: int) -> Crew:
    """Childhood stage (4-10): knowledge is objective, absolute truth from authority."""
    gemini_llm = LLM(model="gemini/gemini-3.5-flash", api_key=API_KEY)

    researcher = Agent(
        role="Fact Finder",
        goal=f"Find {num_sections} clear, definitive facts about {topic} that a 6-year-old can understand.",
        backstory=(
            "You are a trusted teacher who knows everything. You present facts as simple, absolute truths. "
            "Everything you say is definitely right. You use very short sentences and only the simplest words. "
            "You never say 'maybe' or 'some people think' — you state what IS, clearly and confidently."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Simple Storyteller",
        goal="Turn facts into a clear, definitive story a young child can follow easily.",
        backstory=(
            "You are a trusted author who writes for children aged 6 to 10. "
            "You use only simple vocabulary, very short sentences, and declare facts confidently. "
            "There is no ambiguity in your writing — things are simply true or not true. "
            "You never hedge. Every sentence ends with certainty."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Find {num_sections} clear, definitive facts about '{topic}' that a 6-year-old can understand. "
            f"Write each fact as a simple, confident statement. No maybes. No 'some experts say'. "
            f"Use only words a young child knows."
        ),
        expected_output=f"A bulleted list of {num_sections} simple, definitive facts about {topic} for young children.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the facts provided, write a simple blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Use very short sentences. Declare everything as clear fact. "
            f"Use only vocabulary a 6-year-old knows. No hedging, no 'maybe', no complexity. "
            f"For each section, add three special helper fields. "
            f"'cognitive_load' is a number from 0.0 to 1.0 — use low numbers like 0.1 or 0.2 because this is simple writing for children. "
            f"'emotional_valence' must be exactly one word chosen from: uplifting, neutral, cautionary, reflective, mixed — pick the one that matches how the section feels. "
            f"'review_prompts' is a list of exactly 2 simple questions a young child can answer after reading, like 'What is the main thing you learned?'"
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema, written for young children as clear absolute facts. "
            "Each section includes cognitive_load (a low float near 0.1–0.3), emotional_valence (one of the 5 allowed values), and review_prompts (2 simple recall questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


def _build_multiplist_crew(topic: str, num_sections: int, words_per_section: int) -> Crew:
    """Adolescence stage (11-17): all viewpoints are equally valid, no evaluation."""
    gemini_llm = LLM(model="gemini/gemini-3.5-flash", api_key=API_KEY)

    researcher = Agent(
        role="Perspective Collector",
        goal=f"Gather {num_sections} different viewpoints that people hold about {topic}, without judging which is best.",
        backstory=(
            "You are an open-minded explorer who believes everyone's opinion deserves to be heard. "
            "You collect perspectives from all sides without deciding who is right. "
            "You present each viewpoint fairly and equally, because you know truth is subjective "
            "and different people see things differently. You never conclude one view is better than another."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Opinion Journalist",
        goal="Present multiple perspectives on a topic in a conversational way, without picking a winner.",
        backstory=(
            "You are a conversational writer who speaks to teenagers and young adults. "
            "You use casual, engaging language and present all sides of a debate equally. "
            "You never conclude which view is correct — you say things like 'some people think', "
            "'others argue', 'it depends on your perspective'. "
            "Your readers should feel that all opinions are valid and worth considering."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Collect {num_sections} distinct viewpoints or perspectives that people hold about '{topic}'. "
            f"For each perspective, describe who holds it and why they believe it. "
            f"Do NOT evaluate which perspective is better — just present them all fairly."
        ),
        expected_output=f"A bulleted list of {num_sections} different perspectives on {topic}, each described without judgment.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the perspectives provided, write a blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Each section presents a different viewpoint in a casual, conversational tone. "
            f"Never conclude which view is correct. Use phrases like 'some people believe', "
            f"'others feel', 'it really depends on your own experience'. "
            f"The tone should feel like a thoughtful teen exploring different ideas. "
            f"For each section, include three extra fields. "
            f"'cognitive_load': a decimal 0.0–1.0 showing how mentally demanding the section is — conversational sections should be around 0.3–0.5. "
            f"'emotional_valence': exactly one of uplifting, neutral, cautionary, reflective, mixed based on the overall vibe. "
            f"'review_prompts': a list of 2–3 casual questions someone could ask themselves after reading, like 'What perspective surprised you most?'"
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema, presenting multiple equal perspectives without evaluation. "
            "Each section includes cognitive_load (float roughly 0.3–0.5), emotional_valence (one of the 5 allowed values), and review_prompts (2–3 casual recall questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


def _build_evaluativist_crew(topic: str, num_sections: int, words_per_section: int) -> Crew:
    """Young adulthood stage (18+): evidence-based reasoning, weighing claims analytically."""
    gemini_llm = LLM(model="gemini/gemini-3.5-flash", api_key=API_KEY)

    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Uncover cutting-edge developments and trends in {topic}, evaluating evidence quality.",
        backstory=(
            "You are an expert researcher who evaluates claims based on evidence and logic. "
            "You understand that not all opinions are equal — some are better supported than others. "
            "You identify the strongest evidence, weigh conflicting data, and focus on what reasoning supports."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Tech Content Writer",
        goal="Create evidence-based blog posts that help readers evaluate claims for themselves.",
        backstory=(
            "You are a skilled analytical writer who presents arguments with supporting evidence. "
            "You help readers understand WHY certain conclusions are better supported than others. "
            "You use clarity, accuracy, and logic as your standards. You distinguish strong evidence from weak."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=f"List {num_sections} major trends or developments in {topic}, noting the evidence supporting each.",
        expected_output=f"A bulleted list of {num_sections} evidence-backed trends in {topic}.",
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Write a blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each, based on the trends provided. "
            f"Topic: {topic}. Each section should present evidence, evaluate its strength, "
            f"and help the reader understand why certain conclusions are better supported. "
            f"For each section, populate three analytical metadata fields. "
            f"'cognitive_load': a float 0.0–1.0 estimating working memory demand — analytical sections with dense evidence should score 0.5–0.75. "
            f"'emotional_valence': exactly one value from [uplifting, neutral, cautionary, reflective, mixed] based on the section's rhetorical register. "
            f"'review_prompts': 2–3 evidence-focused recall questions that test whether the reader understood the reasoning, not just the conclusion."
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema. "
            "Each section includes cognitive_load (float 0.0–1.0), emotional_valence (one of 5 allowed values), and review_prompts (2–3 analytical recall questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


def _build_master_crew(topic: str, num_sections: int, words_per_section: int) -> Crew:
    """Mature adulthood stage: habitual critical self-reflection, surfaces blind spots and uncertainty."""
    gemini_llm = LLM(model="gemini/gemini-3.5-flash", api_key=API_KEY)

    researcher = Agent(
        role="Epistemic Analyst",
        goal=(
            f"Analyze {num_sections} key claims about {topic}, explicitly surfacing assumptions, "
            f"blind spots, and genuine uncertainty in each."
        ),
        backstory=(
            "You are a master thinker who has spent decades examining not just what people know, "
            "but HOW they know it and what they might be missing. "
            "For every claim, you automatically ask: What assumptions underlie this? "
            "Where is the evidence thin? What would change this conclusion? "
            "What cognitive biases might be distorting the picture? "
            "You treat intellectual humility as a strength, not a weakness."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    writer = Agent(
        role="Reflective Scholar",
        goal="Synthesize complex ideas across frameworks while openly acknowledging limits and inviting critical reader engagement.",
        backstory=(
            "You are a distinguished scholar whose writing models the highest form of critical thinking. "
            "You use hedged, precise language ('the evidence suggests', 'one must be cautious', "
            "'this conclusion rests on the assumption that'). "
            "You synthesize across multiple frameworks and disciplines. "
            "You explicitly acknowledge what remains unknown or contested. "
            "You invite readers to examine their own priors and challenge your conclusions. "
            "Your writing does not perform certainty — it demonstrates intellectual integrity."
        ),
        verbose=True,
        llm=gemini_llm,
    )

    task1 = Task(
        description=(
            f"Analyze {num_sections} key claims, arguments, or developments related to '{topic}'. "
            f"For each, explicitly identify: the underlying assumptions, the quality and limits of supporting evidence, "
            f"where expert consensus is genuinely weak or contested, and what a thoughtful critic would challenge. "
            f"Flag your own potential blind spots in this analysis."
        ),
        expected_output=(
            f"A structured list of {num_sections} epistemic analyses of claims about {topic}, "
            f"each including assumptions, evidence assessment, points of genuine uncertainty, and potential blind spots."
        ),
        agent=researcher,
    )

    task2 = Task(
        description=(
            f"Using the epistemic analyses provided, write a scholarly blog post with exactly {num_sections} sections, "
            f"approximately {words_per_section} words each. Topic: {topic}. "
            f"Use precise, hedged language. Synthesize across frameworks. "
            f"Explicitly acknowledge what remains uncertain or unknown. "
            f"Invite readers to question both your conclusions and their own assumptions. "
            f"The tone should model habitual critical self-reflection — confident in its reasoning process, "
            f"humble about the limits of its conclusions. "
            f"For each section, assign three epistemic-metadata fields. "
            f"'cognitive_load': a float 0.0–1.0 reflecting working-memory burden from nested qualifications and multi-framework synthesis — expect values in the 0.65–0.95 range. "
            f"'emotional_valence': one of exactly five values — uplifting, neutral, cautionary, reflective, mixed — representing the dominant epistemic-emotional register of the section. "
            f"'review_prompts': precisely 2–3 questions requiring the reader to reconstruct the core argument, identify a key assumption, and articulate one remaining point of genuine uncertainty."
        ),
        expected_output=(
            "A structured database-ready payload matching the StructuredBlogPost schema, "
            "written with master-thinker epistemic standards: hedged, self-reflective, synthesizing, and intellectually honest. "
            "Each section includes cognitive_load (float expected 0.65–0.95), emotional_valence (one of 5 allowed values), and review_prompts (2–3 deep reflective questions)."
        ),
        agent=writer,
        output_json=StructuredBlogPost,
    )

    return Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)


def run_crew_streaming(topic: str, num_sections: int, words_per_section: int, crew_type: str = "evaluativist"):
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
            if crew_type == "absolutist":
                crew = _build_absolutist_crew(topic, num_sections, words_per_section)
            elif crew_type == "multiplist":
                crew = _build_multiplist_crew(topic, num_sections, words_per_section)
            elif crew_type == "master":
                crew = _build_master_crew(topic, num_sections, words_per_section)
            else:
                crew = _build_evaluativist_crew(topic, num_sections, words_per_section)
            result = crew.kickoff()
            blog_data = result.json_dict
            if blog_data is None:
                blog_data = json.loads(result.raw)
            StructuredBlogPost(**blog_data)
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

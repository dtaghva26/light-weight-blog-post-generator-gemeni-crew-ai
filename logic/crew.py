import sys
import io
import json
import queue
import threading
from dotenv import load_dotenv
from pydantic import ValidationError

from logic.models import StructuredBlogPost
from logic.logger import get_logger

load_dotenv()

_log = get_logger("crew")


def run_crew_streaming(topic: str, num_sections: int, words_per_section: int,
                       crew_type: str = "evaluativist", subject: str = None):
    """
    Generator that yields stdout log lines from the crew run, then a
    ("RESULT", dict) tuple on success or ("ERROR", str) on failure.

    `subject` is an optional National Curriculum subject (e.g. "Science") that
    steers the Researcher toward curriculum-relevant content.
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
        _log.info("run_start  crew_type=%s  topic=%r  sections=%d  words=%d  subject=%s",
                  crew_type, topic, num_sections, words_per_section, subject)
        old_stdout = sys.stdout
        sys.stdout = QueueWriter()
        try:
            from modes.registry import get as get_mode
            crew = get_mode(crew_type).build_crew(topic, num_sections, words_per_section, subject=subject)
            result = crew.kickoff()
            blog_data = result.json_dict
            if blog_data is None:
                blog_data = json.loads(result.raw)
            StructuredBlogPost(**blog_data)
            _log.info("run_success  crew_type=%s  title=%r  sections=%d",
                      crew_type, blog_data.get("title", ""), len(blog_data.get("sections", [])))
            log_q.put(("RESULT", blog_data))
        except ValidationError as e:
            _log.error("run_validation_error  crew_type=%s  error=%s", crew_type, e)
            log_q.put(("ERROR", f"LLM returned invalid structure: {e}"))
        except Exception as e:
            _log.error("run_error  crew_type=%s  error=%s", crew_type, e, exc_info=True)
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

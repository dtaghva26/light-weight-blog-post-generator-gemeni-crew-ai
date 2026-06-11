import sys
import io
import json
import queue
import threading
from dotenv import load_dotenv
from pydantic import ValidationError

from logic.models import StructuredBlogPost

load_dotenv()


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
            from modes.registry import get as get_mode
            crew = get_mode(crew_type).build_crew(topic, num_sections, words_per_section)
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

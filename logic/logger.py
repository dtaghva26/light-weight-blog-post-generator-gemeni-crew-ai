import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGS_DIR = Path("logs")
_LOG_FILE = _LOGS_DIR / "app.log"
_FMT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    _LOGS_DIR.mkdir(exist_ok=True)

    root = logging.getLogger("multiagent")
    root.setLevel(logging.DEBUG)

    # Rotating file — 5 MB cap, keep 3 backups
    fh = RotatingFileHandler(_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # Console — INFO and above only, so it doesn't flood the terminal
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(f"multiagent.{name}")

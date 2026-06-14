"""Single logging setup: all logs go to app.log in the project root.

Every module uses logging.getLogger(...) and its records propagate up to the
root logger configured here, so one FileHandler captures everything.
"""
import logging
from pathlib import Path

from app.config import LOG_LEVEL

# app.log in the project root (parent of the app/ package), regardless of CWD.
LOG_FILE = Path(__file__).resolve().parent.parent / "app.log"


def setup_logging(level: str = LOG_LEVEL) -> None:
    """Attach a FileHandler to the root logger once."""
    root = logging.getLogger()
    root.setLevel(level)
    # Idempotent: don't add a second file handler on repeat calls.
    if any(isinstance(h, logging.FileHandler) for h in root.handlers):
        return
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-7s %(name)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)

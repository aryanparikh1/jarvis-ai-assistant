"""
Jarvis Logger
=============
Structured logging using loguru. Outputs to console (rich) and rotating file.
"""

import sys
from pathlib import Path
from loguru import logger as _logger

from jarvis.utils.config import config


def _setup_logger():
    _logger.remove()  # Remove default handler

    level = config.get("log_level", "INFO")

    # ── Console handler (colorized) ─────────────────────────────────────────
    _logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        backtrace=True,
        diagnose=True,
    )

    # ── File handler (rotating, max 10MB, keep 7 days) ──────────────────────
    if config.get("log_to_file", True):
        log_file = config.logs_dir / "jarvis.log"
        _logger.add(
            str(log_file),
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                "{name}:{function}:{line} — {message}"
            ),
            backtrace=True,
            diagnose=False,  # No sensitive info in file
        )

    return _logger


logger = _setup_logger()

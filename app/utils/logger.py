"""Shared logging setup used by the GUI and feature modules."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from app.config.settings import APP_NAME


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid adding duplicate handlers

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    # A PyInstaller --windowed build has no console attached, so sys.stdout
    # is None (not just closed) - StreamHandler(None) would raise the first
    # time anything gets logged. Only add the console handler when there's
    # an actual stream to write to; the file handler below covers logging
    # for windowed builds regardless.
    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    app_data = os.environ.get("APPDATA") or str(Path.home())
    log_dir = Path(app_data) / APP_NAME / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

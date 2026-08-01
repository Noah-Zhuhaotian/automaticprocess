"""Application entry point: launches the GUI main window."""

from __future__ import annotations

from app.gui.main_window import run
from app.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Application starting")
    run()


if __name__ == "__main__":
    main()

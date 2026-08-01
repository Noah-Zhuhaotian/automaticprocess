"""Step 3: automatically submit content to the timesheet/info website.

The actual interaction method (form structure, browser automation vs. API,
etc.) will be implemented once the website details are known.
"""

from __future__ import annotations

from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


def submit_to_website(website_url: str, data: dict[str, Any]) -> bool:
    """Submit data to website_url, returning whether it succeeded."""
    raise NotImplementedError

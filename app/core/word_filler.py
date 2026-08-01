"""Step 2: automatically fill user-provided content into a Word document.

The actual template field mapping will be implemented once the Word
template format is decided.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


def fill_word(template_path: str, output_path: str, data: dict[str, Any]) -> Path:
    """Fill the Word template at template_path with data and save as output_path."""
    raise NotImplementedError

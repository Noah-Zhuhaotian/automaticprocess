"""Switching to a shared data folder (Settings): bring this PC's saved
projects, templates and dropdown lists along, so nothing someone already
saved disappears when the office starts sharing - and two PCs switching to
the same folder end up with everything from both.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.config.settings import SHARED_LIST_KEYS, load_shared_lists
from app.utils.logger import get_logger

logger = get_logger(__name__)

DATA_SUBFOLDERS = ("projects", "templates")


def copy_saved_data(source: Path, target: Path) -> dict[str, int]:
    """Copy projects/*.json and templates/*.json from source to target,
    never overwriting (a file already there - the shared copy - wins).
    Returns how many of each were copied."""
    copied = {}
    for name in DATA_SUBFOLDERS:
        (target / name).mkdir(parents=True, exist_ok=True)
        count = 0
        for path in sorted((source / name).glob("*.json")):
            destination = target / name / path.name
            if not destination.exists():
                shutil.copy2(path, destination)
                count += 1
        copied[name] = count
    logger.info("Copied saved data %s -> %s: %s", source, target, copied)
    return copied


def _list_key(key: str, item: Any) -> Any:
    """What makes two entries of a list "the same" when merging."""
    if key == "inspection_other_items":
        return str(item.get("description", "")).casefold()
    if key == "legal_description_formats":
        return tuple(str(part).casefold() for part in item)
    return str(item).casefold()


def merged_lists(folder: Path, settings: dict[str, Any]) -> dict[str, list[Any]]:
    """The folder's shared lists with this PC's entries that aren't in them
    yet appended (shared entries keep their order and spelling)."""
    shared = load_shared_lists(str(folder)) or {}
    merged = {}
    for key in SHARED_LIST_KEYS:
        items = list(shared.get(key, []))
        seen = {_list_key(key, item) for item in items}
        for item in settings.get(key, []):
            if _list_key(key, item) not in seen:
                items.append(item)
                seen.add(_list_key(key, item))
        merged[key] = items
    return merged

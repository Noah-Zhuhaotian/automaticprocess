"""Saved wizard input per project, so a project made with this app can be
opened again later and its documents regenerated with changes.

One JSON file per project, named by job number (unique per job), in
%APPDATA%\\AutomaticProcess\\projects\\ - next to user_settings.json and the
logs, deliberately *not* inside the project folders themselves, and not in
the install directory either: the installer only replaces files under
Program Files, so app updates (and uninstalls) leave this data alone.

Local to this computer/Windows account by design (single-user for now); a
shared location would be a later, separate change.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from app.config.settings import get_settings_path
from app.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_VERSION = 1

# Characters not allowed in Windows file names (job numbers normally have none).
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def projects_dir() -> Path:
    directory = get_settings_path().parent / "projects"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _project_path(job_number: str) -> Path:
    safe = _INVALID_CHARS.sub("-", job_number.strip())
    return projects_dir() / f"{safe}.json"


def save_project(job_number: str, data: dict[str, Any]) -> Path:
    """Write the project's data atomically (temp file + replace), so a crash
    mid-write can never leave a half-written, unreadable file behind."""
    path = _project_path(job_number)
    payload = {"schema_version": SCHEMA_VERSION, **data}
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    logger.info("Saved project data for job %s -> %s", job_number, path)
    return path


def load_project(job_number: str) -> dict[str, Any] | None:
    """The saved data for this job number, or None if there is none (or it
    can't be read - logged, never raised, so a damaged file only means the
    wizard starts blank for that project)."""
    path = _project_path(job_number)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        logger.exception("Couldn't read saved project data %s", path)
        return None


def saved_job_numbers() -> set[str]:
    """Job numbers (case-folded) that have saved data."""
    return {path.stem.casefold() for path in projects_dir().glob("*.json")}

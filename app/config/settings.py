"""Persistent app configuration (saved base folder, Word template path,
website URL, etc.).

Settings are stored as JSON in the user's local app-data directory, kept
out of source control, so each machine has its own configuration.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

APP_NAME = "AutomaticProcess"

DEFAULT_SETTINGS: dict[str, Any] = {
    # Step 1: root path of each drive that gets a project folder.
    # User-configurable so it keeps working when these move from the NAS
    # to OneDrive/SharePoint later - just point the setting at the new path.
    "engineer_drive": "",
    "drafting_drive": "",
    "admin_drive": "",
    "word_template": "",     # Step 2: Word template file path
    "website_url": "",       # Step 3: timesheet/info website URL
    "council_names": [],     # user-maintained list, e.g. for the PS1 Input step
}


def get_settings_path() -> Path:
    app_data = os.environ.get("APPDATA") or str(Path.home())
    settings_dir = Path(app_data) / APP_NAME
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "user_settings.json"


def load_settings() -> dict[str, Any]:
    path = get_settings_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_SETTINGS)

    with path.open("r", encoding="utf-8") as f:
        saved = json.load(f)

    merged = copy.deepcopy(DEFAULT_SETTINGS)
    merged.update(saved)
    return merged


def save_settings(settings: dict[str, Any]) -> None:
    path = get_settings_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

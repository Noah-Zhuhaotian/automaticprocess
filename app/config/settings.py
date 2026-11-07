"""Persistent app configuration (saved base folder, Word template path,
MinuteDock access token, etc.).

Settings are stored as JSON in the user's local app-data directory, kept
out of source control, so each machine has its own configuration.

Optionally a shared data folder (e.g. on the NAS) holds what the office
shares: the saved projects and templates (project_store/template_store put
them under data_dir()) and the user-maintained dropdown lists
(SHARED_LIST_KEYS, in shared_settings.json there). Drive paths, the
MinuteDock token and the logs always stay per-PC.
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
    "minutedock_access_token": "",  # Step 3: MinuteDock Personal Access Token (required, set during Settings)
    # Optional folder (e.g. on the NAS) shared by everyone using the app -
    # see the module docstring. "" = everything stays on this PC.
    "shared_data_folder": "",
    "council_names": [],     # user-maintained list, e.g. for the PS1 Input step
    "description_of_work_names": [],  # same, for PS1 Input's Description of work
    # PS1 Legal description "Other" formats as [first label, second label],
    # e.g. ["Section", "SO"] -> "Section 3 SO 1234" (Lot/DP is built in).
    "legal_description_formats": [],
    # Inspection Schedule "Other" items used before, offered again in each
    # Other row's dropdown: [{"description": ..., "time_frame": ...}, ...]
    "inspection_other_items": [],
    # User-maintained Suburb / Town lists for the General step's (and the
    # batch Jobs table's) dropdowns - Add/Edit on the General step.
    "suburb_names": [],
    "town_names": [],
}

# The dropdown lists kept in the shared data folder when one is set.
SHARED_LIST_KEYS = (
    "council_names",
    "description_of_work_names",
    "legal_description_formats",
    "inspection_other_items",
    "suburb_names",
    "town_names",
)
SHARED_SETTINGS_FILE = "shared_settings.json"

# The shared data folder in effect, set by load_settings/save_settings. A
# module value (not passed around) so project_store/template_store, also
# used from the Create worker thread, can call data_dir() without tkinter.
_shared_data_folder = ""


def get_settings_path() -> Path:
    app_data = os.environ.get("APPDATA") or str(Path.home())
    settings_dir = Path(app_data) / APP_NAME
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "user_settings.json"


def local_data_dir() -> Path:
    return get_settings_path().parent


def data_dir() -> Path:
    """Where projects/ and templates/ live: the shared data folder if one
    is set, otherwise this PC's app-data folder."""
    return Path(_shared_data_folder) if _shared_data_folder else local_data_dir()


def _write_json_atomic(path: Path, data: Any) -> None:
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_shared_lists(folder: str) -> dict[str, Any] | None:
    """The dropdown lists saved in `folder`, or None if it has none yet.
    Raises OSError/ValueError if the file can't be read."""
    path = Path(folder) / SHARED_SETTINGS_FILE
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        saved = json.load(f)
    return {key: saved[key] for key in SHARED_LIST_KEYS if key in saved}


def refresh_shared_lists(settings: dict[str, Any]) -> None:
    """Re-read the shared dropdown lists into `settings`, so lists another
    PC changed show up (called when a step is shown). Keeps the current
    values if the shared folder can't be read right now (e.g. the NAS is
    offline)."""
    folder = settings.get("shared_data_folder", "").strip()
    if not folder:
        return
    try:
        shared = load_shared_lists(folder)
    except (OSError, ValueError):
        from app.utils.logger import get_logger

        get_logger(__name__).warning("Couldn't read shared lists from %s", folder, exc_info=True)
        return
    if shared:
        settings.update(copy.deepcopy(shared))


def load_settings() -> dict[str, Any]:
    global _shared_data_folder
    path = get_settings_path()
    merged = copy.deepcopy(DEFAULT_SETTINGS)
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            merged.update(json.load(f))
    _shared_data_folder = merged.get("shared_data_folder", "").strip()
    refresh_shared_lists(merged)
    return merged


def save_settings(settings: dict[str, Any]) -> None:
    """Save this PC's settings, and - with a shared data folder - the
    dropdown lists to that folder too (raises OSError if it can't be
    written). The local file keeps its own copy of the lists as well."""
    global _shared_data_folder
    _write_json_atomic(get_settings_path(), settings)
    _shared_data_folder = settings.get("shared_data_folder", "").strip()
    if _shared_data_folder:
        _write_json_atomic(
            Path(_shared_data_folder) / SHARED_SETTINGS_FILE,
            {key: settings.get(key, copy.deepcopy(DEFAULT_SETTINGS[key])) for key in SHARED_LIST_KEYS},
        )

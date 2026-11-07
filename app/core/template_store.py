"""Reusable project templates: everything the wizard collects *except* the
per-job General fields (job number, client, street, suburb, town) and the
PS1 date - Scope, Role, PS1, Inspection Schedule, Waivers, Specification,
B2 Letter and the MinuteDock budget. Used to start a new job (or a batch of
jobs) pre-filled.

One JSON file per template in <data_dir>\\templates\\ (the shared data
folder if one is set, otherwise %APPDATA%\\AutomaticProcess), next to the
per-project saves (app/core/project_store.py) and, like them, outside the
install directory, so app updates and uninstalls leave them alone.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from app.config.settings import data_dir
from app.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_VERSION = 1

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


class TemplateError(Exception):
    """A template name that can't be used (empty, invalid, or taken)."""


def templates_dir() -> Path:
    directory = data_dir() / "templates"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _path(name: str) -> Path:
    return templates_dir() / f"{name}.json"


def clean_name(name: str) -> str:
    """Validate a template name for use as a file name (raises TemplateError)."""
    name = name.strip()
    if not name:
        raise TemplateError("Template name can't be empty.")
    if _INVALID_CHARS.search(name):
        raise TemplateError('Template name can\'t contain any of \\ / : * ? " < > |')
    return name


def list_templates() -> list[str]:
    return sorted((path.stem for path in templates_dir().glob("*.json")), key=str.casefold)


def exists(name: str) -> bool:
    return _path(name.strip()).exists()


def load_template(name: str) -> dict[str, Any] | None:
    path = _path(name)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        logger.exception("Couldn't read template %s", path)
        return None


def save_template(name: str, data: dict[str, Any]) -> Path:
    """Write (or overwrite) a template atomically."""
    name = clean_name(name)
    path = _path(name)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump({"schema_version": SCHEMA_VERSION, "name": name, **data}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    logger.info("Saved template %r -> %s", name, path)
    return path


def rename_template(old: str, new: str) -> None:
    new = clean_name(new)
    if new == old:
        return
    if new.casefold() != old.casefold() and exists(new):
        raise TemplateError(f'A template named "{new}" already exists.')
    data = load_template(old) or {}
    save_template(new, {k: v for k, v in data.items() if k not in ("schema_version", "name")})
    if new.casefold() != old.casefold():
        _path(old).unlink(missing_ok=True)


def delete_template(name: str) -> None:
    _path(name).unlink(missing_ok=True)
    logger.info("Deleted template %r", name)

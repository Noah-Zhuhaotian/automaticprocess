"""Self-update from the project's GitHub releases.

Pure logic, no tkinter - safe to call from a worker thread. The GUI side is
app/gui/update_check.py.

- check_for_update(): GET /repos/{GITHUB_REPO}/releases/latest (public repo,
  no token; GitHub allows 60 unauthenticated calls/hour per IP, plenty for
  a manual "Check for updates" button). A release is an update when its
  tag ("v1.2.3") is newer than app/version.py's __version__ and it has an
  asset named SETUP_ASSET_NAME (.github/workflows/release.yml uploads it).
- download_installer(): streams that asset to %TEMP%, checks its size and,
  when GitHub reports one, its SHA-256 digest.
- launch_installer(): starts it silently via ShellExecute (os.startfile) -
  the installer elevates itself (UAC) to write Program Files. The caller
  then closes the app; the installer's Restart Manager support
  (/CLOSEAPPLICATIONS) covers the case where it hasn't exited yet, and
  installer.iss relaunches the app after a silent install.

User data lives in %APPDATA%\\AutomaticProcess, which the installer never
touches, so an upgrade keeps settings, saved projects and templates.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

from app.utils.logger import get_logger
from app.version import __version__

logger = get_logger(__name__)

GITHUB_REPO = "Noah-Zhuhaotian/automaticprocess"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SETUP_ASSET_NAME = "AutomaticProcess-Setup.exe"
INSTALLER_ARGS = "/SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS"
CHECK_TIMEOUT = 15
DOWNLOAD_CHUNK = 256 * 1024


class UpdateError(Exception):
    """Raised for any update failure - network, GitHub, or a bad download."""


def parse_version(text: str) -> tuple[int, ...] | None:
    """A tag like "v1.2.3" or "1.2.3" -> (1, 2, 3); None if it isn't
    purely numeric."""
    parts = text.strip().lstrip("vV").split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def is_newer(tag: str, current: str = __version__) -> bool:
    latest, installed = parse_version(tag), parse_version(current)
    if latest is None or installed is None:
        logger.warning("Can't compare versions %r and %r", tag, current)
        return False
    return latest > installed


def is_packaged() -> bool:
    """True in the PyInstaller build; False when run with `python main.py`,
    where installing would update the installed copy, not this one."""
    return bool(getattr(sys, "frozen", False))


def check_for_update() -> dict[str, Any] | None:
    """The latest release as {"version", "notes", "url", "size", "sha256"}
    if it's newer than this app and has an installer, else None."""
    try:
        response = requests.get(
            LATEST_RELEASE_URL,
            headers={"Accept": "application/vnd.github+json"},
            timeout=CHECK_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise UpdateError(f"Could not reach GitHub: {exc}") from exc
    if response.status_code == 404:
        return None  # no published release yet
    if response.status_code >= 400:
        raise UpdateError(f"GitHub returned {response.status_code}: {response.text[:200]}")

    release = response.json()
    tag = release.get("tag_name", "")
    if not is_newer(tag):
        return None
    asset = next((a for a in release.get("assets", []) if a.get("name") == SETUP_ASSET_NAME), None)
    if asset is None:
        logger.warning("Release %s has no %s asset - not offered as an update", tag, SETUP_ASSET_NAME)
        return None

    digest = asset.get("digest") or ""
    return {
        "version": tag.lstrip("vV"),
        "notes": (release.get("body") or "").strip(),
        "url": asset["browser_download_url"],
        "size": asset.get("size") or 0,
        "sha256": digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else None,
    }


def download_installer(update: dict[str, Any], on_progress: Callable[[int, int], None] | None = None) -> Path:
    """Download the update's installer to a temp folder and verify it.
    on_progress(done_bytes, total_bytes) is called from this (worker)
    thread - it must not touch tkinter."""
    target_dir = Path(tempfile.gettempdir()) / "AutomaticProcess-update"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"AutomaticProcess-Setup-{update['version']}.exe"
    partial = target.with_suffix(".part")

    sha256 = hashlib.sha256()
    done = 0
    try:
        with requests.get(update["url"], stream=True, timeout=CHECK_TIMEOUT) as response:
            if response.status_code >= 400:
                raise UpdateError(f"Download failed: GitHub returned {response.status_code}")
            total = update["size"] or int(response.headers.get("Content-Length") or 0)
            with open(partial, "wb") as handle:
                for chunk in response.iter_content(DOWNLOAD_CHUNK):
                    handle.write(chunk)
                    sha256.update(chunk)
                    done += len(chunk)
                    if on_progress is not None:
                        on_progress(done, total)
    except requests.RequestException as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"Download failed: {exc}") from exc
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"Could not save the installer: {exc}") from exc

    if update["size"] and done != update["size"]:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"Download incomplete ({done} of {update['size']} bytes) - please try again.")
    if update["sha256"] and sha256.hexdigest() != update["sha256"]:
        partial.unlink(missing_ok=True)
        raise UpdateError("The downloaded installer failed its checksum - please try again.")

    os.replace(partial, target)
    logger.info("Downloaded update %s to %s", update["version"], target)
    return target


def launch_installer(installer: Path) -> None:
    """Start the installer silently. Raises UpdateError if Windows refuses
    to start it (e.g. the user cancelled the UAC prompt)."""
    try:
        os.startfile(str(installer), arguments=INSTALLER_ARGS)
    except OSError as exc:
        raise UpdateError(f"Could not start the installer: {exc}") from exc
    logger.info("Started installer %s %s", installer, INSTALLER_ARGS)

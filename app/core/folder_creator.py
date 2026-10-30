"""Step 1: automatically create the project folder structure across the
three drives (Engineer, Drafting, Admin).

Naming rule: "{job_number} - {street}", e.g. "1234 - 211 Ferry Rd". Only
the street (not suburb/town) feeds the folder name. The same project
folder name is used on all three drives. Only the Engineer drive gets
the fixed set of subfolders; Drafting and Admin only get the bare
project folder.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Fixed subfolders created only under the Engineer drive's project folder.
ENGINEER_SUBFOLDERS = [
    "01 Architectural",
    "02 Design",
    "03 Drawings",
    "04 Construction Monitoring",
    "05 Soil",
    "06 Consent Document",
]

# Characters not allowed in Windows file/folder names.
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def build_project_folder_name(job_number: str, street: str) -> str:
    job_number = job_number.strip()
    street = street.strip()
    if not job_number:
        raise ValueError("Job number is required.")
    if not street:
        raise ValueError("Street is required.")

    name = f"{job_number} - {street}"
    return _INVALID_CHARS.sub("-", name)


def _project_targets(
    job_number: str,
    street: str,
    engineer_drive: str,
    drafting_drive: str,
    admin_drive: str,
    *,
    require_all_configured: bool,
) -> dict[str, Path]:
    project_name = build_project_folder_name(job_number, street)

    drives = {
        "engineer": engineer_drive,
        "drafting": drafting_drive,
        "admin": admin_drive,
    }

    targets: dict[str, Path] = {}
    for drive_name, drive_root in drives.items():
        if not drive_root.strip():
            if require_all_configured:
                raise ValueError(f"The {drive_name} drive path is not configured yet. Set it in Settings.")
            continue
        targets[drive_name] = Path(drive_root) / project_name

    return targets


def check_availability(
    job_number: str,
    street: str,
    engineer_drive: str,
    drafting_drive: str,
    admin_drive: str,
) -> list[Path]:
    """Cheap existence check for the "live" UI status, without creating anything.

    Only checks the exact target path on each configured drive (no
    directory listing). Drives that aren't configured yet are silently
    skipped rather than raising, since this is meant to run while the
    user is still filling in the form. Returns the list of paths that
    already exist (empty means the name is available).
    """
    targets = _project_targets(
        job_number, street, engineer_drive, drafting_drive, admin_drive, require_all_configured=False
    )
    return [path for path in targets.values() if path.exists()]


def parse_project_folder_name(name: str) -> tuple[str, str] | None:
    """Split a folder name in this app's "{job_number} - {street}" format
    back into (job_number, street). Returns None for any folder not in that
    format (no " - ", or an empty job number or street) - those aren't
    project folders this app made, so callers skip them."""
    job_number, separator, street = name.partition(" - ")
    job_number, street = job_number.strip(), street.strip()
    if not separator or not job_number or not street:
        return None
    return job_number, street


def find_job_number_conflicts(
    job_number: str,
    engineer_drive: str,
    drafting_drive: str,
    admin_drive: str,
) -> list[Path]:
    """Job numbers are unique per job regardless of street: every project
    folder on every configured drive is parsed back into its job number
    (parse_project_folder_name - folders not in the "{job_number} -
    {street}" format are skipped), and any whose job number equals this one
    (case-insensitive) is a conflict, whatever its street. Unconfigured or
    unreachable drives are skipped rather than raising.
    """
    target = job_number.strip().casefold()
    if not target:
        return []

    conflicts: list[Path] = []
    for drive_root in (engineer_drive, drafting_drive, admin_drive):
        drive_root = drive_root.strip()
        if not drive_root:
            continue
        root = Path(drive_root)
        try:
            if not root.is_dir():
                continue
            for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if not entry.is_dir():
                    continue
                parsed = parse_project_folder_name(entry.name)
                if parsed is not None and parsed[0].casefold() == target:
                    conflicts.append(entry)
        except OSError:
            continue
    return conflicts


def list_available_project_folders(engineer_drive: str) -> list[str]:
    """Project folders on the Engineer drive with no documents yet in "06
    Consent Document" - candidates for "fill documents into an existing
    folder" mode (app/gui/steps/mode_step.py). A folder qualifies if its
    name follows the "{job_number} - {street}" convention (so it can be
    split back apart the same way build_project_folder_name built it) and
    its "06 Consent Document" subfolder is missing or has zero files in it.
    """
    engineer_drive = engineer_drive.strip()
    if not engineer_drive:
        return []
    root = Path(engineer_drive)
    if not root.is_dir():
        return []

    candidates: list[str] = []
    try:
        for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir() or parse_project_folder_name(entry.name) is None:
                continue
            consent_dir = entry / "06 Consent Document"
            if not consent_dir.is_dir() or not any(consent_dir.iterdir()):
                candidates.append(entry.name)
    except OSError:
        return []
    return candidates


def create_project_folders(
    job_number: str,
    street: str,
    engineer_drive: str,
    drafting_drive: str,
    admin_drive: str,
) -> dict[str, Path]:
    """Create the project folder on each configured drive.

    Returns a dict mapping drive name -> created folder path. Raises
    FileExistsError (listing every conflict) without creating anything if
    the project folder already exists on any drive, and raises ValueError
    if a drive path has not been configured yet.
    """
    targets = _project_targets(
        job_number, street, engineer_drive, drafting_drive, admin_drive, require_all_configured=True
    )

    conflicts = [str(path) for path in targets.values() if path.exists()]
    if conflicts:
        raise FileExistsError(
            "The project folder already exists, nothing was created:\n" + "\n".join(conflicts)
        )

    created: dict[str, Path] = {}
    for drive_name, path in targets.items():
        path.mkdir(parents=True)
        created[drive_name] = path
        logger.info("Created folder: %s", path)

    for subfolder in ENGINEER_SUBFOLDERS:
        (created["engineer"] / subfolder).mkdir()

    return created

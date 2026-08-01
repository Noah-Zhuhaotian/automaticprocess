"""Step 1: automatically create the project folder structure across the
three drives (Engineer, Drafting, Admin).

Naming rule: "{job_number} - {address}", e.g. "1234 - 211 Ferry Rd".
The same project folder name is used on all three drives. Only the
Engineer drive gets the fixed set of subfolders; Drafting and Admin only
get the bare project folder.
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
]

# Characters not allowed in Windows file/folder names.
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def build_project_folder_name(job_number: str, address: str) -> str:
    job_number = job_number.strip()
    address = address.strip()
    if not job_number:
        raise ValueError("Job number is required.")
    if not address:
        raise ValueError("Address is required.")

    name = f"{job_number} - {address}"
    return _INVALID_CHARS.sub("-", name)


def create_project_folders(
    job_number: str,
    address: str,
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
    project_name = build_project_folder_name(job_number, address)

    drives = {
        "engineer": engineer_drive,
        "drafting": drafting_drive,
        "admin": admin_drive,
    }

    targets: dict[str, Path] = {}
    for drive_name, drive_root in drives.items():
        if not drive_root.strip():
            raise ValueError(f"The {drive_name} drive path is not configured yet. Set it in Settings.")
        targets[drive_name] = Path(drive_root) / project_name

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

"""Step 3: sync project data to MinuteDock (https://minutedock.com).

Business logic on top of app/core/minutedock_client.py's thin API wrapper:
decides *what* to find-or-create and in what order. Find-or-create (not
create-only) for both the Contact and the Project matters because
_on_create in review_step.py can plausibly be re-run for the same job (e.g.
retrying after an earlier Word-doc-fill failure left folders already
created) - re-running this must not create duplicate MinuteDock records.
"""

from __future__ import annotations

from typing import Any

from app.core import minutedock_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


def sync_to_minutedock(
    access_token: str,
    *,
    client_name: str,
    project_name: str,
    billable: bool,
    standard_rate_dollars: str | None,
) -> dict[str, Any]:
    """Find-or-create the MinuteDock Contact and Project for this job.

    Returns {"contact": {...}, "project": {...}}. Raises
    minutedock_client.MinuteDockError on any failure.
    """
    contact = minutedock_client.find_or_create_contact(access_token, client_name)
    project = minutedock_client.find_or_create_project(
        access_token,
        contact_id=contact["id"],
        name=project_name,
        billable=billable,
        default_rate_dollars=standard_rate_dollars,
    )
    logger.info("Synced to MinuteDock: contact %r, project %r", contact.get("name"), project.get("name"))
    return {"contact": contact, "project": project}

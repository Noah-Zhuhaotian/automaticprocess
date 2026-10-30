"""Batch creation: several jobs from one template ("batch" Create mode).

The Create-mode step applies the chosen template to every document step;
this "Jobs" step is a table of the per-job General fields only (job number,
client, street, suburb, town), one row per job. On Create each row becomes
a full normal job (folders + documents + MinuteDock), run one after another
in the background; a failed job doesn't stop the rest, and the results are
listed at the end. Jobs that weren't created at all stay in the table so
they can be fixed and retried.
"""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.core import folder_creator, minutedock_client, project_store
from app.core.minutedock_client import MinuteDockError
from app.gui.constants import MONTH_NAMES
from app.utils.logger import get_logger

logger = get_logger(__name__)

BATCH_FIELDS = [
    ("job_number", "Job number", 10),
    ("client_info", "Client", 20),
    ("street", "Street", 22),
    ("suburb", "Suburb", 14),
    ("town", "Town", 12),
]


class BatchStepMixin:
    def _init_batch_vars(self) -> None:
        # One dict of StringVars per job row, keyed by BATCH_FIELDS keys.
        self.batch_rows: list[dict[str, tk.StringVar]] = []
        self._batch_rows_frame: ttk.Frame | None = None

    def _new_batch_row(self, values: dict[str, str] | None = None) -> dict[str, tk.StringVar]:
        return {key: tk.StringVar(value=(values or {}).get(key, "")) for key, _label, _width in BATCH_FIELDS}

    # ---------- Step: Jobs ----------
    def _build_batch_step(self, parent: ttk.Frame) -> None:
        if not self.batch_rows:
            self.batch_rows = [self._new_batch_row()]

        ttk.Label(
            parent,
            text=(
                f'Each row is one job created from the template "{self._applied_template}". '
                "Only these General details differ per job - everything else comes from the template. "
                "Client: pick an existing MinuteDock contact or type a new name (added to MinuteDock on Create)."
            ),
            wraplength=700,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._batch_rows_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self._batch_rows_frame, anchor="nw")
        self._batch_rows_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

        ttk.Button(parent, text="Add job", command=self._add_batch_row).pack(anchor="w", pady=(8, 0))
        self._render_batch_rows()

    def _render_batch_rows(self) -> None:
        frame = self._batch_rows_frame
        if frame is None or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            child.destroy()

        contact_names = self._batch_contact_names()
        ttk.Label(frame, text="#").grid(row=0, column=0, sticky="w")
        for col, (_key, label, _width) in enumerate(BATCH_FIELDS, start=1):
            ttk.Label(frame, text=label).grid(row=0, column=col, sticky="w", padx=2)
        for row_index, row in enumerate(self.batch_rows, start=1):
            ttk.Label(frame, text=str(row_index)).grid(row=row_index, column=0, sticky="w", pady=2)
            for col, (key, _label, width) in enumerate(BATCH_FIELDS, start=1):
                if key == "client_info":
                    widget = ttk.Combobox(frame, textvariable=row[key], values=contact_names, width=width)
                else:
                    widget = ttk.Entry(frame, textvariable=row[key], width=width)
                widget.grid(row=row_index, column=col, sticky="w", padx=2, pady=2)
            ttk.Button(
                frame, text="Remove", width=8, command=lambda r=row: self._remove_batch_row(r)
            ).grid(row=row_index, column=len(BATCH_FIELDS) + 1, padx=(4, 0), pady=2)

    def _batch_contact_names(self) -> list[str]:
        """Existing MinuteDock contacts for the Client dropdowns (shares the
        General step's cache). Empty if MinuteDock can't be reached - the
        boxes still accept a typed name."""
        if self._minutedock_contact_names is None:
            token = self.settings.get("minutedock_access_token", "").strip()
            try:
                contacts = minutedock_client.list_contacts(token)
            except MinuteDockError:
                logger.warning("Couldn't load MinuteDock contacts for the batch table", exc_info=True)
                return []
            self._minutedock_contact_names = sorted(
                {str(c.get("name", "")).strip() for c in contacts if str(c.get("name", "")).strip()},
                key=str.casefold,
            )
        return list(self._minutedock_contact_names)

    def _add_batch_row(self) -> None:
        self.batch_rows.append(self._new_batch_row())
        self._render_batch_rows()

    def _remove_batch_row(self, row: dict[str, tk.StringVar]) -> None:
        self.batch_rows = [r for r in self.batch_rows if r is not row]
        if not self.batch_rows:
            self.batch_rows = [self._new_batch_row()]
        self._render_batch_rows()

    def _batch_values(self) -> list[dict[str, str]]:
        """Non-blank rows, stripped."""
        rows = [{key: var.get().strip() for key, var in row.items()} for row in self.batch_rows]
        return [row for row in rows if any(row.values())]

    def _validate_batch_step(self) -> bool:
        rows = self._batch_values()
        if not rows:
            messagebox.showerror("Missing info", "Add at least one job.")
            return False

        problems: list[str] = []
        labels = {key: label for key, label, _width in BATCH_FIELDS}
        seen: dict[str, int] = {}
        for index, row in enumerate(rows, start=1):
            missing = [labels[key] for key, value in row.items() if not value]
            if missing:
                problems.append(f"Row {index}: {', '.join(missing)} missing")
            job = row["job_number"].casefold()
            if job:
                if job in seen:
                    problems.append(f"Row {index}: job number {row['job_number']} is also in row {seen[job]}")
                else:
                    seen[job] = index
        if problems:
            messagebox.showerror("Check the jobs", "\n".join(problems))
            return False

        # Every job number must be unused on the drives and in MinuteDock
        # (active and archived projects), same rule as a single job.
        token = self.settings.get("minutedock_access_token", "").strip()
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            projects = minutedock_client.list_projects(token)
            projects += minutedock_client._request(
                "GET", token, "/projects", params={"active": "false"}, timeout=minutedock_client.LIST_TIMEOUT
            )
        except MinuteDockError as exc:
            messagebox.showerror(
                "Can't check MinuteDock",
                f"Couldn't check whether these job numbers are already used in MinuteDock:\n{exc}",
            )
            return False
        finally:
            self.config(cursor="")
        used_short_codes = {str(p.get("short_code", "")).strip().casefold() for p in projects}

        for index, row in enumerate(rows, start=1):
            conflicts = folder_creator.find_job_number_conflicts(
                row["job_number"],
                self.settings.get("engineer_drive", ""),
                self.settings.get("drafting_drive", ""),
                self.settings.get("admin_drive", ""),
            )
            if conflicts:
                problems.append(f"Row {index}: job number {row['job_number']} is already used by {conflicts[0]}")
            if row["job_number"].casefold() in used_short_codes:
                problems.append(f"Row {index}: job number {row['job_number']} is already a MinuteDock project")
        if problems:
            messagebox.showerror("Job number already used", "\n".join(problems))
            return False

        self.batch_rows = [self._new_batch_row(row) for row in rows]  # drop blank rows
        return True

    # ---------- Create (batch) ----------
    def _build_batch_jobs(self) -> list[dict[str, Any]]:
        """One normal "both" job per row, built on the main thread by
        loading each row into the General fields in turn - every other
        field already holds the template's values. The PS1 date is today."""
        today = datetime.date.today()
        self.date_year_var.set(str(today.year))
        self.date_month_var.set(MONTH_NAMES[today.month - 1])
        self.date_day_var.set(str(today.day))

        jobs = []
        for row in self._batch_values():
            self.job_number_var.set(row["job_number"])
            self.client_info_var.set(row["client_info"])
            self.street_var.set(row["street"])
            self.suburb_var.set(row["suburb"])
            self.town_var.set(row["town"])
            job = self._build_job()
            job["mode"] = "both"
            job["existing_minutedock_project"] = None
            job["minutedock_budget_changed"] = False
            job["project_data"] = self._collect_project_data()
            job["row"] = row
            jobs.append(job)
        return jobs

    def _run_batch_jobs(self, jobs: list[dict[str, Any]]) -> None:
        """Worker thread: each job in turn - a failure never stops the
        rest. Progress and the final results go through the queue."""
        results = []
        for index, job in enumerate(jobs, start=1):
            self._create_result_queue.put(
                {"kind": "progress", "text": f"Creating job {index} of {len(jobs)}: {job['job_number']}..."}
            )
            try:
                outcome = self._execute_job(job)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Batch job %s failed", job["job_number"])
                outcome = {"kind": "error", "message": str(exc)}
            if outcome["kind"] in ("success", "partial"):
                try:
                    project_store.save_project(job["job_number"], job["project_data"])
                except Exception:  # noqa: BLE001
                    logger.exception("Couldn't save project data for batch job %s", job["job_number"])
            results.append({"row": job["row"], "outcome": outcome})
        self._create_result_queue.put({"kind": "batch", "results": results})

    def _on_batch_done(self, results: list[dict[str, Any]]) -> None:
        lines = []
        retry_rows = []
        for result in results:
            row, outcome = result["row"], result["outcome"]
            name = f"{row['job_number']} - {row['street']}"
            if outcome["kind"] == "success":
                lines.append(f"OK       {name}")
            elif outcome["kind"] == "partial":
                lines.append(f"PARTIAL  {name}: {outcome['message']}")
            else:
                lines.append(f"FAILED   {name}: not created - {outcome['message']}")
                retry_rows.append(row)
        report = "\n".join(lines)
        self.create_result_var.set(report)

        if all(result["outcome"]["kind"] == "success" for result in results):
            self._show_success_dialog("Batch done", f"All {len(results)} jobs were created.\n\n{report}")
            self._reset_for_new_project()
            return

        created = sum(result["outcome"]["kind"] in ("success", "partial") for result in results)
        tail = (
            "\n\nJobs that weren't created are kept in the table - fix them and click Create again."
            if retry_rows
            else "\n\nUse \"Open an existing project\" to fix a partially created job."
        )
        messagebox.showwarning("Batch finished with problems", f"{created} of {len(results)} jobs created.\n\n{report}{tail}")
        if retry_rows:
            self.batch_rows = [self._new_batch_row(row) for row in retry_rows]
            jobs_index = [step["title"] for step in self.steps].index("Jobs")
            self.current_step = jobs_index
            self._show_step(jobs_index)
        else:
            self._reset_for_new_project()

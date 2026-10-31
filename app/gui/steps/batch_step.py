"""Batch creation: several jobs from one template ("batch" Create mode).

The Create-mode step applies the chosen template to every document step;
this "Jobs" step is a table of the per-job General fields only (job number,
client, street, suburb, town), one row per job, plus the PS1 date shared by
all of them (defaults to today). Clients can be existing MinuteDock contacts
or new ones ("Add new client..." / typed) - new ones are created in
MinuteDock on Create, like on the General step. On Create each row becomes
a full normal job (folders + documents + MinuteDock), run one after another
in the background; a failed job doesn't stop the rest, and the results are
listed at the end. Jobs that weren't created at all stay in the table so
they can be fixed and retried.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
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
                "Client: pick an existing MinuteDock contact, or add a new one with \"Add new client...\" "
                "(or just type it) - new clients are added to MinuteDock on Create."
            ),
            wraplength=700,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        self._build_batch_date_row(parent)

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

        buttons = ttk.Frame(parent)
        buttons.pack(anchor="w", pady=(8, 0))
        ttk.Button(buttons, text="Add job", command=self._add_batch_row).pack(side="left")
        ttk.Button(buttons, text="Add new client...", command=self._add_batch_client).pack(side="left", padx=(8, 0))
        self._batch_client_status = ttk.Label(buttons, foreground="green")
        self._batch_client_status.pack(side="left", padx=(12, 0))
        self._render_batch_rows()

    def _build_batch_date_row(self, parent: ttk.Frame) -> None:
        """The PS1 date for every job in the batch - the same Year/Month/Day
        widgets and rules as PS1 Input (they share the date vars and the
        _month_combobox/_day_combobox handles, since only one step is ever
        built at a time). Defaults to today."""
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=(0, 8))
        ttk.Label(row, text="Date (PS1, all jobs):").grid(row=0, column=0, padx=(0, 8))
        year_vcmd = (self.register(self._validate_year_input), "%P")
        ttk.Label(row, text="Year:").grid(row=0, column=1)
        year_entry = ttk.Entry(row, textvariable=self.date_year_var, width=6, validate="key", validatecommand=year_vcmd)
        year_entry.grid(row=0, column=2, padx=(4, 12))
        year_entry.bind("<KeyRelease>", self._on_year_changed)
        ttk.Label(row, text="Month:").grid(row=0, column=3)
        self._month_combobox = ttk.Combobox(
            row, textvariable=self.date_month_var, values=MONTH_NAMES, width=10, state="disabled"
        )
        self._month_combobox.grid(row=0, column=4, padx=(4, 12))
        self._month_combobox.bind("<<ComboboxSelected>>", self._refresh_day_options)
        ttk.Label(row, text="Day:").grid(row=0, column=5)
        self._day_combobox = ttk.Combobox(row, textvariable=self.date_day_var, width=5, state="disabled")
        self._day_combobox.grid(row=0, column=6, padx=(4, 12))
        ttk.Button(row, text="Today", command=self._set_date_today).grid(row=0, column=7)

        if not self._format_selected_date():
            self._set_date_today()
        else:
            self._on_year_changed()

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
        """Client dropdown values: the MinuteDock contacts (shares the
        General step's cache) plus any new clients added this session with
        "Add new client...". If MinuteDock can't be reached, just the new
        ones - the boxes still accept a typed name."""
        if self._minutedock_contact_names is None:
            token = self.settings.get("minutedock_access_token", "").strip()
            try:
                contacts = minutedock_client.list_contacts(token)
                self._minutedock_contact_names = sorted(
                    {str(c.get("name", "")).strip() for c in contacts if str(c.get("name", "")).strip()},
                    key=str.casefold,
                )
            except MinuteDockError:
                logger.warning("Couldn't load MinuteDock contacts for the batch table", exc_info=True)
        names = list(self._minutedock_contact_names or [])
        known = {name.casefold() for name in names}
        names += [name for name in self._new_contact_names if name.casefold() not in known]
        return names

    def _add_batch_client(self) -> None:
        """Add a client that isn't in MinuteDock yet to every row's dropdown
        (created in MinuteDock on Create by find-or-create, like the General
        step's "Add new contact...")."""
        name = simpledialog.askstring("Add new client", "Client name:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        status = getattr(self, "_batch_client_status", None)
        existing = {n.casefold(): n for n in (self._minutedock_contact_names or [])}
        if name.casefold() in existing:
            message = f'"{existing[name.casefold()]}" is already a MinuteDock contact - pick it from the list.'
        else:
            if name.casefold() not in {n.casefold() for n in self._new_contact_names}:
                self._new_contact_names.append(name)
            message = f'"{name}" added - it will be created in MinuteDock on Create.'
            self._render_batch_rows()
        if status is not None and status.winfo_exists():
            status.configure(text=message)

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
        if not self._format_selected_date():
            problems.insert(0, "Date: pick a full date (or click Today)")
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
        field already holds the template's values, and the date vars hold
        the Jobs step's date."""
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

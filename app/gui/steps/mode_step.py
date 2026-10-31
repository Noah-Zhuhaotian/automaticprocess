"""Step: Create mode - choose whether this Create should make project
folders only, open an existing project (fill or regenerate its Word
documents in its already-existing folder), or do both together (the
original, still-default behavior). Always the first
project-specific step (right after Settings, before General) so every
later step and Review & Create can branch on the choice - see
main_window.py's _build_step_list().
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from app.core import folder_creator, minutedock_client, project_store
from app.core.minutedock_client import MinuteDockError
from app.gui.steps.template_step import NO_TEMPLATE

CREATE_MODE_OPTIONS = [
    ("folder_only", "Create project folders only"),
    ("documents_only", "Open an existing project (fill or regenerate its documents)"),
    ("both", "Create folders and documents together (normal)"),
    ("batch", "Create several jobs from a template"),
]

# Modes where the "Start from template" picker applies (required for batch).
TEMPLATE_MODES = ("folder_only", "both", "batch")


class ModeStepMixin:
    def _init_mode_vars(self) -> None:
        self.create_mode_var = tk.StringVar(value="both")
        self.existing_project_folder_var = tk.StringVar()
        self._mode_folder_label: ttk.Label | None = None
        self._mode_folder_combo: ttk.Combobox | None = None
        # In "documents_only" mode, the MinuteDock Project already made for
        # this job (looked up by job number = Short Code), as
        # {"id", "name", "contact_id", "contact_name", "budget",
        # "other_budget"} - see
        # _read_project_budget. None when not in that mode or no such
        # Project exists yet.
        self.existing_minutedock_project: dict | None = None
        # The folder whose saved data (project_store) is currently loaded
        # into the wizard, so re-validating this step doesn't reload it over
        # edits, and picking a different folder starts from a clean slate.
        self._loaded_project_folder: str | None = None
        # True when the opened project already had its documents generated,
        # so this run *updates* it (button "Update", changes listed on
        # Review) rather than creating its documents for the first time.
        self.is_update_run = False
        # The Review summary rows as they were right after the project was
        # opened - what _review_changes() compares against.
        self._update_baseline: dict[tuple[str, str], str] | None = None
        self._pending_update_baseline = False

    # ---------- Step: Create mode ----------
    def _build_mode_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Choose what this Create should do for this project.",
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        for row, (value, label) in enumerate(CREATE_MODE_OPTIONS, start=1):
            ttk.Radiobutton(
                parent,
                text=label,
                variable=self.create_mode_var,
                value=value,
                command=self._on_create_mode_change,
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)

        folder_row = 1 + len(CREATE_MODE_OPTIONS)
        self._mode_folder_label = ttk.Label(parent, text="Existing project folder:")
        self._mode_folder_label.grid(row=folder_row, column=0, sticky="w", pady=(12, 4), padx=(20, 0))
        self._mode_folder_combo = ttk.Combobox(
            parent, textvariable=self.existing_project_folder_var, state="readonly", width=45
        )
        self._mode_folder_combo.grid(row=folder_row, column=1, sticky="w", pady=(12, 4), padx=8)

        template_row = folder_row + 1
        self._mode_template_label = ttk.Label(parent, text="Start from template:")
        self._mode_template_label.grid(row=template_row, column=0, sticky="w", pady=(12, 4), padx=(20, 0))
        template_frame = ttk.Frame(parent)
        template_frame.grid(row=template_row, column=1, sticky="w", pady=(12, 4), padx=8)
        self._template_combo = ttk.Combobox(
            template_frame, textvariable=self.template_choice_var, state="readonly", width=32
        )
        self._template_combo.grid(row=0, column=0, sticky="w")
        ttk.Button(template_frame, text="Manage templates...", command=self._open_manage_templates_dialog).grid(
            row=0, column=1, padx=(8, 0)
        )
        self._mode_template_frame = template_frame
        self._refresh_template_combo()

        self._sync_mode_folder_widgets()

    def _sync_mode_folder_widgets(self) -> None:
        """Idempotent - safe to call on every _build_mode_step() (i.e. every
        time this step is (re)shown, including navigating Back to it), since
        it has no data side effects. Repopulates the folder combobox and
        shows/hides it based on the *current* mode, without touching
        job_number_var/street_var/existing_project_folder_var's own value -
        that clearing only happens in _on_create_mode_change, fired by an
        actual radio click (a real transition), not a rebuild-revisit.
        """
        combo = self._mode_folder_combo
        label = self._mode_folder_label
        if combo is None or not combo.winfo_exists():
            return

        mode = self.create_mode_var.get()
        if mode == "documents_only":
            combo["values"] = self._openable_project_folders()
            label.grid()
            combo.grid()
        else:
            label.grid_remove()
            combo.grid_remove()

        template_label = getattr(self, "_mode_template_label", None)
        if template_label is not None and template_label.winfo_exists():
            if mode in TEMPLATE_MODES:
                template_label.configure(text="Template:" if mode == "batch" else "Start from template:")
                template_label.grid()
                self._mode_template_frame.grid()
            else:
                template_label.grid_remove()
                self._mode_template_frame.grid_remove()

    def _openable_project_folders(self) -> list[str]:
        """Engineer-drive project folders that can be opened: ones with no
        documents yet (made by "folder_only"), plus any with saved wizard
        data from an earlier Create (project_store) - those can be reopened
        to change and regenerate their documents."""
        engineer_drive = self.settings.get("engineer_drive", "")
        names = set(folder_creator.list_available_project_folders(engineer_drive))
        saved = project_store.saved_job_numbers()
        root = Path(engineer_drive.strip()) if engineer_drive.strip() else None
        if saved and root is not None:
            try:
                for entry in root.iterdir():
                    parsed = folder_creator.parse_project_folder_name(entry.name)
                    if entry.is_dir() and parsed is not None and parsed[0].casefold() in saved:
                        names.add(entry.name)
            except OSError:
                pass
        return sorted(names, key=str.casefold)

    def _on_create_mode_change(self) -> None:
        """Fired only by an actual Radiobutton click - a real mode switch,
        not just revisiting this step. Moving away from "documents_only"
        clears the locked folder selection and the job number/street it
        drove, so General doesn't silently keep showing a locked, stale
        value for a folder that no longer applies to the newly-chosen mode.
        """
        if self.create_mode_var.get() != "documents_only":
            self.existing_project_folder_var.set("")
            self._clear_update_state()
            if self._loaded_project_folder is not None:
                # Everything in the wizard came from that project's saved data.
                self._loaded_project_folder = None
                self._clear_project_fields()
                self._applied_template = None
            self.job_number_var.set("")
            self.street_var.set("")
            if self.existing_minutedock_project is not None:
                # The Contact and budget came from that Project, not the user.
                self.existing_minutedock_project = None
                self.client_info_var.set("")
                self.minutedock_budget_enabled_var.set(False)
                self.minutedock_budget_amount_var.set("")
        self._sync_mode_folder_widgets()

    def _validate_mode_step(self) -> bool:
        mode = self.create_mode_var.get()
        if mode == "documents_only":
            folder_name = self.existing_project_folder_var.get().strip()
            if not folder_name:
                messagebox.showerror(
                    "Missing info",
                    'Select an existing project folder to fill documents into - '
                    'or use "Create project folders only" first if none are available.',
                )
                return False
            job_number, _, street = folder_name.partition(" - ")
            if folder_name != self._loaded_project_folder:
                # A newly picked project: start clean, then restore whatever
                # was saved for it last time (nothing, for a folder_only
                # project made before saving existed).
                self._clear_project_fields()
                self._applied_template = None
                self.existing_minutedock_project = None
                saved = project_store.load_project(job_number)
                if saved is not None:
                    self._apply_project_data(saved)
                self._loaded_project_folder = folder_name
                self.is_update_run = bool(saved and saved.get("documents_generated"))
                self._update_baseline = None
                # Taken at the end of this method, once MinuteDock has filled
                # in the client/budget too (survives a failed attempt).
                self._pending_update_baseline = self.is_update_run
            self.job_number_var.set(job_number)
            self.street_var.set(street)
            if not self._load_existing_minutedock_project(job_number):
                return False
        else:
            self.existing_minutedock_project = None
            self._clear_update_state()
            if mode == "batch" and self.template_choice_var.get() == NO_TEMPLATE:
                messagebox.showerror("Missing info", "Choose the template to create the jobs from.")
                return False
            if not self._apply_chosen_template():
                return False

        # Whichever mode was chosen, the step list downstream (General
        # onward, or just Review & Create for folder_only) depends on it -
        # rebuild now so _go_next's upcoming self.current_step += 1 lands
        # on the right step. Safe regardless of mode: this step's own index
        # is identical in every step-list shape, since only what comes
        # *after* General differs.
        self.steps = self._build_step_list()
        if self._pending_update_baseline:
            self._update_baseline = self._summary_values()
            self._pending_update_baseline = False
        return True

    def _clear_update_state(self) -> None:
        self.is_update_run = False
        self._update_baseline = None
        self._pending_update_baseline = False

    def _load_existing_minutedock_project(self, job_number: str) -> bool:
        """Find the job's MinuteDock Project (made by an earlier
        "folder_only" run) so documents_only doesn't create a second one:
        its Contact gets pre-filled and locked on General, and its current
        budget pre-fills the MinuteDock step - a changed budget is saved
        back to it on Create (web_filler.update_project_budget). No
        Project found means one gets created on Create, as in the normal
        flow. Returns False (stay on this step) if MinuteDock can't be
        reached, since we can't tell which of those applies."""
        previous = self.existing_minutedock_project
        token = self.settings.get("minutedock_access_token", "").strip()
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            project = minutedock_client.find_project_by_short_code(token, job_number)
            contact_name = ""
            if project is not None:
                contacts = minutedock_client.list_contacts(token)
                contact_id = str(project.get("contact_id", ""))
                contact_name = next(
                    (str(c.get("name", "")) for c in contacts if str(c.get("id", "")) == contact_id), ""
                )
        except MinuteDockError as exc:
            messagebox.showerror(
                "Can't reach MinuteDock",
                f"Couldn't look up job {job_number} in MinuteDock:\n{exc}\n\nCheck the connection and try again.",
            )
            return False
        finally:
            self.config(cursor="")

        if project is None:
            self.existing_minutedock_project = None
            if previous is not None:
                self.client_info_var.set("")
            return True

        budget, other_budget = self._read_project_budget(project)
        same_project = previous is not None and previous["id"] == str(project.get("id", ""))
        self.existing_minutedock_project = {
            "id": str(project.get("id", "")),
            # name + contact_id are kept as-is because MinuteDock's update
            # endpoint requires both on every PUT (web_filler.update_project_budget).
            "name": project.get("name", ""),
            "contact_id": project.get("contact_id"),
            "contact_name": contact_name,
            "budget": budget,
            "other_budget": other_budget,
        }
        self.client_info_var.set(contact_name)
        if not same_project:
            # Only pre-fill when this Project was newly picked - revisiting
            # this step mustn't wipe budget edits made on the MinuteDock step.
            self.minutedock_budget_enabled_var.set(budget is not None)
            self.minutedock_budget_amount_var.set(budget or "")
        return True

    @staticmethod
    def _read_project_budget(project: dict) -> tuple[str | None, str]:
        """Split a Project's budget into what the MinuteDock step can show:
        ("<amount>", "") for a "$ Billable, in total" budget - the only kind
        this app sets - or (None, "<description>") for any other kind (e.g.
        an hours or monthly budget set in MinuteDock's web UI), which the
        step leaves alone unless the user ticks "Set a budget" to replace
        it. (None, "") means no budget at all."""
        target = project.get("budget_target")
        if target in (None, "", 0, "0", "0.0", "0.00"):
            return None, ""
        budget_type = project.get("budget_type")
        frequency = project.get("budget_frequency")
        if (
            budget_type == minutedock_client.BUDGET_TYPE_BILLABLE
            and frequency == minutedock_client.BUDGET_FREQUENCY_TOTAL
        ):
            try:
                return f"{float(target):.2f}", ""
            except (TypeError, ValueError):
                return str(target).strip(), ""
        return None, f"{budget_type or '?'} {target}, {frequency or '?'}"

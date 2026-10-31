"""Main application window: a step-by-step wizard.

Steps:
0. Settings (drive paths + MinuteDock token) - only shown on first run,
   i.e. when the three drive paths and/or the MinuteDock token haven't
   been configured yet. Skipped on subsequent runs. Both are required -
   the wizard can't proceed to Create mode until all four are set.
1. Create mode - choose whether this Create should make project folders
   only, open an existing project (fill or regenerate its documents in its
   already-existing folder), or do both together (the original, default
   behavior). Every Create saves the wizard's input per job number
   (app/core/project_store.py, outside the project folders), and opening
   an existing project loads it back into every step for editing. Always shown. This choice
   determines which of the steps below are even in the list - see
   _build_step_list().
2. General - job number (unique across all three drives and MinuteDock),
   client info (picked from MinuteDock Contacts, or added as new),
   street/suburb/town. In "documents_only" mode, Job number/Street are
   pre-filled from the folder picked on the Create-mode step and locked
   read-only, and so is the client if the job's MinuteDock Project exists.
3. Scope - which scope items apply (each with a description) and the Role.
4. PS1 Input - council, description of work, scope of statement,
   construction-monitoring level, basis of statement, date.
5. Inspection Schedule - which of PS1's typical inspection items apply,
   plus an optional free-text "Other" item, and their order.
6. Waivers and Modifications - the LBP form's YES/NO waiver section.
7. Specification - pick which Specifications.docx sections apply.
8. B2 Letter - which material rows apply.
9. MinuteDock - optional "$ Billable, in total" budget for the job's
   MinuteDock Project. Rates are always "Use contact rates" and every
   project is billable=True, neither user-facing - see minutedock_step.py.
10. Review & Create - a summary of everything entered (by step, for the
    steps in this mode's flow), then a single Create button that generates
    everything the chosen Create mode calls for.

Steps 3-8 (Scope through B2 Letter) are only in the list when the Create
mode is "documents_only" or "both" - "folder_only" goes General ->
MinuteDock -> Review & Create, since it creates the job's MinuteDock
Project but no Word documents. "documents_only" doesn't create a second
Project: it reuses the one found by job number and only saves a changed
budget back to it - see app/gui/steps/mode_step.py and review_step.py's
_run_create_job for the full branching.

There's no separate "submit to MinuteDock" step or button: it reuses data
already collected earlier in the wizard and rides along inside the same
Create action (app/core/web_filler.py) - only the budget *input* (step 9
above) gets its own step, since that's project-specific data nothing else
in the wizard collects.

Each step's fields, build/validate logic, and per-step tk variables live
in their own mixin under app/gui/steps/ - this class just composes them
and owns the state/logic shared across steps: window setup, the step
list and navigation. Shared constants (SCOPE_ITEMS, template paths, etc.)
live in app/gui/constants.py so every step module can import them without
importing this one.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from app.config.settings import load_settings
from app.gui.project_state import ProjectStateMixin
from app.gui.steps.b2_letter_step import B2LetterStepMixin
from app.gui.steps.batch_step import BatchStepMixin
from app.gui.steps.general_step import GeneralStepMixin
from app.gui.steps.inspection_step import InspectionStepMixin
from app.gui.steps.minutedock_step import MinuteDockStepMixin
from app.gui.steps.mode_step import ModeStepMixin
from app.gui.steps.ps1_step import Ps1StepMixin
from app.gui.steps.review_step import ReviewStepMixin
from app.gui.steps.review_summary import ReviewSummaryMixin
from app.gui.steps.scope_step import ScopeStepMixin
from app.gui.steps.settings_step import SettingsStepMixin
from app.gui.steps.specification_step import SpecificationStepMixin
from app.gui.steps.template_step import TemplateStepMixin
from app.gui.steps.waivers_step import WaiversStepMixin


class MainWindow(
    SettingsStepMixin,
    ModeStepMixin,
    TemplateStepMixin,
    BatchStepMixin,
    GeneralStepMixin,
    ScopeStepMixin,
    Ps1StepMixin,
    InspectionStepMixin,
    WaiversStepMixin,
    SpecificationStepMixin,
    B2LetterStepMixin,
    MinuteDockStepMixin,
    ReviewStepMixin,
    ReviewSummaryMixin,
    ProjectStateMixin,
    tk.Tk,
):
    def __init__(self) -> None:
        super().__init__()
        self.title("Automatic Process Assistant")
        self.geometry("760x620")
        self.resizable(True, True)

        style = ttk.Style(self)
        style.map(
            "TCheckbutton",
            foreground=[("disabled", "gray"), ("!selected", "gray"), ("selected", "black")],
        )

        self.settings = load_settings()
        self._init_vars()

        self.steps: list[dict[str, Any]] = self._build_step_list()
        self.current_step = 0

        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=16, pady=(14, 6))
        self.header_var = tk.StringVar()
        ttk.Label(header_frame, textvariable=self.header_var, font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(header_frame, text="Settings", command=self._open_settings_dialog).pack(side="right")

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=4)

        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill="x", padx=16, pady=14)
        self.back_button = ttk.Button(nav_frame, text="< Back", command=self._go_back)
        self.back_button.pack(side="left")
        self.next_button = ttk.Button(nav_frame, text="Next >", command=self._go_next)
        self.next_button.pack(side="right")

        self._show_step(0)

    # ---------- persistent variables (created once, reused across steps) ----------
    def _init_vars(self) -> None:
        self._init_settings_vars()
        self._init_mode_vars()
        self._init_template_vars()
        self._init_batch_vars()
        self._init_general_vars()
        self._init_scope_vars()
        self._init_ps1_vars()
        self._init_inspection_vars()
        self._init_waivers_vars()
        self._init_specification_vars()
        self._init_b2_letter_vars()
        self._init_minutedock_vars()

    # ---------- step list / navigation ----------
    def _build_step_list(self) -> list[dict[str, Any]]:
        mode = self.create_mode_var.get()
        if mode == "edit_template":
            # Editing a saved template: only the steps a template holds,
            # with no Settings/Create mode/General, and a Review that saves.
            return [
                {"title": "Edit template", "build": self._build_template_edit_step, "validate": None},
                *self._document_steps(),
                self._minutedock_step(),
                {"title": "Review & Save", "build": self._build_review_step, "validate": None},
            ]

        steps: list[dict[str, Any]] = []
        if not self._settings_configured():
            steps.append(
                {"title": "Settings", "build": self._build_settings_step, "validate": self._validate_settings_step}
            )
        steps.append(
            {"title": "Create mode", "build": self._build_mode_step, "validate": self._validate_mode_step}
        )

        if mode == "batch":
            # Everything but General comes from the template, so only the
            # per-job table is asked for.
            steps.append({"title": "Jobs", "build": self._build_batch_step, "validate": self._validate_batch_step})
        else:
            steps.append(
                {"title": "General", "build": self._build_general_step, "validate": self._validate_general_step}
            )
            # "folder_only" needs none of the document-content steps - none
            # of that data feeds a Word document when none is being created
            # - but it does create the job's MinuteDock Project, so it keeps
            # the MinuteDock step. "documents_only" and "both" need them all.
            if mode != "folder_only":
                steps.extend(self._document_steps())
            steps.append(self._minutedock_step())

        review_title = "Review & Update" if mode == "documents_only" and self.is_update_run else "Review & Create"
        steps.append({"title": review_title, "build": self._build_review_step, "validate": None})
        return steps

    def _document_steps(self) -> list[dict[str, Any]]:
        return [
            {"title": "Scope", "build": self._build_scope_step, "validate": self._validate_scope_step},
            {"title": "PS1 Input", "build": self._build_ps1_step, "validate": self._validate_ps1_step},
            {
                "title": "Inspection Schedule",
                "build": self._build_inspection_step,
                "validate": self._validate_inspection_step,
            },
            {
                "title": "Waivers and Modifications",
                "build": self._build_waivers_step,
                "validate": self._validate_waivers_step,
            },
            {
                "title": "Specification",
                "build": self._build_specification_step,
                "validate": self._validate_specification_step,
            },
            {"title": "B2 Letter", "build": self._build_b2_letter_step, "validate": self._validate_b2_letter_step},
        ]

    def _minutedock_step(self) -> dict[str, Any]:
        return {"title": "MinuteDock", "build": self._build_minutedock_step, "validate": self._validate_minutedock_step}

    def _show_step(self, index: int) -> None:
        for child in self.content_frame.winfo_children():
            child.destroy()

        step = self.steps[index]
        header = f"Step {index + 1} of {len(self.steps)}: {step['title']}"
        mode = self.create_mode_var.get()
        if mode == "documents_only":
            folder = self.existing_project_folder_var.get().strip()
            if folder:
                header += f"  —  {folder}"
        elif mode == "edit_template":
            header += f"  —  template: {self.editing_template_name}"
        self.header_var.set(header)
        step["build"](self.content_frame)

        self.back_button.configure(state="normal" if index > 0 else "disabled")
        if index == len(self.steps) - 1:
            final = {"edit_template": "Save template", "batch": "Create all"}.get(mode, "Create")
            if mode == "documents_only" and self.is_update_run:
                final = "Update"
            self.next_button.configure(text=final)
        else:
            self.next_button.configure(text="Next >")

    def _go_back(self) -> None:
        if self.current_step > 0:
            self.current_step -= 1
            self._show_step(self.current_step)

    def _go_next(self) -> None:
        step = self.steps[self.current_step]
        validate = step.get("validate")
        if validate is not None and not validate():
            return

        if self.current_step == len(self.steps) - 1:
            self._on_create()
            return

        self.current_step += 1
        self._show_step(self.current_step)


def run() -> None:
    app = MainWindow()
    app.mainloop()

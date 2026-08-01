"""Main application window: a step-by-step wizard.

Steps:
0. Settings (drive paths) - only shown on first run, i.e. when the three
   drive paths haven't been configured yet. Skipped on subsequent runs.
1. General - job number, client info, street/suburb/town, scope, role.
2. PS1 Input - council, description of work, scope of statement,
   construction-monitoring level, basis of statement, date.
3. Waivers and Modifications - the LBP form's YES/NO waiver section.
4. Specification - pick which Specifications.docx sections apply.
5. B2 Letter - placeholder, details TBD.
6. Review & Create - single Create button that generates everything:
   project folders plus the Project register, PS1, LBP form, Calculation
   Statement, and Specifications documents.

There's no separate "fill the website" step: the website only needs data
already collected earlier in the wizard, so it's produced by the same
Create action (once Step 3/web_filler.py is implemented).

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
from app.gui.steps.b2_letter_step import B2LetterStepMixin
from app.gui.steps.general_step import GeneralStepMixin
from app.gui.steps.ps1_step import Ps1StepMixin
from app.gui.steps.review_step import ReviewStepMixin
from app.gui.steps.settings_step import SettingsStepMixin
from app.gui.steps.specification_step import SpecificationStepMixin
from app.gui.steps.waivers_step import WaiversStepMixin


class MainWindow(
    SettingsStepMixin,
    GeneralStepMixin,
    Ps1StepMixin,
    WaiversStepMixin,
    SpecificationStepMixin,
    B2LetterStepMixin,
    ReviewStepMixin,
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
        ttk.Button(header_frame, text="File path", command=self._open_settings_dialog).pack(side="right")

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
        self._init_general_vars()
        self._init_ps1_vars()
        self._init_waivers_vars()
        self._init_specification_vars()
        self._init_b2_letter_vars()

    # ---------- step list / navigation ----------
    def _build_step_list(self) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        if not self._drives_configured():
            steps.append(
                {"title": "Settings", "build": self._build_settings_step, "validate": self._validate_settings_step}
            )
        steps.append({"title": "General", "build": self._build_general_step, "validate": self._validate_general_step})
        steps.append({"title": "PS1 Input", "build": self._build_ps1_step, "validate": self._validate_ps1_step})
        steps.append(
            {
                "title": "Waivers and Modifications",
                "build": self._build_waivers_step,
                "validate": self._validate_waivers_step,
            }
        )
        steps.append(
            {
                "title": "Specification",
                "build": self._build_specification_step,
                "validate": self._validate_specification_step,
            }
        )
        steps.append(
            {"title": "B2 Letter", "build": self._build_b2_letter_step, "validate": self._validate_b2_letter_step}
        )
        steps.append({"title": "Review & Create", "build": self._build_review_step, "validate": None})
        return steps

    def _show_step(self, index: int) -> None:
        for child in self.content_frame.winfo_children():
            child.destroy()

        step = self.steps[index]
        self.header_var.set(f"Step {index + 1} of {len(self.steps)}: {step['title']}")
        step["build"](self.content_frame)

        self.back_button.configure(state="normal" if index > 0 else "disabled")
        self.next_button.configure(text="Create" if index == len(self.steps) - 1 else "Next >")

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

"""Step: Waivers and Modifications - the LBP form's YES/NO waiver section
("Are waivers or modifications of the Building Code required?").
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.gui.constants import LABEL_WIDTH, YES_NO_OPTIONS


class WaiversStepMixin:
    def _init_waivers_vars(self) -> None:
        self.waivers_required_var = tk.StringVar()
        self.building_code_clause_var = tk.StringVar()
        self.waiver_modification_text = ""
        self._building_code_clause_widget: ttk.Entry | None = None
        self._waiver_modification_widget: tk.Text | None = None

    # ---------- Step: Waivers and Modifications (LBP form) ----------
    def _build_waivers_step(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=7)

        ttk.Label(
            frame,
            text="Are waivers or modifications of the\nBuilding Code required?",
            justify="left",
            width=LABEL_WIDTH,
        ).grid(row=0, column=0, sticky="nw", pady=4)
        yes_no_frame = ttk.Frame(frame)
        yes_no_frame.grid(row=0, column=1, columnspan=2, sticky="w", pady=4)
        for col, option in enumerate(YES_NO_OPTIONS):
            ttk.Radiobutton(
                yes_no_frame,
                text=option,
                variable=self.waivers_required_var,
                value=option,
                command=self._on_waivers_required_change,
            ).grid(row=0, column=col, sticky="w", padx=(0, 16))

        ttk.Label(frame, text="Building Code Clause:", width=LABEL_WIDTH).grid(row=1, column=0, sticky="w", pady=4)
        self._building_code_clause_widget = ttk.Entry(frame, textvariable=self.building_code_clause_var, width=42)
        self._building_code_clause_widget.grid(row=1, column=1, columnspan=2, sticky="w", pady=4, padx=8)

        ttk.Label(frame, text="Waiver/modification\nrequired:", justify="left", width=LABEL_WIDTH).grid(
            row=2, column=0, sticky="nw", pady=4
        )
        self._waiver_modification_widget = tk.Text(frame, width=42, height=3, wrap="word")
        self._waiver_modification_widget.grid(row=2, column=1, columnspan=2, sticky="we", pady=4, padx=8)
        self._waiver_modification_widget.insert("1.0", self.waiver_modification_text)

        self._on_waivers_required_change()

    def _on_waivers_required_change(self) -> None:
        choice = self.waivers_required_var.get()
        required = choice == "Yes"

        entry = self._building_code_clause_widget
        if entry is not None and entry.winfo_exists():
            if required:
                entry.configure(state="normal")
            else:
                self.building_code_clause_var.set("")
                entry.configure(state="disabled")

        text_widget = self._waiver_modification_widget
        if text_widget is not None and text_widget.winfo_exists():
            if required:
                text_widget.configure(state="normal")
            else:
                text_widget.configure(state="normal")
                text_widget.delete("1.0", "end")
                self.waiver_modification_text = ""
                text_widget.configure(state="disabled")

    def _sync_waivers_text_fields(self) -> None:
        widget = self._waiver_modification_widget
        if widget is not None and widget.winfo_exists() and self.waivers_required_var.get() == "Yes":
            self.waiver_modification_text = widget.get("1.0", "end-1c")

    def _validate_waivers_step(self) -> bool:
        self._sync_waivers_text_fields()

        if self.waivers_required_var.get() not in YES_NO_OPTIONS:
            messagebox.showerror("Missing info", 'Select "Yes" or "No" for waivers or modifications.')
            return False
        if self.waivers_required_var.get() == "Yes":
            if not self.building_code_clause_var.get().strip():
                messagebox.showerror("Missing info", 'Building Code Clause is required when "Yes" is selected.')
                return False
            if not self.waiver_modification_text.strip():
                messagebox.showerror(
                    "Missing info", 'Waiver/modification required is required when "Yes" is selected.'
                )
                return False
        return True

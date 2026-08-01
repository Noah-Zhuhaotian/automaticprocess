"""Step: Specification - pick which Specifications.docx sections apply to
this project (see word_filler.remove_unselected_sections), plus the
numeric fields embedded in specific sections.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.gui.constants import SPECIFICATION_NUMERIC_FIELDS, SPECIFICATION_SECTIONS


class SpecificationStepMixin:
    def _init_specification_vars(self) -> None:
        self.specification_vars: dict[str, tk.BooleanVar] = {
            title: tk.BooleanVar(value=False) for title in SPECIFICATION_SECTIONS
        }
        self.capacity_var = tk.StringVar()
        self.precast_strength_var = tk.StringVar()
        self.foundation_plain_strength_var = tk.StringVar()
        self.foundation_fibre_strength_var = tk.StringVar()
        self.metal_deck_topping_strength_var = tk.StringVar()
        self.grout_strength_var = tk.StringVar()
        self._specification_numeric_widgets: dict[str, ttk.Entry] = {}

    # ---------- Step: Specification ----------
    def _build_specification_step(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Select which sections of the Specification apply to this project:",
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._specification_numeric_widgets = {}
        row = 1
        for title in SPECIFICATION_SECTIONS:
            selected_var = self.specification_vars[title]
            ttk.Checkbutton(
                frame,
                text=title,
                variable=selected_var,
                command=lambda t=title: self._on_specification_toggle(t),
            ).grid(row=row, column=0, sticky="nw", pady=4)

            fields = SPECIFICATION_NUMERIC_FIELDS.get(title, [])
            if fields:
                fields_frame = ttk.Frame(frame)
                fields_frame.grid(row=row, column=1, sticky="w", padx=(16, 0), pady=4)
                for field_row, (var_name, label_text) in enumerate(fields):
                    ttk.Label(fields_frame, text=label_text).grid(row=field_row, column=0, sticky="w", pady=1)
                    entry = ttk.Entry(
                        fields_frame,
                        textvariable=getattr(self, var_name),
                        width=10,
                        state="normal" if selected_var.get() else "disabled",
                    )
                    entry.grid(row=field_row, column=1, sticky="w", padx=(6, 0), pady=1)
                    self._specification_numeric_widgets[var_name] = entry
            row += 1

    def _on_specification_toggle(self, title: str) -> None:
        selected = self.specification_vars[title].get()
        for var_name, _label in SPECIFICATION_NUMERIC_FIELDS.get(title, []):
            entry = self._specification_numeric_widgets.get(var_name)
            if entry is None or not entry.winfo_exists():
                continue
            if selected:
                entry.configure(state="normal")
            else:
                getattr(self, var_name).set("")
                entry.configure(state="disabled")

    def _validate_specification_step(self) -> bool:
        if not any(self.specification_vars[title].get() for title in SPECIFICATION_SECTIONS):
            messagebox.showerror("Missing info", "Select at least one Specification section.")
            return False
        for title in SPECIFICATION_SECTIONS:
            if not self.specification_vars[title].get():
                continue
            for var_name, label_text in SPECIFICATION_NUMERIC_FIELDS.get(title, []):
                if not getattr(self, var_name).get().strip():
                    messagebox.showerror("Missing info", f'"{label_text.rstrip(":")}" is required for {title}.')
                    return False
        return True

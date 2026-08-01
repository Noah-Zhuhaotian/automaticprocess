"""Step: B2 Letter - pick which materials' rows appear in B2 Letter.docx's
Material/Means of Compliance/Notes table (see
word_filler.remove_unselected_table_rows). Row content itself is fixed;
this step only controls which rows survive.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.gui.constants import B2_LETTER_MATERIALS


class B2LetterStepMixin:
    def _init_b2_letter_vars(self) -> None:
        self.b2_letter_material_vars: dict[str, tk.BooleanVar] = {
            material: tk.BooleanVar(value=False) for material in B2_LETTER_MATERIALS
        }

    # ---------- Step: B2 Letter ----------
    def _build_b2_letter_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Select which materials' rows appear in the B2 Letter's compliance table:",
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        for row, material in enumerate(B2_LETTER_MATERIALS, start=1):
            ttk.Checkbutton(
                parent, text=material, variable=self.b2_letter_material_vars[material]
            ).grid(row=row, column=0, sticky="w", pady=4)

    def _validate_b2_letter_step(self) -> bool:
        if not any(self.b2_letter_material_vars[material].get() for material in B2_LETTER_MATERIALS):
            messagebox.showerror("Missing info", "Select at least one material for the B2 Letter table.")
            return False
        return True

"""Step: Specification - pick which Specifications.docx sections apply to
this project (see word_filler.remove_unselected_sections), plus the
numeric fields embedded in specific sections.

CONCRETE - GENERAL's strengths (SPECIFICATION_TICKABLE_FIELDS) each have
their own tickbox: only ticked ones are written to the document, an
unticked one's line is removed. Numeric fields only accept numbers.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.gui.constants import (
    SPECIFICATION_DROPDOWN_FIELDS,
    SPECIFICATION_NUMERIC_FIELDS,
    SPECIFICATION_SECTIONS,
    SPECIFICATION_TICKABLE_FIELDS,
)


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
        self.concrete_other_strength_var = tk.StringVar()
        self.grout_strength_var = tk.StringVar()
        # Per-field tickboxes for SPECIFICATION_TICKABLE_FIELDS.
        self.specification_field_enabled_vars: dict[str, tk.BooleanVar] = {
            var_name: tk.BooleanVar(value=False) for var_name in SPECIFICATION_TICKABLE_FIELDS
        }
        self._specification_numeric_widgets: dict[str, ttk.Entry] = {}
        self._specification_field_checkbuttons: dict[str, ttk.Checkbutton] = {}

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

        number_vcmd = (self.register(self._validate_number_input), "%P")
        self._specification_numeric_widgets = {}
        self._specification_field_checkbuttons = {}
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
                    if var_name in SPECIFICATION_TICKABLE_FIELDS:
                        checkbutton = ttk.Checkbutton(
                            fields_frame,
                            text=label_text,
                            variable=self.specification_field_enabled_vars[var_name],
                            command=lambda t=title: self._on_specification_toggle(t),
                        )
                        checkbutton.grid(row=field_row, column=0, sticky="w", pady=1)
                        self._specification_field_checkbuttons[var_name] = checkbutton
                    else:
                        ttk.Label(fields_frame, text=label_text).grid(row=field_row, column=0, sticky="w", pady=1)

                    options = SPECIFICATION_DROPDOWN_FIELDS.get(var_name)
                    if options is not None:
                        entry = ttk.Combobox(
                            fields_frame, textvariable=getattr(self, var_name), values=options, width=16
                        )
                    else:
                        entry = ttk.Entry(
                            fields_frame,
                            textvariable=getattr(self, var_name),
                            width=10,
                            validate="key",
                            validatecommand=number_vcmd,
                        )
                    entry.grid(row=field_row, column=1, sticky="w", padx=(6, 0), pady=1)
                    self._specification_numeric_widgets[var_name] = entry
            # Reflect the current section/field ticks in the widgets just built.
            self._on_specification_toggle(title)
            row += 1

    def _validate_number_input(self, proposed: str) -> bool:
        """Keystroke filter for numeric fields: digits with at most one
        decimal point - nothing else can be typed."""
        if proposed == "":
            return True
        whole, dot, fraction = proposed.partition(".")
        return (whole.isdigit() or (dot and whole == "")) and (not dot or fraction == "" or fraction.isdigit())

    def _field_is_active(self, title: str, var_name: str) -> bool:
        if not self.specification_vars[title].get():
            return False
        if var_name in SPECIFICATION_TICKABLE_FIELDS:
            return self.specification_field_enabled_vars[var_name].get()
        return True

    def _on_specification_toggle(self, title: str) -> None:
        """Enable a field's entry only while its section - and, for a
        tickable field, its own tickbox - is ticked; clear it otherwise.
        Unticking the section also unticks its tickable fields."""
        section_selected = self.specification_vars[title].get()
        for var_name, _label in SPECIFICATION_NUMERIC_FIELDS.get(title, []):
            if var_name in SPECIFICATION_TICKABLE_FIELDS:
                if not section_selected:
                    self.specification_field_enabled_vars[var_name].set(False)
                checkbutton = self._specification_field_checkbuttons.get(var_name)
                if checkbutton is not None and checkbutton.winfo_exists():
                    checkbutton.configure(state="normal" if section_selected else "disabled")

            entry = self._specification_numeric_widgets.get(var_name)
            if entry is None or not entry.winfo_exists():
                continue
            if self._field_is_active(title, var_name):
                entry.configure(state="readonly" if var_name in SPECIFICATION_DROPDOWN_FIELDS else "normal")
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
            fields = SPECIFICATION_NUMERIC_FIELDS.get(title, [])
            tickable = [var_name for var_name, _label in fields if var_name in SPECIFICATION_TICKABLE_FIELDS]
            if tickable and not any(self.specification_field_enabled_vars[v].get() for v in tickable):
                messagebox.showerror("Missing info", f"Tick at least one strength for {title}.")
                return False
            for var_name, label_text in fields:
                if not self._field_is_active(title, var_name):
                    continue
                value = getattr(self, var_name).get().strip()
                if not value:
                    messagebox.showerror("Missing info", f'"{label_text.rstrip(":")}" is required for {title}.')
                    return False
                if var_name not in SPECIFICATION_DROPDOWN_FIELDS:
                    try:
                        number = float(value)
                    except ValueError:
                        number = 0
                    if number <= 0:
                        messagebox.showerror(
                            "Missing info", f'"{label_text.rstrip(":")}" must be a number greater than 0.'
                        )
                        return False
        return True

    def _specification_strength_paragraphs(self) -> tuple[dict[str, str], set[str]]:
        """Replacements for CONCRETE - GENERAL's strength lines, plus the
        tokens of lines to delete because nothing on them is ticked. Plain
        and Fibre foundations share one "Foundations:" line, so it's built
        here from whichever of the two are ticked."""
        enabled = {v: self.specification_field_enabled_vars[v].get() for v in SPECIFICATION_TICKABLE_FIELDS}
        replacements: dict[str, str] = {}
        remove: set[str] = set()

        for var_name, token in (
            ("precast_strength_var", "precast_strength"),
            ("metal_deck_topping_strength_var", "metal_deck_topping_strength"),
            ("concrete_other_strength_var", "concrete_other_strength"),
        ):
            if enabled[var_name]:
                replacements[token] = getattr(self, var_name).get().strip()
            else:
                remove.add(token)

        foundation_parts = []
        if enabled["foundation_plain_strength_var"]:
            foundation_parts.append(f"{self.foundation_plain_strength_var.get().strip()} MPa Plain Concrete")
        if enabled["foundation_fibre_strength_var"]:
            foundation_parts.append(f"{self.foundation_fibre_strength_var.get().strip()} MPa Fibre Concrete")
        if foundation_parts:
            replacements["foundation_strengths"] = " / ".join(foundation_parts)
        else:
            remove.add("foundation_strengths")
        return replacements, remove

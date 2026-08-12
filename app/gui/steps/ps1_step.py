"""Step: PS1 Input - council, description of work, legal description,
scope of statement, construction-monitoring level, basis of statement,
date. Feeds the PS1 Producer Statement document.
"""

from __future__ import annotations

import calendar
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app.config.settings import save_settings
from app.gui.constants import (
    ALL_PART_OPTIONS,
    B1_OPTIONS,
    CM_ITEMS,
    LABEL_WIDTH,
    MONTH_NAMES,
)


def _format_ordinal_date(value: datetime.date) -> str:
    """e.g. 1 -> "1st", 2 -> "2nd", 22 -> "22nd" -> "1st August 2026"."""
    day = value.day
    suffix = "th" if 11 <= day % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {value.strftime('%B')} {value.year}"


class Ps1StepMixin:
    def _init_ps1_vars(self) -> None:
        self.council_name_var = tk.StringVar()
        self.description_of_work_text = ""
        self.legal_description_text = ""
        self.site_verification_text = ""
        self.all_part_var = tk.StringVar()
        self.cm_vars: dict[str, tk.BooleanVar] = {item: tk.BooleanVar(value=False) for item in CM_ITEMS}
        self.compliance_var = tk.BooleanVar(value=False)
        self.alternative_var = tk.BooleanVar(value=False)
        self.b1_vars: dict[str, tk.BooleanVar] = {item: tk.BooleanVar(value=False) for item in B1_OPTIONS}
        self.alternative_solution_text = ""
        self.date_year_var = tk.StringVar()
        self.date_month_var = tk.StringVar()
        self.date_day_var = tk.StringVar()
        self._month_combobox: ttk.Combobox | None = None
        self._day_combobox: ttk.Combobox | None = None

        self._b1_checkbuttons: dict[str, ttk.Checkbutton] = {}
        self._alternative_solution_widget: tk.Text | None = None
        self._description_of_work_widget: tk.Text | None = None
        self._legal_description_widget: tk.Text | None = None
        self._site_verification_widget: tk.Text | None = None
        self._council_combobox: ttk.Combobox | None = None
        self._council_warning_label: ttk.Label | None = None

    # ---------- Step: PS1 Input ----------
    def _build_ps1_step(self, parent: ttk.Frame) -> None:
        # A dedicated frame (rather than configuring `parent` directly) so
        # this 3:7 label:input column split doesn't leak into other steps,
        # which reuse the same `parent` (content_frame) with their own layout.
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=7)

        row = 0
        council_names = self.settings.get("council_names", [])

        ttk.Label(frame, text="Council name:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=4)
        council_row = ttk.Frame(frame)
        council_row.grid(row=row, column=1, columnspan=2, sticky="w", pady=4, padx=8)
        self._council_combobox = ttk.Combobox(
            council_row,
            textvariable=self.council_name_var,
            values=council_names,
            width=28,
            state="readonly" if council_names else "disabled",
        )
        self._council_combobox.grid(row=0, column=0, sticky="w")
        ttk.Button(council_row, text="Add Council...", command=self._add_council_name).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(council_row, text="Edit Council...", command=self._edit_council_name).grid(
            row=0, column=2, padx=(8, 0)
        )
        row += 1

        self._council_warning_label = None
        if not council_names:
            self._council_warning_label = ttk.Label(
                frame,
                text='No councils configured yet - click "Add Council..." to add one.',
                foreground="red",
            )
            self._council_warning_label.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))
            row += 1

        ttk.Label(frame, text="Description of work:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="nw", pady=4)
        self._description_of_work_widget = tk.Text(frame, width=42, height=3, wrap="word")
        self._description_of_work_widget.grid(row=row, column=1, columnspan=2, sticky="we", pady=4, padx=8)
        self._description_of_work_widget.insert("1.0", self.description_of_work_text)
        row += 1

        ttk.Label(frame, text="Legal description:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="nw", pady=4)
        self._legal_description_widget = tk.Text(frame, width=42, height=3, wrap="word")
        self._legal_description_widget.grid(row=row, column=1, columnspan=2, sticky="we", pady=4, padx=8)
        self._legal_description_widget.insert("1.0", self.legal_description_text)
        row += 1

        ttk.Label(frame, text="Site verification:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="nw", pady=4)
        self._site_verification_widget = tk.Text(frame, width=42, height=3, wrap="word")
        self._site_verification_widget.grid(row=row, column=1, columnspan=2, sticky="we", pady=4, padx=8)
        self._site_verification_widget.insert("1.0", self.site_verification_text)
        row += 1

        ttk.Label(frame, text="Scope of statement:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=(12, 4))
        all_part_frame = ttk.Frame(frame)
        all_part_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=(12, 4), padx=8)
        for col, option in enumerate(ALL_PART_OPTIONS):
            ttk.Radiobutton(all_part_frame, text=option, variable=self.all_part_var, value=option).grid(
                row=0, column=col, sticky="w", padx=(0, 20)
            )
        row += 1

        ttk.Label(frame, text="Level of construction\nmonitoring:", justify="left", width=LABEL_WIDTH).grid(
            row=row, column=0, sticky="nw", pady=4
        )
        cm_frame = ttk.Frame(frame)
        cm_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4, padx=8)
        for col, item in enumerate(CM_ITEMS):
            ttk.Checkbutton(cm_frame, text=item, variable=self.cm_vars[item]).grid(
                row=0, column=col, sticky="w", padx=(0, 12)
            )
        row += 1

        ttk.Label(frame, text="Basis of statement:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=(12, 4))
        compliance_frame = ttk.Frame(frame)
        compliance_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=(12, 4), padx=8)
        # Independent checkboxes, not mutually-exclusive radios - a PS1 can
        # rely on both Compliance and Alternative solution at once.
        ttk.Checkbutton(
            compliance_frame, text="Compliance", variable=self.compliance_var, command=self._on_compliance_alt_change
        ).grid(row=0, column=0, sticky="w", padx=(0, 16))
        ttk.Checkbutton(
            compliance_frame, text="Alternative", variable=self.alternative_var, command=self._on_compliance_alt_change
        ).grid(row=0, column=1, sticky="w", padx=(0, 16))
        row += 1

        ttk.Label(frame, text="Compliance method(s)\n(if Compliance):", justify="left", width=LABEL_WIDTH).grid(
            row=row, column=0, sticky="nw", pady=4
        )
        b1_frame = ttk.Frame(frame)
        b1_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4, padx=8)
        self._b1_checkbuttons = {}
        b1_state = "normal" if self.compliance_var.get() else "disabled"
        for col, option in enumerate(B1_OPTIONS):
            cb = ttk.Checkbutton(b1_frame, text=option, variable=self.b1_vars[option], state=b1_state)
            cb.grid(row=0, column=col, sticky="w", padx=(0, 16))
            self._b1_checkbuttons[option] = cb
        row += 1

        ttk.Label(frame, text="Alternative solution\n(if Alternative):", justify="left", width=LABEL_WIDTH).grid(
            row=row, column=0, sticky="nw", pady=4
        )
        self._alternative_solution_widget = tk.Text(frame, width=42, height=3, wrap="word")
        self._alternative_solution_widget.grid(row=row, column=1, columnspan=2, sticky="we", pady=4, padx=8)
        row += 1

        ttk.Label(frame, text="Date:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=4)
        date_frame = ttk.Frame(frame)
        date_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4, padx=8)

        year_vcmd = (self.register(self._validate_year_input), "%P")
        ttk.Label(date_frame, text="Year:").grid(row=0, column=0)
        year_entry = ttk.Entry(
            date_frame, textvariable=self.date_year_var, width=6, validate="key", validatecommand=year_vcmd
        )
        year_entry.grid(row=0, column=1, padx=(4, 12))
        year_entry.bind("<KeyRelease>", self._on_year_changed)

        ttk.Label(date_frame, text="Month:").grid(row=0, column=2)
        self._month_combobox = ttk.Combobox(
            date_frame, textvariable=self.date_month_var, values=MONTH_NAMES, width=10, state="disabled"
        )
        self._month_combobox.grid(row=0, column=3, padx=(4, 12))
        self._month_combobox.bind("<<ComboboxSelected>>", self._refresh_day_options)

        ttk.Label(date_frame, text="Day:").grid(row=0, column=4)
        self._day_combobox = ttk.Combobox(date_frame, textvariable=self.date_day_var, width=5, state="disabled")
        self._day_combobox.grid(row=0, column=5, padx=(4, 12))

        ttk.Button(date_frame, text="Today", command=self._set_date_today).grid(row=0, column=6, padx=(4, 0))
        self._on_year_changed()
        row += 1

        # Reflect the current Compliance/Alternative choice in the widgets just built.
        self._on_compliance_alt_change()

    def _add_council_name(self) -> None:
        name = simpledialog.askstring("Add Council", "Council name:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()

        council_names = self.settings.setdefault("council_names", [])
        if name not in council_names:
            council_names.append(name)
            save_settings(self.settings)

        self.council_name_var.set(name)
        if self._council_combobox.winfo_exists():
            self._council_combobox.configure(values=council_names, state="readonly")
        if self._council_warning_label is not None and self._council_warning_label.winfo_exists():
            self._council_warning_label.grid_remove()

    def _edit_council_name(self) -> None:
        council_names = self.settings.get("council_names", [])
        current = self.council_name_var.get().strip()
        if not current or current not in council_names:
            messagebox.showinfo("Edit Council", "Select a council from the list first.")
            return

        new_name = simpledialog.askstring("Edit Council", "Council name:", initialvalue=current, parent=self)
        if not new_name or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name == current:
            return
        if new_name in council_names:
            messagebox.showerror("Edit Council", f'"{new_name}" already exists.')
            return

        council_names[council_names.index(current)] = new_name
        save_settings(self.settings)

        self.council_name_var.set(new_name)
        if self._council_combobox is not None and self._council_combobox.winfo_exists():
            self._council_combobox.configure(values=council_names)

    def _validate_year_input(self, proposed: str) -> bool:
        return proposed == "" or (proposed.isdigit() and len(proposed) <= 4)

    def _year_is_valid(self) -> bool:
        year_str = self.date_year_var.get()
        return year_str.isdigit() and len(year_str) == 4

    def _on_year_changed(self, event: object = None) -> None:
        """Month (and, transitively, Day) can't be picked until Year holds
        a valid 4-digit value - there's no sensible day count otherwise.
        """
        if self._month_combobox is None or not self._month_combobox.winfo_exists():
            return

        if self._year_is_valid():
            self._month_combobox.configure(state="readonly")
        else:
            self._month_combobox.configure(state="disabled")
            self.date_month_var.set("")
        self._refresh_day_options()

    def _refresh_day_options(self, event: object = None) -> None:
        if self._day_combobox is None or not self._day_combobox.winfo_exists():
            return

        month_name = self.date_month_var.get()
        if not (self._year_is_valid() and month_name in MONTH_NAMES):
            self._day_combobox.configure(values=[], state="disabled")
            self.date_day_var.set("")
            return

        days_in_month = calendar.monthrange(int(self.date_year_var.get()), MONTH_NAMES.index(month_name) + 1)[1]
        self._day_combobox.configure(values=[str(d) for d in range(1, days_in_month + 1)], state="readonly")
        if self.date_day_var.get() and int(self.date_day_var.get()) > days_in_month:
            self.date_day_var.set(str(days_in_month))

    def _set_date_today(self) -> None:
        today = datetime.date.today()
        self.date_year_var.set(str(today.year))
        self._on_year_changed()
        self.date_month_var.set(MONTH_NAMES[today.month - 1])
        self._refresh_day_options()
        self.date_day_var.set(str(today.day))

    def _format_selected_date(self) -> str:
        year_str = self.date_year_var.get()
        month_name = self.date_month_var.get()
        day_str = self.date_day_var.get()
        if not (year_str.isdigit() and len(year_str) == 4 and month_name in MONTH_NAMES and day_str.isdigit()):
            return ""
        date_value = datetime.date(int(year_str), MONTH_NAMES.index(month_name) + 1, int(day_str))
        return _format_ordinal_date(date_value)

    def _on_compliance_alt_change(self) -> None:
        b1_state = "normal" if self.compliance_var.get() else "disabled"
        for cb in self._b1_checkbuttons.values():
            if cb.winfo_exists():
                cb.configure(state=b1_state)
        if not self.compliance_var.get():
            for var in self.b1_vars.values():
                var.set(False)

        widget = self._alternative_solution_widget
        if widget is None or not widget.winfo_exists():
            return

        if self.alternative_var.get():
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", self.alternative_solution_text)
        else:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", "N/A")
            widget.configure(state="disabled")

    def _sync_ps1_text_fields(self) -> None:
        if self._description_of_work_widget is not None and self._description_of_work_widget.winfo_exists():
            self.description_of_work_text = self._description_of_work_widget.get("1.0", "end-1c")
        if self._legal_description_widget is not None and self._legal_description_widget.winfo_exists():
            self.legal_description_text = self._legal_description_widget.get("1.0", "end-1c")
        if self._site_verification_widget is not None and self._site_verification_widget.winfo_exists():
            self.site_verification_text = self._site_verification_widget.get("1.0", "end-1c")
        if (
            self.alternative_var.get()
            and self._alternative_solution_widget is not None
            and self._alternative_solution_widget.winfo_exists()
        ):
            self.alternative_solution_text = self._alternative_solution_widget.get("1.0", "end-1c")

    def _validate_ps1_step(self) -> bool:
        self._sync_ps1_text_fields()

        if not self.council_name_var.get().strip():
            messagebox.showerror(
                "Missing info", 'Council name is required. Use "Add Council..." if the list is empty.'
            )
            return False
        if self.all_part_var.get() not in ALL_PART_OPTIONS:
            messagebox.showerror("Missing info", 'Select "All" or "Part only".')
            return False
        if not self.compliance_var.get() and not self.alternative_var.get():
            messagebox.showerror("Missing info", 'Select "Compliance" and/or "Alternative".')
            return False
        if self.alternative_var.get() and not self.alternative_solution_text.strip():
            messagebox.showerror("Missing info", 'Alternative solution is required when "Alternative" is selected.')
            return False
        return True

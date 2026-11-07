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
    ALTERNATIVE_SOLUTION_TEXT,
    B1_OPTIONS,
    CM_ITEMS,
    LABEL_WIDTH,
    LEGAL_FORMAT_LOT_DP,
    LEGAL_FORMAT_OTHER,
    LEGAL_LOT_DP_LABELS,
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
        self.description_of_work_var = tk.StringVar()
        # Legal description = "<first label> <value> <second label> <value>":
        # "Lot 12 DP 34567" by default, or a user-added Other format (e.g.
        # "Section 3 SO 1234") picked from the "legal_description_formats"
        # list. Only the two values are typed per job.
        self.legal_format_var = tk.StringVar(value=LEGAL_FORMAT_LOT_DP)
        self.legal_other_format_var = tk.StringVar()  # display text, see _legal_format_display
        self.legal_first_value_var = tk.StringVar()
        self.legal_second_value_var = tk.StringVar()
        for var in (self.legal_format_var, self.legal_other_format_var, self.legal_first_value_var, self.legal_second_value_var):
            var.trace_add("write", lambda *_args: self._refresh_legal_widgets())
        self.site_verification_text = ""
        self.all_part_var = tk.StringVar()
        self.cm_vars: dict[str, tk.BooleanVar] = {item: tk.BooleanVar(value=False) for item in CM_ITEMS}
        self.compliance_var = tk.BooleanVar(value=False)
        self.alternative_var = tk.BooleanVar(value=False)
        self.b1_vars: dict[str, tk.BooleanVar] = {item: tk.BooleanVar(value=False) for item in B1_OPTIONS}
        self.date_year_var = tk.StringVar()
        self.date_month_var = tk.StringVar()
        self.date_day_var = tk.StringVar()
        self._month_combobox: ttk.Combobox | None = None
        self._day_combobox: ttk.Combobox | None = None

        self._b1_checkbuttons: dict[str, ttk.Checkbutton] = {}
        self._alternative_solution_widget: tk.Text | None = None
        self._description_of_work_combobox: ttk.Combobox | None = None
        self._legal_other_combobox: ttk.Combobox | None = None
        self._legal_first_label: ttk.Label | None = None
        self._legal_second_label: ttk.Label | None = None
        self._legal_preview_label: ttk.Label | None = None
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
        ttk.Button(
            council_row,
            text="Add Council...",
            command=lambda: self._add_list_name(
                "council_names", "Council", self.council_name_var, self._council_combobox
            ),
        ).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(
            council_row,
            text="Edit Council...",
            command=lambda: self._edit_list_name(
                "council_names", "Council", self.council_name_var, self._council_combobox
            ),
        ).grid(row=0, column=2, padx=(8, 0))
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

        # Picked from a user-maintained list, like the council.
        description_names = self.settings.get("description_of_work_names", [])
        ttk.Label(frame, text="Description of work:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=4)
        description_row = ttk.Frame(frame)
        description_row.grid(row=row, column=1, columnspan=2, sticky="w", pady=4, padx=8)
        self._description_of_work_combobox = ttk.Combobox(
            description_row,
            textvariable=self.description_of_work_var,
            values=description_names,
            width=28,
            state="readonly" if description_names else "disabled",
        )
        self._description_of_work_combobox.grid(row=0, column=0, sticky="w")
        ttk.Button(
            description_row,
            text="Add...",
            command=lambda: self._add_list_name(
                "description_of_work_names",
                "Description of work",
                self.description_of_work_var,
                self._description_of_work_combobox,
            ),
        ).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(
            description_row,
            text="Edit...",
            command=lambda: self._edit_list_name(
                "description_of_work_names",
                "Description of work",
                self.description_of_work_var,
                self._description_of_work_combobox,
            ),
        ).grid(row=0, column=2, padx=(8, 0))
        row += 1

        ttk.Label(frame, text="Legal description:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="nw", pady=4)
        legal_frame = ttk.Frame(frame)
        legal_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4, padx=8)
        format_row = ttk.Frame(legal_frame)
        format_row.grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            format_row, text="Lot ... DP ...", variable=self.legal_format_var, value=LEGAL_FORMAT_LOT_DP
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Radiobutton(
            format_row, text="Other format:", variable=self.legal_format_var, value=LEGAL_FORMAT_OTHER
        ).grid(row=0, column=1, sticky="w")
        self._legal_other_combobox = ttk.Combobox(
            format_row,
            textvariable=self.legal_other_format_var,
            values=self._legal_format_names(),
            width=22,
            state="disabled",
        )
        self._legal_other_combobox.grid(row=0, column=2, sticky="w", padx=(4, 0))
        ttk.Button(format_row, text="Add...", command=self._add_legal_format).grid(row=0, column=3, padx=(8, 0))
        ttk.Button(format_row, text="Edit...", command=self._edit_legal_format).grid(row=0, column=4, padx=(8, 0))

        values_row = ttk.Frame(legal_frame)
        values_row.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._legal_first_label = ttk.Label(values_row)
        self._legal_first_label.grid(row=0, column=0, sticky="w")
        ttk.Entry(values_row, textvariable=self.legal_first_value_var, width=10).grid(row=0, column=1, padx=(4, 12))
        self._legal_second_label = ttk.Label(values_row)
        self._legal_second_label.grid(row=0, column=2, sticky="w")
        ttk.Entry(values_row, textvariable=self.legal_second_value_var, width=14).grid(row=0, column=3, padx=(4, 12))
        self._legal_preview_label = ttk.Label(values_row, foreground="gray")
        self._legal_preview_label.grid(row=0, column=4, sticky="w")
        self._refresh_legal_widgets()
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
        # Defaults to today (like the batch Jobs step) - a blank date left
        # the PS1's "dated" and the Specifications cover date empty.
        if not (self.date_year_var.get() or self.date_month_var.get() or self.date_day_var.get()):
            self._set_date_today()
        else:
            self._on_year_changed()
        row += 1

        # Reflect the current Compliance/Alternative choice in the widgets just built.
        self._on_compliance_alt_change()

    # ---------- User-maintained lists (Council, Description of work) ----------
    # `key` is the settings list, `var`/`combobox` the field it fills.
    def _add_list_name(self, key: str, label: str, var: tk.StringVar, combobox: ttk.Combobox | None) -> None:
        name = simpledialog.askstring(f"Add {label}", f"{label}:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()

        names = self.settings.setdefault(key, [])
        if name not in names:
            names.append(name)
            save_settings(self.settings)

        var.set(name)
        if combobox is not None and combobox.winfo_exists():
            combobox.configure(values=names, state="readonly")
        if key == "council_names" and self._council_warning_label is not None and self._council_warning_label.winfo_exists():
            self._council_warning_label.grid_remove()

    def _edit_list_name(self, key: str, label: str, var: tk.StringVar, combobox: ttk.Combobox | None) -> None:
        names = self.settings.get(key, [])
        current = var.get().strip()
        if not current or current not in names:
            messagebox.showinfo(f"Edit {label}", f"Select a {label.lower()} from the list first.")
            return

        new_name = simpledialog.askstring(f"Edit {label}", f"{label}:", initialvalue=current, parent=self)
        if not new_name or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name == current:
            return
        if new_name in names:
            messagebox.showerror(f"Edit {label}", f'"{new_name}" already exists.')
            return

        names[names.index(current)] = new_name
        save_settings(self.settings)

        var.set(new_name)
        if combobox is not None and combobox.winfo_exists():
            combobox.configure(values=names)

    # ---------- Legal description ----------
    @staticmethod
    def _legal_format_display(first: str, second: str) -> str:
        return f"{first} ... {second} ..."

    def _legal_format_names(self) -> list[str]:
        return [self._legal_format_display(first, second) for first, second in self.settings.get("legal_description_formats", [])]

    def _legal_labels(self) -> tuple[str, str] | None:
        """The current format's two labels, or None if Other is chosen but
        no format is picked. Parsed back from the display text (not looked
        up in the list), so a reopened project keeps its format even if it
        was since renamed."""
        if self.legal_format_var.get() != LEGAL_FORMAT_OTHER:
            return LEGAL_LOT_DP_LABELS
        display = self.legal_other_format_var.get()
        if not display.endswith(" ...") or " ... " not in display:
            return None
        first, second = display[: -len(" ...")].split(" ... ", 1)
        return first, second

    def _legal_description(self) -> str:
        """e.g. "Lot 12 DP 34567" - empty if neither value is filled in."""
        first, second = self.legal_first_value_var.get().strip(), self.legal_second_value_var.get().strip()
        labels = self._legal_labels()
        if not (first or second) or labels is None:
            return ""
        return " ".join(part for part in (labels[0], first, labels[1], second) if part)

    def _refresh_legal_widgets(self) -> None:
        """Value labels and preview follow the chosen format; the Other
        dropdown is only usable while "Other format" is selected."""
        if self._legal_preview_label is None or not self._legal_preview_label.winfo_exists():
            return
        labels = self._legal_labels() or ("?", "?")
        self._legal_first_label.configure(text=labels[0])
        self._legal_second_label.configure(text=labels[1])
        description = self._legal_description()
        self._legal_preview_label.configure(text=f"= {description}" if description else "")
        names = self._legal_format_names()
        other = self.legal_format_var.get() == LEGAL_FORMAT_OTHER
        self._legal_other_combobox.configure(values=names, state="readonly" if other and names else "disabled")

    def _ask_legal_labels(self, title: str, initial: tuple[str, str] = ("", "")) -> tuple[str, str] | None:
        first = simpledialog.askstring(
            title, 'First word (before the first number), e.g. "Section":', initialvalue=initial[0], parent=self
        )
        if not first or not first.strip():
            return None
        second = simpledialog.askstring(
            title, 'Second word (before the second number), e.g. "SO":', initialvalue=initial[1], parent=self
        )
        if not second or not second.strip():
            return None
        return first.strip(), second.strip()

    def _add_legal_format(self) -> None:
        labels = self._ask_legal_labels("Add legal description format")
        if labels is None:
            return
        formats = self.settings.setdefault("legal_description_formats", [])
        if list(labels) not in formats:
            formats.append(list(labels))
            save_settings(self.settings)
        self.legal_format_var.set(LEGAL_FORMAT_OTHER)
        self.legal_other_format_var.set(self._legal_format_display(*labels))

    def _edit_legal_format(self) -> None:
        formats = self.settings.get("legal_description_formats", [])
        current = self._legal_labels() if self.legal_format_var.get() == LEGAL_FORMAT_OTHER else None
        if current is None or list(current) not in formats:
            messagebox.showinfo("Edit legal description format", 'Select "Other format" and pick one from the list first.')
            return
        labels = self._ask_legal_labels("Edit legal description format", current)
        if labels is None or labels == current:
            return
        if list(labels) in formats:
            messagebox.showerror("Edit legal description format", f'"{self._legal_format_display(*labels)}" already exists.')
            return
        formats[formats.index(list(current))] = list(labels)
        save_settings(self.settings)
        self.legal_other_format_var.set(self._legal_format_display(*labels))

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

    def _selected_date(self) -> datetime.date | None:
        year_str = self.date_year_var.get()
        month_name = self.date_month_var.get()
        day_str = self.date_day_var.get()
        if not (year_str.isdigit() and len(year_str) == 4 and month_name in MONTH_NAMES and day_str.isdigit()):
            return None
        return datetime.date(int(year_str), MONTH_NAMES.index(month_name) + 1, int(day_str))

    def _format_selected_date(self) -> str:
        date_value = self._selected_date()
        return _format_ordinal_date(date_value) if date_value is not None else ""

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

        # Read-only either way: the fixed Alternative solution text when
        # Alternative is ticked, "N/A" when it isn't - nothing to type.
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", ALTERNATIVE_SOLUTION_TEXT if self.alternative_var.get() else "N/A")
        widget.configure(state="disabled")

    def _sync_ps1_text_fields(self) -> None:
        if self._site_verification_widget is not None and self._site_verification_widget.winfo_exists():
            self.site_verification_text = self._site_verification_widget.get("1.0", "end-1c")

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
        # Legal description is optional, but if started it must be complete.
        first, second = self.legal_first_value_var.get().strip(), self.legal_second_value_var.get().strip()
        if first or second:
            if self._legal_labels() is None:
                messagebox.showerror("Missing info", 'Legal description: pick an Other format (or "Add..." one).')
                return False
            if not (first and second):
                labels = self._legal_labels()
                messagebox.showerror("Missing info", f"Legal description: fill in both {labels[0]} and {labels[1]}.")
                return False
        # Templates don't store the date, so only a real job needs one.
        if self.create_mode_var.get() != "edit_template" and not self._format_selected_date():
            messagebox.showerror("Missing info", "Date is required - pick a full date (or click Today).")
            return False
        return True

"""Main application window: a step-by-step wizard.

Steps:
0. Settings (drive paths) - only shown on first run, i.e. when the three
   drive paths haven't been configured yet. Skipped on subsequent runs.
1. General - the info shared by everything generated later (folders,
   documents, website submission).
2. PS1 Input - placeholder, details TBD.
3. Specification - placeholder, details TBD.
4. B2 Letter - placeholder, details TBD.
5. Review & Create - single Create button that generates everything
   (currently just the project folders; document generation and the
   website submission are wired in once their templates/details land).

There's no separate "fill the website" step: the website only needs data
already collected in General, so it's produced by the same Create action.
"""

from __future__ import annotations

import calendar
import datetime
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from app.config.settings import load_settings, save_settings
from app.core import folder_creator, word_filler
from app.utils.logger import get_logger

logger = get_logger(__name__)

SCOPE_ITEMS = ["Foundation", "Retaining", "Beams", "Portal", "Bracing", "Others"]
ROLE_OPTIONS = ["Carried out", "Supervised"]
ALL_PART_OPTIONS = ["All", "Part only"]
CM_ITEMS = ["CM1", "CM2", "CM3", "CM4", "CM5"]
COMPLIANCE_ALT_OPTIONS = ["Compliance", "Alternative"]
B1_OPTIONS = ["B1/VM1", "B1/MV4", "B1/AS1"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Symbols used for tick-box placeholders in the Word templates.
CHECKED = "☒"    # ☒
UNCHECKED = "☐"  # ☐

DRIVE_KEYS = ("engineer_drive", "drafting_drive", "admin_drive")

# Fixed label width (characters) on the PS1 step so every input widget
# starts at the same x position, regardless of label text length.
LABEL_WIDTH = 20


def _format_ordinal_date(value: datetime.date) -> str:
    """e.g. 1 -> "1st", 2 -> "2nd", 22 -> "22nd" -> "1st August 2026"."""
    day = value.day
    suffix = "th" if 11 <= day % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {value.strftime('%B')} {value.year}"

# Templates live in the repo (versioned), not in per-machine settings.
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "templates"
PROJECT_REGISTER_TEMPLATE = TEMPLATES_DIR / "Project register.docx"
PS1_TEMPLATE = TEMPLATES_DIR / "PS1 Producer Statement.docx"


class MainWindow(tk.Tk):
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
        self.engineer_drive_var = tk.StringVar(value=self.settings.get("engineer_drive", ""))
        self.drafting_drive_var = tk.StringVar(value=self.settings.get("drafting_drive", ""))
        self.admin_drive_var = tk.StringVar(value=self.settings.get("admin_drive", ""))

        self.job_number_var = tk.StringVar()
        self.client_info_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.role_var = tk.StringVar()

        self.scope_vars: dict[str, dict[str, Any]] = {
            item: {"selected": tk.BooleanVar(value=False), "description": ""} for item in SCOPE_ITEMS
        }
        self._scope_entries: dict[str, tk.Text] = {}

        self.availability_var = tk.StringVar()

        # ---- PS1 Input ----
        self.council_name_var = tk.StringVar()
        self.description_of_work_text = ""
        self.legal_description_text = ""
        self.all_part_var = tk.StringVar()
        self.cm_vars: dict[str, tk.BooleanVar] = {item: tk.BooleanVar(value=False) for item in CM_ITEMS}
        self.compliance_alt_var = tk.StringVar()
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
        self._council_combobox: ttk.Combobox | None = None
        self._council_warning_label: ttk.Label | None = None

    def _drives_configured(self) -> bool:
        return all(self.settings.get(key, "").strip() for key in DRIVE_KEYS)

    def _open_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Drive Settings")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text="Root path of each drive. Point these at the NAS or a synced OneDrive/SharePoint folder.",
            wraplength=420,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 8))

        drive_rows = [
            ("Engineer drive:", self.engineer_drive_var),
            ("Drafting drive:", self.drafting_drive_var),
            ("Admin drive:", self.admin_drive_var),
        ]
        for row, (label, var) in enumerate(drive_rows, start=1):
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=4)
            ttk.Entry(dialog, textvariable=var, width=40).grid(row=row, column=1, pady=4, padx=8)
            ttk.Button(dialog, text="Browse...", command=lambda v=var: self._browse_folder(v)).grid(
                row=row, column=2, pady=4, padx=(0, 12)
            )

        def on_save() -> None:
            if self._save_drive_settings():
                dialog.destroy()
                self._update_availability_status()

        ttk.Button(dialog, text="Save", command=on_save).grid(
            row=len(drive_rows) + 1, column=2, sticky="e", padx=12, pady=12
        )

    # ---------- step list / navigation ----------
    def _build_step_list(self) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        if not self._drives_configured():
            steps.append(
                {"title": "Settings", "build": self._build_settings_step, "validate": self._validate_settings_step}
            )
        steps.append({"title": "General", "build": self._build_general_step, "validate": self._validate_general_step})
        steps.append({"title": "PS1 Input", "build": self._build_ps1_step, "validate": self._validate_ps1_step})
        steps.append({"title": "Specification", "build": self._build_specification_step, "validate": None})
        steps.append({"title": "B2 Letter", "build": self._build_b2_letter_step, "validate": None})
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

    # ---------- Step: Settings ----------
    def _build_settings_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Set the root path of each drive once. These can point at the NAS "
                "today and be repointed at a synced OneDrive/SharePoint folder "
                "later without any code changes."
            ),
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        drive_rows = [
            ("Engineer drive:", self.engineer_drive_var),
            ("Drafting drive:", self.drafting_drive_var),
            ("Admin drive:", self.admin_drive_var),
        ]
        for row, (label, var) in enumerate(drive_rows, start=1):
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(parent, textvariable=var, width=45).grid(row=row, column=1, pady=4, padx=8)
            ttk.Button(parent, text="Browse...", command=lambda v=var: self._browse_folder(v)).grid(
                row=row, column=2, pady=4
            )

    def _browse_folder(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory(initialdir=var.get() or None)
        if path:
            var.set(path)

    def _save_drive_settings(self) -> bool:
        engineer = self.engineer_drive_var.get().strip()
        drafting = self.drafting_drive_var.get().strip()
        admin = self.admin_drive_var.get().strip()
        if not (engineer and drafting and admin):
            messagebox.showerror("Missing info", "All three drive paths are required.")
            return False

        self.settings["engineer_drive"] = engineer
        self.settings["drafting_drive"] = drafting
        self.settings["admin_drive"] = admin
        save_settings(self.settings)
        return True

    def _validate_settings_step(self) -> bool:
        return self._save_drive_settings()

    # ---------- Step: General ----------
    def _build_general_step(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Job number:").grid(row=0, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=self.job_number_var, width=40)
        entry.grid(row=0, column=1, sticky="w", pady=4, padx=8)
        entry.bind("<FocusOut>", lambda event: self._update_availability_status())

        ttk.Label(parent, text="Client info:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=self.client_info_var, width=40).grid(
            row=1, column=1, sticky="w", pady=4, padx=8
        )

        ttk.Label(parent, text="Address:").grid(row=2, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=self.address_var, width=40)
        entry.grid(row=2, column=1, sticky="w", pady=4, padx=8)
        entry.bind("<FocusOut>", lambda event: self._update_availability_status())

        self.availability_label = ttk.Label(parent, textvariable=self.availability_var, wraplength=560, justify="left")
        self.availability_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 8))
        self._update_availability_status()

        ttk.Label(parent, text="Scope:").grid(row=4, column=0, sticky="nw", pady=4)
        scope_frame = ttk.Frame(parent)
        scope_frame.grid(row=4, column=1, columnspan=2, sticky="w", pady=4)
        self._scope_entries = {}
        for row, item in enumerate(SCOPE_ITEMS):
            selected_var = self.scope_vars[item]["selected"]
            ttk.Checkbutton(
                scope_frame, text=item, variable=selected_var, command=lambda i=item: self._on_scope_toggle(i)
            ).grid(row=row, column=0, sticky="nw", pady=2)
            desc_text = tk.Text(
                scope_frame,
                width=60,
                height=2,
                wrap="word",
                state="normal" if selected_var.get() else "disabled",
            )
            desc_text.insert("1.0", self.scope_vars[item]["description"])
            if not selected_var.get():
                desc_text.configure(state="disabled")
            desc_text.grid(row=row, column=1, sticky="w", padx=8, pady=2)
            self._scope_entries[item] = desc_text

        ttk.Label(parent, text="Role:").grid(row=5, column=0, sticky="w", pady=(12, 4))
        role_frame = ttk.Frame(parent)
        role_frame.grid(row=5, column=1, columnspan=2, sticky="w", pady=(12, 4))
        for col, option in enumerate(ROLE_OPTIONS):
            ttk.Radiobutton(role_frame, text=option, variable=self.role_var, value=option).grid(
                row=0, column=col, sticky="w", padx=(0, 16)
            )

    def _on_scope_toggle(self, item: str) -> None:
        text_widget = self._scope_entries[item]
        selected = self.scope_vars[item]["selected"].get()
        if selected:
            text_widget.configure(state="normal")
        else:
            text_widget.configure(state="normal")
            text_widget.delete("1.0", "end")
            self.scope_vars[item]["description"] = ""
            text_widget.configure(state="disabled")

    def _sync_scope_descriptions(self) -> None:
        for item, widget in self._scope_entries.items():
            if widget.winfo_exists() and str(widget.cget("state")) == "normal":
                self.scope_vars[item]["description"] = widget.get("1.0", "end-1c")

    def _update_availability_status(self) -> None:
        # The label lives on the General step and gets destroyed whenever the
        # wizard navigates to a different step, so a stale reference here
        # would raise TclError - skip the update unless it's currently shown.
        if not hasattr(self, "availability_label") or not self.availability_label.winfo_exists():
            return

        job_number = self.job_number_var.get().strip()
        address = self.address_var.get().strip()
        if not job_number or not address:
            self.availability_var.set("")
            return

        conflicts = folder_creator.check_availability(
            job_number=job_number,
            address=address,
            engineer_drive=self.settings.get("engineer_drive", ""),
            drafting_drive=self.settings.get("drafting_drive", ""),
            admin_drive=self.settings.get("admin_drive", ""),
        )
        if conflicts:
            self.availability_label.configure(foreground="red")
            self.availability_var.set("Already exists on:\n" + "\n".join(str(path) for path in conflicts))
        else:
            project_name = folder_creator.build_project_folder_name(job_number, address)
            self.availability_label.configure(foreground="green")
            self.availability_var.set(f'Available: "{project_name}"')

    def _validate_general_step(self) -> bool:
        self._sync_scope_descriptions()
        if not self.job_number_var.get().strip():
            messagebox.showerror("Missing info", "Job number is required.")
            return False
        if not self.client_info_var.get().strip():
            messagebox.showerror("Missing info", "Client info is required.")
            return False
        if not self.address_var.get().strip():
            messagebox.showerror("Missing info", "Address is required.")
            return False
        if not any(self.scope_vars[item]["selected"].get() for item in SCOPE_ITEMS):
            messagebox.showerror("Missing info", "Select at least one Scope item.")
            return False
        for item in SCOPE_ITEMS:
            if self.scope_vars[item]["selected"].get() and not self.scope_vars[item]["description"].strip():
                messagebox.showerror("Missing info", f'"{item}" is checked but has no description.')
                return False
        if not self.role_var.get():
            messagebox.showerror("Missing info", "Select a Role.")
            return False

        job_number = self.job_number_var.get().strip()
        address = self.address_var.get().strip()
        conflicts = folder_creator.check_availability(
            job_number=job_number,
            address=address,
            engineer_drive=self.settings.get("engineer_drive", ""),
            drafting_drive=self.settings.get("drafting_drive", ""),
            admin_drive=self.settings.get("admin_drive", ""),
        )
        if conflicts:
            messagebox.showerror(
                "Folder already exists",
                "A project folder for this Job number/Address already exists on:\n"
                + "\n".join(str(path) for path in conflicts)
                + "\n\nChange the Job number or Address to continue.",
            )
            return False
        return True

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
        council_row.grid(row=row, column=1, columnspan=2, sticky="w", pady=4)
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

        ttk.Label(frame, text="Scope of statement:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=(12, 4))
        all_part_frame = ttk.Frame(frame)
        all_part_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=(12, 4))
        for col, option in enumerate(ALL_PART_OPTIONS):
            ttk.Radiobutton(all_part_frame, text=option, variable=self.all_part_var, value=option).grid(
                row=0, column=col, sticky="w", padx=(0, 16)
            )
        row += 1

        ttk.Label(frame, text="Level of construction\nmonitoring:", justify="left", width=LABEL_WIDTH).grid(
            row=row, column=0, sticky="nw", pady=4
        )
        cm_frame = ttk.Frame(frame)
        cm_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4)
        for col, item in enumerate(CM_ITEMS):
            ttk.Checkbutton(cm_frame, text=item, variable=self.cm_vars[item]).grid(
                row=0, column=col, sticky="w", padx=(0, 12)
            )
        row += 1

        ttk.Label(frame, text="Basis of statement:", width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", pady=(12, 4))
        compliance_frame = ttk.Frame(frame)
        compliance_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=(12, 4))
        for col, option in enumerate(COMPLIANCE_ALT_OPTIONS):
            ttk.Radiobutton(
                compliance_frame,
                text=option,
                variable=self.compliance_alt_var,
                value=option,
                command=self._on_compliance_alt_change,
            ).grid(row=0, column=col, sticky="w", padx=(0, 16))
        row += 1

        ttk.Label(frame, text="Compliance method(s)\n(if Compliance):", justify="left", width=LABEL_WIDTH).grid(
            row=row, column=0, sticky="nw", pady=4
        )
        b1_frame = ttk.Frame(frame)
        b1_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4)
        self._b1_checkbuttons = {}
        b1_state = "normal" if self.compliance_alt_var.get() == "Compliance" else "disabled"
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
        date_frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=4)

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
        choice = self.compliance_alt_var.get()

        b1_state = "normal" if choice == "Compliance" else "disabled"
        for cb in self._b1_checkbuttons.values():
            if cb.winfo_exists():
                cb.configure(state=b1_state)
        if choice != "Compliance":
            for var in self.b1_vars.values():
                var.set(False)

        widget = self._alternative_solution_widget
        if widget is None or not widget.winfo_exists():
            return

        if choice == "Compliance":
            widget.delete("1.0", "end")
            widget.insert("1.0", "N/A")
            widget.configure(state="disabled")
        elif choice == "Alternative":
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", self.alternative_solution_text)

    def _sync_ps1_text_fields(self) -> None:
        if self._description_of_work_widget is not None and self._description_of_work_widget.winfo_exists():
            self.description_of_work_text = self._description_of_work_widget.get("1.0", "end-1c")
        if self._legal_description_widget is not None and self._legal_description_widget.winfo_exists():
            self.legal_description_text = self._legal_description_widget.get("1.0", "end-1c")
        if (
            self.compliance_alt_var.get() == "Alternative"
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
        if self.compliance_alt_var.get() not in COMPLIANCE_ALT_OPTIONS:
            messagebox.showerror("Missing info", 'Select "Compliance" or "Alternative".')
            return False
        if self.compliance_alt_var.get() == "Alternative" and not self.alternative_solution_text.strip():
            messagebox.showerror("Missing info", 'Alternative solution is required when "Alternative" is selected.')
            return False
        return True

    # ---------- Step: Specification (placeholder) ----------
    def _build_specification_step(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Specification checklist - details coming soon.").grid(row=0, column=0, sticky="w")

    # ---------- Step: B2 Letter (placeholder) ----------
    def _build_b2_letter_step(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="B2 Letter - details coming soon.").grid(row=0, column=0, sticky="w")

    # ---------- Step: Review & Create ----------
    def _build_review_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Click Create to generate everything for this project.\n\n"
                "Currently implemented: project folders on the Engineer/Drafting/"
                "Admin drives.\n"
                "Coming once their templates/details are provided: the Project "
                "register and Consent Document files, PS1/B2 letter documents, "
                "and the timesheet website submission."
            ),
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        self.create_result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.create_result_var, wraplength=560, justify="left").grid(
            row=1, column=0, sticky="w", pady=(12, 0)
        )

    def _build_scope_lines(self) -> list[str]:
        # Plain text, no manual "- " prefix: the bullet glyph comes from a
        # real Word numbering definition, not a typed dash character.
        self._sync_scope_descriptions()
        return [
            self.scope_vars[item]["description"].strip()
            for item in SCOPE_ITEMS
            if self.scope_vars[item]["selected"].get()
        ]

    def _build_replacements(self) -> dict[str, str]:
        all_part = self.all_part_var.get()
        compliance_alt = self.compliance_alt_var.get()
        b1_selected = [option for option in B1_OPTIONS if self.b1_vars[option].get()]

        replacements = {
            "job_number": self.job_number_var.get().strip(),
            "client_info": self.client_info_var.get().strip(),
            "address": self.address_var.get().strip(),
            "role": self.role_var.get().strip(),
            "council_name": self.council_name_var.get().strip(),
            "description_of_work": self.description_of_work_text.strip(),
            # "legel_description" matches a typo baked into the PS1 template's placeholder token.
            "legel_description": self.legal_description_text.strip(),
            "all_box": CHECKED if all_part == "All" else UNCHECKED,
            "part_box": CHECKED if all_part == "Part only" else UNCHECKED,
            "compliance_box": CHECKED if compliance_alt == "Compliance" else UNCHECKED,
            "alternative_box": CHECKED if compliance_alt == "Alternative" else UNCHECKED,
            "compliance_solution": "; ".join(b1_selected) if compliance_alt == "Compliance" else "",
            "alternative_solution": "N/A" if compliance_alt == "Compliance" else self.alternative_solution_text.strip(),
            "date": self._format_selected_date(),
        }
        for item in CM_ITEMS:
            replacements[f"{item.lower()}_box"] = CHECKED if self.cm_vars[item].get() else UNCHECKED
        return replacements

    def _on_create(self) -> None:
        try:
            created = folder_creator.create_project_folders(
                job_number=self.job_number_var.get(),
                address=self.address_var.get(),
                engineer_drive=self.settings.get("engineer_drive", ""),
                drafting_drive=self.settings.get("drafting_drive", ""),
                admin_drive=self.settings.get("admin_drive", ""),
            )
        except (ValueError, FileExistsError) as exc:
            messagebox.showerror("Cannot create", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create project folders")
            messagebox.showerror("Error", str(exc))
            return

        summary = "\n".join(f"{name}: {path}" for name, path in created.items())
        replacements = self._build_replacements()
        bullet_lists = {"scope": self._build_scope_lines()}

        documents = [
            (PROJECT_REGISTER_TEMPLATE, Path("Project register.docx")),
            (PS1_TEMPLATE, Path("06 Consent Document") / "PS1 Producer Statement.docx"),
        ]
        for template_path, relative_output in documents:
            if not template_path.exists():
                logger.info("Template not found at %s, skipping", template_path)
                continue
            try:
                output_path = word_filler.fill_docx_template(
                    str(template_path), str(created["engineer"] / relative_output), replacements, bullet_lists
                )
                summary += f"\n{relative_output}: {output_path}"
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to fill template %s", template_path)
                self.create_result_var.set(f"Created:\n{summary}")
                messagebox.showwarning(
                    "Partial success", f"Some items were created, but {relative_output} failed:\n{exc}"
                )
                return

        self.create_result_var.set(f"Created:\n{summary}")
        self._update_availability_status()
        messagebox.showinfo("Done", "Project created successfully.")
        self._reset_for_new_project()

    def _reset_for_new_project(self) -> None:
        """Clear all per-project input and jump back to General, ready for
        the next project. Drive paths and the saved council list are app
        configuration, not project data, so they're left untouched.
        """
        self.job_number_var.set("")
        self.client_info_var.set("")
        self.address_var.set("")
        self.role_var.set("")
        for item in SCOPE_ITEMS:
            self.scope_vars[item]["selected"].set(False)
            self.scope_vars[item]["description"] = ""
        self.availability_var.set("")

        self.council_name_var.set("")
        self.description_of_work_text = ""
        self.legal_description_text = ""
        self.all_part_var.set("")
        for item in CM_ITEMS:
            self.cm_vars[item].set(False)
        self.compliance_alt_var.set("")
        for option in B1_OPTIONS:
            self.b1_vars[option].set(False)
        self.alternative_solution_text = ""
        self.date_year_var.set("")
        self.date_month_var.set("")
        self.date_day_var.set("")

        general_index = next(i for i, s in enumerate(self.steps) if s["title"] == "General")
        self.current_step = general_index
        self._show_step(general_index)


def run() -> None:
    app = MainWindow()
    app.mainloop()

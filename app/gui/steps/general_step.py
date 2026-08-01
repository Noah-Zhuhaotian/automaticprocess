"""Step: General - job number, client info, street/suburb/town, scope, role.

The info shared by everything generated later (folders, documents,
website submission).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.core import folder_creator
from app.gui.constants import ROLE_OPTIONS, SCOPE_ITEMS


class GeneralStepMixin:
    def _init_general_vars(self) -> None:
        self.job_number_var = tk.StringVar()
        self.client_info_var = tk.StringVar()
        self.street_var = tk.StringVar()
        self.suburb_var = tk.StringVar()
        self.town_var = tk.StringVar()
        self.role_var = tk.StringVar()

        self.scope_vars: dict[str, dict[str, Any]] = {
            item: {"selected": tk.BooleanVar(value=False), "description": ""} for item in SCOPE_ITEMS
        }
        self._scope_entries: dict[str, tk.Text] = {}

        self.availability_var = tk.StringVar()

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

        ttk.Label(parent, text="Street:").grid(row=2, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=self.street_var, width=40)
        entry.grid(row=2, column=1, sticky="w", pady=4, padx=8)
        entry.bind("<FocusOut>", lambda event: self._update_availability_status())

        ttk.Label(parent, text="Suburb:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=self.suburb_var, width=40).grid(row=3, column=1, sticky="w", pady=4, padx=8)

        ttk.Label(parent, text="Town:").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=self.town_var, width=40).grid(row=4, column=1, sticky="w", pady=4, padx=8)

        self.availability_label = ttk.Label(parent, textvariable=self.availability_var, wraplength=560, justify="left")
        self.availability_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))
        self._update_availability_status()

        ttk.Label(parent, text="Scope:").grid(row=6, column=0, sticky="nw", pady=4)
        scope_frame = ttk.Frame(parent)
        scope_frame.grid(row=6, column=1, columnspan=2, sticky="w", pady=4)
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

        ttk.Label(parent, text="Role:").grid(row=7, column=0, sticky="w", pady=(12, 4))
        role_frame = ttk.Frame(parent)
        role_frame.grid(row=7, column=1, columnspan=2, sticky="w", pady=(12, 4))
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
        street = self.street_var.get().strip()
        if not job_number or not street:
            self.availability_var.set("")
            return

        conflicts = folder_creator.check_availability(
            job_number=job_number,
            street=street,
            engineer_drive=self.settings.get("engineer_drive", ""),
            drafting_drive=self.settings.get("drafting_drive", ""),
            admin_drive=self.settings.get("admin_drive", ""),
        )
        if conflicts:
            self.availability_label.configure(foreground="red")
            self.availability_var.set("Already exists on:\n" + "\n".join(str(path) for path in conflicts))
        else:
            project_name = folder_creator.build_project_folder_name(job_number, street)
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
        if not self.street_var.get().strip():
            messagebox.showerror("Missing info", "Street is required.")
            return False
        if not self.suburb_var.get().strip():
            messagebox.showerror("Missing info", "Suburb is required.")
            return False
        if not self.town_var.get().strip():
            messagebox.showerror("Missing info", "Town is required.")
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
        street = self.street_var.get().strip()
        conflicts = folder_creator.check_availability(
            job_number=job_number,
            street=street,
            engineer_drive=self.settings.get("engineer_drive", ""),
            drafting_drive=self.settings.get("drafting_drive", ""),
            admin_drive=self.settings.get("admin_drive", ""),
        )
        if conflicts:
            messagebox.showerror(
                "Folder already exists",
                "A project folder for this Job number/Street already exists on:\n"
                + "\n".join(str(path) for path in conflicts)
                + "\n\nChange the Job number or Street to continue.",
            )
            return False
        return True

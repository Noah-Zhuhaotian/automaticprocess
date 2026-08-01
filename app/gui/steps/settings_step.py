"""Step: Settings - drive paths (Engineer/Drafting/Admin).

Only shown in the step list on first run, i.e. when any of the three
paths is still unconfigured; always reachable afterwards via the header's
"File path" button (_open_settings_dialog).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.config.settings import save_settings
from app.gui.constants import DRIVE_KEYS


class SettingsStepMixin:
    def _init_settings_vars(self) -> None:
        self.engineer_drive_var = tk.StringVar(value=self.settings.get("engineer_drive", ""))
        self.drafting_drive_var = tk.StringVar(value=self.settings.get("drafting_drive", ""))
        self.admin_drive_var = tk.StringVar(value=self.settings.get("admin_drive", ""))

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

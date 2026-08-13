"""Step: Settings - drive paths (Engineer/Drafting/Admin) plus the
MinuteDock Personal Access Token. Both are required - the app can't create
a project without the drives, and MinuteDock sync is a mandatory part of
Create now, not an optional add-on.

The first-run step (_build_settings_step) covers drives and the token and
is only shown in the step list when any of them is still unconfigured; the
dialog (_open_settings_dialog, always reachable via the header's
"Settings" button) covers the same fields for changing them later.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.config.settings import save_settings
from app.core import minutedock_client
from app.core.minutedock_client import MinuteDockError
from app.gui.constants import DRIVE_KEYS


class SettingsStepMixin:
    def _init_settings_vars(self) -> None:
        self.engineer_drive_var = tk.StringVar(value=self.settings.get("engineer_drive", ""))
        self.drafting_drive_var = tk.StringVar(value=self.settings.get("drafting_drive", ""))
        self.admin_drive_var = tk.StringVar(value=self.settings.get("admin_drive", ""))
        self.minutedock_token_var = tk.StringVar(value=self.settings.get("minutedock_access_token", ""))

    def _settings_configured(self) -> bool:
        return all(self.settings.get(key, "").strip() for key in DRIVE_KEYS) and bool(
            self.settings.get("minutedock_access_token", "").strip()
        )

    def _open_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Settings")
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

        token_row = len(drive_rows) + 1
        ttk.Separator(dialog, orient="horizontal").grid(
            row=token_row, column=0, columnspan=3, sticky="ew", padx=12, pady=(8, 8)
        )
        ttk.Label(
            dialog,
            text=(
                "MinuteDock Personal Access Token (required). Generate one from your "
                "MinuteDock profile → Manage Access Tokens."
            ),
            wraplength=420,
            justify="left",
        ).grid(row=token_row + 1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))
        ttk.Label(dialog, text="MinuteDock token:").grid(
            row=token_row + 2, column=0, sticky="w", padx=12, pady=4
        )
        ttk.Entry(dialog, textvariable=self.minutedock_token_var, width=40, show="*").grid(
            row=token_row + 2, column=1, pady=4, padx=8
        )
        ttk.Button(dialog, text="Test connection", command=self._test_minutedock_connection).grid(
            row=token_row + 2, column=2, pady=4, padx=(0, 12)
        )

        def on_save() -> None:
            if self._save_settings():
                dialog.destroy()
                self._update_availability_status()
                self._refresh_step_list_preserving_position()

        ttk.Button(dialog, text="Save", command=on_save).grid(
            row=token_row + 3, column=2, sticky="e", padx=12, pady=12
        )

    def _refresh_step_list_preserving_position(self) -> None:
        """Rebuild self.steps after Settings changes something that affects
        _build_step_list() (currently: whether the first-run "Settings" step
        is still needed, i.e. _settings_configured() flipping from False to
        True) - self.steps is otherwise only ever rebuilt in
        _reset_for_new_project(), which runs after a full successful Create,
        not right after Settings is saved. Without this, completing Settings
        mid-session (the dialog can be opened from any step, not just a
        first-run flow that always lands back on General) wouldn't drop the
        "Settings" step from the list until the app was restarted - stay on
        the same *named* step across the rebuild rather than assuming an
        index.
        """
        current_title = self.steps[self.current_step]["title"]
        self.steps = self._build_step_list()
        for index, step in enumerate(self.steps):
            if step["title"] == current_title:
                self.current_step = index
                break
        else:
            self.current_step = min(self.current_step, len(self.steps) - 1)
        self._show_step(self.current_step)

    def _test_minutedock_connection(self) -> None:
        token = self.minutedock_token_var.get().strip()
        if not token:
            messagebox.showerror("Missing token", "Enter a MinuteDock token first.")
            return
        try:
            account_name = minutedock_client.test_connection(token)
        except MinuteDockError as exc:
            messagebox.showerror("Connection failed", str(exc))
            return
        messagebox.showinfo("Connection successful", f"Connected to MinuteDock account: {account_name}")

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

        token_row = len(drive_rows) + 1
        ttk.Separator(parent, orient="horizontal").grid(
            row=token_row, column=0, columnspan=3, sticky="ew", pady=(8, 8)
        )
        ttk.Label(
            parent,
            text=(
                "MinuteDock Personal Access Token (required). Generate one from your "
                "MinuteDock profile → Manage Access Tokens."
            ),
            wraplength=560,
            justify="left",
        ).grid(row=token_row + 1, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(parent, text="MinuteDock token:").grid(row=token_row + 2, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=self.minutedock_token_var, width=45, show="*").grid(
            row=token_row + 2, column=1, pady=4, padx=8
        )
        ttk.Button(parent, text="Test connection", command=self._test_minutedock_connection).grid(
            row=token_row + 2, column=2, pady=4
        )

    def _browse_folder(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory(initialdir=var.get() or None)
        if path:
            var.set(path)

    def _save_settings(self) -> bool:
        engineer = self.engineer_drive_var.get().strip()
        drafting = self.drafting_drive_var.get().strip()
        admin = self.admin_drive_var.get().strip()
        token = self.minutedock_token_var.get().strip()
        if not (engineer and drafting and admin):
            messagebox.showerror("Missing info", "All three drive paths are required.")
            return False
        if not token:
            messagebox.showerror("Missing info", "A MinuteDock Personal Access Token is required.")
            return False

        # Two drives resolving to the same folder isn't just redundant - it
        # makes create_project_folders() try to create the identical
        # physical folder twice for one project and fail on the second
        # attempt with a raw "already exists" OSError, after the first
        # attempt already succeeded (a real incident: admin_drive got set
        # equal to engineer_drive, silently leaving empty orphaned project
        # folders with no documents and no MinuteDock sync for every job
        # created in that state).
        drives = {"Engineer": engineer, "Drafting": drafting, "Admin": admin}
        seen: dict[str, str] = {}
        for label, path in drives.items():
            key = os.path.normcase(os.path.normpath(path))
            if key in seen:
                messagebox.showerror(
                    "Duplicate drive path",
                    f"{seen[key]} drive and {label} drive point at the same folder:\n{path}\n\n"
                    "Each of the three drives needs its own separate folder.",
                )
                return False
            seen[key] = label

        self.settings["engineer_drive"] = engineer
        self.settings["drafting_drive"] = drafting
        self.settings["admin_drive"] = admin
        self.settings["minutedock_access_token"] = token
        save_settings(self.settings)
        return True

    def _validate_settings_step(self) -> bool:
        return self._save_settings()

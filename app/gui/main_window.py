"""Main application window.

Layout:
- A "shared input" panel at the top (Job Number, Client Info, Address,
  Scope, Budget) whose values are reused across all three feature tabs.
- A notebook with one tab per feature, plus a Settings tab for the
  configurable drive paths used by Step 1.

Steps 2 and 3 are still placeholders (NotImplementedError) and will be
implemented later.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.config.settings import load_settings, save_settings
from app.core import folder_creator, web_filler, word_filler
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Automatic Process Assistant")
        self.geometry("560x520")
        self.resizable(False, False)

        self.settings = load_settings()

        self._build_shared_input_frame()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        notebook.add(self._build_folder_tab(notebook), text="1. Create Folders")
        notebook.add(self._build_word_tab(notebook), text="2. Fill Word")
        notebook.add(self._build_web_tab(notebook), text="3. Fill Timesheet Site")
        notebook.add(self._build_settings_tab(notebook), text="Settings")

    # ---------- Shared input panel ----------
    def _build_shared_input_frame(self) -> None:
        frame = ttk.LabelFrame(self, text="Shared Input")
        frame.pack(fill="x", padx=10, pady=(10, 0))

        self.job_number_var = tk.StringVar()
        self.client_info_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.scope_var = tk.StringVar()
        self.budget_var = tk.StringVar()

        fields = [
            ("Job number:", self.job_number_var),
            ("Client info:", self.client_info_var),
            ("Address:", self.address_var),
            ("Scope:", self.scope_var),
            ("Budget:", self.budget_var),
        ]
        for row, (label, var) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
            ttk.Entry(frame, textvariable=var, width=45).grid(row=row, column=1, padx=8, pady=4)

    # ---------- Step 1: create folders ----------
    def _build_folder_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent)

        ttk.Label(
            frame,
            text=(
                "Creates the project folder \"Job Number - Address\" on the "
                "Engineer, Drafting and Admin drives configured in Settings.\n"
                "The Engineer drive also gets the fixed subfolders."
            ),
            wraplength=480,
            justify="left",
        ).pack(padx=8, pady=8, anchor="w")

        ttk.Button(frame, text="Create Project Folders", command=self._on_create_folders).pack(
            padx=8, pady=12, anchor="e"
        )

        self.folder_result_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.folder_result_var, wraplength=480, justify="left").pack(
            padx=8, pady=8, anchor="w"
        )
        return frame

    def _on_create_folders(self) -> None:
        try:
            created = folder_creator.create_project_folders(
                job_number=self.job_number_var.get(),
                address=self.address_var.get(),
                engineer_drive=self.settings.get("engineer_drive", ""),
                drafting_drive=self.settings.get("drafting_drive", ""),
                admin_drive=self.settings.get("admin_drive", ""),
            )
        except (ValueError, FileExistsError) as exc:
            messagebox.showerror("Cannot create folders", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create project folders")
            messagebox.showerror("Error", str(exc))
            return

        summary = "\n".join(f"{name}: {path}" for name, path in created.items())
        self.folder_result_var.set(f"Created:\n{summary}")
        messagebox.showinfo("Done", "Project folders created successfully.")

    # ---------- Step 2: fill Word ----------
    def _build_word_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Word feature coming in step 2").pack(padx=8, pady=8)
        return frame

    # ---------- Step 3: fill timesheet website ----------
    def _build_web_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Website feature coming in step 3").pack(padx=8, pady=8)
        return frame

    # ---------- Settings ----------
    def _build_settings_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent)

        ttk.Label(
            frame,
            text=(
                "Configure the root path of each drive. These can point at the "
                "NAS today and be repointed at a synced OneDrive/SharePoint "
                "folder later without any code changes."
            ),
            wraplength=480,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=8, pady=(8, 12))

        self.engineer_drive_var = tk.StringVar(value=self.settings.get("engineer_drive", ""))
        self.drafting_drive_var = tk.StringVar(value=self.settings.get("drafting_drive", ""))
        self.admin_drive_var = tk.StringVar(value=self.settings.get("admin_drive", ""))

        drive_rows = [
            ("Engineer drive:", self.engineer_drive_var),
            ("Drafting drive:", self.drafting_drive_var),
            ("Admin drive:", self.admin_drive_var),
        ]
        for row, (label, var) in enumerate(drive_rows, start=1):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
            ttk.Entry(frame, textvariable=var, width=40).grid(row=row, column=1, padx=8, pady=4)
            ttk.Button(frame, text="Browse...", command=lambda v=var: self._browse_folder(v)).grid(
                row=row, column=2, padx=8, pady=4
            )

        ttk.Button(frame, text="Save Settings", command=self._on_save_settings).grid(
            row=len(drive_rows) + 1, column=2, sticky="e", padx=8, pady=12
        )
        return frame

    def _browse_folder(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory(initialdir=var.get() or None)
        if path:
            var.set(path)

    def _on_save_settings(self) -> None:
        self.settings["engineer_drive"] = self.engineer_drive_var.get()
        self.settings["drafting_drive"] = self.drafting_drive_var.get()
        self.settings["admin_drive"] = self.admin_drive_var.get()
        save_settings(self.settings)
        messagebox.showinfo("Saved", "Settings saved.")


def run() -> None:
    app = MainWindow()
    app.mainloop()

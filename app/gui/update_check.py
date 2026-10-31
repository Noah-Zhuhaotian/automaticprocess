"""The header's "Check for updates" button: GUI side of app/core/updater.py.

Checking and downloading run on a worker thread that only ever queue.put()s
(the same rule as Create - see review_step._poll_create_result); the main
thread polls the queue with self.after. Messages: {"kind": "checked",
"update"}, {"kind": "progress", "done", "total"}, {"kind": "downloaded",
"path"}, {"kind": "error", "message"}.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from app.core import updater
from app.utils.logger import get_logger
from app.version import __version__

logger = get_logger(__name__)

# Release notes longer than this are cut in the "update available" prompt.
MAX_NOTES_CHARS = 800


class UpdateCheckMixin:
    def _check_for_updates(self) -> None:
        self._update_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._show_update_dialog("Checking for updates...")
        threading.Thread(target=self._run_update_check, daemon=True).start()
        self.after(100, self._poll_update_queue)

    def _run_update_check(self) -> None:
        try:
            self._update_queue.put({"kind": "checked", "update": updater.check_for_update()})
        except updater.UpdateError as exc:
            self._update_queue.put({"kind": "error", "message": str(exc)})

    def _run_update_download(self, update: dict[str, Any]) -> None:
        def on_progress(done: int, total: int) -> None:
            self._update_queue.put({"kind": "progress", "done": done, "total": total})

        try:
            path = updater.download_installer(update, on_progress)
            self._update_queue.put({"kind": "downloaded", "path": path})
        except updater.UpdateError as exc:
            self._update_queue.put({"kind": "error", "message": str(exc)})

    def _poll_update_queue(self) -> None:
        try:
            message = self._update_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_update_queue)
            return

        kind = message["kind"]
        if kind == "progress":
            # Only the latest progress matters - skip any backlog.
            while True:
                try:
                    newer = self._update_queue.get_nowait()
                except queue.Empty:
                    break
                if newer["kind"] != "progress":
                    self._update_queue.put(newer)
                    break
                message = newer
            self._set_update_progress(message["done"], message["total"])
            self.after(100, self._poll_update_queue)
            return

        self._hide_update_dialog()
        if kind == "error":
            logger.warning("Update failed: %s", message["message"])
            messagebox.showerror("Check for updates", message["message"], parent=self)
        elif kind == "checked":
            self._on_update_checked(message["update"])
        elif kind == "downloaded":
            self._install_update(message["path"])

    def _on_update_checked(self, update: dict[str, Any] | None) -> None:
        if update is None:
            messagebox.showinfo(
                "Check for updates", f"You have the latest version ({__version__}).", parent=self
            )
            return
        if not updater.is_packaged():
            messagebox.showinfo(
                "Check for updates",
                f"Version {update['version']} is available (this is {__version__}), but this copy is running "
                "from source - updates install only into the installed app.",
                parent=self,
            )
            return

        notes = update["notes"]
        if len(notes) > MAX_NOTES_CHARS:
            notes = notes[:MAX_NOTES_CHARS].rstrip() + "..."
        text = f"Version {update['version']} is available (you have {__version__})."
        if notes:
            text += f"\n\nWhat's new:\n{notes}"
        text += (
            "\n\nDownload and install it now? The app will close while it upgrades and reopen when it's done. "
            "Your settings, saved projects and templates are kept. Anything not yet created in the wizard "
            "will be lost."
        )
        if not messagebox.askyesno("Update available", text, parent=self):
            return

        self._update_queue = queue.Queue()
        self._show_update_dialog(f"Downloading version {update['version']}...", determinate=True)
        threading.Thread(target=self._run_update_download, args=(update,), daemon=True).start()
        self.after(100, self._poll_update_queue)

    def _install_update(self, installer: Path) -> None:
        try:
            updater.launch_installer(installer)
        except updater.UpdateError as exc:
            logger.warning("Update failed: %s", exc)
            messagebox.showerror("Update", f"{exc}\n\nThe app was not updated.", parent=self)
            return
        self.destroy()

    # ---------- progress dialog ----------
    def _show_update_dialog(self, text: str, determinate: bool = False) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Please wait")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # no closing while the work is running

        frame = ttk.Frame(dialog, padding=24)
        frame.pack(fill="both", expand=True)
        self._update_text_var = tk.StringVar(value=text)
        ttk.Label(frame, textvariable=self._update_text_var).pack(pady=(0, 12))
        self._update_progress = ttk.Progressbar(
            frame, mode="determinate" if determinate else "indeterminate", length=260, maximum=100
        )
        self._update_progress.pack()
        if not determinate:
            self._update_progress.start(12)

        self.update_idletasks()
        x = self.winfo_rootx() + max((self.winfo_width() - 320) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - 120) // 2, 0)
        dialog.geometry(f"+{x}+{y}")

        dialog.grab_set()
        self._update_dialog = dialog
        self._update_base_text = text

    def _set_update_progress(self, done: int, total: int) -> None:
        if total:
            percent = min(done * 100 // total, 100)
            self._update_progress["value"] = percent
            self._update_text_var.set(f"{self._update_base_text} {percent}%")

    def _hide_update_dialog(self) -> None:
        dialog = getattr(self, "_update_dialog", None)
        if dialog is not None and dialog.winfo_exists():
            dialog.destroy()
        self._update_dialog = None

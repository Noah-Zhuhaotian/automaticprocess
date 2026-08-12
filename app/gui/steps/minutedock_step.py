"""Step: MinuteDock - per-project billing settings synced to MinuteDock
(https://minutedock.com) alongside the Word documents on Create.

Only shown when a MinuteDock Personal Access Token is configured in
Settings - see main_window.py's _build_step_list. The token itself is
machine/app config, not project data, so it lives in Settings, not here.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

RATE_MODE_OPTIONS = [("contact", "Use contact rates"), ("standard", "Set a standard rate for this project")]


class MinuteDockStepMixin:
    def _init_minutedock_vars(self) -> None:
        self.minutedock_billable_var = tk.BooleanVar(value=True)
        self.minutedock_rate_mode_var = tk.StringVar(value="contact")
        self.minutedock_standard_rate_var = tk.StringVar()
        self._minutedock_rate_widget: ttk.Entry | None = None

    # ---------- Step: MinuteDock ----------
    def _build_minutedock_step(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="These settings control the Project MinuteDock creates for this job.",
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Checkbutton(
            frame, text="Project is billable", variable=self.minutedock_billable_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        for row, (value, label) in enumerate(RATE_MODE_OPTIONS, start=2):
            ttk.Radiobutton(
                frame,
                text=label,
                variable=self.minutedock_rate_mode_var,
                value=value,
                command=self._on_minutedock_rate_mode_change,
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)

        rate_row = 2 + len(RATE_MODE_OPTIONS)
        ttk.Label(frame, text="Standard rate ($/hour):").grid(row=rate_row, column=0, sticky="w", pady=(4, 4), padx=(20, 0))
        self._minutedock_rate_widget = ttk.Entry(frame, textvariable=self.minutedock_standard_rate_var, width=12)
        self._minutedock_rate_widget.grid(row=rate_row, column=1, sticky="w", pady=(4, 4), padx=8)

        self._on_minutedock_rate_mode_change()

    def _on_minutedock_rate_mode_change(self) -> None:
        widget = self._minutedock_rate_widget
        if widget is None or not widget.winfo_exists():
            return
        if self.minutedock_rate_mode_var.get() == "standard":
            widget.configure(state="normal")
        else:
            self.minutedock_standard_rate_var.set("")
            widget.configure(state="disabled")

    def _validate_minutedock_step(self) -> bool:
        if self.minutedock_rate_mode_var.get() != "standard":
            return True

        raw = self.minutedock_standard_rate_var.get().strip()
        try:
            rate = float(raw)
        except ValueError:
            messagebox.showerror("Missing info", "Enter a numeric standard rate.")
            return False
        if rate <= 0:
            messagebox.showerror("Missing info", "Standard rate must be greater than 0.")
            return False

        # Normalize to MinuteDock's CurrencyString format (exactly 2 decimals) now,
        # so review_step.py never has to reformat it before sending.
        self.minutedock_standard_rate_var.set(f"{rate:.2f}")
        return True

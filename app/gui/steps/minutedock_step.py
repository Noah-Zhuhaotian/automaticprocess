"""Step: MinuteDock - per-project settings synced to MinuteDock
(https://minutedock.com) on Create.

Rates are always "Use contact rates" - the client's own rate in MinuteDock
applies, so there's no per-project rate to choose here. The only choice is
an optional budget: a "$ Billable" amount "in total" (one budget for the
whole project, never resets) - no hours budget and no weekly/monthly reset,
by the user's request, so neither is offered.

Every project is created billable=True, with no user-facing toggle -
unchecking it stops MinuteDock's own web UI from accepting time entries
against that project at all, so it's not a real per-project choice.

The Personal Access Token itself is machine/app config, not project data,
so it lives in Settings, not here.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk


class MinuteDockStepMixin:
    def _init_minutedock_vars(self) -> None:
        self.minutedock_budget_enabled_var = tk.BooleanVar(value=False)
        self.minutedock_budget_amount_var = tk.StringVar()
        self._minutedock_budget_widget: ttk.Entry | None = None

    # ---------- Step: MinuteDock ----------
    def _build_minutedock_step(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        existing = self.existing_minutedock_project
        if existing is not None:
            intro = (
                f"Job {self.job_number_var.get().strip()} already has a MinuteDock project "
                f"(client: {existing['contact_name'] or 'unknown'}). These are its current settings - "
                "if you change them, they'll be saved back to that project on Create. "
                "No new project is created."
            )
        else:
            intro = "These settings control the Project MinuteDock creates for this job."
        ttk.Label(frame, text=intro, wraplength=560, justify="left").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )

        ttk.Label(frame, text="Rates:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(frame, text="Use contact rates").grid(row=1, column=1, columnspan=2, sticky="w", pady=4, padx=8)

        ttk.Checkbutton(
            frame,
            text="Set a budget",
            variable=self.minutedock_budget_enabled_var,
            command=self._on_minutedock_budget_toggle,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 4))

        ttk.Label(frame, text="$ Billable:").grid(row=3, column=0, sticky="w", pady=4, padx=(20, 0))
        amount_vcmd = (self.register(self._validate_budget_input), "%P")
        self._minutedock_budget_widget = ttk.Entry(
            frame,
            textvariable=self.minutedock_budget_amount_var,
            width=14,
            validate="key",
            validatecommand=amount_vcmd,
        )
        self._minutedock_budget_widget.grid(row=3, column=1, sticky="w", pady=4, padx=8)
        ttk.Label(frame, text="in total").grid(row=3, column=2, sticky="w", pady=4)

        if existing is not None and existing.get("other_budget"):
            ttk.Label(
                frame,
                text=(
                    f"This project currently has a budget this app doesn't edit ({existing['other_budget']}). "
                    'Leave "Set a budget" unticked to keep it as it is; ticking it replaces it.'
                ),
                foreground="gray",
                wraplength=560,
                justify="left",
            ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self._on_minutedock_budget_toggle()

    def _validate_budget_input(self, proposed: str) -> bool:
        """Keystroke filter: digits with at most one decimal point and two
        decimal places - nothing else can be typed."""
        if proposed == "":
            return True
        whole, dot, cents = proposed.partition(".")
        return whole.isdigit() if not dot else (whole.isdigit() or whole == "") and (
            cents == "" or (cents.isdigit() and len(cents) <= 2)
        )

    def _on_minutedock_budget_toggle(self) -> None:
        widget = self._minutedock_budget_widget
        if widget is None or not widget.winfo_exists():
            return
        if self.minutedock_budget_enabled_var.get():
            widget.configure(state="normal")
        else:
            self.minutedock_budget_amount_var.set("")
            widget.configure(state="disabled")

    def _validate_minutedock_step(self) -> bool:
        if not self.minutedock_budget_enabled_var.get():
            return True

        raw = self.minutedock_budget_amount_var.get().strip()
        try:
            amount = float(raw)
        except ValueError:
            messagebox.showerror("Missing info", "Enter the budget amount ($ Billable).")
            return False
        if amount <= 0:
            messagebox.showerror("Missing info", "Budget amount must be greater than 0.")
            return False

        # Normalize to MinuteDock's CurrencyString format (exactly 2 decimals)
        # now, so review_step.py never has to reformat it before sending.
        self.minutedock_budget_amount_var.set(f"{amount:.2f}")
        return True

    def _minutedock_budget_dollars(self) -> str | None:
        """The budget to send: the normalized amount, or None for no budget."""
        if not self.minutedock_budget_enabled_var.get():
            return None
        return self.minutedock_budget_amount_var.get().strip() or None

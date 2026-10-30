"""Step: Scope - which of the six scope items apply (each with a
free-text description) plus the Role. Only shown when Word documents are
being generated ("documents_only" / "both" Create modes), right after
General: the selected items feed the Project register's and PS1's
{{scope}} bullet list and the LBP form's restricted-building-work table,
where Role fills each selected item's "Carried out / Supervised" cell.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.gui.constants import ROLE_OPTIONS, SCOPE_ITEMS


class ScopeStepMixin:
    def _init_scope_vars(self) -> None:
        self.role_var = tk.StringVar()
        self.scope_vars: dict[str, dict[str, Any]] = {
            item: {"selected": tk.BooleanVar(value=False), "description": ""} for item in SCOPE_ITEMS
        }
        self._scope_entries: dict[str, tk.Text] = {}

    # ---------- Step: Scope ----------
    def _build_scope_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Tick each scope item that applies and describe it - press Enter between points; "
            "each line becomes its own bullet in the documents.",
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._scope_entries = {}
        for row, item in enumerate(SCOPE_ITEMS, start=1):
            selected_var = self.scope_vars[item]["selected"]
            ttk.Checkbutton(
                parent, text=item, variable=selected_var, command=lambda i=item: self._on_scope_toggle(i)
            ).grid(row=row, column=0, sticky="nw", pady=2)
            desc_text = tk.Text(parent, width=60, height=2, wrap="word")
            desc_text.insert("1.0", self.scope_vars[item]["description"])
            if not selected_var.get():
                desc_text.configure(state="disabled")
            desc_text.grid(row=row, column=1, sticky="w", padx=8, pady=2)
            self._scope_entries[item] = desc_text

        role_row = len(SCOPE_ITEMS) + 1
        ttk.Label(parent, text="Role:").grid(row=role_row, column=0, sticky="w", pady=(12, 4))
        role_frame = ttk.Frame(parent)
        role_frame.grid(row=role_row, column=1, sticky="w", pady=(12, 4), padx=8)
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

    def _scope_description_lines(self, item: str) -> list[str]:
        """Split a scope item's free-text description into individual
        lines - each Enter-separated line the user types becomes one
        bullet point (in the LBP form's description cell) or one
        semicolon-joined clause (in the {{scope}} summary list)."""
        text = self.scope_vars[item]["description"]
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _validate_scope_step(self) -> bool:
        self._sync_scope_descriptions()
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
        return True

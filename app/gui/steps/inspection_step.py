"""Step: Inspection Schedule - PS1's "Schedule 3 - Schedule of
Inspections" table. The user picks which of the 7 typical inspection
items apply (plus an optional free-text "Other" item) and orders them;
that order becomes the table's No. column (see word_filler's
_remove_unselected_table_rows and INSPECTION_ITEMS/INSPECTION_OTHER_* in
constants.py).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.gui.constants import INSPECTION_ITEMS, INSPECTION_OTHER_KEY


class InspectionStepMixin:
    def _init_inspection_vars(self) -> None:
        self.inspection_vars: dict[str, tk.BooleanVar] = {
            key: tk.BooleanVar(value=False) for key, _item, _time_frame in INSPECTION_ITEMS
        }
        self.inspection_other_var = tk.BooleanVar(value=False)
        self.inspection_other_description_var = tk.StringVar()
        self.inspection_other_time_frame_var = tk.StringVar()
        # Order of *selected* keys only - the single source of truth for
        # both what's included and the No. column each gets. Kept in sync
        # with the checkboxes by _on_inspection_toggle rather than derived
        # fresh each time, so a user's manual reordering (Move Up/Down)
        # survives further checkbox changes elsewhere in the list.
        self.inspection_order: list[str] = []
        self._inspection_other_widgets: list[tk.Widget] = []
        self._inspection_order_listbox: tk.Listbox | None = None

    def _inspection_item_text(self, key: str) -> str:
        if key == INSPECTION_OTHER_KEY:
            description = self.inspection_other_description_var.get().strip()
            return f"Other: {description}" if description else "Other"
        for item_key, item_text, _time_frame in INSPECTION_ITEMS:
            if item_key == key:
                return item_text
        raise KeyError(key)

    # ---------- Step: Inspection Schedule ----------
    def _build_inspection_step(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=(
                "Select which inspections apply to this project, then use Move Up/"
                "Move Down to set the order - that order becomes the No. column in "
                "PS1's Schedule of Inspections."
            ),
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        row = 1
        for key, item_text, _time_frame in INSPECTION_ITEMS:
            ttk.Checkbutton(
                frame,
                text=item_text,
                variable=self.inspection_vars[key],
                command=lambda k=key: self._on_inspection_toggle(k, self.inspection_vars[k].get()),
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
            row += 1

        ttk.Checkbutton(
            frame,
            text="Other",
            variable=self.inspection_other_var,
            command=self._on_inspection_other_toggle,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 2))
        row += 1

        other_frame = ttk.Frame(frame)
        other_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=(20, 0), pady=(0, 8))
        ttk.Label(other_frame, text="Item of inspection:").grid(row=0, column=0, sticky="w")
        description_entry = ttk.Entry(
            other_frame, textvariable=self.inspection_other_description_var, width=42, state="disabled"
        )
        description_entry.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=2)
        description_entry.bind("<KeyRelease>", lambda event: self._refresh_inspection_order_listbox())
        ttk.Label(other_frame, text="Time frame:").grid(row=1, column=0, sticky="w")
        time_frame_entry = ttk.Entry(
            other_frame, textvariable=self.inspection_other_time_frame_var, width=42, state="disabled"
        )
        time_frame_entry.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=2)
        self._inspection_other_widgets = [description_entry, time_frame_entry]
        row += 1

        ttk.Label(frame, text="Order (top = No. 1):").grid(row=row, column=0, sticky="w", pady=(8, 4))
        row += 1

        order_row_frame = ttk.Frame(frame)
        order_row_frame.grid(row=row, column=0, columnspan=2, sticky="w")
        self._inspection_order_listbox = tk.Listbox(order_row_frame, width=60, height=8, exportselection=False)
        self._inspection_order_listbox.grid(row=0, column=0, sticky="w")
        buttons_frame = ttk.Frame(order_row_frame)
        buttons_frame.grid(row=0, column=1, sticky="n", padx=(8, 0))
        ttk.Button(buttons_frame, text="Move Up", command=lambda: self._move_inspection_item(-1)).grid(
            row=0, column=0, pady=(0, 4), sticky="we"
        )
        ttk.Button(buttons_frame, text="Move Down", command=lambda: self._move_inspection_item(1)).grid(
            row=1, column=0, sticky="we"
        )

        self._refresh_inspection_order_listbox()

    def _on_inspection_toggle(self, key: str, selected: bool) -> None:
        if selected:
            if key not in self.inspection_order:
                self.inspection_order.append(key)
        else:
            if key in self.inspection_order:
                self.inspection_order.remove(key)
        self._refresh_inspection_order_listbox()

    def _on_inspection_other_toggle(self) -> None:
        selected = self.inspection_other_var.get()
        for widget in self._inspection_other_widgets:
            if widget.winfo_exists():
                widget.configure(state="normal" if selected else "disabled")
        if not selected:
            self.inspection_other_description_var.set("")
            self.inspection_other_time_frame_var.set("")
        self._on_inspection_toggle(INSPECTION_OTHER_KEY, selected)

    def _move_inspection_item(self, direction: int) -> None:
        listbox = self._inspection_order_listbox
        if listbox is None or not listbox.winfo_exists():
            return
        selection = listbox.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + direction
        if not (0 <= new_index < len(self.inspection_order)):
            return
        order = self.inspection_order
        order[index], order[new_index] = order[new_index], order[index]
        self._refresh_inspection_order_listbox()
        listbox.selection_set(new_index)

    def _refresh_inspection_order_listbox(self) -> None:
        listbox = self._inspection_order_listbox
        if listbox is None or not listbox.winfo_exists():
            return
        listbox.delete(0, "end")
        for position, key in enumerate(self.inspection_order, start=1):
            listbox.insert("end", f"{position}. {self._inspection_item_text(key)}")

    def _validate_inspection_step(self) -> bool:
        if not self.inspection_order:
            messagebox.showerror("Missing info", "Select at least one inspection item.")
            return False
        if self.inspection_other_var.get():
            if not self.inspection_other_description_var.get().strip():
                messagebox.showerror("Missing info", '"Item of inspection" is required for Other.')
                return False
            if not self.inspection_other_time_frame_var.get().strip():
                messagebox.showerror("Missing info", '"Time frame" is required for Other.')
                return False
        return True

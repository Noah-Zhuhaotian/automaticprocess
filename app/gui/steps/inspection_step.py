"""Step: Inspection Schedule - PS1's "Schedule 3 - Schedule of
Inspections" table. The user picks which of the 7 typical inspection
items apply, adds any number of free-text "Other" items, and orders
everything; that order becomes the table's No. column (see word_filler's
_reorder_table_rows/_insert_dynamic_table_rows and
INSPECTION_ITEMS/INSPECTION_OTHER_LABEL in constants.py).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.gui.constants import INSPECTION_ITEM_LABELS, INSPECTION_ITEMS


class InspectionStepMixin:
    def _init_inspection_vars(self) -> None:
        self.inspection_vars: dict[str, tk.BooleanVar] = {
            key: tk.BooleanVar(value=False) for key, _item, _time_frame in INSPECTION_ITEMS
        }
        # Other items are unbounded, so each one gets a generated id
        # ("other_1", "other_2", ...) rather than a single fixed key -
        # self.inspection_order (shared with the fixed items above) is the
        # single source of truth for both which are included and in what
        # sequence, same as before.
        self.inspection_other_items_by_id: dict[str, dict[str, tk.StringVar]] = {}
        self._inspection_other_counter = 0
        self.inspection_order: list[str] = []

        self._inspection_other_container: ttk.Frame | None = None
        self._inspection_other_item_frames: dict[str, ttk.Frame] = {}
        self._inspection_order_listbox: tk.Listbox | None = None

    def _inspection_item_text(self, key: str) -> str:
        if key in INSPECTION_ITEM_LABELS:
            return INSPECTION_ITEM_LABELS[key]
        entry = self.inspection_other_items_by_id.get(key)
        if entry is None:
            return "Other"
        description = entry["description_var"].get().strip()
        return f"Other: {description}" if description else "Other"

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

        ttk.Label(frame, text="Other items:").grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 2))
        row += 1

        self._inspection_other_container = ttk.Frame(frame)
        self._inspection_other_container.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        self._inspection_other_item_frames = {}
        for item_id in self.inspection_other_items_by_id:
            self._build_inspection_other_item_row(item_id)

        ttk.Button(frame, text="Add Other", command=self._add_inspection_other_item).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
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

    def _build_inspection_other_item_row(self, item_id: str) -> None:
        container = self._inspection_other_container
        if container is None or not container.winfo_exists():
            return
        entry_vars = self.inspection_other_items_by_id[item_id]

        row_frame = ttk.Frame(container)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text="Item of inspection:").grid(row=0, column=0, sticky="w")
        description_entry = ttk.Entry(row_frame, textvariable=entry_vars["description_var"], width=32)
        description_entry.grid(row=0, column=1, sticky="w", padx=(6, 0))
        description_entry.bind("<KeyRelease>", lambda event: self._refresh_inspection_order_listbox())
        ttk.Label(row_frame, text="Time frame:").grid(row=0, column=2, sticky="w", padx=(12, 0))
        time_frame_entry = ttk.Entry(row_frame, textvariable=entry_vars["time_frame_var"], width=22)
        time_frame_entry.grid(row=0, column=3, sticky="w", padx=(6, 0))
        ttk.Button(row_frame, text="Remove", command=lambda: self._remove_inspection_other_item(item_id)).grid(
            row=0, column=4, sticky="w", padx=(8, 0)
        )
        self._inspection_other_item_frames[item_id] = row_frame

    def _add_inspection_other_item(self) -> None:
        self._inspection_other_counter += 1
        item_id = f"other_{self._inspection_other_counter}"
        self.inspection_other_items_by_id[item_id] = {
            "description_var": tk.StringVar(),
            "time_frame_var": tk.StringVar(),
        }
        self._build_inspection_other_item_row(item_id)
        self.inspection_order.append(item_id)
        self._refresh_inspection_order_listbox()

    def _remove_inspection_other_item(self, item_id: str) -> None:
        frame = self._inspection_other_item_frames.pop(item_id, None)
        if frame is not None and frame.winfo_exists():
            frame.destroy()
        self.inspection_other_items_by_id.pop(item_id, None)
        if item_id in self.inspection_order:
            self.inspection_order.remove(item_id)
        self._refresh_inspection_order_listbox()

    def _on_inspection_toggle(self, key: str, selected: bool) -> None:
        if selected:
            if key not in self.inspection_order:
                self.inspection_order.append(key)
        else:
            if key in self.inspection_order:
                self.inspection_order.remove(key)
        self._refresh_inspection_order_listbox()

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
        for entry in self.inspection_other_items_by_id.values():
            if not entry["description_var"].get().strip():
                messagebox.showerror("Missing info", '"Item of inspection" is required for every Other item.')
                return False
            if not entry["time_frame_var"].get().strip():
                messagebox.showerror("Missing info", '"Time frame" is required for every Other item.')
                return False
        return True

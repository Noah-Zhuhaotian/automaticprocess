"""Project templates in the wizard (storage: app/core/template_store.py).

- Applying: the Create-mode step's "Template" dropdown pre-fills every step
  but General (and the PS1 date) from a saved template - optional for a
  single new job, required for "batch".
- Saving: "Save as template..." on Review & Create stores the current
  input (minus General/date) under a name.
- Managing: "Manage templates..." lists templates to rename, delete, or
  edit. Editing runs the wizard in an "edit_template" pseudo-mode: Edit
  template -> Scope -> ... -> MinuteDock -> Review, where the final button
  saves back to the template instead of creating anything.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app.core import template_store
from app.core.template_store import TemplateError

NO_TEMPLATE = "(none)"


class TemplateStepMixin:
    def _init_template_vars(self) -> None:
        self.template_choice_var = tk.StringVar(value=NO_TEMPLATE)
        # The template whose values are currently applied to the wizard, so
        # re-validating the Create-mode step doesn't re-apply it over edits.
        self._applied_template: str | None = None
        # Set while the wizard is in "edit_template" mode.
        self.editing_template_name: str | None = None
        self._template_combo: ttk.Combobox | None = None

    # ---------- template picker (on the Create-mode step) ----------
    def _template_choices(self) -> list[str]:
        return [NO_TEMPLATE, *template_store.list_templates()]

    def _refresh_template_combo(self) -> None:
        combo = self._template_combo
        if combo is not None and combo.winfo_exists():
            combo["values"] = self._template_choices()
        if self.template_choice_var.get() not in self._template_choices():
            self.template_choice_var.set(NO_TEMPLATE)

    def _apply_chosen_template(self) -> bool:
        """Called when the Create-mode step is validated. Applies the
        chosen template if it isn't already the applied one; choosing
        "(none)" after a template was applied clears what it filled in."""
        chosen = self.template_choice_var.get()
        if chosen == NO_TEMPLATE:
            if self._applied_template is not None:
                self._clear_document_fields()
                self._applied_template = None
            return True
        if chosen == self._applied_template:
            return True
        data = template_store.load_template(chosen)
        if data is None:
            messagebox.showerror("Template not found", f'The template "{chosen}" couldn\'t be read.')
            self._refresh_template_combo()
            return False
        self._apply_template_data(data)
        self._applied_template = chosen
        return True

    # ---------- Save as template (Review & Create) ----------
    def _save_as_template(self) -> None:
        name = simpledialog.askstring(
            "Save as template",
            "Template name - saves everything except General (job number, client, address) and the date:",
            parent=self,
        )
        if name is None:
            return
        try:
            name = template_store.clean_name(name)
        except TemplateError as exc:
            messagebox.showerror("Save as template", str(exc))
            return
        if template_store.exists(name) and not messagebox.askyesno(
            "Save as template", f'A template named "{name}" already exists. Replace it?'
        ):
            return
        template_store.save_template(name, self._collect_template_data())
        messagebox.showinfo("Save as template", f'Saved template "{name}".')

    # ---------- Manage templates dialog ----------
    def _open_manage_templates_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Manage templates")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(frame, width=40, height=10, exportselection=False)
        listbox.grid(row=0, column=0, rowspan=5, sticky="nsew")
        buttons = ttk.Frame(frame)
        buttons.grid(row=0, column=1, sticky="n", padx=(10, 0))

        def refresh(select: str | None = None) -> None:
            listbox.delete(0, "end")
            names = template_store.list_templates()
            for name in names:
                listbox.insert("end", name)
            if select in names:
                listbox.selection_set(names.index(select))
            self._refresh_template_combo()

        def selected() -> str | None:
            selection = listbox.curselection()
            if not selection:
                messagebox.showinfo("Manage templates", "Select a template first.", parent=dialog)
                return None
            return listbox.get(selection[0])

        def edit() -> None:
            name = selected()
            if name is None:
                return
            if not messagebox.askyesno(
                "Edit template",
                f'Edit the values of "{name}"?\n\nThe wizard switches to editing this template - '
                "anything entered for the current project so far is cleared.",
                parent=dialog,
            ):
                return
            dialog.destroy()
            self._start_template_edit(name)

        def rename() -> None:
            name = selected()
            if name is None:
                return
            new = simpledialog.askstring("Rename template", "New name:", initialvalue=name, parent=dialog)
            if new is None:
                return
            try:
                template_store.rename_template(name, new)
            except TemplateError as exc:
                messagebox.showerror("Rename template", str(exc), parent=dialog)
                return
            new = new.strip()
            if self._applied_template == name:
                self._applied_template = new
            if self.template_choice_var.get() == name:
                self.template_choice_var.set(new)
            refresh(select=new)

        def delete() -> None:
            name = selected()
            if name is None:
                return
            if not messagebox.askyesno("Delete template", f'Delete the template "{name}"?', parent=dialog):
                return
            template_store.delete_template(name)
            if self._applied_template == name:
                self._applied_template = None
            refresh()

        ttk.Button(buttons, text="Edit values...", command=edit).grid(row=0, column=0, sticky="we", pady=(0, 4))
        ttk.Button(buttons, text="Rename...", command=rename).grid(row=1, column=0, sticky="we", pady=(0, 4))
        ttk.Button(buttons, text="Delete", command=delete).grid(row=2, column=0, sticky="we", pady=(0, 12))
        ttk.Button(buttons, text="Close", command=dialog.destroy).grid(row=3, column=0, sticky="we")
        refresh()
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    # ---------- editing a template's values ----------
    def _start_template_edit(self, name: str) -> None:
        data = template_store.load_template(name)
        if data is None:
            messagebox.showerror("Edit template", f'The template "{name}" couldn\'t be read.')
            return
        self._clear_project_fields()
        self._apply_template_data(data)
        self.editing_template_name = name
        self._applied_template = None
        self.existing_minutedock_project = None
        self.existing_project_folder_var.set("")
        self.create_mode_var.set("edit_template")
        self.steps = self._build_step_list()
        self.current_step = 0
        self._show_step(0)

    def _build_template_edit_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                f'Editing the template "{self.editing_template_name}".\n\n'
                "Click Next to go through its Scope, PS1 Input, Inspection Schedule, Waivers, "
                "Specification, B2 Letter and MinuteDock settings, then save them on the last page. "
                "Nothing is created while editing a template."
            ),
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 16))
        ttk.Button(parent, text="Cancel editing", command=self._cancel_template_edit).grid(row=1, column=0, sticky="w")

    def _cancel_template_edit(self) -> None:
        self._reset_for_new_project()

    def _save_edited_template(self) -> None:
        name = self.editing_template_name
        template_store.save_template(name, self._collect_template_data())
        self._show_success_dialog("Template saved", f'Saved the template "{name}".')
        self._reset_for_new_project()

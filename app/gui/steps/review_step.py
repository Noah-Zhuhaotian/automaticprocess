"""Step: Review & Create - single Create button that builds the shared
replacements dict and generates everything for the current project:
project folders plus the Project register, PS1, LBP form, Calculation
Statement, Specifications, and B2 Letter documents.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from app.core import folder_creator, word_filler
from app.gui.constants import (
    B1_OPTIONS,
    B2_LETTER_MATERIALS,
    B2_LETTER_TEMPLATE,
    CALCULATION_STATEMENT_TEMPLATE,
    CHECKED,
    CM_ITEMS,
    INSPECTION_ITEM_LABELS,
    INSPECTION_OTHER_LABEL,
    LBP_TEMPLATE,
    PROJECT_REGISTER_TEMPLATE,
    PS1_INSPECTION_TABLE_INDEX,
    PS1_TEMPLATE,
    SCOPE_ITEMS,
    SPECIFICATION_SECTIONS,
    SPECIFICATION_TEMPLATE,
    UNCHECKED,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReviewStepMixin:
    # ---------- Step: Review & Create ----------
    def _build_review_step(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "Click Create to generate everything for this project.\n\n"
                "Currently implemented: project folders on the Engineer/Drafting/"
                "Admin drives.\n"
                "Coming once their templates/details are provided: the Project "
                "register and Consent Document files, PS1/B2 letter documents, "
                "and the timesheet website submission."
            ),
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        self.create_result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.create_result_var, wraplength=560, justify="left").grid(
            row=1, column=0, sticky="w", pady=(12, 0)
        )

    def _build_scope_lines(self) -> list[str]:
        # Plain text, no manual "- " prefix: the bullet glyph comes from a
        # real Word numbering definition, not a typed dash character.
        # {{scope}} is every selected item's individual bullet lines
        # flattened into one combined list - the exact same lines that
        # appear (per item) in the LBP form's description cells, just
        # gathered together here instead of split by item.
        self._sync_scope_descriptions()
        lines: list[str] = []
        for item in SCOPE_ITEMS:
            if self.scope_vars[item]["selected"].get():
                lines.extend(self._scope_description_lines(item))
        return lines

    def _build_lbp_description_bullets(self) -> dict[str, list[str]]:
        # LBP form's per-item description cell: each Enter-separated line
        # the user typed becomes its own real bullet point, one {{lbp_
        # <item>_description}} placeholder per selected Scope item. Only
        # selected items are included - unselected ones keep their token in
        # the plain replacements dict instead (see _build_replacements),
        # blanked to "" so their cell's paragraph survives, since an empty
        # bullet list here would delete the placeholder's own paragraph and
        # leave the table cell without one.
        self._sync_scope_descriptions()
        return {
            f"lbp_{item.lower()}_description": self._scope_description_lines(item)
            for item in SCOPE_ITEMS
            if self.scope_vars[item]["selected"].get()
        }

    def _build_inspection_replacements(self) -> dict[str, str]:
        # inspection_<key>_no is only for the 7 *fixed* items - the user's
        # chosen order (1-based position in self.inspection_order), the
        # No. column in PS1's Schedule of Inspections. Other items don't
        # go through {{token}} replacement at all - see
        # _build_inspection_table_data, which bakes their No./description/
        # time frame directly when building each new row.
        return {
            f"inspection_{key}_no": str(position)
            for position, key in enumerate(self.inspection_order, start=1)
            if key in INSPECTION_ITEM_LABELS
        }

    def _build_inspection_table_data(self):
        """Everything _on_create needs to drive PS1's Schedule of
        Inspections table, derived once from self.inspection_order (fixed
        item keys and inspection_other_items_by_id ids, interleaved in
        the user's chosen sequence):
        - fixed_keep_labels: which fixed items' rows survive (keep_table_rows)
        - fixed_row_order: those same fixed items' Item-of-inspection text,
          in order, for reordering them relative to each other
          (table_row_order) - Other items are excluded here since they
          don't exist as rows yet at that point.
        - dynamic_order: the *full* interleaved sequence (fixed items'
          Item-of-inspection text mixed with Other items' ids) that
          _insert_dynamic_table_rows walks to insert each Other row at the
          right spot among the now-correctly-ordered fixed rows.
        - dynamic_values: each Other id's own [No, description, time
          frame] cell values, already resolved - no {{token}}s involved.
        """
        fixed_keep_labels: set[str] = set()
        fixed_row_order: list[str] = []
        dynamic_order: list[str] = []
        dynamic_values: dict[str, list[str]] = {}

        for position, key in enumerate(self.inspection_order, start=1):
            if key in INSPECTION_ITEM_LABELS:
                label = INSPECTION_ITEM_LABELS[key]
                fixed_keep_labels.add(label)
                fixed_row_order.append(label)
                dynamic_order.append(label)
            else:
                entry = self.inspection_other_items_by_id[key]
                dynamic_order.append(key)
                dynamic_values[key] = [
                    str(position),
                    entry["description_var"].get().strip(),
                    entry["time_frame_var"].get().strip(),
                ]

        return fixed_keep_labels, fixed_row_order, dynamic_order, dynamic_values

    def _build_replacements(self) -> dict[str, str]:
        all_part = self.all_part_var.get()
        compliance_selected = self.compliance_var.get()
        alternative_selected = self.alternative_var.get()
        b1_selected = [option for option in B1_OPTIONS if self.b1_vars[option].get()]

        street = self.street_var.get().strip()
        replacements = {
            "job_number": self.job_number_var.get().strip(),
            "client_info": self.client_info_var.get().strip(),
            # "address" is the token name baked into the Project register/PS1
            # templates; it's filled with the street only (see HANDOFF).
            "address": street,
            "street": street,
            "suburb": self.suburb_var.get().strip(),
            "town": self.town_var.get().strip(),
            "role": self.role_var.get().strip(),
            "council_name": self.council_name_var.get().strip(),
            "description_of_work": self.description_of_work_text.strip(),
            # "legel_description" matches a typo baked into the PS1 template's placeholder token.
            "legel_description": self.legal_description_text.strip(),
            # "site_verfication" matches a typo baked into the PS1 template's placeholder token.
            "site_verfication": self.site_verification_text.strip(),
            "all_box": CHECKED if all_part == "All" else UNCHECKED,
            "part_box": CHECKED if all_part == "Part only" else UNCHECKED,
            # Compliance and Alternative are independent checkboxes now, not
            # mutually exclusive - both can be ticked in the output at once.
            "compliance_box": CHECKED if compliance_selected else UNCHECKED,
            "alternative_box": CHECKED if alternative_selected else UNCHECKED,
            "compliance_solution": "; ".join(b1_selected) if compliance_selected else "",
            "alternative_solution": self.alternative_solution_text.strip() if alternative_selected else "N/A",
            "date": self._format_selected_date(),
        }
        for item in CM_ITEMS:
            replacements[f"{item.lower()}_box"] = CHECKED if self.cm_vars[item].get() else UNCHECKED

        replacements.update(self._build_inspection_replacements())

        # LBP form's "restricted building work" table: one row per Scope
        # item, only filled in for items the user actually checked on the
        # General step.
        job_number = replacements["job_number"]
        role = replacements["role"]
        for item in SCOPE_ITEMS:
            key = item.lower()
            selected = self.scope_vars[item]["selected"].get()
            replacements[f"lbp_{key}_box"] = CHECKED if selected else UNCHECKED
            if selected:
                # lbp_{key}_description is deliberately not set here - it
                # goes through bullet_lists instead (see
                # _build_lbp_description_bullets).
                replacements[f"lbp_{key}_carried_by"] = role
                replacements[f"lbp_{key}_reference"] = f"Engsolution drawings #{job_number}"
            else:
                replacements[f"lbp_{key}_description"] = ""
                replacements[f"lbp_{key}_carried_by"] = ""
                replacements[f"lbp_{key}_reference"] = ""

        # LBP form's "Waivers and Modifications" section.
        waivers_required = self.waivers_required_var.get() == "Yes"
        replacements["lbp_waiver_yes_box"] = CHECKED if waivers_required else UNCHECKED
        replacements["lbp_waiver_no_box"] = UNCHECKED if waivers_required else CHECKED
        replacements["lbp_building_code_clause"] = (
            self.building_code_clause_var.get().strip() if waivers_required else ""
        )
        replacements["lbp_waiver_modification"] = self.waiver_modification_text.strip() if waivers_required else ""

        # Specification's numeric fields. Harmless to send even when the
        # owning section wasn't selected - remove_unselected_sections()
        # deletes those paragraphs before replacement runs, so an empty
        # value here never actually reaches the output document.
        replacements["capacity"] = self.capacity_var.get().strip()
        replacements["precast_strength"] = self.precast_strength_var.get().strip()
        replacements["foundation_plain_strength"] = self.foundation_plain_strength_var.get().strip()
        replacements["foundation_fibre_strength"] = self.foundation_fibre_strength_var.get().strip()
        replacements["metal_deck_topping_strength"] = self.metal_deck_topping_strength_var.get().strip()
        replacements["grout_strength"] = self.grout_strength_var.get().strip()

        return replacements

    def _on_create(self) -> None:
        try:
            created = folder_creator.create_project_folders(
                job_number=self.job_number_var.get(),
                street=self.street_var.get(),
                engineer_drive=self.settings.get("engineer_drive", ""),
                drafting_drive=self.settings.get("drafting_drive", ""),
                admin_drive=self.settings.get("admin_drive", ""),
            )
        except (ValueError, FileExistsError) as exc:
            messagebox.showerror("Cannot create", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create project folders")
            messagebox.showerror("Error", str(exc))
            return

        summary = "\n".join(f"{name}: {path}" for name, path in created.items())
        replacements = self._build_replacements()
        bullet_lists = {"scope": self._build_scope_lines()}
        bullet_lists.update(self._build_lbp_description_bullets())

        specification_sections = {title for title in SPECIFICATION_SECTIONS if self.specification_vars[title].get()}
        b2_letter_materials = {
            material for material in B2_LETTER_MATERIALS if self.b2_letter_material_vars[material].get()
        }
        fixed_keep_labels, fixed_row_order, dynamic_order, dynamic_values = self._build_inspection_table_data()

        # Dicts, not positional tuples - the PS1 entry alone needs 6 of
        # word_filler's optional table-editing parameters, all None for
        # every other document; .get() with a default reads far better
        # than a growing all-None tuple per document.
        documents = [
            {"template": PROJECT_REGISTER_TEMPLATE, "output": Path("Project register.docx")},
            {
                "template": PS1_TEMPLATE,
                "output": Path("06 Consent Document") / "PS1 Producer Statement.docx",
                "keep_table_rows": {PS1_INSPECTION_TABLE_INDEX: fixed_keep_labels},
                "keep_table_row_label_columns": {PS1_INSPECTION_TABLE_INDEX: 1},
                "table_row_order": {PS1_INSPECTION_TABLE_INDEX: fixed_row_order},
                "dynamic_table_row_templates": {PS1_INSPECTION_TABLE_INDEX: INSPECTION_OTHER_LABEL},
                "dynamic_table_row_order": {PS1_INSPECTION_TABLE_INDEX: dynamic_order},
                "dynamic_table_row_values": {PS1_INSPECTION_TABLE_INDEX: dynamic_values},
            },
            {"template": LBP_TEMPLATE, "output": Path("06 Consent Document") / "LBP form.docx"},
            {
                "template": CALCULATION_STATEMENT_TEMPLATE,
                "output": Path("06 Consent Document") / "Calculation Statement.docx",
            },
            {
                "template": SPECIFICATION_TEMPLATE,
                "output": Path("06 Consent Document") / "Specifications.docx",
                "keep_sections": specification_sections,
            },
            {
                "template": B2_LETTER_TEMPLATE,
                "output": Path("06 Consent Document") / "B2 Letter.docx",
                "keep_table_rows": {0: b2_letter_materials},
            },
        ]
        for doc in documents:
            template_path = doc["template"]
            relative_output = doc["output"]
            if not template_path.exists():
                logger.info("Template not found at %s, skipping", template_path)
                continue
            try:
                output_path = word_filler.fill_docx_template(
                    str(template_path),
                    str(created["engineer"] / relative_output),
                    replacements,
                    bullet_lists,
                    keep_sections=doc.get("keep_sections"),
                    keep_table_rows=doc.get("keep_table_rows"),
                    keep_table_row_label_columns=doc.get("keep_table_row_label_columns"),
                    table_row_order=doc.get("table_row_order"),
                    dynamic_table_row_templates=doc.get("dynamic_table_row_templates"),
                    dynamic_table_row_order=doc.get("dynamic_table_row_order"),
                    dynamic_table_row_values=doc.get("dynamic_table_row_values"),
                )
                summary += f"\n{relative_output}: {output_path}"
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to fill template %s", template_path)
                self.create_result_var.set(f"Created:\n{summary}")
                messagebox.showwarning(
                    "Partial success", f"Some items were created, but {relative_output} failed:\n{exc}"
                )
                return

        self.create_result_var.set(f"Created:\n{summary}")
        self._update_availability_status()
        self._show_success_dialog("Done", "Project created successfully.")
        self._reset_for_new_project()

    def _show_success_dialog(self, title: str, message: str) -> None:
        """Same modal, blocks-until-closed behavior as messagebox.showinfo,
        but with a green checkmark instead of the OS "info" icon -
        tkinter's messagebox only supports its fixed icon set ("info"/
        "warning"/"error"/"question"), so a custom Toplevel is the only
        way to get a checkmark in there. Falls back to the plain
        messagebox (its default icon) if building the custom dialog fails
        for any reason.
        """
        try:
            dialog = tk.Toplevel(self)
            dialog.title(title)
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()

            frame = ttk.Frame(dialog, padding=20)
            frame.pack(fill="both", expand=True)

            ttk.Label(frame, text="✔", font=("Segoe UI", 28), foreground="#107C10").grid(
                row=0, column=0, padx=(0, 16), sticky="n"
            )
            ttk.Label(frame, text=message, wraplength=360, justify="left").grid(row=0, column=1, sticky="w")

            ok_button = ttk.Button(frame, text="OK", command=dialog.destroy)
            ok_button.grid(row=1, column=0, columnspan=2, pady=(16, 0))
            ok_button.focus_set()

            dialog.bind("<Return>", lambda event: dialog.destroy())
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

            self.wait_window(dialog)
        except Exception:  # noqa: BLE001
            logger.exception("Custom success dialog failed, falling back to the default messagebox icon")
            messagebox.showinfo(title, message)

    def _reset_for_new_project(self) -> None:
        """Clear all per-project input and jump back to General, ready for
        the next project. Drive paths and the saved council list are app
        configuration, not project data, so they're left untouched.
        """
        self.job_number_var.set("")
        self.client_info_var.set("")
        self.street_var.set("")
        self.suburb_var.set("")
        self.town_var.set("")
        self.role_var.set("")
        for item in SCOPE_ITEMS:
            self.scope_vars[item]["selected"].set(False)
            self.scope_vars[item]["description"] = ""
        self.availability_var.set("")

        self.council_name_var.set("")
        self.description_of_work_text = ""
        self.legal_description_text = ""
        self.site_verification_text = ""
        self.all_part_var.set("")
        for item in CM_ITEMS:
            self.cm_vars[item].set(False)
        self.compliance_var.set(False)
        self.alternative_var.set(False)
        for option in B1_OPTIONS:
            self.b1_vars[option].set(False)
        self.alternative_solution_text = ""
        self.date_year_var.set("")
        self.date_month_var.set("")
        self.date_day_var.set("")

        for key in self.inspection_vars:
            self.inspection_vars[key].set(False)
        self.inspection_other_items_by_id = {}
        self._inspection_other_counter = 0
        self._inspection_other_item_frames = {}
        self.inspection_order = []

        self.waivers_required_var.set("")
        self.building_code_clause_var.set("")
        self.waiver_modification_text = ""

        for title in SPECIFICATION_SECTIONS:
            self.specification_vars[title].set(False)
        self.capacity_var.set("")
        self.precast_strength_var.set("")
        self.foundation_plain_strength_var.set("")
        self.foundation_fibre_strength_var.set("")
        self.metal_deck_topping_strength_var.set("")
        self.grout_strength_var.set("")

        for material in B2_LETTER_MATERIALS:
            self.b2_letter_material_vars[material].set(False)

        # Rebuild the step list: if this was the first run, Settings just
        # got filled in and saved during this very session, but self.steps
        # was only computed once at startup and still includes it. Without
        # this, General would keep showing as "2 of 7" (with Settings) for
        # the rest of the session instead of "1 of 6" like a fresh restart
        # (where _drives_configured() is already true) would show.
        self.steps = self._build_step_list()
        general_index = next(i for i, s in enumerate(self.steps) if s["title"] == "General")
        self.current_step = general_index
        self._show_step(general_index)

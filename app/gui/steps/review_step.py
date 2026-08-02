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
    LBP_TEMPLATE,
    PROJECT_REGISTER_TEMPLATE,
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
        self._sync_scope_descriptions()
        return [
            self.scope_vars[item]["description"].strip()
            for item in SCOPE_ITEMS
            if self.scope_vars[item]["selected"].get()
        ]

    def _build_replacements(self) -> dict[str, str]:
        all_part = self.all_part_var.get()
        compliance_alt = self.compliance_alt_var.get()
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
            "all_box": CHECKED if all_part == "All" else UNCHECKED,
            "part_box": CHECKED if all_part == "Part only" else UNCHECKED,
            "compliance_box": CHECKED if compliance_alt == "Compliance" else UNCHECKED,
            "alternative_box": CHECKED if compliance_alt == "Alternative" else UNCHECKED,
            "compliance_solution": "; ".join(b1_selected) if compliance_alt == "Compliance" else "",
            "alternative_solution": "N/A" if compliance_alt == "Compliance" else self.alternative_solution_text.strip(),
            "date": self._format_selected_date(),
        }
        for item in CM_ITEMS:
            replacements[f"{item.lower()}_box"] = CHECKED if self.cm_vars[item].get() else UNCHECKED

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
                replacements[f"lbp_{key}_description"] = self.scope_vars[item]["description"].strip()
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

        specification_sections = {title for title in SPECIFICATION_SECTIONS if self.specification_vars[title].get()}
        b2_letter_materials = {
            material for material in B2_LETTER_MATERIALS if self.b2_letter_material_vars[material].get()
        }
        documents = [
            (PROJECT_REGISTER_TEMPLATE, Path("Project register.docx"), None, None),
            (PS1_TEMPLATE, Path("06 Consent Document") / "PS1 Producer Statement.docx", None, None),
            (LBP_TEMPLATE, Path("06 Consent Document") / "LBP form.docx", None, None),
            (CALCULATION_STATEMENT_TEMPLATE, Path("06 Consent Document") / "Calculation Statement.docx", None, None),
            (
                SPECIFICATION_TEMPLATE,
                Path("06 Consent Document") / "Specifications.docx",
                specification_sections,
                None,
            ),
            (
                B2_LETTER_TEMPLATE,
                Path("06 Consent Document") / "B2 Letter.docx",
                None,
                {0: b2_letter_materials},
            ),
        ]
        for template_path, relative_output, keep_sections, keep_table_rows in documents:
            if not template_path.exists():
                logger.info("Template not found at %s, skipping", template_path)
                continue
            try:
                output_path = word_filler.fill_docx_template(
                    str(template_path),
                    str(created["engineer"] / relative_output),
                    replacements,
                    bullet_lists,
                    keep_sections=keep_sections,
                    keep_table_rows=keep_table_rows,
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
        self.all_part_var.set("")
        for item in CM_ITEMS:
            self.cm_vars[item].set(False)
        self.compliance_alt_var.set("")
        for option in B1_OPTIONS:
            self.b1_vars[option].set(False)
        self.alternative_solution_text = ""
        self.date_year_var.set("")
        self.date_month_var.set("")
        self.date_day_var.set("")

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

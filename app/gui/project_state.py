"""Every per-project wizard field in one place: clear them all, snapshot
them to a plain dict (saved per project by app/core/project_store.py on
Create), and restore them from that dict (when an existing project is
opened again in the "documents_only" Create mode).

Keeping clear/collect/apply side by side means a new wizard field only has
to be added here once to be reset between projects, saved, and reloaded.
Restoring sets the tk variables and the plain-text fields each step builds
its widgets from, so every step shows the loaded values when it's next
shown - no widget is touched here.
"""

from __future__ import annotations

import datetime
from typing import Any

import tkinter as tk

from app.gui.constants import (
    B1_OPTIONS,
    B2_LETTER_MATERIALS,
    CM_ITEMS,
    INSPECTION_ITEM_LABELS,
    SCOPE_ITEMS,
    SPECIFICATION_NUMERIC_FIELDS,
    SPECIFICATION_SECTIONS,
)

SPECIFICATION_VALUE_VARS = [var_name for fields in SPECIFICATION_NUMERIC_FIELDS.values() for var_name, _ in fields]


class ProjectStateMixin:
    def _clear_project_fields(self) -> None:
        """Blank every per-project field. Leaves app configuration (drives,
        token, council list) and the Create-mode choice alone."""
        self.job_number_var.set("")
        self.client_info_var.set("")
        self.street_var.set("")
        self.suburb_var.set("")
        self.town_var.set("")
        self.availability_var.set("")
        self._clear_document_fields()

    def _clear_document_fields(self) -> None:
        """Blank everything except General - i.e. everything a template
        holds (plus the PS1 date)."""
        self.role_var.set("")
        for item in SCOPE_ITEMS:
            self.scope_vars[item]["selected"].set(False)
            self.scope_vars[item]["description"] = ""

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
        for var_name in SPECIFICATION_VALUE_VARS:
            getattr(self, var_name).set("")
        for var in self.specification_field_enabled_vars.values():
            var.set(False)

        for material in B2_LETTER_MATERIALS:
            self.b2_letter_material_vars[material].set(False)

        self.minutedock_budget_enabled_var.set(False)
        self.minutedock_budget_amount_var.set("")

    def _collect_project_data(self) -> dict[str, Any]:
        self._sync_scope_descriptions()
        self._sync_ps1_text_fields()
        self._sync_waivers_text_fields()

        inspection_order = []
        for key in self.inspection_order:
            if key in INSPECTION_ITEM_LABELS:
                inspection_order.append({"key": key})
            else:
                entry = self.inspection_other_items_by_id[key]
                inspection_order.append(
                    {
                        "other": entry["description_var"].get().strip(),
                        "time_frame": entry["time_frame_var"].get().strip(),
                    }
                )

        return {
            "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "last_mode": self.create_mode_var.get(),
            "documents_generated": self.create_mode_var.get() != "folder_only",
            "general": {
                "job_number": self.job_number_var.get().strip(),
                "client_info": self.client_info_var.get().strip(),
                "street": self.street_var.get().strip(),
                "suburb": self.suburb_var.get().strip(),
                "town": self.town_var.get().strip(),
            },
            "scope": {
                "items": {
                    item: {
                        "selected": self.scope_vars[item]["selected"].get(),
                        "description": self.scope_vars[item]["description"],
                    }
                    for item in SCOPE_ITEMS
                },
                "role": self.role_var.get(),
            },
            "ps1": {
                "council_name": self.council_name_var.get(),
                "description_of_work": self.description_of_work_text,
                "legal_description": self.legal_description_text,
                "site_verification": self.site_verification_text,
                "all_part": self.all_part_var.get(),
                "cm": [item for item in CM_ITEMS if self.cm_vars[item].get()],
                "compliance": self.compliance_var.get(),
                "alternative": self.alternative_var.get(),
                "b1": [option for option in B1_OPTIONS if self.b1_vars[option].get()],
                "date": [self.date_year_var.get(), self.date_month_var.get(), self.date_day_var.get()],
            },
            "inspection": {"order": inspection_order},
            "waivers": {
                "required": self.waivers_required_var.get(),
                "building_code_clause": self.building_code_clause_var.get(),
                "waiver_modification": self.waiver_modification_text,
            },
            "specification": {
                "sections": [title for title in SPECIFICATION_SECTIONS if self.specification_vars[title].get()],
                "values": {var_name: getattr(self, var_name).get() for var_name in SPECIFICATION_VALUE_VARS},
                "ticked_fields": [
                    var_name for var_name, var in self.specification_field_enabled_vars.items() if var.get()
                ],
            },
            "b2_letter": {
                "materials": [m for m in B2_LETTER_MATERIALS if self.b2_letter_material_vars[m].get()],
            },
            "minutedock": {
                "budget_enabled": self.minutedock_budget_enabled_var.get(),
                "budget_amount": self.minutedock_budget_amount_var.get(),
                "project_id": (self.existing_minutedock_project or {}).get("id"),
            },
        }

    def _apply_project_data(self, data: dict[str, Any]) -> None:
        """Restore fields from a _collect_project_data() dict. Job number and
        Street are left as they are - in "documents_only" they come from the
        chosen folder's name, which is what the documents must match. Missing
        keys (e.g. a folder_only save has no document data) just stay blank,
        and values that no longer exist (a renamed option) are skipped."""
        if "general" in data:  # templates have no General section - leave it alone
            general = data["general"]
            self.client_info_var.set(general.get("client_info", ""))
            self.suburb_var.set(general.get("suburb", ""))
            self.town_var.set(general.get("town", ""))

        scope = data.get("scope", {})
        for item, saved in scope.get("items", {}).items():
            if item in self.scope_vars:
                self.scope_vars[item]["selected"].set(bool(saved.get("selected")))
                self.scope_vars[item]["description"] = saved.get("description", "")
        self.role_var.set(scope.get("role", ""))

        ps1 = data.get("ps1", {})
        self.council_name_var.set(ps1.get("council_name", ""))
        self.description_of_work_text = ps1.get("description_of_work", "")
        self.legal_description_text = ps1.get("legal_description", "")
        self.site_verification_text = ps1.get("site_verification", "")
        self.all_part_var.set(ps1.get("all_part", ""))
        for item in ps1.get("cm", []):
            if item in self.cm_vars:
                self.cm_vars[item].set(True)
        self.compliance_var.set(bool(ps1.get("compliance")))
        self.alternative_var.set(bool(ps1.get("alternative")))
        for option in ps1.get("b1", []):
            if option in self.b1_vars:
                self.b1_vars[option].set(True)
        if "date" in ps1:  # templates have no date - leave it alone
            year, month, day = (list(ps1["date"]) + ["", "", ""])[:3]
            self.date_year_var.set(year)
            self.date_month_var.set(month)
            self.date_day_var.set(day)

        for saved in data.get("inspection", {}).get("order", []):
            key = saved.get("key")
            if key is not None:
                if key in self.inspection_vars:
                    self.inspection_vars[key].set(True)
                    self.inspection_order.append(key)
                continue
            self._inspection_other_counter += 1
            item_id = f"other_{self._inspection_other_counter}"
            self.inspection_other_items_by_id[item_id] = {
                "description_var": tk.StringVar(value=saved.get("other", "")),
                "time_frame_var": tk.StringVar(value=saved.get("time_frame", "")),
            }
            self.inspection_order.append(item_id)

        waivers = data.get("waivers", {})
        self.waivers_required_var.set(waivers.get("required", ""))
        self.building_code_clause_var.set(waivers.get("building_code_clause", ""))
        self.waiver_modification_text = waivers.get("waiver_modification", "")

        specification = data.get("specification", {})
        for title in specification.get("sections", []):
            if title in self.specification_vars:
                self.specification_vars[title].set(True)
        for var_name, value in specification.get("values", {}).items():
            if var_name in SPECIFICATION_VALUE_VARS:
                getattr(self, var_name).set(value)
        for var_name in specification.get("ticked_fields", []):
            if var_name in self.specification_field_enabled_vars:
                self.specification_field_enabled_vars[var_name].set(True)

        for material in data.get("b2_letter", {}).get("materials", []):
            if material in self.b2_letter_material_vars:
                self.b2_letter_material_vars[material].set(True)

        minutedock = data.get("minutedock", {})
        self.minutedock_budget_enabled_var.set(bool(minutedock.get("budget_enabled")))
        self.minutedock_budget_amount_var.set(minutedock.get("budget_amount", ""))

    # ---------- templates (app/core/template_store.py) ----------
    def _collect_template_data(self) -> dict[str, Any]:
        """A project snapshot minus everything job-specific: General, the
        PS1 date, and which MinuteDock project it belonged to."""
        data = self._collect_project_data()
        for key in ("general", "saved_at", "last_mode", "documents_generated"):
            data.pop(key, None)
        data["ps1"].pop("date", None)
        data["minutedock"].pop("project_id", None)
        return data

    def _apply_template_data(self, data: dict[str, Any]) -> None:
        """Replace everything but General (and the PS1 date) with the
        template's values."""
        year, month, day = self.date_year_var.get(), self.date_month_var.get(), self.date_day_var.get()
        self._clear_document_fields()
        self.date_year_var.set(year)
        self.date_month_var.set(month)
        self.date_day_var.set(day)
        self._apply_project_data({k: v for k, v in data.items() if k != "general"})

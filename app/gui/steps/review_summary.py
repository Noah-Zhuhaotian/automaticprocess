"""The read-back summary shown on the Review & Create step: everything the
user entered or ticked, grouped by wizard step, so it can actually be
reviewed before clicking Create. Only steps in the current Create mode's
flow are listed (e.g. "folder_only" has no Scope/PS1/... sections).

Pure read-only formatting of the tk variables the step mixins already own -
no validation or side effects. Builds the summary as plain data
(_build_review_summary) so the Review step just renders it.
"""

from __future__ import annotations

from pathlib import Path

from app.core import folder_creator
from app.gui.constants import (
    ALTERNATIVE_SOLUTION_TEXT,
    B1_OPTIONS,
    B2_LETTER_MATERIALS,
    CHANGES_HEADING,
    CM_ITEMS,
    INSPECTION_ITEMS,
    SCOPE_ITEMS,
    SPECIFICATION_NUMERIC_FIELDS,
    SPECIFICATION_SECTIONS,
    SPECIFICATION_TICKABLE_FIELDS,
    UPDATED_SUFFIX,
)
from app.gui.steps.mode_step import CREATE_MODE_OPTIONS
from app.gui.steps.template_step import NO_TEMPLATE
from app.gui.steps.review_step import DOCUMENT_OUTPUTS, PREVIOUS_VERSIONS_FOLDER

# (section title, [(label, value), ...]) - a value may span several lines.
Summary = list[tuple[str, list[tuple[str, str]]]]

_NOT_SET = "(not set)"


def _text(value: str) -> str:
    value = value.strip()
    return value if value else _NOT_SET


class ReviewSummaryMixin:
    def _build_review_summary(self) -> Summary:
        """The summary shown on Review. When updating an existing project,
        a "Changes" section comes first and changed rows are marked."""
        sections = self._build_plain_summary()
        if not self.is_update_run or self._update_baseline is None:
            return sections
        changes = self._review_changes()
        changed_keys = {(section, label) for section, label, _old, _new in changes}
        marked: Summary = [
            (
                heading,
                [
                    (label + UPDATED_SUFFIX if (heading, label) in changed_keys else label, value)
                    for label, value in rows
                ],
            )
            for heading, rows in sections
        ]
        if changes:
            change_rows = []
            for section, label, old, new in changes:
                if "\n" in old or "\n" in new:
                    value = f"before:\n{old}\nnow:\n{new}"
                else:
                    value = f"{old}  \u2192  {new}"
                change_rows.append((f"{section} \u203a {label}", value))
        else:
            change_rows = [("No changes", "The documents will be regenerated with the same values.")]
        return [marked[0], (CHANGES_HEADING, change_rows), *marked[1:]]

    def _summary_values(self) -> dict[tuple[str, str], str]:
        """{(section, label): value} for every row except the "Create"
        section (which describes the run, not the project's data)."""
        values = {}
        for heading, rows in self._build_plain_summary()[1:]:
            for label, value in rows:
                if heading == "MinuteDock" and label == "Budget":
                    # Drop the "(changed - will be saved)" / "(unchanged)" note.
                    value = value.split("   (")[0]
                values[(heading, label)] = value
        return values

    def _review_changes(self) -> list[tuple[str, str, str, str]]:
        """(section, label, before, now) for every value that differs from
        when the project was opened, in summary order."""
        before = self._update_baseline or {}
        now = self._summary_values()
        changes = []
        for key in list(now) + [k for k in before if k not in now]:
            old, new = before.get(key, _NOT_SET), now.get(key, "(removed)")
            if old != new:
                changes.append((key[0], key[1], old, new))
        return changes

    def _build_plain_summary(self) -> Summary:
        titles = {step["title"] for step in self.steps}
        mode = self.create_mode_var.get()
        if mode == "batch":
            # The document steps aren't shown in batch mode, but every job
            # gets the template's values for them - list those too.
            titles |= {"Scope", "PS1 Input", "Inspection Schedule", "Waivers and Modifications",
                       "Specification", "B2 Letter", "MinuteDock"}
        sections: Summary = [self._summary_mode()]
        builders = [
            ("General", self._summary_general),
            ("Scope", self._summary_scope),
            ("PS1 Input", self._summary_ps1),
            ("Inspection Schedule", self._summary_inspection),
            ("Waivers and Modifications", self._summary_waivers),
            ("Specification", self._summary_specification),
            ("B2 Letter", self._summary_b2_letter),
            ("MinuteDock", self._summary_minutedock),
        ]
        for title, builder in builders:
            if title in titles:
                sections.append((title, builder()))
        return sections

    def _summary_mode(self) -> tuple[str, list[tuple[str, str]]]:
        mode = self.create_mode_var.get()
        if mode == "edit_template":
            return "Template", [
                ("Editing", self.editing_template_name or _NOT_SET),
                ("Not stored in templates", "General (job number, client, address) and the PS1 date"),
            ]
        mode_label = dict(CREATE_MODE_OPTIONS).get(mode, mode)
        rows = [("Mode", mode_label)]
        if mode == "batch":
            jobs = self._batch_values()
            rows.append(("Template", self._applied_template or _NOT_SET))
            rows.append(
                (
                    f"Jobs ({len(jobs)})",
                    "\n".join(
                        f"{row['job_number']} - {row['street']}, {row['suburb']}, {row['town']}   "
                        f"(client: {row['client_info']}{self._new_client_note(row['client_info'])})"
                        for row in jobs
                    ),
                )
            )
            rows.append(("Each job", "Folders on all three drives + all six documents + its MinuteDock project"))
            return "Create", rows
        if self.template_choice_var.get() != NO_TEMPLATE and self._applied_template:
            rows.append(("Started from template", self._applied_template))

        job_number = self.job_number_var.get().strip()
        street = self.street_var.get().strip()
        try:
            project_name = folder_creator.build_project_folder_name(job_number, street)
        except ValueError:
            project_name = _NOT_SET

        if mode == "documents_only":
            rows.append(("Existing folder", f"{self.settings.get('engineer_drive', '')}\\{project_name}"))
            engineer = Path(self.settings.get("engineer_drive", "")) / project_name
            if any((engineer / doc).exists() for doc in DOCUMENT_OUTPUTS):
                rows.append(
                    (
                        "Existing documents",
                        f'Will be moved to "{PREVIOUS_VERSIONS_FOLDER}\\<date time>" before regenerating',
                    )
                )
        else:
            rows.append(
                (
                    "Folders to create",
                    "\n".join(
                        f"{self.settings.get(key, '')}\\{project_name}"
                        for key in ("engineer_drive", "drafting_drive", "admin_drive")
                    ),
                )
            )
        if mode != "folder_only":
            rows.append(
                (
                    "Documents",
                    "Project register, PS1 Producer Statement, LBP form, Calculation Statement, "
                    "Specifications, B2 Letter",
                )
            )
        return "Create", rows

    def _new_client_note(self, client: str) -> str:
        """" - new, added to MinuteDock on Create" for a client that isn't an
        existing MinuteDock contact (when the contact list is known)."""
        known = self._minutedock_contact_names
        if client and known is not None and client.casefold() not in {n.casefold() for n in known}:
            return " - new, added to MinuteDock on Create"
        return ""

    def _summary_general(self) -> list[tuple[str, str]]:
        client = self.client_info_var.get().strip()
        if client and client.casefold() in {name.casefold() for name in self._new_contact_names}:
            client += "   (new - will be added to MinuteDock contacts)"
        return [
            ("Job number", _text(self.job_number_var.get())),
            ("Client info", _text(client)),
            ("Street", _text(self.street_var.get())),
            ("Suburb", _text(self.suburb_var.get())),
            ("Town", _text(self.town_var.get())),
        ]

    def _summary_scope(self) -> list[tuple[str, str]]:
        rows = []
        for item in SCOPE_ITEMS:
            if self.scope_vars[item]["selected"].get():
                lines = self._scope_description_lines(item)
                rows.append((item, "\n".join(f"- {line}" for line in lines) or _NOT_SET))
        if not rows:
            rows.append(("Scope items", "(none ticked)"))
        rows.append(("Role", _text(self.role_var.get())))
        return rows

    def _summary_ps1(self) -> list[tuple[str, str]]:
        cm = [item for item in CM_ITEMS if self.cm_vars[item].get()]
        basis = []
        if self.compliance_var.get():
            methods = [option for option in B1_OPTIONS if self.b1_vars[option].get()]
            basis.append("Compliance" + (f" ({', '.join(methods)})" if methods else ""))
        if self.alternative_var.get():
            basis.append(f"Alternative - {ALTERNATIVE_SOLUTION_TEXT}")
        return [
            ("Council", _text(self.council_name_var.get())),
            ("Description of work", _text(self.description_of_work_text)),
            ("Legal description", _text(self.legal_description_text)),
            ("Site verification", _text(self.site_verification_text)),
            ("Scope of statement", _text(self.all_part_var.get())),
            ("Construction monitoring", ", ".join(cm) if cm else "(none ticked)"),
            ("Basis of statement", "\n".join(basis) if basis else _NOT_SET),
            (
                "Date",
                "(not stored in templates)"
                if self.create_mode_var.get() == "edit_template"
                else _text(self._format_selected_date()),
            ),
        ]

    def _summary_inspection(self) -> list[tuple[str, str]]:
        time_frames = {key: time_frame for key, _item, time_frame in INSPECTION_ITEMS}
        lines = []
        for position, key in enumerate(self.inspection_order, start=1):
            if key in time_frames:
                text, time_frame = self._inspection_item_text(key), time_frames[key]
            else:
                entry = self.inspection_other_items_by_id[key]
                text = f"Other: {entry['description_var'].get().strip()}"
                time_frame = entry["time_frame_var"].get().strip()
            lines.append(f"{position}. {text}  -  {time_frame}")
        return [("Inspections (in order)", "\n".join(lines) if lines else "(none)")]

    def _summary_waivers(self) -> list[tuple[str, str]]:
        required = self.waivers_required_var.get()
        rows = [("Waivers/modifications required", _text(required))]
        if required == "Yes":
            rows.append(("Building Code Clause", _text(self.building_code_clause_var.get())))
            rows.append(("Waiver/modification", _text(self.waiver_modification_text)))
        return rows

    def _summary_specification(self) -> list[tuple[str, str]]:
        rows = []
        for title in SPECIFICATION_SECTIONS:
            if not self.specification_vars[title].get():
                continue
            values = []
            for var_name, label in SPECIFICATION_NUMERIC_FIELDS.get(title, []):
                if var_name in SPECIFICATION_TICKABLE_FIELDS and not self.specification_field_enabled_vars[var_name].get():
                    continue
                # Labels already carry the unit, e.g. "Precast elements (MPa)".
                value = getattr(self, var_name).get().strip()
                values.append(f"{label.rstrip(':')}: {value or _NOT_SET}")
            rows.append((title, "\n".join(values) if values else "included"))
        if not rows:
            rows.append(("Sections", "(none ticked)"))
        return rows

    def _summary_b2_letter(self) -> list[tuple[str, str]]:
        materials = [m for m in B2_LETTER_MATERIALS if self.b2_letter_material_vars[m].get()]
        return [("Materials", "\n".join(materials) if materials else "(none ticked)")]

    def _summary_minutedock(self) -> list[tuple[str, str]]:
        budget = self._minutedock_budget_dollars()
        budget_text = f"${budget} billable, in total" if budget else "No budget"
        existing = self.existing_minutedock_project
        mode = self.create_mode_var.get()
        if mode in ("batch", "edit_template"):
            rows = [("Budget", budget_text)]
            if mode == "batch":
                rows.insert(0, ("Project", "One new project per job (Short Code = its job number)"))
            rows.insert(len(rows) - 1, ("Rates", "Use contact rates"))
            return rows
        if existing is not None:
            changed = self._minutedock_budget_changed(budget)
            rows = [
                ("Project", f"Existing project {self.job_number_var.get().strip()} (no new project is created)"),
                ("Client", _text(existing.get("contact_name", ""))),
                ("Budget", budget_text + ("   (changed - will be saved)" if changed else "   (unchanged)")),
            ]
            if existing.get("other_budget") and budget is None:
                rows[-1] = ("Budget", f"Kept as is in MinuteDock ({existing['other_budget']})")
        else:
            rows = [
                ("Project", f"New: {_text(self.street_var.get())}  (Short Code {_text(self.job_number_var.get())})"),
                ("Client", _text(self.client_info_var.get())),
                ("Budget", budget_text),
            ]
        rows.insert(2, ("Rates", "Use contact rates"))
        return rows

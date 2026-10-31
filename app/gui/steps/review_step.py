"""Step: Review & Create - single Create button that builds the shared
replacements dict and generates everything for the current project:
project folders plus the Project register, PS1, LBP form, Calculation
Statement, Specifications, and B2 Letter documents, then syncs the
matching Contact/Project to MinuteDock. What actually runs depends on the
Create-mode choice from mode_step.py ("folder_only" skips documents but
still creates the MinuteDock Project; "documents_only" skips folder
creation, fills into an already-existing folder, and reuses that job's
existing MinuteDock Project instead of creating another; "both" is this
full sequence).
"""

from __future__ import annotations

import datetime
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from app.core import folder_creator, project_store, web_filler, word_filler
from app.core.minutedock_client import MinuteDockError
from app.gui.constants import (
    ALTERNATIVE_SOLUTION_TEXT,
    B1_OPTIONS,
    B2_LETTER_MATERIALS,
    B2_LETTER_TEMPLATE,
    CALCULATION_STATEMENT_TEMPLATE,
    CHANGES_HEADING,
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
    UPDATED_SUFFIX,
)
from app.gui.steps.template_step import NO_TEMPLATE
from app.utils.logger import get_logger

logger = get_logger(__name__)

PREVIOUS_VERSIONS_FOLDER = "_previous versions"

# Where each generated document lands, relative to the Engineer project
# folder (used as the "output" paths in _on_create's documents list).
DOCUMENT_OUTPUTS = [
    Path("Project register.docx"),
    Path("06 Consent Document") / "PS1 Producer Statement.docx",
    Path("06 Consent Document") / "LBP form.docx",
    Path("06 Consent Document") / "Calculation Statement.docx",
    Path("06 Consent Document") / "Specifications.docx",
    Path("06 Consent Document") / "B2 Letter.docx",
]


def _archive_existing_documents(engineer_folder: Path, outputs: list[Path]) -> Path | None:
    """Before regenerating an opened project's documents, move any of them
    that already exist into "_previous versions/<timestamp>/" (keeping their
    relative paths), since word_filler never overwrites. Returns that folder,
    or None if there was nothing to move. All-or-nothing: if one can't be
    moved (e.g. open in Word), the ones already moved are put back and the
    OSError is re-raised, so the project is never left half-archived."""
    existing = [relative for relative in outputs if (engineer_folder / relative).exists()]
    if not existing:
        return None

    archive = engineer_folder / PREVIOUS_VERSIONS_FOLDER / datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    moved: list[Path] = []
    try:
        for relative in existing:
            target = archive / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            (engineer_folder / relative).rename(target)
            moved.append(relative)
    except OSError:
        for relative in moved:
            (archive / relative).rename(engineer_folder / relative)
        raise
    logger.info("Moved %d previous document(s) to %s", len(moved), archive)
    return archive


class ReviewStepMixin:
    # ---------- Step: Review & Create ----------
    def _build_review_step(self, parent: ttk.Frame) -> None:
        mode = self.create_mode_var.get()
        documents = (
            "the Project register, PS1, LBP form, Calculation Statement, Specifications, and B2 Letter documents"
        )
        if mode == "folder_only":
            text = (
                "Click Create to make the project folders on the Engineer/Drafting/Admin drives "
                "and the job's MinuteDock project (plus the client's Contact, if it's new). "
                "No documents are generated."
            )
        elif mode == "documents_only":
            if self.existing_minutedock_project is not None:
                minutedock = (
                    "No new MinuteDock project is created - this job's existing one gets its "
                    "budget updated only if you changed it."
                )
            else:
                minutedock = "This job has no MinuteDock project yet, so one is created."
            folder = self.existing_project_folder_var.get().strip()
            engineer = Path(self.settings.get("engineer_drive", "")) / folder
            has_documents = any((engineer / doc).exists() for doc in DOCUMENT_OUTPUTS)
            regenerate = (
                f' Its current documents will be moved to "{PREVIOUS_VERSIONS_FOLDER}" first (nothing is deleted).'
                if has_documents
                else ""
            )
            if self.is_update_run:
                text = (
                    f'Click Update to regenerate {documents} of "{folder}" with your changes '
                    f'(listed under "Changes" below).{regenerate} {minutedock}'
                )
            else:
                text = f'Click Create to generate {documents} into the existing folder "{folder}".{regenerate} {minutedock}'
        elif mode == "batch":
            count = len(self._batch_values())
            text = (
                f"Click Create all to create {count} job(s) from the template \"{self._applied_template}\" - "
                f"for each: folders on the Engineer/Drafting/Admin drives, {documents}, and its MinuteDock "
                "project. A job that fails doesn't stop the others; the results are listed at the end."
            )
        elif mode == "edit_template":
            text = (
                f'Click Save template to save these settings back to the template "{self.editing_template_name}". '
                "Nothing is created."
            )
        else:
            text = (
                "Click Create to generate everything for this project: folders on the "
                f"Engineer/Drafting/Admin drives, {documents}, and the matching MinuteDock "
                "Contact/Project."
            )
        # A dedicated frame so the row/column weights below (letting the
        # summary fill the window) don't leak into other steps, which reuse
        # the same content_frame with their own layout.
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text=text, wraplength=700, justify="left").grid(row=0, column=0, columnspan=2, sticky="w")
        self._build_review_summary_view(frame, row=1)

        if mode in ("both", "documents_only"):
            ttk.Button(frame, text="Save these settings as a template...", command=self._save_as_template).grid(
                row=2, column=0, sticky="w", pady=(8, 0)
            )

        self.create_result_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.create_result_var, wraplength=700, justify="left").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

    def _build_review_summary_view(self, frame: ttk.Frame, row: int) -> None:
        """Everything entered so far, grouped by step, in a scrollable
        read-only text box - use < Back to change anything."""
        text = tk.Text(frame, wrap="word", height=18, relief="solid", borderwidth=1, padx=8, pady=6)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=row, column=0, sticky="nsew", pady=(10, 0))
        scrollbar.grid(row=row, column=1, sticky="ns", pady=(10, 0))

        text.tag_configure("heading", font=("Segoe UI", 10, "bold"), spacing1=12, spacing3=2)
        text.tag_configure("label", font=("Segoe UI", 9, "bold"), lmargin1=12)
        text.tag_configure("value", font=("Segoe UI", 9), lmargin1=12, lmargin2=12)
        # Updated values (update runs only) stand out in orange.
        text.tag_configure("updated", foreground="#C55A11")

        for heading, rows in self._build_review_summary():
            in_changes = heading == CHANGES_HEADING
            text.insert("end", heading + "\n", ("heading", "updated") if in_changes else "heading")
            for label, value in rows:
                highlight = in_changes or label.endswith(UPDATED_SUFFIX)
                text.insert("end", f"{label}: ", ("label", "updated") if highlight else "label")
                if "\n" in value:
                    value = "\n" + "\n".join(f"    {line}" for line in value.split("\n"))
                text.insert("end", value + "\n", ("value", "updated") if highlight else "value")
        text.configure(state="disabled")

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
            "alternative_solution": ALTERNATIVE_SOLUTION_TEXT if alternative_selected else "N/A",
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
        # CONCRETE - GENERAL's strengths: only ticked ones get a value; the
        # lines of unticked ones are deleted (see _on_create's
        # remove_paragraphs_with_tokens), so they never need one.
        replacements.update(self._specification_strength_paragraphs()[0])
        replacements["grout_strength"] = self.grout_strength_var.get().strip()

        return replacements

    def _on_create(self) -> None:
        """Gathers everything the worker needs from tkinter variables (must
        happen here, on the main thread - tkinter itself isn't thread-safe)
        into plain-data `job` dicts, then hands the actual folder/document/
        MinuteDock work to a background thread so the window stays
        responsive instead of freezing for the whole operation. See
        _run_create_job/_run_batch_jobs/_on_create_done for the rest.
        """
        mode = self.create_mode_var.get()
        if mode == "edit_template":
            self._save_edited_template()
            return
        if mode != "folder_only":
            self._remember_inspection_other_items()

        self._create_result_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        if mode == "batch":
            jobs = self._build_batch_jobs()
            self._set_busy(True)
            threading.Thread(target=self._run_batch_jobs, args=(jobs,), daemon=True).start()
        else:
            job = self._build_job()
            self._set_busy(True)
            threading.Thread(target=self._run_create_job, args=(job,), daemon=True).start()
        self.after(100, self._poll_create_result)

    def _build_job(self) -> dict[str, Any]:
        """One job's plain-data description, from the wizard's current tk
        variables (main thread only)."""
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
            {"template": PROJECT_REGISTER_TEMPLATE, "output": DOCUMENT_OUTPUTS[0]},
            {
                "template": PS1_TEMPLATE,
                "output": DOCUMENT_OUTPUTS[1],
                "keep_table_rows": {PS1_INSPECTION_TABLE_INDEX: fixed_keep_labels},
                "keep_table_row_label_columns": {PS1_INSPECTION_TABLE_INDEX: 1},
                "table_row_order": {PS1_INSPECTION_TABLE_INDEX: fixed_row_order},
                "dynamic_table_row_templates": {PS1_INSPECTION_TABLE_INDEX: INSPECTION_OTHER_LABEL},
                "dynamic_table_row_order": {PS1_INSPECTION_TABLE_INDEX: dynamic_order},
                "dynamic_table_row_values": {PS1_INSPECTION_TABLE_INDEX: dynamic_values},
            },
            {"template": LBP_TEMPLATE, "output": DOCUMENT_OUTPUTS[2]},
            {
                "template": CALCULATION_STATEMENT_TEMPLATE,
                "output": DOCUMENT_OUTPUTS[3],
            },
            {
                "template": SPECIFICATION_TEMPLATE,
                "output": DOCUMENT_OUTPUTS[4],
                "keep_sections": specification_sections,
                "remove_paragraphs_with_tokens": self._specification_strength_paragraphs()[1],
            },
            {
                "template": B2_LETTER_TEMPLATE,
                "output": DOCUMENT_OUTPUTS[5],
                "keep_table_rows": {0: b2_letter_materials},
            },
        ]

        # MinuteDock sync is a required part of Create - Settings validation
        # guarantees a token is present by the time this step is reachable.
        minutedock_args = {
            "access_token": self.settings.get("minutedock_access_token", "").strip(),
            "client_name": replacements["client_info"],
            # MinuteDock's Project Name is the street only; the job
            # number goes in its own Short Code field below, not smashed
            # together into one string (see minutedock_client.py).
            "project_name": replacements["street"],
            "project_short_code": replacements["job_number"],
            # Always billable - see minutedock_step.py for why this isn't a
            # user-facing toggle.
            "billable": True,
            # No rate is sent - projects always "Use contact rates".
            "budget_dollars": self._minutedock_budget_dollars(),
        }

        job = {
            "mode": self.create_mode_var.get(),
            "job_number": self.job_number_var.get(),
            "street": self.street_var.get(),
            "engineer_drive": self.settings.get("engineer_drive", ""),
            "drafting_drive": self.settings.get("drafting_drive", ""),
            "admin_drive": self.settings.get("admin_drive", ""),
            "replacements": replacements,
            "bullet_lists": bullet_lists,
            "documents": documents,
            "minutedock": minutedock_args,
            "existing_minutedock_project": self.existing_minutedock_project,
            "minutedock_budget_changed": self._minutedock_budget_changed(minutedock_args["budget_dollars"]),
        }
        return job

    def _minutedock_budget_changed(self, budget_dollars: str | None) -> bool:
        """Whether the MinuteDock step's budget differs from the existing
        Project's (documents_only), compared as money ("500" == "500.00").
        A budget kind this app doesn't set (e.g. hours, set in MinuteDock's
        web UI) counts as unchanged while "Set a budget" stays unticked, so
        it's left alone; ticking it replaces that budget. Always False with
        no existing Project."""
        existing = self.existing_minutedock_project
        if existing is None:
            return False
        if budget_dollars is None and existing.get("other_budget"):
            return False

        def normalize(value: str | None) -> str | None:
            if value is None or not str(value).strip():
                return None
            try:
                return f"{float(value):.2f}"
            except ValueError:
                return str(value).strip()

        return normalize(budget_dollars) != normalize(existing["budget"])

    def _poll_create_result(self) -> None:
        """Runs entirely on the main thread (self.after only ever
        reschedules itself from here, never from the worker thread) -
        calling self.after() directly from _run_create_job's own thread
        raises "RuntimeError: main thread is not in main loop" on this
        Python version, confirmed by actually running it, not assumed.
        queue.Queue is the thread-safe hand-off instead: the worker only
        ever calls queue.put(), never touches tkinter itself.
        """
        try:
            outcome = self._create_result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_create_result)
            return
        if outcome["kind"] == "progress":
            self._set_progress_text(outcome["text"])
            self.after(100, self._poll_create_result)
            return
        self._on_create_done(outcome)

    def _run_create_job(self, job: dict[str, Any]) -> None:
        """Worker thread for a single job: run it and hand its outcome to
        the main thread (see _poll_create_result)."""
        self._create_result_queue.put(self._execute_job(job))

    def _execute_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Runs off the main thread - must never touch tkinter widgets,
        variables, or any tkinter method (including self.after - see
        _poll_create_result) directly; it only returns the job's outcome
        dict ({"kind": "success" | "partial" | "cannot_create" | "error",
        ...}), which the caller queues. folder_creator/word_filler/web_filler are
        plain file-IO/network functions with no tkinter dependency, so
        they're safe to run here unlike the code that gathered `job`.

        job["mode"] (see mode_step.py) branches this into three shapes:
        "documents_only" skips folder creation (the folder must already
        exist - create_project_folders would raise on it); "folder_only"
        creates folders then returns immediately, skipping documents and
        MinuteDock; "both" (the default/original behavior) does all three
        stages, unchanged.
        """
        mode = job["mode"]

        if mode == "documents_only":
            # The folder was picked on the Create-mode step precisely
            # because it already exists - create_project_folders() would
            # raise FileExistsError on it, so build the path directly
            # instead of calling it.
            project_name = folder_creator.build_project_folder_name(job["job_number"], job["street"])
            engineer_path = Path(job["engineer_drive"]) / project_name
            if not engineer_path.is_dir():
                message = f"The selected project folder no longer exists:\n{engineer_path}"
                logger.warning("Cannot fill documents: %s", message)
                return {"kind": "cannot_create", "message": message}
            created = {"engineer": engineer_path}
            summary = f"Using existing folder: {engineer_path}"
        else:
            try:
                created = folder_creator.create_project_folders(
                    job_number=job["job_number"],
                    street=job["street"],
                    engineer_drive=job["engineer_drive"],
                    drafting_drive=job["drafting_drive"],
                    admin_drive=job["admin_drive"],
                )
            except (ValueError, FileExistsError) as exc:
                logger.warning("Cannot create project folders: %s", exc)
                return {"kind": "cannot_create", "message": str(exc)}
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to create project folders")
                return {"kind": "error", "message": str(exc)}
            summary = "\n".join(f"{name}: {path}" for name, path in created.items())

        if mode != "folder_only":
            summary, failure = self._fill_documents(job, created, summary)
            if failure is not None:
                return failure

        return self._sync_job_to_minutedock(job, summary)

    def _fill_documents(
        self, job: dict[str, Any], created: dict[str, Path], summary: str
    ) -> tuple[str, dict[str, Any] | None]:
        """Worker-thread stage: fill every Word template into the Engineer
        folder. Returns (extended summary, None), or (summary, failure
        outcome) if the documents couldn't all be made."""
        replacements = job["replacements"]
        bullet_lists = job["bullet_lists"]

        try:
            archive = _archive_existing_documents(created["engineer"], [doc["output"] for doc in job["documents"]])
        except OSError as exc:
            logger.exception("Failed to move previous documents aside")
            return summary, (
                {
                    "kind": "error",
                    "message": f"Couldn't move the existing documents aside before regenerating them:\n{exc}\n\n"
                    "Is one of them open in Word? Close it and try again.",
                }
            )
        if archive is not None:
            summary += f"\nPrevious documents moved to: {archive}"

        for doc in job["documents"]:
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
                    remove_paragraphs_with_tokens=doc.get("remove_paragraphs_with_tokens"),
                )
                summary += f"\n{relative_output}: {output_path}"
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to fill template %s", template_path)
                return summary, {
                    "kind": "partial",
                    "summary": summary,
                    "message": f"Some items were created, but {relative_output} failed:\n{exc}",
                }
        return summary, None

    def _sync_job_to_minutedock(self, job: dict[str, Any], summary: str) -> dict[str, Any]:
        """Worker-thread final stage, returning the job's outcome:
        - documents_only with the job's Project already in MinuteDock: no
          new Project - save the budget back only if it changed.
        - otherwise (folder_only, both, or documents_only with no Project
          yet): find-or-create the Contact (a newly-added client name gets
          created here) and the Project.
        """
        existing = job["existing_minutedock_project"]
        done_label = "Documents were created" if job["mode"] == "documents_only" else (
            "Folders were created" if job["mode"] == "folder_only" else "Folders and documents were created"
        )
        try:
            if existing is not None:
                if job["minutedock_budget_changed"]:
                    budget = job["minutedock"]["budget_dollars"]
                    web_filler.update_project_budget(
                        job["minutedock"]["access_token"],
                        project_id=existing["id"],
                        project_name=existing["name"],
                        contact_id=existing["contact_id"],
                        budget_dollars=budget,
                    )
                    summary += (
                        f"\nMinuteDock: existing project {job['job_number']} budget "
                        + (f"set to ${budget} in total" if budget else "removed")
                    )
                else:
                    summary += f"\nMinuteDock: existing project {job['job_number']} unchanged"
            else:
                result = web_filler.sync_to_minutedock(**job["minutedock"])
                summary += (
                    f"\nMinuteDock: contact '{result['contact']['name']}', "
                    f"project '{result['project']['name']}'"
                )
        except MinuteDockError as exc:
            logger.exception("Failed to sync to MinuteDock")
            return {
                "kind": "partial",
                "summary": summary,
                "message": f"{done_label}, but MinuteDock sync failed:\n{exc}",
            }

        return {"kind": "success", "summary": summary}

    def _on_create_done(self, outcome: dict[str, Any]) -> None:
        """Runs back on the main thread (scheduled via self.after from
        _run_create_job) - the only place in this create flow allowed to
        touch tkinter widgets again once the background thread starts."""
        self._set_busy(False)
        kind = outcome["kind"]

        if kind == "batch":
            self._on_batch_done(outcome["results"])
            return
        if kind == "cannot_create":
            messagebox.showerror("Cannot create", outcome["message"])
            return
        if kind == "error":
            messagebox.showerror("Error", outcome["message"])
            return
        # The project's folder exists from here on (success or partial), so
        # remember everything entered for it - it can be opened again later.
        self._save_project_data()

        if kind == "partial":
            self.create_result_var.set(f"Created:\n{outcome['summary']}")
            messagebox.showwarning("Partial success", outcome["message"])
            return

        self.create_result_var.set(f"Created:\n{outcome['summary']}")
        self._update_availability_status()
        self._show_success_dialog(
            "Done", "Project updated successfully." if self.is_update_run else "Project created successfully."
        )
        self._reset_for_new_project()

    def _save_project_data(self) -> None:
        """Save this project's wizard input (app/core/project_store.py). A
        failure here is logged and shown, but never undoes or blocks the
        Create itself - the folders/documents already exist either way."""
        try:
            project_store.save_project(self.job_number_var.get().strip(), self._collect_project_data())
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save project data")
            messagebox.showwarning(
                "Couldn't save project data",
                "The project was created, but its input couldn't be saved for opening again later:\n"
                f"{exc}",
            )

    def _set_busy(self, busy: bool) -> None:
        self.next_button.configure(state="disabled" if busy else "normal")
        self.back_button.configure(state="disabled" if busy else ("normal" if self.current_step > 0 else "disabled"))
        if busy:
            self._show_progress_dialog()
        else:
            self._hide_progress_dialog()

    def _show_progress_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Please wait")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # no closing while the work is running

        frame = ttk.Frame(dialog, padding=24)
        frame.pack(fill="both", expand=True)
        self._progress_text_var = tk.StringVar(
            value="Updating project, please wait..." if self.is_update_run else "Creating project, please wait..."
        )
        ttk.Label(frame, textvariable=self._progress_text_var).pack(pady=(0, 12))
        progress = ttk.Progressbar(frame, mode="indeterminate", length=260)
        progress.pack()
        progress.start(12)

        self.update_idletasks()
        x = self.winfo_rootx() + max((self.winfo_width() - 320) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - 120) // 2, 0)
        dialog.geometry(f"+{x}+{y}")

        dialog.grab_set()
        self._progress_dialog = dialog

    def _set_progress_text(self, text: str) -> None:
        var = getattr(self, "_progress_text_var", None)
        if var is not None:
            var.set(text)

    def _hide_progress_dialog(self) -> None:
        dialog = getattr(self, "_progress_dialog", None)
        if dialog is not None and dialog.winfo_exists():
            dialog.destroy()
        self._progress_dialog = None

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
        """Clear all per-project input and jump back to Create mode, ready
        for the next project. Drive paths and the saved council list are app
        configuration, not project data, so they're left untouched.
        """
        self._clear_project_fields()

        # Create mode is itself per-project data - back to the default
        # ("both") so the next project starts from the same choice everyone
        # else sees, rather than silently inheriting whatever this one used.
        self.create_mode_var.set("both")
        self.existing_project_folder_var.set("")
        self.existing_minutedock_project = None
        self._loaded_project_folder = None
        self._clear_update_state()
        self.template_choice_var.set(NO_TEMPLATE)
        self._applied_template = None
        self.editing_template_name = None
        self.batch_rows = []
        # A client added this run now exists in MinuteDock - re-fetch the
        # Contact list next time General is shown so it appears there.
        self._new_contact_names = []
        self._minutedock_contact_names = None
        self.contact_status_var.set("")

        # Rebuild the step list: if this was the first run, Settings just
        # got filled in and saved during this very session, but self.steps
        # was only computed once at startup and still includes it. Without
        # this, "Create mode" would keep showing as "2 of 10" (with
        # Settings) for the rest of the session instead of "1 of 9" like a
        # fresh restart (where _settings_configured() is already true)
        # would show. The create_mode_var reset above must happen first,
        # since _build_step_list() reads it.
        self.steps = self._build_step_list()
        mode_index = next(i for i, s in enumerate(self.steps) if s["title"] == "Create mode")
        self.current_step = mode_index
        self._show_step(mode_index)

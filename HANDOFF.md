# Handoff: automaticprocess

Read this first. It's the current state of the project for whoever picks it
up next (human or agent): what the app does, how the code is organised,
the conventions and traps that have actually bitten, and what's open.
For user-facing behaviour see [USER_GUIDE.md](USER_GUIDE.md); for a
developer overview see [README.md](README.md). The long chronological
history of earlier sessions was retired from this file - it's in git
(`git show 6d3a93d:HANDOFF.md`).

## 1. The project in one minute

- Windows desktop app, **Python 3.13 + tkinter**, deps: `python-docx`,
  `requests`, `pyinstaller` (build only). Run with `python main.py`.
- Packaged as an installer: PyInstaller onedir → Inno Setup
  `AutomaticProcess-Setup.exe` (`build_scripts/`, see its README), published
  as a GitHub release by GitHub Actions (`.github/workflows/release.yml`,
  started by pushing tag `v<version>`; see build_scripts/README). Never
  publish from the dev PC. Users upgrade with the
  in-app "Check for updates" button (section 6a). Version lives only in
  `app/version.py`; bump it for every release.
- Built for one engineering office (Christchurch, NZ) by one user, who
  communicates in **Chinese** but wants **all code, comments and UI text
  in English**. Reply to them in Chinese.
- A wizard collects a job's details and then: creates project folders on 3
  drives, fills 4 Word templates + 1 Excel workbook (QA / Safety in Design),
  copies 1 fixed PDF (Calculation Statement),
  and creates the job in **MinuteDock**
  (timesheet SaaS, REST API).
- Repo: https://github.com/Noah-Zhuhaotian/automaticprocess (`main`).
  Commit/push only when the user asks; they decide when to package.

## 2. Features (current)

**Settings** (first run / header button): Engineer, Drafting, Admin drive
paths (all required, must be distinct - `_save_settings` rejects
duplicates) + MinuteDock Personal Access Token (required).

**Create mode** (first project step) - `self.create_mode_var`:

| value | label | steps after Create mode | Create does |
|---|---|---|---|
| `folder_only` | Create project folders only | General, MinuteDock, Review | folders + MinuteDock Contact/Project |
| `documents_only` | Open an existing project (fill or regenerate its documents) | General, Scope, PS1 Input, Inspection Schedule, Waivers and Modifications, Specification, B2 Letter, MinuteDock, Review | documents into the chosen existing folder; old documents moved to `_previous versions/<timestamp>/`; reuses the job's MinuteDock Project (budget written back only if changed). If the project's documents were generated before (`saved["documents_generated"]`) it's an **update run** (`is_update_run`): "Review & Update", button "Update", and a "Changes" section | 
| `both` (default) | Create folders and documents together (normal) | same as documents_only | folders + documents + MinuteDock |
| `batch` | Create several jobs from a template | Jobs, Review | one `both` job per table row, all from a template; failures don't stop the batch. The Jobs step also has the PS1 date for all jobs (defaults to today) and "Add new client..." (new clients created in MinuteDock on Create) |
| `edit_template` | (internal, from Manage templates) | Edit template, Scope … MinuteDock, Review & Save | saves the template; creates nothing |

Other behaviour worth knowing:
- **Job numbers are unique**: blocked if any `"{job} - {anything}"` folder
  exists on any of the 3 drives (folders not in that format are ignored),
  or any MinuteDock Project (active *or* archived) has that Short Code.
- **General** = Job number, Client info (MinuteDock Contact picker: pick
  existing / "Add new contact..." - created at Create time), Street, Suburb,
  Town. Suburb/Town are read-only dropdowns of user-maintained lists
  (settings `suburb_names`/`town_names`), managed like the council list:
  Add/Edit (`general_step`, `PLACE_LISTS`); the batch Jobs table uses the
  same lists and has Add buttons. In `documents_only`, Job number/Street are locked (they're the
  folder name) and Client is locked if the job's MinuteDock Project exists.
- **Addresses in documents**: `{{address}}` = "street, suburb, town" (PS1
  "AT:" + Schedule 2's report title, and the Specifications cover); B2
  Letter/LBP use `{{street}}`/`{{suburb}}`/`{{town}}` separately.
- **PS1 date** defaults to today when the PS1 step is first shown and is
  required (not in `edit_template` - templates don't store it); it also
  fills the Specifications cover date.
- **Scope** step = 6 scope items (tick + multi-line description → bullet
  points) + Role.
- **PS1 Input**: council and Description of work (persisted lists
  `council_names`/`description_of_work_names`, Add/Edit via ps1_step's
  `_add_list_name`/`_edit_list_name`), Legal description (two values +
  format: built-in Lot/DP or an Other format = two labels from
  `legal_description_formats`, Add/Edit; `_legal_description()` builds
  "Lot 12 DP 34567"), Site verification (free text), All/Part,
  CM1-5, Compliance (B1/VM1, B1/VM2, B1/AS1) and/or Alternative (fixed text
  `ALTERNATIVE_SOLUTION_TEXT`, read-only), date.
- **Inspection Schedule**: 7 fixed items + unlimited "Other" rows whose
  Item box is a dropdown of previously used Others (settings
  `inspection_other_items`, saved on Create); order via Move Up/Down.
- **Specification**: 7 sections; CONCRETE - GENERAL strengths (Precast,
  Foundations Plain, Foundations Fibre, Metal deck, Others) each have a
  tickbox - unticked lines are removed from the document; numeric-only
  fields; grout is a dropdown.
- **MinuteDock** step: rates fixed to "Use contact rates"; optional "Set a
  budget" = $ Billable, in total, numbers only. Every Project billable=True.
- **Review & Create**: full read-back summary of everything entered
  (`review_summary.py`), "Save these settings as a template..." button
  (both/documents_only). In an update run, `mode_step` snapshots the
  summary rows (`_summary_values()`) right after the project is loaded;
  Review then diffs against it (`_review_changes()`), prepends a "Changes"
  section and marks changed rows with `UPDATED_SUFFIX` (rendered orange).
  New creations (incl. first-time documents for a folder-only project)
  keep "Create".
- **Saved projects**: every successful/partial Create saves all wizard input
  to `<data_dir>\projects\<job>.json`; "Open an existing
  project" lists empty project folders + folders with a save, and reloads it.
- **Templates**: `<data_dir>\templates\<name>.json` =
  everything except General and the PS1 date. Apply on Create mode ("Start
  from template"), save from Review, manage (Edit values / Rename / Delete).
- All user data (`user_settings.json`, `projects/`, `templates/`, `logs/`)
  is under `%APPDATA%\AutomaticProcess`. The installer only writes Program
  Files, so updates/uninstalls never delete it (requirement from the user).
- **Shared data folder** (Settings, optional, e.g. on the NAS): then
  `data_dir()` (settings.py) is that folder, so `projects/` and
  `templates/` live there, and the dropdown lists (`SHARED_LIST_KEYS`) are
  written to its `shared_settings.json` by `save_settings` and re-read by
  `refresh_shared_lists` on every `_show_step` (and at startup). Drives,
  token and logs stay per-PC. Switching folders copies the old location's
  projects/templates (never overwriting) and merges the lists
  (`app/core/shared_data.py`). No locking: concurrent edits of one project
  are last-write-wins.

## 3. Code map

```
app/core/            (no tkinter - safe to call from the Create worker thread)
  folder_creator.py   build_project_folder_name / parse_project_folder_name,
                      find_job_number_conflicts, list_available_project_folders,
                      create_project_folders (3 drives + 6 ENGINEER_SUBFOLDERS)
  word_filler.py      fill_docx_template(...) - the Word engine (section 5)
  excel_filler.py     fill_xlsx_template(...) - fixed cells, openpyxl (section 5)
  minutedock_client.py thin API wrapper: list_contacts, list_projects,
                      find_project_by_short_code (active then archived),
                      find_or_create_contact/project, update_project (PUT),
                      budget_fields, BUDGET_TYPE_BILLABLE/BUDGET_FREQUENCY_TOTAL
  web_filler.py       sync_to_minutedock (find-or-create Contact then Project),
                      update_project_budget
  project_store.py    save_project / load_project / saved_job_numbers
  template_store.py   list/load/save/rename/delete templates
  shared_data.py      switching to a shared data folder: copy saves, merge lists
  updater.py          check_for_update / download_installer / launch_installer
app/version.py        __version__
app/config/settings.py  DEFAULT_SETTINGS, load_settings/save_settings
app/gui/
  main_window.py      MainWindow = all step mixins + tk.Tk; _init_vars,
                      _build_step_list (mode-dependent), _show_step (header),
                      _go_back/_go_next (last step → _on_create),
                      _build_scroll_area (see below)
  update_check.py     UpdateCheckMixin: header "Check for updates" button
  constants.py        SCOPE_ITEMS, B1_OPTIONS, INSPECTION_ITEMS,
                      SPECIFICATION_* tables, template paths, fixed texts
  project_state.py    ProjectStateMixin: _clear_project_fields /
                      _clear_document_fields / _collect_project_data /
                      _apply_project_data / _collect_template_data /
                      _apply_template_data  ← single source of truth for
                      "every per-project field"
  steps/              one mixin per step: _init_<x>_vars, _build_<x>_step,
                      _validate_<x>_step (+ helpers)
    settings_step, mode_step (+ existing-project & MinuteDock lookup),
    template_step (picker, save-as, manage dialog, edit_template),
    batch_step (Jobs table, batch build/run/results), general_step
    (contact picker, uniqueness), scope_step, ps1_step, inspection_step,
    waivers_step, specification_step, b2_letter_step, minutedock_step,
    review_step (review page, _on_create, worker, archive, reset),
    review_summary (read-back summary)
```

**Adding a wizard field** - do all of: tk var in the step's
`_init_*_vars`; widget in `_build_*_step` (build from the var, so revisiting
a step shows current values); validation; `project_state.py` clear + collect
+ apply (otherwise reset/reopen/templates silently drop it); replacement in
`review_step._build_replacements`; a line in `review_summary.py`.

**Adding a step**: new mixin in `steps/`, add to `MainWindow` bases and
`_init_vars`, add to `_build_step_list` (and `_document_steps()` if it's a
document step - that also puts it into template editing), and a summary
builder.

**Window layout**: the Back/Next bar is packed `side="bottom"` *before* the
content so it stays visible in a small window. Steps build into
`self.content_frame`, which lives inside a Canvas (`_scroll_canvas`) that
scrolls when the step doesn't fit; scrollbars show only when needed. The
frame is stretched to at least the visible area (grid `minsize` on its
holder `_scroll_body`), so `pack(fill="both", expand=True)` still fills the
window (Jobs table, Review summary). The page-level `<MouseWheel>` is
`bind_all`: it leaves the wheel to a Text/Listbox that can scroll, scrolls
an inner Canvas that can scroll (batch Jobs), and ignores Comboboxes.

## 4. Create flow (threading)

`_go_next` on the last step → `review_step._on_create` (main thread):
- `edit_template` → `_save_edited_template`, done.
- otherwise gathers plain-data job dict(s) (`_build_job`, or
  `_build_batch_jobs` which loads each table row into the General vars and
  calls `_build_job`), shows the modal progress dialog, starts a daemon
  thread (`_run_create_job` / `_run_batch_jobs`), and polls a
  `queue.Queue` with `self.after(100, _poll_create_result)`.
- Worker: `_execute_job(job)` → folders (or existing folder for
  documents_only) → `_fill_documents` (archives old docs first) →
  `_sync_job_to_minutedock`; each stage *returns* an outcome dict
  `{"kind": success|partial|cannot_create|error, ...}`. Batch also puts
  `{"kind": "progress"}` messages and finally `{"kind": "batch", "results"}`.
- Main thread `_on_create_done`: messageboxes, `_save_project_data`
  (success/partial), reset to Create mode (`_reset_for_new_project`) on
  success. Batch: `_on_batch_done` lists OK/PARTIAL/FAILED; FAILED (nothing
  created) rows stay in the Jobs table for retry.

**Rule: the worker thread must never touch tkinter** - not widgets, not
`StringVar`s, not `self.after` (on Python 3.13 `self.after` from a thread
raises `RuntimeError: main thread is not in main loop`). Only
`queue.put`. Gather everything on the main thread first.

## 5. Word filling (`word_filler.py`) - how and why

`fill_docx_template(template, output, replacements, bullet_lists=None,
keep_sections, keep_table_rows, keep_table_row_label_columns,
table_row_order, dynamic_table_row_templates/_order/_values,
remove_paragraphs_with_tokens)`. Order: structural cuts first (sections →
paragraphs-by-token → dynamic-row prototype capture → keep rows → reorder
rows → insert dynamic rows), then token replacement, checkboxes, bullets.
Cutting first means tokens inside removed content never need values.

Hard-won rules:
- **Replace tokens surgically per run** (`_replace_in_paragraph`), never
  collapse a paragraph into one run - that smeared one run's formatting
  (e.g. a highlight) over the whole paragraph. Tokens typed by hand in Word
  can straddle runs; `_ensure_run_boundary`/`_split_run` split safely.
- **Checkboxes are real Word content controls** (`<w:sdt>` + `<w14:checkbox>`
  tagged `<w:tag w:val="name">`), toggled by tag. Don't hand-author checkbox
  XML; copy an existing `sdt` from a template and add a tag.
- **Bullets are real numbering** (reuses the template's `-` bullet
  abstractNum, copies the placeholder's `rPr` and paragraph shading). An
  empty bullet list deletes the placeholder paragraph - never do that inside
  a table cell (cells must keep a `<w:p>`); send "" via replacements instead.
- Row matching happens *before* replacement, so a row/cell matched by text
  must contain the literal token text (e.g. `INSPECTION_OTHER_LABEL =
  "{{inspection_other_description}}"`).
- "User picks the order" needs the physical row order verified in the
  output .docx, not just the numbers.
- Template typos are baked into token names: `{{legel_description}}`,
  `{{site_verfication}}` - keep them.
- **Template surgery workflow**: inspect raw XML/runs with python-docx first,
  run the migration on a copy, diff all paragraph texts + tables against
  the original, then apply to the real file (git has the original). Ask the
  user to close the template in Word (PermissionError otherwise).
- `fill_docx_template` never overwrites an output - regeneration therefore
  moves old documents aside first (`_archive_existing_documents`,
  all-or-nothing with rollback).

**Excel** (`excel_filler.fill_xlsx_template`, the QA / Safety in Design
workbook): no tokens - values go into fixed cells (`QA_*`/`SID_*` in
constants.py), a documents-list entry with `xlsx_cells` goes to
excel_filler instead of word_filler. Cell styles and the sheets' drop-down
data validations survive openpyxl. Excel doesn't re-fit a fixed row height,
so a multi-line value grows its row (`_fit_row_height`). Dates are written
as real dates with a number format (`dd/mm/yy`) and left-aligned. Also never
overwrites; it's in `DOCUMENT_OUTPUTS`, so regeneration archives it too.
Checked by reading the cells back and in real Excel (displayed text +
`CopyPicture` screenshot via COM).

## 6. MinuteDock

Docs: https://developers.minutedock.com (OpenAPI). Base
`https://minutedock.com/api/v1`, `Authorization: Bearer <token>`. Bodies are
nested under the resource name (`{"project": {...}}`).
- Project: `name` = street, `short_code` = job number (the unique key; GET
  /projects can't filter by it, so we fetch and match locally),
  `contact_id`, `billable: true`, no `default_rate_dollars` (null → falls
  back to contact rate = "Use contact rates").
- Budget: `budget_type` "hours"|"billable" (null = not tracked),
  `budget_frequency` "total"|"weekly"|"monthly"|"quarterly"|"yearly",
  `budget_target` **number**. The app only sets billable/total.
- `PUT /projects/{id}` requires `name` and `contact_id` in every update
  (we resend the Project's own values). Verified by the user on the live
  account: the nested body updates the budget, and null budget fields
  clear it.
- Real error bodies can be `{"status":"error","message":...}` rather than
  the documented `{"error":...}` - `_request` checks both.
- Listing calls from the UI thread use a 10s timeout (`LIST_TIMEOUT`).
- Contact/Project lists are fetched unpaginated (default page 500) - fine
  for one small firm; add pagination if that ever stops being true.
- Unchecking "billable" in MinuteDock blocks time entries - that's why it's
  not a user option.

## 6a. Self-update (GitHub releases)

- `updater.check_for_update` reads
  `api.github.com/repos/Noah-Zhuhaotian/automaticprocess/releases/latest`
  (public repo, no token). It's an update only if the tag (`v1.2.3`) is
  newer than `__version__` **and** the release has an asset named exactly
  `AutomaticProcess-Setup.exe` (`v1.0.0` only has a zip, so it's never
  offered).
- Download goes to `%TEMP%\AutomaticProcess-update\`, checked against the
  asset's size and GitHub's `digest` (`sha256:...`).
- Install: `os.startfile(setup, arguments="/SILENT /SUPPRESSMSGBOXES
  /NORESTART /CLOSEAPPLICATIONS")` (ShellExecute, so UAC works), then the
  app `destroy()`s itself. `installer.iss` has `CloseApplications=force` and
  a `WizardSilent` `[Run]` entry with `runasoriginaluser` that reopens the
  app - as the signed-in user, so `%APPDATA%` is theirs even when an admin
  typed credentials into UAC. A cancelled UAC prompt usually happens after
  the app has closed (Inno's loader elevates itself); the user just reopens it.
- Running from source (`not sys.frozen`) only reports the new version.
- `installer.iss` refuses to compile without `/DMyAppVersion` so the
  installer and `app/version.py` can't drift; the release workflow passes
  it, and fails if the pushed tag isn't `v` + `__version__`.
- Machines still on 1.0.0 have no button - they need one manual install.

## 7. Testing - how changes have been verified

There's no test suite (`tests/` is empty). Every feature was verified with
throwaway headless scripts that drive the real `MainWindow`. Conventions
that matter (each one was learned from a real failure):

- **Never touch the user's real data.** Simplest: patch
  `app.config.settings.get_settings_path` to a temp file (then the real
  load/save_settings and `data_dir()` all stay in temp). Otherwise patch the
  *importing* module's names: `app.gui.main_window.load_settings`, plus
  `app.gui.steps.inspection_step.save_settings`,
  `app.gui.steps.general_step.save_settings` (Suburb/Town lists),
  `app.gui.steps.ps1_step.save_settings` (Council/Description lists, legal formats),
  `app.gui.steps.settings_step.save_settings` if a test reaches them,
  `project_store.projects_dir` and `template_store.templates_dir` → temp
  dirs. (A test once called the real `_save_settings` and corrupted the
  user's `admin_drive`; another wrote real project folders to their D:
  drive.) Assert `app.settings["engineer_drive"]` is your temp dir before
  any Create.
- Stub MinuteDock at `minutedock_client._request` (or the list/find
  functions) - never hit the real account except read-only, and say so.
- Suppress `messagebox.showerror/showwarning/showinfo/askyesno`,
  `simpledialog.askstring`, and `app._show_success_dialog` - real modals
  block a headless run forever.
- Drive Create the way the app does: `app._go_next()` / `_on_create()`, then
  loop `app.update()` until the Create button is re-enabled; don't read the
  result queue yourself (races the app's own poller). `_show_step` the
  Review step first (it creates `create_result_var`).
- **One `MainWindow` per Python process for anything that runs Create.**
  Chaining several in one process causes Tcl/GC flakiness (`Variable.__del__
  ... main thread is not in main loop`, hangs) that isn't an app bug.
- Read back the generated `.docx` (python-docx) and check the actual
  text/rows, not just the replacements dict.
- Real-window screenshot (PIL `ImageGrab` of the window bbox) is the cheap
  way to check layout. Don't simulate mouse/keyboard input.
- **This environment's bash heredocs mangle backslashes** (`"\\n"` became a
  real newline twice). For Python edit scripts containing `\`, write a .py
  file in the scratchpad with the Write tool and run it, or use Edit.
- Use raw strings / `pathlib` for Windows paths in tests (`"\admin"` silently
  became `\x07dmin` - BEL).
- `rm` on a `$VAR` path is blocked by a safety check; use `"${VAR:?}"`.

## 8. Open items / next steps

Done by the user after `7ec22ed` (no longer open): live MinuteDock budget
update/clear verified; real click-through of all the new features;
Specifications.docx `Foundations:` now uses a space like the other strength
lines (already in `7ec22ed`); the old duplicate-job-number test folders on
the D: drive were cleaned up.

1. **Releases**: `v1.0.1` (first with the updater) was published by hand
   via the GitHub API; from `v1.0.2` on, the release workflow does it.
   Office PCs on 1.0.0 need one manual install. Release notes (tag
   message) are shown as plain text in the update prompt - no Markdown
   (`**` shows literally). The real end-to-end upgrade (download → UAC →
   silent install → app reopens) is untested until a 1.0.1 install
   upgrades to 1.0.2.
2. Shared data folder is in (section 2) but untested on the real NAS /
   two real PCs; there's no locking (last write wins).
3. No automated tests - the scripts described in section 7 would be a good
   base for a pytest suite.
4. Ideas mentioned but not requested: managing saved Inspection "Other"
   items (rename/delete); a "description" text for the concrete "Others"
   strength line.

## 9. Recent history (newest first)

Shared data folder (two people were generating on separate PCs with
separate saves). Verified headless with temp "appdata" + temp "NAS":
switch copies/keeps files, list merge (case-insensitive), refresh picks up
another PC's list change, list add writes the shared file, fresh
load_settings reads it, error paths, Settings dialog screenshot.

PS1 Legal description: free text -> Lot/DP (or an Other two-label format)
+ two values. Saves store the built text plus `legal_format`,
`legal_other_format`, `legal_values`; older saves' "Lot X DP Y" text is
split back into values on reopen (other old text must be re-entered).
Verified headless (preview, validation, Add/Edit, save/clear/reload,
legacy parse, screenshot).

Calculation Statement is now a fixed PDF template (exported from the old
.docx with Word; it had no tokens), copied as-is via a `copy_only`
documents entry. The old `.docx` output is in `LEGACY_DOCUMENT_OUTPUTS`.

Specifications cover `{{street}}` -> `{{address}}` (template-only, diffed).
PS1 date defaults to today + is required (a blank date had left the
Specifications cover date and the PS1 "dated" empty). Checked by exporting
the generated PS1/Specifications to PDF with Word and looking at the pages.

PS1 template: Schedule 1's `{{scope}}` bullet list is now followed by 3
empty paragraphs with the placeholder's grey shading (copies of the
`{{scope}}` paragraph's pPr, no runs), then the original plain empty line
and Schedule 2 - template-only change, diffed against the original and
checked in a Word-exported PDF.

PS1 address ("AT:" + Schedule 2) now "street, suburb, town" (was street
only); Suburb/Town and PS1's Description of work became council-style
lists (Add/Edit, no Delete - the user doesn't want one);
`description_of_work_text` became `description_of_work_var` (saved JSON key
unchanged). Verified headless: PS1 read back, list add/edit/duplicate
(save_settings stubbed), save/reload round trip, General + PS1 + batch
Jobs screenshots.

Project register dropped (template deleted). The QA / SiD workbook is now
generated in its place - the Engineer project folder root - instead of
`06 Consent Document`. Old outputs at the previous paths
(`LEGACY_DOCUMENT_OUTPUTS` in review_step) are still archived on
regeneration.

Specification: Foundations Plain/Fibre made mutually exclusive
(`SPECIFICATION_EXCLUSIVE_FIELDS`); ticking one unticks/clears the other.
Older saves/templates with both ticked are caught by the Specification
step's and the batch Jobs step's validation. Released as `v1.0.4`.

`v1.0.3`: installer sets `ChangesAssociations=yes` so Explorer refreshes
shortcut icons after an upgrade (1.0.2 installs kept showing the cached old
icon until `ie4uinit.exe -show` / Explorer restart). Release workflow skips
docs-only releases (see build_scripts/README).

Releases moved to GitHub Actions (`.github/workflows/release.yml`;
`release.ps1` removed); the user guide PDF is now a script
(`build_scripts/make_user_guide_pdf.py`).

New app icon drawn by `build_scripts/make_icon.py` (replaces the old
photo-based one; `resources/automation.png` removed). Also set as the
window/dialog title-bar icon (`APP_ICON`, bundled by the spec).

QA / Safety in Design Excel workbook added as the 7th document
(`excel_filler.py`, openpyxl added to requirements). Verified with a
headless "both" Create (temp drives, MinuteDock stubbed) + reading the
cells back + real Excel showing `07/03/26`. Shipped in `v1.0.2`.

Self-update (section 6a): "Check for updates" button, `app/version.py`
(1.0.1), installer version passed in. Verified: version
compare, real GitHub check (read-only), real download + digest check,
headless GUI flows (no update / offline / from source / declined /
install / UAC cancelled) with the network and installer stubbed, local
PyInstaller + ISCC build (Setup.exe FileVersion 1.0.1) and the packaged
exe starting. Not yet: a real silent upgrade.

Back/Next pinned to the bottom of the window and the step content made
scrollable (`main_window._build_scroll_area`); verified headless at
760x420 across every step.

`9d6d37b`: batch Jobs step gets the PS1 date and "Add new client...";
reopening a project whose documents were generated is an update run
("Review & Update", "Update", "Changes" section).

`7ec22ed` (one large commit): Create modes;
MinuteDock Contact picker; job-number uniqueness (folders + MinuteDock,
incl. archived); Scope step; PS1 B1/VM2 + fixed Alternative text;
remembered Inspection Others; Specification strength tickboxes + Others;
MinuteDock budget (no rates); review summary; saved projects + reopen +
regenerate; templates + batch creation; doc refresh.

Earlier commits (see `git log`): `6d3a93d` duplicate-drive-path check +
logging (root cause of a real "already exists" bug: admin_drive equal to
engineer_drive); `6bac1ab` MinuteDock made mandatory, billable toggle
removed; `09cfacc` Project name = street / short code = job number;
`b004dbf` MinuteDock sync + installer; `e097e68` threaded Create; and the
original wizard/Word-filling work back to `4c27d83`.

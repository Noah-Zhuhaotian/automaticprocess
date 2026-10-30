# automaticprocess

A Windows desktop app (tkinter; packaged as a Windows installer via
PyInstaller + Inno Setup) that automates repetitive project setup for an
engineering office. A step-by-step wizard collects a project's info once,
then **Create**:

1. Builds the project folder structure on three NAS drives (Engineer /
   Drafting / Admin), named `"{job number} - {street}"`
2. Fills six Word templates (Project register, PS1 Producer Statement, LBP
   form, Calculation Statement, Specifications, B2 Letter) - real Word
   checkboxes, genuine bulleted lists, user-selected sections/table rows
3. Creates the matching Contact and Project in
   [MinuteDock](https://minutedock.com) via its REST API

The wizard has four **Create modes** (folders only / open an existing
project / folders + documents / batch from a template), every Create saves
its input so the project can be reopened and regenerated, and reusable
**templates** pre-fill everything except the per-job General fields.

Non-technical usage instructions live in [USER_GUIDE.md](USER_GUIDE.md).
**New to the codebase? Read [HANDOFF.md](HANDOFF.md) first** - it covers
architecture, conventions, gotchas and open items.

## Wizard

Settings (first run only) → **Create mode** → then, depending on the mode:

| Mode (`create_mode_var`) | Steps after Create mode | Create does |
|---|---|---|
| `folder_only` | General → MinuteDock → Review | folders + MinuteDock Project |
| `documents_only` ("Open an existing project") | General → Scope → PS1 Input → Inspection Schedule → Waivers → Specification → B2 Letter → MinuteDock → Review | documents into the existing folder (old ones moved to `_previous versions/`); reuses the job's MinuteDock Project |
| `both` (default) | same as above | folders + documents + MinuteDock |
| `batch` | Jobs (table of per-job General fields) → Review | one `both` job per row, template-filled |
| `edit_template` (internal) | Edit template → Scope … MinuteDock → Review & Save | saves the template, creates nothing |

Review & Create shows a full summary of everything entered.

## Project structure

```
app/
├── main.py                    # entry point
├── config/settings.py         # %APPDATA%\AutomaticProcess\user_settings.json
├── utils/logger.py            # console + %APPDATA%\AutomaticProcess\logs\app.log
├── core/                      # no tkinter - safe on the Create worker thread
│   ├── folder_creator.py      # folder naming/parsing, job-number uniqueness, creation
│   ├── word_filler.py         # Word template filling engine
│   ├── minutedock_client.py   # thin MinuteDock REST wrapper
│   ├── web_filler.py          # MinuteDock business logic (find-or-create, budget update)
│   ├── project_store.py       # saved wizard input per job  (%APPDATA%\...\projects\<job>.json)
│   └── template_store.py      # saved templates             (%APPDATA%\...\templates\<name>.json)
└── gui/
    ├── main_window.py         # MainWindow: composes the step mixins, step list, navigation
    ├── constants.py           # shared lists, template paths, fixed texts
    ├── project_state.py       # clear / collect / apply every per-project field (saves, reopen, templates)
    └── steps/                 # one mixin per step (vars, build, validate)
        settings_step, mode_step, template_step, batch_step, general_step,
        scope_step, ps1_step, inspection_step, waivers_step,
        specification_step, b2_letter_step, minutedock_step,
        review_step (Create orchestration + worker), review_summary

resources/templates/           # the six Word templates
build_scripts/                 # PyInstaller spec + Inno Setup script (see its README)
USER_GUIDE.md / HANDOFF.md
```

## Word templates (`resources/templates/`)

- **Project register.docx** - `{{job_number}}`, `{{address}}` (street only), `{{scope}}` (bulleted list).
- **PS1 Producer Statement.docx** - text tokens, tagged Word checkbox content
  controls, `{{scope}}` list, and the Schedule of Inspections table (rows
  selected, reordered, and unlimited "Other" rows cloned from a prototype row).
- **LBP form.docx** - per-Scope-item table (checkbox + bulleted description +
  role + drawing reference) and the Waivers YES/NO section.
- **Calculation Statement.docx** - copied unchanged.
- **Specifications.docx** - 7 `"Title 1"` sections, unselected ones deleted;
  numeric tokens; CONCRETE - GENERAL's strength lines are each optional
  (unticked lines deleted via `remove_paragraphs_with_tokens`; the
  Foundations line is built as `{{foundation_strengths}}`).
- **B2 Letter.docx** - text tokens; material rows selected.

`word_filler.fill_docx_template` copies the template, does structural cuts
first (sections, paragraphs, table rows, reorder, dynamic rows), then token
replacement (splitting runs when a token straddles them), checkbox toggling,
and bullet lists - leaving all other formatting untouched. It never
overwrites an existing output file.

## MinuteDock (`minutedock_client.py`, `web_filler.py`)

API docs: https://developers.minutedock.com. Bearer token from Settings.
Contacts are picked/added on General; a Project's Short Code is the job
number (unique), Name is the street, billable is always true, rates always
"Use contact rates" (no `default_rate_dollars` sent), optional budget is
`budget_type="billable"`, `budget_frequency="total"`, numeric
`budget_target`. Existing Projects are updated with `PUT /projects/{id}`
(requires `name` + `contact_id`) - see HANDOFF.md for what's still
unverified against the live API.

## Dev setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

No automated test suite yet - see HANDOFF.md for how changes have been
verified (headless `MainWindow` scripts) and the gotchas to follow.

## Packaging

`AutomaticProcess-Setup.exe` via PyInstaller + Inno Setup - see
[build_scripts/README.md](build_scripts/README.md). User data lives in
`%APPDATA%\AutomaticProcess` and is never touched by install/update/uninstall.

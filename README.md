# automaticprocess

A Windows desktop app (tkinter; packaged as an exe later) that automates
repetitive project-setup work for an engineering office. A step-by-step
wizard collects a project's info once, then a single **Create** click:

1. Builds the project folder structure across three NAS drives
   (Engineer / Drafting / Admin)
2. Fills in six Word document templates (Project register, PS1 Producer
   Statement, LBP form, Calculation Statement, Specifications, B2
   Letter) from the same data — including toggling real, interactive
   Word checkboxes, inserting genuine bulleted lists (not typed
   look-alikes), and letting the user pick which sections/rows of the
   longer documents apply to this project
3. *(planned)* Submits the same data to the office's timesheet/project
   website

After a successful Create, the wizard resets itself and jumps back to
General, ready for the next project. Drive paths and the saved council
list are app configuration and are never cleared by this reset.

## Wizard steps

**Settings** (drive paths — shown only on first run, i.e. while any of
the three drive paths is unconfigured; reachable afterwards via the
**File path** button) → **General** (job number, client, street/suburb/
town, scope, role) → **PS1 Input** (council, descriptions, PS1
checkboxes/dates) → **Waivers and Modifications** (LBP form's YES/NO
waiver section) → **Specification** (pick which of Specifications.docx's
7 sections apply) → **B2 Letter** (pick which material rows apply) →
**Review & Create**.

## Project structure

```
app/
├── main.py               # entry point, launches the GUI
├── gui/
│   ├── main_window.py    # MainWindow: window setup + step-list/navigation only
│   ├── constants.py      # constants shared across steps (item lists, template paths, ...)
│   └── steps/             # one mixin class per wizard step (build/validate/tk-vars)
├── core/
│   ├── folder_creator.py # Step 1 — folder creation, IMPLEMENTED
│   ├── word_filler.py    # Step 2 — Word template filling, IMPLEMENTED
│   └── web_filler.py     # Step 3 — website submission, stub (NotImplementedError)
├── config/settings.py    # user settings persisted to %APPDATA%\AutomaticProcess\user_settings.json
└── utils/logger.py       # logs to console + %APPDATA%\AutomaticProcess\logs\app.log

resources/templates/      # Word templates filled at Create time (see below)
build_scripts/            # exe build scripts (added later)
tests/                    # empty - no automated tests yet
main.py                   # root entry script: `python main.py`
requirements.txt
```

## Word templates (`resources/templates/`)

- **`Project register.docx`** — placeholders `{{job_number}}`,
  `{{address}}` (fed from Street only), `{{scope}}` (genuine bulleted
  list, see below).
- **`PS1 Producer Statement.docx`** — ~18 text placeholders, 9 real Word
  checkbox content controls (each tagged via `<w:tag>` so the app can
  find and toggle them), and a genuine bulleted list for `{{scope}}`.
- **`LBP form.docx`** — text placeholders for street/suburb/town/client
  info/date, plus two tables driven entirely by real Word checkbox
  content controls: one row per Scope item ("restricted building work"),
  and a YES/NO pair for "Waivers and Modifications".
- **`Calculation Statement.docx`** — no placeholders or tables, copied
  through unchanged.
- **`Specifications.docx`** — 7 top-level sections (each a `"Title 1"`
  -styled heading); the user picks which apply on the Specification
  step, and `word_filler._remove_unselected_sections` deletes the rest
  (heading, body, tables) before any token replacement runs. A few
  sections also gate numeric MPa/kPa placeholders.
- **`B2 Letter.docx`** — text placeholders for job number/date/council,
  plus a Material/Means of Compliance/Notes table where the user picks
  which material rows (Reinforced concrete / Structural timber / Mild
  steel structure) survive via `word_filler._remove_unselected_table_rows`
  - row content itself never changes, only which rows are present.

`app/core/word_filler.py` fills these by copying the template,
optionally deleting unselected sections/table rows first, then
replacing `{{token}}` placeholders, toggling tagged checkboxes, and
splicing in genuine bulleted-list paragraphs — the rest of each
document's formatting is left completely untouched.

## Dev setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Progress

- [x] Project skeleton
- [x] Step 1: folder creation (Engineer/Drafting/Admin, fixed Engineer subfolders)
- [x] Wizard GUI: Settings, General, PS1 Input, Waivers and Modifications,
      Specification, B2 Letter, Review & Create
- [x] Word template filling: text placeholders, real checkboxes, genuine
      bullet lists, section/table-row selection
- [x] Reset-to-blank after a successful Create
- [x] Consent Document template filling: PS1, LBP form, Calculation
      Statement, Specifications, B2 Letter
- [ ] Step 3: timesheet website submission
- [ ] Automated tests
- [ ] Package as exe

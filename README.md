# automaticprocess

A Windows desktop app (tkinter; packaged as a Windows installer via
PyInstaller + Inno Setup) that automates repetitive project-setup work
for an engineering office. A step-by-step wizard collects a project's
info once, then a single **Create** click:

1. Builds the project folder structure across three NAS drives
   (Engineer / Drafting / Admin)
2. Fills in six Word document templates (Project register, PS1 Producer
   Statement, LBP form, Calculation Statement, Specifications, B2
   Letter) from the same data — including toggling real, interactive
   Word checkboxes, inserting genuine bulleted lists (not typed
   look-alikes), and letting the user pick which sections/rows of the
   longer documents apply to this project
3. If a MinuteDock Personal Access Token is configured, syncs the
   matching Contact and Project to [MinuteDock](https://minutedock.com)
   via its REST API

While Create runs, a "please wait" progress dialog with an indeterminate
bar shows the app is working rather than appearing to hang — the actual
work runs on a background thread so the window stays responsive. After a
successful Create, a green ✔ success dialog confirms it, then the wizard
resets itself and jumps back to General, ready for the next project.
Drive paths, the MinuteDock token, and the saved council list are app
configuration and are never cleared by this reset.

Non-technical usage instructions (installing, first-time setup, what
each field means, where to get a MinuteDock token) live in
[USER_GUIDE.md](USER_GUIDE.md) — this README is for developers.

## Wizard steps

**Settings** (drive paths — shown only on first run, i.e. while any of
the three drive paths is unconfigured; reachable afterwards via the
**Settings** button) → **General** (job number, client, street/suburb/
town, scope, role) → **PS1 Input** (council, descriptions, PS1
checkboxes/dates) → **Inspection Schedule** (PS1's Schedule of
Inspections table — pick which typical items apply, add any number of
free-text "Other" items, order everything) → **Waivers and
Modifications** (LBP form's YES/NO waiver section) → **Specification**
(pick which of Specifications.docx's 7 sections apply) → **B2 Letter**
(pick which material rows apply) → **MinuteDock** (billable/rate —
only shown when a token is configured in Settings) → **Review &
Create**.

## Project structure

```
app/
├── main.py               # entry point, launches the GUI
├── gui/
│   ├── main_window.py    # MainWindow: window setup + step-list/navigation only
│   ├── constants.py      # constants shared across steps (item lists, template paths, ...)
│   └── steps/             # one mixin class per wizard step (build/validate/tk-vars)
├── core/
│   ├── folder_creator.py     # Step 1 — folder creation, IMPLEMENTED
│   ├── word_filler.py        # Step 2 — Word template filling, IMPLEMENTED
│   ├── web_filler.py         # Step 3 — MinuteDock sync business logic, IMPLEMENTED
│   └── minutedock_client.py  # Step 3 — thin MinuteDock REST API wrapper
├── config/settings.py    # user settings persisted to %APPDATA%\AutomaticProcess\user_settings.json
└── utils/logger.py       # logs to console (when one exists) + %APPDATA%\AutomaticProcess\logs\app.log

resources/
├── templates/             # Word templates filled at Create time (see below)
├── automation.png         # source image for the app icon
└── app_icon.ico           # generated from automation.png - see build_scripts/README.md

build_scripts/
├── automaticprocess.spec  # PyInstaller: onedir, windowed build
├── installer.iss          # Inno Setup: wraps the onedir build into Setup.exe
├── output/                 # gitignored - AutomaticProcess-Setup.exe lands here
└── README.md               # build instructions

USER_GUIDE.md             # non-technical usage guide, ships alongside the installer
tests/                     # empty - no automated tests yet
main.py                    # root entry script: `python main.py`
requirements.txt
```

## Word templates (`resources/templates/`)

- **`Project register.docx`** — placeholders `{{job_number}}`,
  `{{address}}` (fed from Street only), `{{scope}}` (genuine bulleted
  list, see below).
- **`PS1 Producer Statement.docx`** — text placeholders, real Word
  checkbox content controls (each tagged via `<w:tag>` so the app can
  find and toggle them), a genuine bulleted list for `{{scope}}`, and
  the "Schedule 3 - Schedule of Inspections" table, whose row set/order
  is driven entirely by the Inspection Schedule step (including
  unlimited free-text "Other" rows, cloned from the template's own
  "Other" row as a prototype).
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
  sections also gate numeric MPa/kPa placeholders, including a
  dropdown-selected grout strength (value + unit + zone chosen as one
  string, not typed).
- **`B2 Letter.docx`** — text placeholders for job number/date/council/
  street/suburb/town, plus a Material/Means of Compliance/Notes table
  where the user picks which material rows (Reinforced concrete /
  Structural timber / Mild steel structure) survive via
  `word_filler._remove_unselected_table_rows` - row content itself never
  changes, only which rows are present.

`app/core/word_filler.py` fills these by copying the template,
optionally deleting/reordering unselected sections/table rows first,
then replacing `{{token}}` placeholders (splitting a run mid-token if
needed, e.g. when a template was hand-typed in Word and autocomplete
glued two tokens into one run), toggling tagged checkboxes, and splicing
in genuine bulleted-list paragraphs and dynamically-cloned table rows —
the rest of each document's formatting is left completely untouched.

## MinuteDock sync (`app/core/minutedock_client.py`, `app/core/web_filler.py`)

Optional - only runs when a MinuteDock Personal Access Token is
configured in Settings. Authenticates as `Authorization: Bearer <token>`
against `https://minutedock.com/api/v1`. `find_or_create_contact`/
`find_or_create_project` are genuinely find-or-create (exact,
case-insensitive name match, not substring) so re-running Create for the
same job never creates duplicates. See `USER_GUIDE.md` for how to
generate a token, and `HANDOFF.md`'s "Feature 3: MinuteDock sync" section
for full implementation detail.

## Dev setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Packaging

Builds a real Windows installer (`AutomaticProcess-Setup.exe`) via
PyInstaller + Inno Setup — see [build_scripts/README.md](build_scripts/README.md)
for the exact commands and one-time tool setup.

## Progress

- [x] Project skeleton
- [x] Step 1: folder creation (Engineer/Drafting/Admin, fixed Engineer subfolders)
- [x] Wizard GUI: Settings, General, PS1 Input, Inspection Schedule,
      Waivers and Modifications, Specification, B2 Letter, MinuteDock,
      Review & Create
- [x] Word template filling: text placeholders, real checkboxes, genuine
      bullet lists, section/table-row selection, dynamic table rows
- [x] Reset-to-blank after a successful Create
- [x] Consent Document template filling: PS1, LBP form, Calculation
      Statement, Specifications, B2 Letter
- [x] Step 3: MinuteDock sync (find-or-create Contact/Project)
- [x] Package as a Windows installer (PyInstaller + Inno Setup)
- [x] Non-blocking Create (background thread + progress dialog)
- [x] Non-technical user guide
- [ ] Automated tests

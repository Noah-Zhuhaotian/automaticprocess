# automaticprocess

A Windows desktop app (tkinter; packaged as an exe later) that automates
repetitive project-setup work for an engineering office. A step-by-step
wizard collects a project's info once, then a single **Create** click:

1. Builds the project folder structure across three NAS drives
   (Engineer / Drafting / Admin)
2. Fills in Word document templates (Project register, PS1 Producer
   Statement) from the same data — including toggling real, interactive
   Word checkboxes and inserting genuine bulleted lists, not typed
   look-alikes
3. *(planned)* Submits the same data to the office's timesheet/project
   website

After a successful Create, the wizard resets itself and jumps back to
General, ready for the next project. Drive paths and the saved council
list are app configuration and are never cleared by this reset.

## Wizard steps

**Settings** (drive paths — shown only on first run, i.e. while any of
the three drive paths is unconfigured; reachable afterwards via the
**File path** button) → **General** (job number, client, address, scope,
role) → **PS1 Input** (council, descriptions, PS1 checkboxes/dates) →
**Specification** (stub) → **B2 Letter** (stub) → **Review & Create**.

## Project structure

```
app/
├── main.py               # entry point, launches the GUI
├── gui/main_window.py    # tkinter wizard window (all steps + validation)
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
  `{{address}}`, `{{scope}}` (genuine bulleted list, see below).
- **`PS1 Producer Statement.docx`** — the working template: ~18 text
  placeholders, 9 real Word checkbox content controls (each tagged via
  `<w:tag>` so the app can find and toggle them), and a genuine bulleted
  list for `{{scope}}`.
- **`PS1 Producer Statement orginal.docx`** *(sic — matches the actual
  filename)* — an untouched reference copy of the client's original PS1
  template. Kept because it's the source the 9 real checkboxes and the
  "-" bullet numbering definition were migrated from; useful again if
  the working template ever needs similar surgery.

`app/core/word_filler.py` fills these by copying the template and
replacing only `{{token}}` placeholders, toggling tagged checkboxes, and
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
- [x] Wizard GUI: Settings, General, PS1 Input, Review & Create
- [x] Word template filling: text placeholders, real checkboxes, genuine bullet lists
- [x] Reset-to-blank after a successful Create
- [ ] Specification step
- [ ] B2 Letter step
- [ ] Consent Document template filling (beyond PS1)
- [ ] Step 3: timesheet website submission
- [ ] Package as exe

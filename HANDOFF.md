# Handoff: automaticprocess

## Goal

Build a Windows desktop Python app (tkinter GUI, packaged as an exe via
PyInstaller later, msi possibly after that) with three features,
requested to be built one step at a time:

1. **Create folders** — auto-create a project folder on each of three NAS
   drives (Engineer, Drafting, Admin), with fixed subfolders on the
   Engineer drive.
2. **Fill Word** — auto-fill Word document templates (Project register,
   PS1 Producer Statement, LBP form, Calculation Statement,
   Specifications, B2 Letter) from one shared data-entry wizard.
3. **Fill timesheet website** — auto-submit the same data to a website
   that records work hours/project info. Not started — there is no
   separate "fill the website" UI step; it's meant to reuse data already
   collected earlier in the wizard.

All code, comments, and UI text must be in **English** (the user
communicates in Chinese but explicitly asked for an English codebase).

Repo: https://github.com/Noah-Zhuhaotian/automaticprocess.git, branch
`main`. Pushed history so far: `4c27d83` (full wizard rebuild - Word
template filling, real checkboxes, bullet lists), `7174142` (three GUI
refinements: folder-conflict blocking, editable council names,
greyed-out checkboxes), `c149832` (Address split into
Street/Suburb/Town; LBP form wired up as a third generated document),
`4814414` (Waivers/Specification/B2 Letter steps implemented,
Calculation Statement wired up, `main_window.py` split into
`constants.py` + `steps/`), `67ce123` (green-✔ success dialog; fixed
stale step numbering after a first-run Settings step - both found by
the user testing the app). *This* handoff is **not yet committed** -
`app/core/word_filler.py`, `app/gui/constants.py`,
`app/gui/steps/general_step.py`, `app/gui/steps/ps1_step.py`,
`app/gui/steps/review_step.py`, and both
`resources/templates/PS1 Producer Statement.docx` and
`resources/templates/LBP form.docx` are modified in the working tree:

1. **Compliance and Alternative on PS1 Input are now independent
   checkboxes, not a mutually-exclusive radio pair.** The user can tick
   both at once (a PS1 can genuinely rely on both at the same time). See
   "PS1 Input" and "Word filling" below for exactly what changed.
2. **New "Site verification" free-text field on PS1 Input**, feeding a
   `{{site_verfication}}` token already present in the PS1 template (typo
   spelling kept, same convention as the pre-existing `legel_description`
   token). Not required, synced/reset the same way as Description of
   work/Legal description.
3. **LBP form's per-item description cells are now genuine Word bulleted
   lists, one bullet per line the user types** (Enter-separated) in that
   Scope item's existing description box on the General step - no new UI,
   the user just presses Enter between points. `{{scope}}` (the PS1/
   Project register summary list) now flattens every selected item's
   individual lines into one combined bullet list, matching exactly what
   appears split across the LBP cells, instead of one merged line per
   item. See "Word filling" for the mechanism and constants.py/
   general_step.py/review_step.py for what changed.
4. **PS1's `{{scope}}` bullets now carry the same grey shading
   (`F2F2F2`/background1/shade F2) as LBP form's description cells,
   growing/shrinking with however many bullets exist.** Previously the
   grey "shading" behind `{{scope}}` in the PS1 template wasn't real
   paragraph/cell shading at all - it was a fixed-size decorative
   rectangle shape floating *behind* the text (`behindDoc="1"`,
   `<a:noAutofit/>`), completely disconnected from the text's actual
   height, so it never grew when more bullets were added. Fixed by a
   one-off template migration (removed the decorative shape, added real
   `w:shd` to the `{{scope}}` paragraph's `w:pPr`) plus a small
   `word_filler.py` change so `_insert_bullet_paragraph_after` now
   propagates a placeholder paragraph's own `w:shd` onto every bullet
   paragraph it generates - the same "reuse the placeholder's own
   formatting" idea already used for `rPr`/font, just extended to
   shading. Verified against the real template: N bullets → N shaded
   paragraphs. Project register.docx's own `{{scope}}` never had any
   shading to begin with (confirmed by inspection) - left untouched.
5. **Unexplained but accepted: `resources/templates/LBP form.docx` picked
   up 8 blank paragraphs before "WAIVERS AND MODIFICATIONS"**, most likely
   from Word auto-save while the user had it open on-screen during this
   session (table content/tokens/checkboxes all confirmed byte-identical
   to the last commit - only body paragraph whitespace changed). Not
   caused by any script or code change this handoff. The user was asked
   and explicitly chose to leave it as-is rather than reverting.
6. **"WAIVERS AND MODIFICATIONS" now always starts on a new page in LBP
   form.docx**, regardless of how much (or little) content precedes it -
   the user noticed short content above it let the heading "ride up" onto
   the same page. Fixed with python-docx's own `paragraph.paragraph_format
   .page_break_before = True` on that heading paragraph (a real Word
   "page break before" paragraph property, not a manually inserted page
   break character) - a one-line template edit, no `word_filler.py`
   change needed. Verified the property survives a full
   `fill_docx_template` pass and that every table's content/tokens are
   still byte-identical to before this edit.

`67ce123`'s own changes (historical record, already pushed):

1. **The Create-success popup now shows a green ✔** instead of the OS
   "info" icon (see "Success dialog" below) - `messagebox` only supports
   its fixed icon set, so this needed a small custom `Toplevel`, with a
   fallback to the plain `messagebox.showinfo` if it ever fails to build.
2. **Fixed stale step numbering after a first-run Settings step.**
   `self.steps` was only computed once at `__init__`; completing Settings
   (which only appears when drives aren't configured yet) and saving the
   drive paths didn't refresh it, so for the rest of that session General
   kept showing as "2 of 7" instead of "1 of 6" even though the drives
   were now configured - `_reset_for_new_project()` now rebuilds
   `self.steps` before jumping back to General. See "What Didn't Work"
   for why this one's easy to miss in code review.

`4814414`'s own changes (historical record, already pushed):

1. A dedicated **Waivers and Modifications** wizard step for the LBP
   form's YES/NO waiver section.
2. The **Specification** step is real now (was a placeholder): the user
   picks which of Specifications.docx's 7 top-level sections apply, and
   unpicked sections are deleted wholesale from the output (see "Word
   filling").
3. **Calculation Statement.docx** wired up as a fourth generated
   document - no template surgery needed, it has no tokens or tables,
   just gets copied into `06 Consent Document` as-is.
4. **`main_window.py` was split** from one 1134-line file into
   `app/gui/constants.py` + a `app/gui/steps/` package (one mixin per
   wizard step) - see "GUI module layout" below. Pure reorganization, no
   behavior change (verified by a full headless walkthrough of every
   step, see "What Worked").
5. The **B2 Letter** step is real now (was a placeholder): the user
   picks which material rows (Reinforced concrete / Structural timber /
   Mild steel structure) appear in B2 Letter.docx's compliance table -
   same "delete what wasn't picked" idea as Specification, just at the
   table-row level instead of the section level.
6. **`resources/templates/PS1 Producer Statement orginal.docx`** (the
   untouched client-original reference copy, kept since the original
   handoff for re-migrating checkboxes if ever needed) was deleted by
   the user. Safe: nothing in code referenced it, and it's still
   recoverable from git history at `4c27d83` if a future checkbox/table
   migration ever needs to diff against the client's original again
   (`git show 4c27d83:"resources/templates/PS1 Producer Statement orginal.docx"`).

`resources/templates/` now has six templates the app fills (Project
register, PS1 Producer Statement, LBP form, Calculation Statement,
Specifications, B2 Letter) and no untouched-original reference copies
anymore.

## Current Progress

Steps 1 and 2 are fully implemented (Step 2 now spans six documents, not
two) and were manually verified end-to-end when first built (synthetic
temp-dir tests, plus the user opening generated `.docx` output in Word).
Everything added since (Waivers, Specification, Calculation Statement,
the module split, B2 Letter) was verified via headless scripts that
drive the real `MainWindow`/`word_filler` code and inspect the resulting
`.docx` with python-docx - see "What Worked". Step 3 is an untouched
stub.

### Project structure

```
app/
├── main.py               # entry point, launches the GUI
├── gui/
│   ├── main_window.py    # MainWindow: window setup + step-list/navigation only (~155 lines)
│   ├── constants.py      # every constant shared across steps (SCOPE_ITEMS, template paths, ...)
│   └── steps/             # one mixin per wizard step - see "GUI module layout" below
│       ├── settings_step.py
│       ├── general_step.py
│       ├── ps1_step.py
│       ├── waivers_step.py
│       ├── specification_step.py
│       ├── b2_letter_step.py
│       └── review_step.py
├── core/
│   ├── folder_creator.py # Step 1 — IMPLEMENTED
│   ├── word_filler.py    # Step 2 — IMPLEMENTED
│   └── web_filler.py     # Step 3 — stub, raises NotImplementedError
├── config/settings.py    # settings persisted to %APPDATA%\AutomaticProcess\user_settings.json
└── utils/logger.py       # logs to console + %APPDATA%\AutomaticProcess\logs\app.log

resources/templates/       # six working templates, no untouched-"original" copies anymore
├── Project register.docx
├── PS1 Producer Statement.docx
├── LBP form.docx             # checkboxes/cells migrated in place (see Word filling)
├── Calculation Statement.docx  # no tokens/tables - copied through as-is
├── Specifications.docx       # section-selectable (see Word filling)
└── B2 Letter.docx            # table-row-selectable (see Word filling)

build_scripts/   # empty aside from a README placeholder
tests/           # empty — no automated tests, everything verified via ad hoc scripts
main.py          # root entry script: `python main.py`
requirements.txt # python-docx, pyinstaller; selenium/requests commented out for Step 3
```

### GUI module layout ([app/gui/](app/gui/))

`main_window.py` used to be one 1134-line file holding every step's
fields, build/validate logic, *and* the window/navigation plumbing. It's
now split by concern, pure reorganization with no logic rewritten:

- **`constants.py`** — every constant more than one step needs
  (`SCOPE_ITEMS`, `CHECKED`/`UNCHECKED`, all six `*_TEMPLATE` paths,
  `LABEL_WIDTH`, etc.), so step modules can import from here without a
  circular import back into `main_window.py`.
- **`steps/*_step.py`** — one mixin class per step (e.g.
  `GeneralStepMixin`, `Ps1StepMixin`). Each owns that step's tk
  variables (via an `_init_*_vars()` method), its `_build_*_step` /
  `_validate_*_step` methods, and any step-local helpers - copied
  verbatim from the old `main_window.py`, just relocated. Methods still
  freely call `self.<other step's method or var>` across mixins (e.g.
  `_open_settings_dialog` in `settings_step.py` calls
  `self._update_availability_status()`, which lives in
  `general_step.py`) - this works because everything ends up on the same
  composed `self`, no imports needed between step modules.
- **`main_window.py`** — `MainWindow(SettingsStepMixin, GeneralStepMixin,
  Ps1StepMixin, WaiversStepMixin, SpecificationStepMixin,
  B2LetterStepMixin, ReviewStepMixin, tk.Tk)` composes every mixin via
  multiple inheritance. `_init_vars()` just calls each mixin's
  `_init_*_vars()` in order; `_build_step_list()`/`_show_step()`/
  `_go_back()`/`_go_next()` (shared navigation, not tied to one step)
  are the only real logic left here, plus `run()`.

**If adding a new step**, follow this pattern: new file in `steps/`,
mixin class with `_init_<name>_vars()` + `_build_<name>_step()` +
`_validate_<name>_step()` (or `None` if it doesn't need validation, like
B2 Letter did originally), then wire it into `main_window.py`'s
`_init_vars()` and `_build_step_list()`, and add the mixin to
`MainWindow`'s base-class list.

### GUI: wizard steps ([app/gui/main_window.py](app/gui/main_window.py), [app/gui/steps/](app/gui/steps/))

A step-list (`self.steps`, built once in `_build_step_list()`) drives a
single content frame that gets destroyed/rebuilt per step. Each step
below now lives in its own `steps/*_step.py` mixin - see "GUI module
layout" above:

1. **Settings** — only included in the step list if any of the three
   drive paths (`engineer_drive`/`drafting_drive`/`admin_drive`) is
   unconfigured at launch. Always reachable afterwards via the **"File
   path"** button (top-right of the header row — deliberately a plain
   `ttk.Button`, *not* a native OS menu bar; a menu bar was tried first
   and looked like an unclickable white strip on the user's machine).
2. **General** — Job number, Client info, **Street / Suburb / Town**
   (three separate required fields as of this handoff — previously one
   combined "Address" field; see "Address split" below), Scope
   (6 checkboxes, each gates a multi-line description `tk.Text` — must
   fill a description if checked, and at least one item must be
   checked), Role (radio, required). Also does a *live* folder-name
   availability check (`folder_creator.check_availability`) on
   Job-number/Street focus-out (Suburb/Town don't affect the folder name
   and aren't part of the check), shown in green/red under the fields —
   and `_validate_general_step` re-runs that same `check_availability`
   call and **blocks Next** with an error dialog if it finds a conflict,
   so the user can no longer click past an already-exists folder name;
   they have to change Job number or Street first.
3. **PS1 Input** — Council name (combobox backed by a persisted list in
   settings + "Add Council..." to grow it live, plus an "Edit Council..."
   button — `_edit_council_name` renames whichever
   council is currently selected in the combobox via a
   `simpledialog.askstring` pre-filled with the current name, rejects
   duplicates, and rewrites it in place in `settings["council_names"]`
   so its position in the list is preserved), Description of work,
   Legal description, Scope-of-statement (All/Part only radio),
   Construction-monitoring level (CM1–CM5, multi-select checkboxes),
   Basis of statement (Compliance and Alternative — **independent
   checkboxes as of this handoff, not a mutually-exclusive radio**;
   `self.compliance_var`/`self.alternative_var`, both `tk.BooleanVar`;
   both may be ticked at once) which gate: the 3 B1 compliance-method
   checkboxes (enabled only while Compliance is ticked, cleared the
   moment it's unticked) and the Alternative-solution text box
   (auto-filled "N/A" and locked while Alternative is unticked; free-text
   and required while it's ticked) — each gate now keys off its own
   checkbox independently, so e.g. Compliance being unticked no longer
   implicitly forces Alternative's state. At least one of the two must be
   ticked to pass validation. Date is a
   Year/Month/Day trio, not a free-text field — Year must be a valid
   4-digit number before Month unlocks, Month before Day unlocks (day
   count is `calendar.monthrange`-correct, i.e. leap years included), and
   a "Today" button fills all three at once. Layout uses a 3:7
   `columnconfigure` weight split (label:input) plus a fixed
   `LABEL_WIDTH` on every label — both were tuned live against user
   screenshots; if asked to adjust spacing again, expect another
   iteration or two of "too wide/too tight" feedback.
4. **Waivers and Modifications** (this handoff) — a step dedicated to the
   LBP form's "WAIVERS AND MODIFICATIONS" section: a Yes/No radio
   (`waivers_required_var`) for "Are waivers or modifications of the
   Building Code required?", gating a Building Code Clause `ttk.Entry`
   and a Waiver/modification-required `tk.Text` — both required and
   enabled only when "Yes" is chosen, disabled+cleared under "No" (same
   gating idiom as PS1's Compliance/Alternative fields:
   `_on_waivers_required_change` mirrors `_on_compliance_alt_change`).
   Reuses `LABEL_WIDTH`/the 3:7 column split from PS1 Input for visual
   consistency.
5. **Specification** — no longer a stub. One checkbox per top-level
   section of Specifications.docx (`SPECIFICATION_SECTIONS`, 7 items -
   GENERAL STRUCTURAL CONSTRUCTION, EXCAVATION AND HARDFILL, CONCRETE -
   GENERAL, REINFORCING STEEL, STRUCTURAL STEELWORK, STRUCTURAL TIMBER,
   MASONRY BLOCKWORK), at least one required. Three of those sections
   also gate numeric MPa/kPa entry fields (`SPECIFICATION_NUMERIC_FIELDS`
   - e.g. "Ultimate bearing capacity (kPa)" under Excavation) that are
   only enabled+required while their owning section is checked, cleared
   and disabled otherwise (same gating idiom as Waivers/Compliance). See
   "Word filling" for how unpicked sections actually get removed from
   the output.
6. **B2 Letter** — no longer a stub either. Three checkboxes
   (`B2_LETTER_MATERIALS`: Reinforced concrete, Structural timber, Mild
   steel structure), at least one required - controls which rows survive
   in B2 Letter.docx's Material/Means of Compliance/Notes table. Row
   *content* is fixed (the user said so explicitly - "内容不用变"); this
   step only toggles which rows appear. See "Word filling" for the
   removal mechanism.
7. **Review & Create** — the Next button becomes "Create" on the last
   step. Runs `folder_creator.create_project_folders`, then
   `word_filler.fill_docx_template` for each of the **six** templates
   (Project register, PS1, LBP form, Calculation Statement,
   Specifications, B2 Letter — skipped individually if its template file
   is missing), then shows a success dialog (see "Success dialog"
   below), then calls `_reset_for_new_project()` which blanks every
   *project* field (job number, street/suburb/town, scope, PS1 fields,
   waivers fields, Specification/B2 Letter selections, date, etc.),
   **rebuilds `self.steps`** (this handoff - see the Repo note above;
   picks up Settings dropping out of the list if it was just completed
   this session), and jumps back to the General step — but leaves drive
   settings and the saved council list alone, since those are machine
   config, not project data.

### Success dialog ([app/gui/steps/review_step.py](app/gui/steps/review_step.py))

`_show_success_dialog(title, message)` replaces the plain
`messagebox.showinfo` call after a successful Create - the user wanted a
green ✔ instead of the OS "info" icon, and `tkinter.messagebox` only
offers its fixed icon set (`"info"`/`"warning"`/`"error"`/`"question"`),
no way to swap in an arbitrary glyph. It's a small `tk.Toplevel` built to
behave like a real messagebox: `transient` + `grab_set()` +
`self.wait_window(dialog)` for the same modal, blocks-the-caller
behavior, a `✔` `ttk.Label` (Segoe UI 28pt, `#107C10` green) where the
icon would be, the message text next to it, an OK button that closes it
(bound to Enter too). The whole thing is wrapped in a `try`/`except` that
falls back to plain `messagebox.showinfo` on any failure, per the user's
explicit "if it can't be built, just use the original icon" ask.

### Word filling ([app/core/word_filler.py](app/core/word_filler.py))

`fill_docx_template(template_path, output_path, replacements, bullet_lists=None, keep_sections=None, keep_table_rows=None)`
is the whole public surface. Structural removal (`keep_sections`/
`keep_table_rows` - see below) runs first if given, then these three
content-editing mechanisms, in this order:

1. **Plain `{{token}}` text substitution** — `_replace_in_paragraph`
   does **surgical, per-token** replacement: it finds each `{{token}}`'s
   *own* run-range within a paragraph (via `_run_text_offsets` /
   `_run_range_for_span`) and only edits those specific runs, never
   collapsing the whole paragraph into one run. This matters a lot: an
   earlier version merged everything into the paragraph's first run,
   which silently propagated that run's own formatting (a stray
   `w:highlight="lightGray"` on an unrelated leading word, in one real
   case) across the *entire* merged paragraph, corrupting unrelated text.
   Multiple tokens can share one paragraph (e.g. "...report titled
   {{address}} and numbered {{job_number}} dated {{date}}." is one
   paragraph with 3 tokens) — matches are processed **right-to-left** so
   earlier (leftward) run-index calculations, computed once from an
   unmutated snapshot, stay valid as later ones get spliced out.
2. **Real Word checkbox content controls** (`_apply_checkbox_controls` /
   `_set_checkbox_state`) — these are genuine `<w:sdt>` +
   `<w14:checkbox>` structured document tags, i.e. actually
   click-to-toggle in Word, not `☐`/`☒` typed as text. The **9 PS1
   checkboxes were migrated** from `PS1 Producer Statement orginal.docx`
   into the working template with a one-off script (not part of the
   shipped app) that copied each `<w:sdt>` block and added a
   `<w:tag w:val="cm1_box">`-style tag so the app can find and toggle
   them by name. `_apply_checkbox_controls` walks every `<w:sdt>` in the
   doc, matches its tag against the `replacements` dict, and flips
   `<w14:checked>` + swaps the visible glyph (read from
   `<w14:checkedState>`/`<w14:uncheckedState>`, which encode the glyph as
   a hex codepoint + font — the original template uses **"MS Gothic"**,
   not the "Segoe UI Symbol" font hack used for the (now-unused)
   plain-text checkbox fallback path). **If any future template needs
   more real checkboxes**, repeat this migration pattern (find the
   `<w:sdt>` in the source doc, copy it into the target with a
   `<w:tag>`) — don't try to hand-author checkbox XML from scratch.
3. **Genuine bulleted lists** (`_replace_placeholder_with_bullet_list` /
   `_ensure_bullet_numbering`) — for `{{scope}}` specifically. The client
   template's own bullet ("-") is a *real* Word numbering definition
   (`w:abstractNum`/`w:lvlText w:val="-"`), not a typed dash — confirmed
   by inspecting the original template's XML. `_ensure_bullet_numbering`
   reuses that definition if the target document already has it (PS1
   does, inherited from the original), or injects a copy
   (`BULLET_ABSTRACT_NUM_XML`) if not (Project register didn't have any
   numbering part at all — `document.part.numbering_part` auto-vivifies
   one, which made this easy). Each bullet line becomes its own real
   `<w:p>` paragraph (inserted via `addnext()` chaining, right after the
   placeholder's original paragraph), and **reuses the placeholder
   token's own `<w:rPr>`** (deep-copied) so the bullets match whatever
   font/size/bold the template author set on `{{scope}}` itself, rather
   than falling back to a generic default. **This handoff:** it also
   reuses the placeholder's own `<w:pPr>/<w:shd>` (paragraph shading) the
   same way, deep-copied onto every generated bullet paragraph before the
   placeholder's own paragraph is removed - so if a bulleted placeholder's
   paragraph has shading, every line of the resulting list gets shaded
   too, growing/shrinking automatically with however many bullets there
   are (see "PS1's `{{scope}}` shading" below for why this was needed).
   Placeholders with no shading (most of them) are unaffected -
   `template_shd` is simply `None` and nothing gets added.

Caller-side contract ([app/gui/steps/review_step.py](app/gui/steps/review_step.py)):
`_build_replacements()` returns the plain-text + checkbox dict;
`_build_scope_lines()` returns the plain description strings (no manual
`"- "` prefix — the bullet glyph is a real list marker now) passed
separately as `bullet_lists={"scope": [...]}`. **This handoff:** LBP's
per-item description cells (`lbp_{key}_description`) also go through
`bullet_lists` now instead of plain `replacements` - see "LBP form's
'restricted building work' table" below for why unselected items still
have to go through plain `replacements` instead (an empty bullet list
would delete the cell's only paragraph and corrupt the table). All
documents get the *same* `bullet_lists` dict — harmless no-op wherever a
given key's placeholder doesn't exist in that template — no
special-casing needed between them now that it's real paragraphs, unlike
an earlier plain-text version that needed a manually-injected leading
`"\n"` for one template but not the other.

**PS1's `{{scope}}` shading now matches LBP's cell shading (this
handoff):** previously the grey background behind `{{scope}}` in the PS1
template *looked* like shading but wasn't - it was a fixed-size
decorative rectangle shape floating **behind** the text
(`behindDoc="1"`, wrapped in `<mc:AlternateContent>` with a
`<wp:anchor>`/`<a:noAutofit/>` DrawingML shape, `bg2` theme fill),
positioned near the paragraph but completely disconnected from its actual
height - so it never grew or shrank as the number of scope bullets
changed. Confirmed by inspecting the raw XML (found via `body.iter(qn(
"wp:anchor"))`, since it's nested inside AlternateContent rather than a
plain `<w:drawing>`, so a naive direct-child search misses it). Fixed
with a one-off migration script (same two-phase copy-verify-then-real-file
workflow as every other template surgery in this project) that removed
the decorative shape entirely and added real `<w:shd w:fill="F2F2F2"
w:themeFill="background1" w:themeFillShade="F2"/>` (LBP's exact shading
color) to the `{{scope}}` paragraph's `<w:pPr>` — combined with the
`word_filler.py` change above (propagating `w:shd` onto generated bullet
paragraphs), a real PS1 document now shows every scope bullet shaded,
however many there are. Project register.docx's own `{{scope}}` was
checked too and never had any shading or decorative shape to begin with -
left untouched.

**PS1's `compliance_box`/`alternative_box` are independently driven now
(this handoff):** no change to `word_filler.py` itself - these were
already two separate tagged checkbox controls in the PS1 template (see
mechanism 2 above), and `_apply_checkbox_controls` already toggles each
by tag independently. The only change is what `_build_replacements()`
feeds them: `"compliance_box": CHECKED if self.compliance_var.get() else
UNCHECKED` and `"alternative_box": CHECKED if
self.alternative_var.get() else UNCHECKED` (previously both derived from
one shared `compliance_alt_var` radio value, so only one could ever be
`CHECKED`). Confirmed end-to-end: ticking both in the GUI and generating
a real PS1 document leaves *both* real Word checkboxes checked
(`w14:checked="1"`) - not just the token dict, the actual `.docx` output.
`compliance_solution`/`alternative_solution` similarly now key off their
own checkbox (`self.compliance_var.get()`/`self.alternative_var.get()`)
instead of a shared value.

**Address → Street/Suburb/Town split (previous handoff, `c149832`):** the General step's
single "Address" field is now three fields. The project folder name and
the Project register/PS1 templates' existing `{{address}}` token are
both fed from **Street only** (`build_project_folder_name` in
`folder_creator.py` was renamed `address` → `street` throughout, and
`_build_replacements()` sets `"address": street` — the token name in
those two templates wasn't touched, only what value it gets). Suburb and
Town are new `{{suburb}}`/`{{town}}` tokens, currently only consumed by
the LBP form.

**LBP form's "restricted building work" table (previous handoff, `c149832`):** table 1
in `LBP form.docx` has 6 item rows (Foundation, Retaining, Beams, Portal,
Bracing, Others — same order as `SCOPE_ITEMS`), each with a real
`<w:sdt>`/`<w14:checkbox>` control (already present in the file the user
added, just like PS1's — Word had it, it just wasn't tagged) plus 3 empty
data cells (Description / Carried out by-Supervised by / Referenced on
drawings). None of these had `{{token}}` text or a `<w:tag>` yet, so a
one-off migration script (`migrate_lbp.py`, run once against the working
template the same two-phase way as the PS1 checkbox migration — copy
first, verify, then the real file) added:
- `<w:tag w:val="lbp_{key}_box">` to each checkbox's `sdtPr` (schema
  order matters: `rPr`, then `tag`, then `id`, then `w14:checkbox` — see
  the PS1 checkboxes for the reference structure), and
- a `{{lbp_{key}_description}}` / `{{lbp_{key}_carried_by}}` /
  `{{lbp_{key}_reference}}` run into each of the 3 empty cells,

where `key` is the lowercased `SCOPE_ITEMS` name. **No changes to
`word_filler.py` were needed at all** — `_iter_all_paragraphs` and
`_iter_checkbox_controls` already walk the entire document subtree via
`.iter()`, which finds paragraphs/sdts nested inside table cells (and
inside a `<w:sdt>` sitting as a direct sibling of `<w:tc>` in the row,
which is how these checkboxes are wired into the grid — not inside a
`<w:tc>` themselves) for free. `_build_replacements()` in
`main_window.py` fills all 18 of these tokens per item: checked → the
Scope description text, the Role value ("Carried out"/"Supervised" — the
exact string already used for `ROLE_OPTIONS`, no mapping needed) in
Carried-out, and `f"Engsolution drawings #{job_number}"` in Reference;
unchecked → all three left as `""`.

**This handoff: `lbp_{key}_description` is now a genuine bulleted list,
not a plain-text blob.** Each Scope item's description box (General step)
is still one `tk.Text`, but now every Enter-separated line the user types
becomes its own bullet point in that item's LBP table cell - no new UI, no
"how many bullets" count field, the user was told to just press Enter
between points. New helper `_scope_description_lines()`
([general_step.py](app/gui/steps/general_step.py)) splits that text into
non-empty stripped lines; `review_step.py`'s new
`_build_lbp_description_bullets()` returns
`{f"lbp_{key}_description": lines}` for every *selected* item, merged into
the shared `bullet_lists` dict passed to `fill_docx_template` (see "Word
filling"). Deliberately **not selected** items still go through the plain
`replacements` dict (`lbp_{key}_description = ""`) instead of an empty
bullet list - `_replace_placeholder_with_bullet_list` deletes the
placeholder's paragraph entirely once its runs are empty, and a table cell
must always retain at least one `<w:p>` or the `.docx` breaks. `{{scope}}`
(`_build_scope_lines()`) now flattens every selected item's lines into one
combined list instead of one merged-with-`"; "` line per item, so it shows
the exact same bullets that appear split across the LBP cells.

**LBP form's "Waivers and Modifications" section (this handoff):** table
2 has a YES/NO checkbox pair in row 0 (`<w:sdt>` elements as direct
siblings of the label `<w:tc>`s, same wiring style as table 1's
checkboxes) and two value cells in row 3 (Building Code Clause / Waiver-
modification-required — row 2 only holds their column headers; row 3's
middle cell, like table 1's spacer columns, is a blank divider, ignore
it). Neither the checkboxes nor the value cells had tags/tokens, so a
second one-off script (`migrate_lbp_waivers.py`, same copy-verify-then-
real-file workflow) tagged the YES box `lbp_waiver_yes_box`, the NO box
`lbp_waiver_no_box`, and inserted `{{lbp_building_code_clause}}` /
`{{lbp_waiver_modification}}` into the two row-3 cells. Driven by the new
"Waivers and Modifications" wizard step (see GUI steps above); when "No"
is chosen (or nothing yet), `_build_replacements()` sends `UNCHECKED` for
the yes-box, `CHECKED` for the no-box, and empty strings for both value
tokens — mirroring the same selected/not-selected pattern as the Scope
items above it, just with a two-way checkbox pair instead of one.

**Calculation Statement.docx (this handoff):** the simplest of the six -
zero `{{token}}`s, zero tables, confirmed by scanning it before wiring it
up. Just added to the `documents` list in `_on_create` and copied through
by `fill_docx_template` unchanged into `06 Consent Document`. No GUI
step, no migration script, nothing else needed.

**Specifications.docx section selection (this handoff) - a fourth
structural mechanism, `_remove_unselected_sections`:** unlike the
token/checkbox/bullet-list mechanisms above (which all edit *within* the
document), this one deletes whole chunks of it. Specifications.docx
marks its 7 top-level sections with a `"Title 1"`-styled paragraph per
section (`SECTION_HEADING_STYLE` constant); `_remove_unselected_sections`
walks `document.element.body`'s direct children in order, finds every
such heading, and for any heading not in the caller's `keep_titles` set,
removes every body element from that heading up to (not including) the
next `"Title 1"` heading (or the document's trailing `<w:sectPr>` for the
last section - that element must survive or the .docx breaks). Content
*before* the first heading (cover-page front matter, with its own
`{{street}}`/`{{job_number}}`/etc. tokens) is untouched. Wired into
`fill_docx_template` as a new `keep_sections: set[str] | None` parameter,
applied *before* token replacement so tokens living only inside a removed
section (e.g. `{{grout_strength}}`, only in MASONRY BLOCKWORK) never need
a value - `_build_replacements()` sends `""` for all of them unconditionally
and it's harmless. Word recalculates that heading style's own
auto-numbering (a real multilevel list) from whichever headings survive,
so surviving sections don't need manual renumbering in code - confirmed
by inspecting the numbering XML, not assumed.

**B2 Letter.docx material-row selection (this handoff) - the same idea,
one level down, `_remove_unselected_table_rows`:** B2 Letter.docx's
Material/Means of Compliance/Notes table has one header row plus one row
per material (Reinforced concrete, Structural timber, Mild steel
structure) - a much simpler grid than LBP's tables, plain `<w:tc>` cells
throughout, no `<w:sdt>` checkboxes, no spacer columns. For each row
after the header, `_remove_unselected_table_rows` reads the first cell's
text and deletes the whole `<w:tr>` if it's not in the caller's
`keep_row_labels` set. Wired into `fill_docx_template` as
`keep_table_rows: dict[int, set[str]] | None` (table index → labels to
keep), applied at the same "before replacement" point as `keep_sections`.
Row *content* was explicitly not to be changed - this only controls
which rows exist, matching the pattern of "structural cut before token
replacement" that Specification established for whole sections.

### Step 1 logic ([app/core/folder_creator.py](app/core/folder_creator.py))
Folder name = `"{Job Number} - {Street}"` (was `{Address}` before the
Street/Suburb/Town split - see "Address → Street/Suburb/Town split"
above; every function's `address` parameter was renamed `street`, no
behavior change beyond which GUI field feeds it). Engineer drive gets 6
fixed subfolders (`01 Architectural` … `06 Consent Document`); PS1
Producer Statement.docx, LBP form.docx, Calculation Statement.docx,
Specifications.docx, and B2 Letter.docx are all generated *inside* `06
Consent Document`, Project register.docx at the Engineer project root;
two-phase validate-then-create so a name collision never leaves a
partial mess.

## What Worked

- **tkinter**, confirmed again — the wizard now has real forms, live
  validation, dynamic enable/disable chains (Compliance↔Alternative,
  Year→Month→Day), and it's all still zero extra dependencies.
- **Asking to see the client's actual original template file** (not just
  a description) turned out to be essential *twice*: once to get the
  exact `{{placeholder}}` names right, and again — much more
  importantly — to discover that the "checkboxes" and "bullets" the user
  described in chat were actually real Word content controls / numbering
  definitions, not typed characters. Guessing from a screenshot alone
  would have produced plausible-looking but structurally wrong output.
  **If the user describes template formatting again, ask for the file
  and inspect its raw XML (`docx.oxml`) rather than assuming plain text.**
- **Surgical per-token run editing** instead of "collapse the paragraph
  into run 0" — directly fixed a real formatting-corruption bug the user
  caught by eye (a stray highlight spreading across unrelated text) and
  is generally the more correct approach any time a paragraph might mix
  differently-formatted runs.
- **Reusing the template's own formatting** (checkbox font from
  `checkedState`/`uncheckedState`, bullet run's `rPr` copied onto new
  bullet paragraphs) instead of hardcoding a font choice — avoids an
  entire class of "doesn't match the template" feedback.
- **Two-phase migration workflow for the checkboxes**: write a one-off
  script, run it against a *copy* first, verify thoroughly (tags, ids,
  checked states, surrounding text still intact), only then run it
  against the real working template (after backing it up). Caught a real
  bug this way (see below) before it touched the real file.
- **`_reset_for_new_project()` after Create** — user explicitly wanted a
  clean slate for the next project, confirmed drive settings/council list
  must survive the reset (they're config, not project data).
- **A single global `ttk.Style().map("TCheckbutton", foreground=...)`**
  (set once in `MainWindow.__init__`) to greys out every checkbox that's
  either unselected or disabled, and shows normal/black only when
  checked *and* enabled. One style rule covers Scope, CM, and B1
  checkboxes at once — no need to touch each `Checkbutton` individually.
  State-spec order matters: `disabled` must be listed before
  `!selected` so a disabled-but-checked box still greys out (ttk style
  maps use first-match-wins). Confirmed visually via screenshot — labels
  for unchecked items render grey, checked items render black.
- **The PS1 checkbox migration pattern generalized cleanly to a second,
  differently-shaped template.** LBP form's checkboxes live inside a
  table (as `<w:sdt>` siblings of `<w:tc>`, not descendants of one) and
  needed matching empty table cells filled with tokens too, not just
  tags — same "inspect the real XML, don't guess" and "script it,
  verify on a copy, then run for real" workflow from the PS1 handoff
  worked unchanged. Confirmed end-to-end with a full `create_project_folders`
  + `fill_docx_template` smoke test against real (test) drives, not just
  unit-level checks.
- **The "structural cut before replacement" idea generalized a third
  time, cleanly, from sections down to table rows.**
  `_remove_unselected_sections` (Specification) and
  `_remove_unselected_table_rows` (B2 Letter) are ~15-line functions each
  because they lean on the same insight: delete first, replace tokens
  second, so anything living only inside deleted content never needs a
  value and never triggers a spurious "no value provided" warning. Worth
  reaching for this pattern again if a future template needs
  user-selectable content at any other granularity (a whole page, a
  single paragraph, etc.).
- **A full headless walkthrough of the real `MainWindow` class** (not
  just `folder_creator`/`word_filler` directly) was what actually caught
  whether the mixin split preserved behavior: instantiate `MainWindow()`,
  jump `current_step`/call `_show_step()` for every step in order, feed
  each step's tk vars synthetic data, call its `_validate_*_step()`, and
  for the last one actually call `_on_create()` and inspect the generated
  `.docx` files with python-docx. Cross-mixin calls (e.g.
  `_build_replacements()` in `review_step.py` reading every other
  mixin's vars) only get exercised by driving the composed class this
  way — a script that only imports `folder_creator`/`word_filler` in
  isolation wouldn't have caught a broken `MainWindow` composition.
- **Re-checking a file's actual state before trusting a description of
  what was done to it.** The user said B2 Letter.docx's tokens were
  already in place; a token scan came back empty, and the file's mtime
  hadn't changed since it was first added - the edit genuinely hadn't
  been saved yet. Re-scanning after the user saved found all three
  tokens exactly as expected. Cheap check, avoided building against a
  stale assumption.
- **Git history as a safety net for deleting a "just in case" reference
  file.** `PS1 Producer Statement orginal.docx` was kept around from the
  very first handoff in case the checkbox/bullet migration ever needed
  re-doing; once it was committed (`4c27d83`), the physical file in
  `resources/templates/` stopped being the only copy - confirmed via
  `git log --all -- <path>` before agreeing it was safe to delete, so
  the reasoning was "recoverable from git if ever needed again," not
  "probably fine."
- **The user's own testing pass caught a real bug the headless scripts
  never would have.** Every headless `MainWindow()` test this handoff
  and last constructed the app *already* pointing at configured test
  drives, so `self.steps` was always the 6-step list from the start -
  the stale-step-list bug (see "What Didn't Work") only exists on a
  genuine first run (drives unconfigured at `__init__`, then configured
  *during* that same session). No amount of headless testing that
  conveniently pre-configures drives would have found this; it needed
  someone testing the actual first-run path end to end. Worth remembering
  when a test setup "conveniently" skips a state a real user starts in.
- **Testing the exact reported scenario, not just the fix in isolation.**
  Reproduced the stale-step-list bug by clearing drive settings *before*
  constructing `MainWindow` (same as a real first run), walking Settings
  for real, then the rest of the wizard, then asserting the post-Create
  step count/index - rather than just confirming `_build_step_list()`
  returns 6 items when called standalone (which wouldn't prove
  `_reset_for_new_project` was calling it, or that the numbers shown to
  the user were actually right).
- **Verifying a checkbox-independence change against the real `.docx`
  output, not just the token dict.** For the Compliance/Alternative
  split, `_build_replacements()` returning `{"compliance_box": "☒",
  "alternative_box": "☒"}` when both are ticked is necessary but not
  sufficient - it doesn't prove `_apply_checkbox_controls` actually
  toggles two *independently tagged* `<w:sdt>` controls rather than, say,
  one control silently controlling both (a real risk if the template
  ever shared a tag). Generated a real PS1 document with both ticked and
  read back `w14:checked` for both tags directly from the saved `.docx`
  XML to confirm. Four widget-state/token-dict cases (neither / both /
  Compliance-only / Alternative-only) were also covered headlessly before
  this - the full-document check was the one that couldn't be skipped
  for a checkbox behavior change specifically.
- **When the user says something "doesn't look right" about template
  formatting, re-inspect the actual XML rather than trusting the first
  plausible explanation.** First guess for the PS1 `{{scope}}` shading
  question was "it's cell/paragraph shading like LBP's, just needs
  copying" - checking the raw XML showed there was *no* shading at all on
  that paragraph, and the grey box the user saw was an unrelated floating
  decorative shape. Asking the user for a screenshot at that point (rather
  than guessing further) was what surfaced the real shape, which a second
  round of raw-XML inspection then explained precisely (`behindDoc="1"`,
  `<a:noAutofit/>`, wrapped in `<mc:AlternateContent>` so a naive
  `w:drawing` direct-child search misses it - had to search for
  `wp:anchor` via `.iter()` instead and walk up to the enclosing `<w:r>`).
- **A prior session's "reuse the placeholder's own formatting" pattern
  (font `rPr` for bullets) generalized cleanly to shading (`w:shd`)
  without needing a new mechanism** - just capture it alongside `rPr`
  before the placeholder paragraph is removed, and copy it onto every
  generated bullet paragraph the same way. Confirmed end-to-end against a
  real filled document (N bullets → N shaded paragraphs), not just by
  inspecting the template after migration.

## What Didn't Work / Avoid Repeating

- **Collapsing an entire paragraph's text into its first run** when
  substituting placeholders. Works fine until a paragraph has non-uniform
  formatting across runs (highlight on some, not others) — then it
  smears the first run's formatting over everything. Fixed by per-token
  surgical replacement (see above); don't revert to the simpler
  whole-paragraph approach even though it reads shorter.
- **Assuming `id(paragraph._p)`-based deduplication is safe** for
  skip-if-already-visited logic while iterating python-docx paragraphs
  gathered via nested `table.rows`/`row.cells` loops. It produced
  bizarre, silent false-positive "already seen" hits during the
  checkbox-migration script (a `replace_placeholder_with_checkbox`
  helper that returned `False` for every field despite the token
  provably being present) — root cause not fully nailed down (something
  about short-lived wrapper objects and `id()` reuse) but removing the
  dedup entirely fixed it immediately and duplicate-processing turned out
  to be harmless anyway (later hits just find no token left). If a
  similar "works in isolation, fails in a loop" python-docx bug shows up
  again, suspect `id()`-based identity checks first.
- **Guessing checkbox rendering fixes without inspecting XML.** Two
  earlier attempts (clearing `<w:rFonts>` overrides; then forcing all
  four font slots to "Segoe UI Symbol") each *looked* like a plausible
  fix for garbled `☐`/`☒` glyphs and each still left something broken,
  because the real cause (plain-text-typed dash vs. a genuine `<w:sdt>`
  checkbox content control) was structural, not a font problem at all.
  Once the user shared the original file and its XML was actually read,
  the real fix (migrate the real checkbox controls) was obvious. Don't
  keep iterating on font tweaks for a rendering complaint — check whether
  the underlying element type is even right first.
- **A single shared `{{scope}}` string** formatted differently per
  target document (a leading `"\n"` hack for one template, not the
  other) was fragile and got reverted more than once as requirements
  shifted. The real bullet-list mechanism made this moot — lines are
  passed as a plain list and each template gets genuine paragraphs, no
  per-document text-formatting special-casing needed anymore.
- Chinese-first drafts and generic-field-picker GUI designs — both
  already flagged in the original handoff; still true, not repeated
  since.
- **Blind coordinate-based UI automation to smoke-test the running app**
  (PowerShell `mouse_event`/`SendKeys` clicking into an Entry by pixel
  offset, then Ctrl+A/Delete/type/Tab). Used to verify the folder-conflict
  block; the window closed unexpectedly mid-sequence with no exception
  logged, and there was no way to be fully sure the keystrokes hadn't
  landed on a different window (e.g. an editor with the same file open)
  instead of the intended field — DPI scaling can desync
  `Cursor.Position` (logical pixels) from `GetWindowRect` (physical
  pixels), so a click can land somewhere unintended. Had to verify after
  the fact via `git diff`/line-count that no file got clobbered — it
  hadn't, but that was luck, not a guarantee. A plain launch-and-screenshot
  (no simulated typing) worked fine and did confirm the checkbox-greying
  change. **If asked to verify GUI behavior again, prefer a single
  no-typing screenshot over simulated multi-field keyboard/mouse input**,
  or ask the user to click through it themselves.
- **Computing `self.steps` once at `__init__` and never revisiting that
  assumption.** It's derived from `_drives_configured()`, which can
  become true *during* a running session (first-run user fills in
  Settings, saves it) - but nothing re-ran `_build_step_list()`
  afterward, so the step list silently stayed stale (Settings still
  present, General showing "2 of 7") for the rest of that session even
  though a fresh restart would correctly show "1 of 6". This survived
  code review and every earlier headless test because none of them
  exercised a real first run (all pre-configured drives before
  constructing `MainWindow`) - only surfaced when the user actually
  tested the literal first-run path (see "What Worked"). Fixed by
  rebuilding `self.steps` in `_reset_for_new_project()`. **Any state
  computed once from settings/config that can change mid-session should
  be recomputed at the point it's read, not cached at construction time**
  - or at minimum, explicitly re-derived at the one point (here, the
  post-Create reset) where the app returns to a "clean slate" a user
  would expect to match a fresh launch.
- **Templates open in Word block migration scripts from saving
  (`PermissionError: [Errno 13]`)** - the user had PS1 Producer
  Statement.docx open while looking at it for a screenshot, and the
  one-off shading migration script couldn't write to it until they closed
  it. Unremarkable on its own, but worth remembering that template
  surgery on a file the user is actively inspecting needs "please close
  it first," not a silent retry loop.
- **`resources/templates/LBP form.docx` picked up 8 blank paragraphs from
  something outside this session's own changes** (Word autosave while the
  user had it open, going by timing - not any script run here). Caught by
  `git status` showing it modified when no code had touched it, then
  confirmed via a HEAD-vs-working-tree text diff that tables/tokens/
  checkboxes were untouched and only body whitespace changed. **`git
  status` after any batch of "read-only" template inspection is worth a
  glance** - reading a `.docx` with python-docx never writes it, but the
  user's own Word session editing the same file concurrently can, and it
  won't show up as something *you* did unless you check.

## Next Steps

1. **Keep having the user click through the app in a real window -
   it already found one real bug headless testing structurally could
   not have caught.** The user testing "starting from File path" (a
   genuine first run) surfaced the stale-`self.steps` bug fixed this
   handoff; every headless script up to that point happened to
   pre-configure drives before constructing `MainWindow`, so the
   first-run path itself was never actually exercised (see "What Worked"
   / "What Didn't Work"). Still nobody has confirmed the real *visual*
   layout (label wrapping, the Specification/B2 Letter checkbox lists,
   the new ✔ success dialog's look, radio/entry enable-disable *feel*)
   or opened the generated `.docx` files in Word to eyeball
   checkboxes/tables/section removal rendering correctly. An earlier
   attempt at simulating clicks/keystrokes to do this closed the app
   unexpectedly (see "What Didn't Work") - keep preferring the user's
   own click-through over more coordinate-based automation.
2. **Consent Document folder** (`06 Consent Document`) now gets PS1, LBP
   form, Calculation Statement, Specifications, and B2 Letter - probably
   everything the user meant by "other documents belong there too" when
   that was mentioned in passing early on, but worth a quick
   confirmation now that the folder is this full rather than assuming.
3. **Step 3 (website submission)** — completely unstarted, no URL, no
   auth method, no field mapping gathered yet. `web_filler.py` is an
   untouched stub.
4. **Packaging (PyInstaller)** — still deferred per the user's original
   preference (get functionality working first). Worth floating again
   now that Step 2 covers all six known documents - in case the user
   wants an early build to test on their own machine before Step 3 is
   done.
5. No automated tests exist (`tests/` is empty aside from `__init__.py`).
   Everything so far was verified via ad hoc scripts run through the Bash
   tool, not committed as reusable tests. `word_filler.py` in particular
   now has four structural mechanisms (token replace, checkbox toggle,
   bullet-list splice, section/row removal) intricate enough to benefit
   from real pytest regression coverage, and the headless `MainWindow`
   walkthrough scripts written this handoff would be a reasonable
   starting point to adapt into actual test cases, if the user wants
   that investment.

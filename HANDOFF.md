# Handoff: automaticprocess

## Goal

Build a Windows desktop Python app (tkinter GUI, packaged as an exe via
PyInstaller later, msi possibly after that) with three features,
requested to be built one step at a time:

1. **Create folders** — auto-create a project folder on each of three NAS
   drives (Engineer, Drafting, Admin), with fixed subfolders on the
   Engineer drive.
2. **Fill Word** — auto-fill Word document templates (Project register,
   PS1 Producer Statement) from one shared data-entry wizard.
3. **Fill timesheet website** — auto-submit the same data to a website
   that records work hours/project info. Not started — there is no
   separate "fill the website" UI step; it's meant to reuse data already
   collected earlier in the wizard.

All code, comments, and UI text must be in **English** (the user
communicates in Chinese but explicitly asked for an English codebase).

Repo: https://github.com/Noah-Zhuhaotian/automaticprocess.git, branch
`main`. The full wizard rebuild (Word template filling, real checkboxes,
bullet lists) was committed and pushed as `4c27d83` ("Rebuild GUI as a
wizard and implement Word template filling") — that was this handoff's
previous "commit and push" action item, now done. On top of that, three
small GUI refinements (folder-conflict blocking, editable council names,
greyed-out checkboxes — see below) are being committed and pushed as
part of *this* handoff.

Note: `resources/templates/LBP form.docx` is sitting untracked in the
working tree (added 2026-07-28, not referenced anywhere in code yet).
Left out of git deliberately for now — the user's push token wasn't set
up when it appeared, and it hasn't been asked about since. Don't commit
it opportunistically; ask first, since it's presumably staged for a
not-yet-defined feature (LBP = Licensed Building Practitioner, a plausible
fit for the still-undefined Specification or B2 Letter step, but that's
a guess, not confirmed).

## Current Progress

Steps 1 and 2 are fully implemented and manually verified end-to-end
(both with synthetic temp-dir tests and by the user opening generated
`.docx` output in Word). Step 3 is an untouched stub.

### Project structure

```
app/
├── main.py               # entry point, launches the GUI
├── gui/main_window.py    # tkinter wizard (~950 lines - see below)
├── core/
│   ├── folder_creator.py # Step 1 — IMPLEMENTED
│   ├── word_filler.py    # Step 2 — IMPLEMENTED
│   └── web_filler.py     # Step 3 — stub, raises NotImplementedError
├── config/settings.py    # settings persisted to %APPDATA%\AutomaticProcess\user_settings.json
└── utils/logger.py       # logs to console + %APPDATA%\AutomaticProcess\logs\app.log

resources/templates/
├── Project register.docx            # working template
├── PS1 Producer Statement.docx      # working template
└── PS1 Producer Statement orginal.docx  # untouched client original — KEEP, see below

build_scripts/   # empty aside from a README placeholder
tests/           # empty — no automated tests, everything verified via ad hoc scripts
main.py          # root entry script: `python main.py`
requirements.txt # python-docx, pyinstaller; selenium/requests commented out for Step 3
```

### GUI: wizard steps ([app/gui/main_window.py](app/gui/main_window.py))

A step-list (`self.steps`, built once in `_build_step_list()`) drives a
single content frame that gets destroyed/rebuilt per step:

1. **Settings** — only included in the step list if any of the three
   drive paths (`engineer_drive`/`drafting_drive`/`admin_drive`) is
   unconfigured at launch. Always reachable afterwards via the **"File
   path"** button (top-right of the header row — deliberately a plain
   `ttk.Button`, *not* a native OS menu bar; a menu bar was tried first
   and looked like an unclickable white strip on the user's machine).
2. **General** — Job number, Client info, Address (all required), Scope
   (6 checkboxes, each gates a multi-line description `tk.Text` — must
   fill a description if checked, and at least one item must be
   checked), Role (radio, required). Also does a *live* folder-name
   availability check (`folder_creator.check_availability`) on
   Job-number/Address focus-out, shown in green/red under the fields —
   and, as of this handoff, `_validate_general_step` re-runs that same
   `check_availability` call and **blocks Next** with an error dialog if
   it finds a conflict, so the user can no longer click past a
   already-exists folder name; they have to change Job number or Address
   first. Previously the red text was purely informational and didn't
   stop navigation.
3. **PS1 Input** — Council name (combobox backed by a persisted list in
   settings + "Add Council..." to grow it live, plus an "Edit Council..."
   button added this handoff — `_edit_council_name` renames whichever
   council is currently selected in the combobox via a
   `simpledialog.askstring` pre-filled with the current name, rejects
   duplicates, and rewrites it in place in `settings["council_names"]`
   so its position in the list is preserved), Description of work,
   Legal description, Scope-of-statement (All/Part only radio),
   Construction-monitoring level (CM1–CM5, multi-select checkboxes),
   Basis of statement (Compliance/Alternative radio) which gates: the 3
   B1 compliance-method checkboxes (enabled only under Compliance) and
   the Alternative-solution text box (auto-filled "N/A" and locked under
   Compliance; free-text and required under Alternative). Date is a
   Year/Month/Day trio, not a free-text field — Year must be a valid
   4-digit number before Month unlocks, Month before Day unlocks (day
   count is `calendar.monthrange`-correct, i.e. leap years included), and
   a "Today" button fills all three at once. Layout uses a 3:7
   `columnconfigure` weight split (label:input) plus a fixed
   `LABEL_WIDTH` on every label — both were tuned live against user
   screenshots; if asked to adjust spacing again, expect another
   iteration or two of "too wide/too tight" feedback.
4. **Specification** — stub, one placeholder label. No details gathered
   yet.
5. **B2 Letter** — stub, one placeholder label. No details gathered yet.
6. **Review & Create** — the Next button becomes "Create" on the last
   step. Runs `folder_creator.create_project_folders`, then
   `word_filler.fill_docx_template` for each of the two templates
   (skipped individually if its template file is missing — this is how
   Specification/B2 Letter documents will slot in later, once their
   templates exist), then shows a summary `messagebox`, then calls
   `_reset_for_new_project()` which blanks every *project* field
   (job number, address, scope, PS1 fields, date, etc.) and jumps back to
   the General step — but leaves drive settings and the saved council
   list alone, since those are machine config, not project data.

### Word filling ([app/core/word_filler.py](app/core/word_filler.py))

`fill_docx_template(template_path, output_path, replacements, bullet_lists=None)`
is the whole public surface. Three independent mechanisms, applied in
this order:

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
   than falling back to a generic default.

Caller-side contract ([app/gui/main_window.py](app/gui/main_window.py)):
`_build_replacements()` returns the plain-text + checkbox dict;
`_build_scope_lines()` returns the plain description strings (no manual
`"- "` prefix — the bullet glyph is a real list marker now) passed
separately as `bullet_lists={"scope": [...]}`. Both templates get the
*same* `bullet_lists["scope"]` — no special-casing needed between them
now that it's real paragraphs, unlike an earlier plain-text version that
needed a manually-injected leading `"\n"` for one template but not the
other.

### Step 1 logic ([app/core/folder_creator.py](app/core/folder_creator.py))
unchanged since the first handoff — see git history / code for details.
Folder name = `"{Job Number} - {Address}"`; Engineer drive gets 6 fixed
subfolders (`01 Architectural` … `06 Consent Document`); PS1 Producer
Statement.docx is generated *inside* `06 Consent Document`, Project
register.docx at the Engineer project root; two-phase
validate-then-create so a name collision never leaves a partial mess.

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

## Next Steps

1. **Manually click through the three refinements above** (folder-conflict
   block, Edit Council, greyed checkboxes) — they were only verified by
   code review plus one static screenshot (confirmed the grey/black
   checkbox contrast), not a full interactive pass, because the attempted
   automated interaction closed the app unexpectedly (see "What Didn't
   Work"). Nothing suggests a bug, but this handoff can't claim
   end-to-end verification the way Steps 1–2 originally got.
2. **`resources/templates/LBP form.docx`** is untracked in the working
   tree, deliberately left out of the commit that produced this handoff
   (see the Repo note above — user's push token wasn't set up yet when
   it appeared). Ask the user what it's for before adding it to git or
   wiring it into any step.
3. **Specification step** — completely undefined. Need the same
   treatment PS1 got: the user will eventually provide a template/mockup;
   ask for the actual file, inspect its XML for any non-obvious
   formatting (checkboxes, bullets, highlights) before assuming plain
   `{{token}}` substitution is enough.
4. **B2 Letter step** — same as above, undefined.
5. **Consent Document folder** (`06 Consent Document`) currently only
   gets the PS1 Producer Statement. The user mentioned other documents
   belong in that folder too, mentioned only in passing early on — worth
   re-confirming what else, if anything, still needs to land there.
6. **Step 3 (website submission)** — completely unstarted, no URL, no
   auth method, no field mapping gathered yet. `web_filler.py` is an
   untouched stub.
7. **Packaging (PyInstaller)** — still deferred per the user's original
   preference (get functionality working first). Worth floating again
   now that Steps 1–2 are functionally complete, in case the user wants
   an early build to test on their own machine before Specification/B2
   Letter/Step 3 are done.
8. No automated tests exist (`tests/` is empty aside from `__init__.py`).
   Everything so far was verified via ad hoc scripts run through the Bash
   tool, not committed as reusable tests. Consider adding real pytest
   coverage for `folder_creator` and `word_filler` (the run-splicing and
   checkbox/bullet-list logic in particular is intricate enough to
   benefit from regression tests) if the user wants that investment.

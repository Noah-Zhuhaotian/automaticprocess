# Handoff: automaticprocess

## Goal

Build a Windows desktop Python app (tkinter GUI, packaged as an exe via
PyInstaller later, msi possibly after that) with three features,
requested to be built one step at a time:

1. **Create folders** — auto-create a project folder on each of three NAS
   drives (Engineer, Drafting, Admin), with fixed subfolders on the
   Engineer drive.
2. **Fill Word** — auto-fill Word document templates (Project register,
   PS1 Producer Statement, LBP form) from one shared data-entry wizard.
3. **Fill timesheet website** — auto-submit the same data to a website
   that records work hours/project info. Not started — there is no
   separate "fill the website" UI step; it's meant to reuse data already
   collected earlier in the wizard.

All code, comments, and UI text must be in **English** (the user
communicates in Chinese but explicitly asked for an English codebase).

Repo: https://github.com/Noah-Zhuhaotian/automaticprocess.git, branch
`main`. The full wizard rebuild (Word template filling, real checkboxes,
bullet lists) was committed and pushed as `4c27d83` ("Rebuild GUI as a
wizard and implement Word template filling"). A follow-up commit
(`7174142`, "Block folder-conflict navigation, add council rename, grey
out unfilled checkboxes") added three GUI refinements. On top of both of
those, *this* handoff's changes — splitting Address into
Street/Suburb/Town and adding the LBP form as a third generated document
— are being committed and pushed next.

`resources/templates/LBP form.docx` (LBP = Licensed Building
Practitioner "Certificate of Design Work" memorandum) is now tracked and
wired into `_on_create`. It arrived in the working tree pre-populated by
the user with `{{street}}`/`{{suburb}}`/`{{town}}`/`{{client_info}}`/
`{{date}}` tokens already placed in its first table and its signature
block — those didn't need any code-side work, `fill_docx_template`
picked them up for free. The "restricted building work" table (6 rows,
one per Scope item, each with a real checkbox content control) needed a
one-off migration exactly like the original PS1 checkboxes did — see
"Word filling" below.

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
├── PS1 Producer Statement orginal.docx  # untouched client original — KEEP, see below
└── LBP form.docx                    # working template — checkboxes/cells migrated in place, no "original" copy kept (see Word filling)

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
   `word_filler.fill_docx_template` for each of the **three** templates
   (Project register, PS1, LBP form — skipped individually if its
   template file is missing, which is how Specification/B2 Letter
   documents will slot in later, once their templates exist), then shows
   a summary `messagebox`, then calls `_reset_for_new_project()` which
   blanks every *project* field (job number, street/suburb/town, scope,
   PS1 fields, date, etc.) and jumps back to the General step — but
   leaves drive settings and the saved council list alone, since those
   are machine config, not project data.

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
separately as `bullet_lists={"scope": [...]}`. All three templates get
the *same* `bullet_lists["scope"]` (harmless no-op for LBP, which has no
`{{scope}}` token) — no special-casing needed between them now that it's
real paragraphs, unlike an earlier plain-text version that needed a
manually-injected leading `"\n"` for one template but not the other.

**Address → Street/Suburb/Town split (this handoff):** the General step's
single "Address" field is now three fields. The project folder name and
the Project register/PS1 templates' existing `{{address}}` token are
both fed from **Street only** (`build_project_folder_name` in
`folder_creator.py` was renamed `address` → `street` throughout, and
`_build_replacements()` sets `"address": street` — the token name in
those two templates wasn't touched, only what value it gets). Suburb and
Town are new `{{suburb}}`/`{{town}}` tokens, currently only consumed by
the LBP form.

**LBP form's "restricted building work" table (this handoff):** table 1
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

### Step 1 logic ([app/core/folder_creator.py](app/core/folder_creator.py))
Folder name = `"{Job Number} - {Street}"` (was `{Address}` before this
handoff's split — see "Address → Street/Suburb/Town split" above; every
function's `address` parameter was renamed `street`, no behavior change
beyond which GUI field feeds it). Engineer drive gets 6 fixed subfolders
(`01 Architectural` … `06 Consent Document`); PS1 Producer Statement.docx
and LBP form.docx are both generated *inside* `06 Consent Document`,
Project register.docx at the Engineer project root; two-phase
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
- **The PS1 checkbox migration pattern generalized cleanly to a second,
  differently-shaped template.** LBP form's checkboxes live inside a
  table (as `<w:sdt>` siblings of `<w:tc>`, not descendants of one) and
  needed matching empty table cells filled with tokens too, not just
  tags — same "inspect the real XML, don't guess" and "script it,
  verify on a copy, then run for real" workflow from the PS1 handoff
  worked unchanged. Confirmed end-to-end with a full `create_project_folders`
  + `fill_docx_template` smoke test against real (test) drives, not just
  unit-level checks.

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

1. **Manually click through the app end-to-end at least once.**
   Everything in this handoff (folder-conflict block, Edit Council,
   greyed checkboxes, Street/Suburb/Town split, LBP form) was verified
   either by code review, one static screenshot, or a *headless* smoke
   script that calls `folder_creator`/`word_filler` directly and inspects
   the resulting `.docx` — never by actually running the tkinter wizard
   and clicking through it, because an earlier attempt at simulating
   clicks/keystrokes closed the app unexpectedly (see "What Didn't
   Work" in the previous entry). Nothing suggests a bug, but this
   handoff can't claim the same real-GUI verification Steps 1–2
   originally got — worth the user doing one real click-through,
   especially opening the generated LBP form.docx in Word to confirm the
   checkboxes/table read correctly (they were only checked via
   python-docx, never visually in Word).
2. **Specification step** — completely undefined. Need the same
   treatment PS1/LBP got: the user will eventually provide a
   template/mockup; ask for the actual file, inspect its XML for any
   non-obvious formatting (checkboxes, bullets, highlights, tables)
   before assuming plain `{{token}}` substitution is enough.
3. **B2 Letter step** — same as above, undefined.
4. **Consent Document folder** (`06 Consent Document`) now gets PS1 and
   LBP form. The user mentioned other documents belong there too,
   mentioned only in passing early on — worth re-confirming what else,
   if anything, still needs to land there.
5. **Step 3 (website submission)** — completely unstarted, no URL, no
   auth method, no field mapping gathered yet. `web_filler.py` is an
   untouched stub.
6. **Packaging (PyInstaller)** — still deferred per the user's original
   preference (get functionality working first). Worth floating again
   now that Steps 1–2 are functionally complete, in case the user wants
   an early build to test on their own machine before Specification/B2
   Letter/Step 3 are done.
7. No automated tests exist (`tests/` is empty aside from `__init__.py`).
   Everything so far was verified via ad hoc scripts run through the Bash
   tool, not committed as reusable tests. Consider adding real pytest
   coverage for `folder_creator` and `word_filler` (the run-splicing and
   checkbox/bullet-list logic in particular is intricate enough to
   benefit from regression tests) if the user wants that investment.

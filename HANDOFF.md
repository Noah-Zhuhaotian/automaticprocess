# Handoff: automaticprocess

## Goal

Build a Windows desktop Python app (tkinter GUI, packaged as a Windows
installer via PyInstaller + Inno Setup - see "Packaging" below) with
three features, requested to be built one step at a time:

1. **Create folders** — auto-create a project folder on each of three NAS
   drives (Engineer, Drafting, Admin), with fixed subfolders on the
   Engineer drive.
2. **Fill Word** — auto-fill Word document templates (Project register,
   PS1 Producer Statement, LBP form, Calculation Statement,
   Specifications, B2 Letter) from one shared data-entry wizard.
3. **Fill timesheet website** — auto-submit the same data to a website
   that records work hours/project info. The target site is **MinuteDock**
   (https://minutedock.com) - implemented this handoff via its public REST
   API. There is no separate "fill the website" UI step for the sync
   itself; it rides along inside the same Create click and reuses data
   already collected earlier in the wizard, per the original plan - see
   "Feature 3: MinuteDock sync" below.

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
the user testing the app), `4a71507` (independent Compliance/Alternative
checkboxes, Site verification field, LBP/`{{scope}}` genuine bullet
lists, PS1's `{{scope}}` shading fix, LBP page break before "WAIVERS AND
MODIFICATIONS"), `2f19aec` (new "Inspection Schedule" wizard step for
PS1's Schedule of Inspections table - pick which of 7 typical items
apply, add one "Other" item, order everything with Move Up/Move Down;
template got the 5 previously-missing fixed items added; a real bug
where reordering changed the No. values but not the physical row
order was caught by the user's own click-through and fixed with
`_reorder_table_rows` - see prior handoff / that commit's message and
git history for the full per-item detail, since it's condensed here to
make room for later handoffs' own work, which builds directly on it),
`f538915` (unlimited Inspection Schedule "Other" items; Specification's
Grout field became a 3-option dropdown; B2 Letter's user-added
street/suburb/town tokens fixed via a general run-boundary-splitting fix
in `word_filler.py` - see that commit's own section below for detail),
`b004dbf` (MinuteDock API sync implemented as Feature 3; packaged the app
as a real Windows installer via PyInstaller + Inno Setup - see that
commit's own section below for detail), `e097e68` (Create runs in a
background thread with a "please wait" progress dialog instead of
freezing the window - see that commit's own section below for detail),
`b511755` (PS1 Input left-edge alignment polish), `76fe6ef` (added
USER_GUIDE.md, a non-technical user guide), `180dbb9` (README brought up
to date with Inspection Schedule/MinuteDock/packaging, which it hadn't
mentioned before), `09cfacc` (fixed MinuteDock's Project Name/Short Code
being smashed into one string - see that commit's own section below for
detail).

*This* handoff is **not yet committed** - MinuteDock sync and its
"Project is billable" setting both went from optional/user-choice to
required/fixed, on the user's own explicit request after using the app
for real. `app/config/settings.py`, `app/gui/main_window.py`,
`app/gui/steps/minutedock_step.py`, `app/gui/steps/review_step.py`,
`app/gui/steps/settings_step.py`, `README.md`, and `USER_GUIDE.md` are
modified in the working tree:

1. **MinuteDock sync is no longer optional.** Previously the MinuteDock
   Personal Access Token was an optional Settings field, and the
   "MinuteDock" wizard step (plus the sync call itself) only appeared/ran
   when a token was configured - the user wants MinuteDock sync to happen
   on every single Create, with no way to skip it. `SettingsStepMixin`
   gained `_settings_configured()` (replacing `_drives_configured()`),
   which now also requires the token, and both the first-run Settings step
   and the always-reachable Settings dialog block **Save** until all four
   fields (three drives + token) are filled in - the first-run step gained
   the token field + Test connection button it was previously missing (only
   the dialog had it). `main_window.py`'s `_build_step_list()` now appends
   the "MinuteDock" step unconditionally instead of gating it on
   `self.settings.get("minutedock_access_token", "")`.
   `review_step.py`'s `_on_create` correspondingly always builds
   `minutedock_args` and always calls `web_filler.sync_to_minutedock` -
   the `if token:` / `if minutedock_args:` guards are gone. Verified
   headlessly: an unconfigured settings dict blocks `_save_settings()`
   until the token is filled in too, and the rebuilt step list is exactly
   `General → ... → MinuteDock → Review & Create` with `Settings` gone
   once configured - see "What Worked".
2. **"Project is billable" is no longer a user-facing checkbox - every
   project is created billable=True, unconditionally.** The user found,
   using a real MinuteDock account, that unchecking "Project is billable"
   on MinuteDock's own web UI stops that project from accepting *any* time
   entries at all - not just "won't be invoiced," but time tracking
   against it breaks outright. Since the wizard's checkbox defaulted to
   checked anyway, exposing it as a toggle only gave the user a way to
   accidentally break time tracking for a project with no warning until
   someone tried to log hours against it later. Removed
   `minutedock_billable_var` entirely (was a `tk.BooleanVar` plus its
   `ttk.Checkbutton` in `minutedock_step.py`, and a reset line in
   `review_step.py`'s `_reset_for_new_project()`); `review_step.py` now
   sends `"billable": True` as a literal in `minutedock_args`, not read
   from a var. The MinuteDock step's two rate-mode radio buttons (`Use
   contact rates` / `Set a standard rate for this project`) are unchanged
   otherwise, just shifted up one grid row to fill the gap. Verified
   headlessly: `hasattr(app, "minutedock_billable_var")` is now `False`,
   and walking the step's widget tree after building it finds no widget
   with the text "Project is billable" anywhere.
3. **Docs updated to match** (`README.md`, `USER_GUIDE.md`) - both no
   longer describe MinuteDock sync or the billable setting as optional/
   toggleable; `USER_GUIDE.md`'s FAQ entry "Why isn't the MinuteDock step
   showing up?" (no longer a possible situation - it always shows now)
   was replaced with "Why won't Settings let me past it?", covering the
   token now being one of the required fields alongside the three drives.

Previous handoff's own changes (historical record, already pushed as
`09cfacc`) - MinuteDock's Project Name/Short Code were being smashed into
one string instead of using both fields as intended.
`app/core/minutedock_client.py`, `app/core/web_filler.py`, and
`app/gui/steps/review_step.py` were modified by that commit:

1. **The user noticed it on MinuteDock's own web UI**: a screenshot
   showed a Project with Name `"23432 - 217 Armagh Street"` and Short
   Code `"23432_-_217_armagh_street"` - MinuteDock had auto-slugified the
   *entire* combined name into the short code, since nothing was ever
   sent for that field. The fix isn't just "stop combining them" - it's
   sending each piece to the field MinuteDock actually has for it:
   `Project.name` = street only, `Project.short_code` = job number only
   (previously `find_or_create_project` never sent `short_code` at all).
2. **`find_or_create_project` gained a required `short_code` parameter**
   and now sends it in the create payload alongside `name`. More
   importantly, **the find-or-create match key changed from `name` to
   `short_code`** - the job number, not the street, is the actual stable
   unique identifier for a project (two unrelated jobs could plausibly
   share a street name over the years; job numbers don't repeat), so
   matching on it is more correct, not just a side effect of having the
   field available now. `_find_by_name` was generalized to
   `_find_by_field(items, field, value)` to support matching on either
   column without duplicating the same loop.
3. **`web_filler.sync_to_minutedock` gained a `project_short_code`
   parameter**, and `review_step.py`'s `_on_create` now passes
   `replacements["street"]` as `project_name` and
   `replacements["job_number"]` as `project_short_code` directly, instead
   of building one combined string via
   `folder_creator.build_project_folder_name` (that helper is still used
   for the actual folder name and the Word `{{address}}` token, which
   legitimately do want the combined form - only the MinuteDock call
   site changed).
4. **Verified the plumbing, not just the diff** - re-ran the same
   threaded-Create headless test used for the earlier progress-dialog
   work (fake token, real folder/document creation, real MinuteDock
   network call) and confirmed it still fails at exactly the same point
   with the same 403 message, meaning the new required `project_short_code`
   argument is wired through correctly end-to-end from the GUI with no
   `TypeError`. The actual Name/Short Code values MinuteDock stores
   couldn't be confirmed against a real account (no token available), so
   this still wants a real-account check - see "Next Steps".

Previous handoff's own changes (historical record, already pushed as
`e097e68`) - Create runs in a background thread with a "please wait"
progress dialog, instead of freezing the window for the whole operation.
`app/gui/steps/review_step.py` was the only file changed:

1. **The user noticed Create has a real wait (folder creation, six Word
   documents, and - if MinuteDock is configured - a network round trip)
   with zero feedback, and asked for something to show it's working, not
   stuck.** Root cause: `_on_create` ran entirely on the main/UI thread,
   so tkinter couldn't repaint or process any events for the whole
   duration - genuinely indistinguishable from a hang, especially once the
   MinuteDock network call could add a few seconds of pure network
   latency on top of the file I/O.
2. **Split into three pieces**, since tkinter itself is not thread-safe
   (only the main thread may touch widgets/variables): `_on_create`
   (main thread) gathers everything the work needs from tkinter
   variables into a plain-data `job` dict (this must happen before the
   background thread starts - reading a `tk.StringVar` from a
   non-main thread isn't safe either), starts a `threading.Thread`
   running `_run_create_job(job)`, and starts a polling loop
   (`_poll_create_result`, itself scheduled via `self.after`, purely on
   the main thread). `_run_create_job` is the same
   `folder_creator`/`word_filler`/`web_filler` logic as before, just
   fed from `job` instead of reading tkinter variables directly - all
   three are plain file-IO/network functions with no tkinter dependency,
   so they're safe to run off-thread. It reports its outcome (success,
   partial failure with what succeeded so far, or a hard folder-creation
   failure) by putting a small dict onto a `queue.Queue`, then
   `_on_create_done` (main thread, called once `_poll_create_result`
   sees something in the queue) does all the actual UI work - the
   messagebox text and control flow for every outcome (`cannot_create`/
   `error`/`partial`/`success`) is byte-for-byte the same as the old
   synchronous version, just relocated.
3. **`self.after(0, ...)` called directly from the worker thread raises
   `RuntimeError: main thread is not in main loop` on this Python
   version** - the first version of this fix tried that (a pattern often
   cited as "the standard way" to signal tkinter from a thread), and it
   only got caught because the new flow was actually run end-to-end
   headlessly (background thread does real folder/doc creation, a test
   loop calls `app.update()` until the result var changes), not because
   the pattern was independently known to be broken - see "What Didn't
   Work" for why this is a standing lesson about that specific claim.
   Fixed with a `queue.Queue`: the worker thread only ever calls
   `queue.put()` (genuinely thread-safe, no Tk/Tcl involvement at all);
   `self.after` is *only* ever called by code already running on the main
   thread (`_on_create` kicking off the first poll, and
   `_poll_create_result` rescheduling itself), never by the worker.
4. **A `ttk.Progressbar(mode="indeterminate")` in a small modal `Toplevel`**
   ("Creating project, please wait...") - indeterminate rather than a
   real percentage, since there's no reliable per-document/per-request
   progress signal to drive a determinate bar off (6 documents of very
   different sizes plus one network call). `grab_set()` and a no-op
   `WM_DELETE_WINDOW` handler while busy - the user can't close it or
   interact with the main window mid-Create, matching how
   `_show_success_dialog` already behaves. `next_button`/`back_button`
   are also explicitly disabled/re-enabled around the operation
   (`_set_busy`), on top of the dialog's own grab, since the grab alone
   wouldn't stop a stray Enter-key binding or similar from reaching the
   main window.
5. **The Review & Create step's own label text was also stale and
   actively wrong** - still described Step 2/3 as not-yet-implemented
   ("Coming once their templates/details are provided...") from a much
   earlier point in the project, visible on the exact screen this feature
   touches. Updated to describe what Create actually does today (six
   documents plus optional MinuteDock sync) while already in this file
   for the threading change.

Previous handoff's own changes (historical record, already pushed as
`b004dbf`) - MinuteDock API sync (Feature 3):
`app/core/minutedock_client.py` (new), `app/core/web_filler.py` (stub
replaced), `app/gui/steps/minutedock_step.py` (new),
`app/gui/steps/settings_step.py`, `app/gui/steps/review_step.py`,
`app/gui/main_window.py`, `app/config/settings.py`, and
`requirements.txt` were modified/added by that commit:

1. **The user identified the target timesheet website (MinuteDock) and
   provided its OpenAPI 3.1.1 spec**, plus a screenshot of MinuteDock's own
   "New Project" page (a "Project is billable" checkbox, "Use contact
   rates" vs "Set a standard rate for this project" radio + a `$/hour`
   field). They asked for two things beyond just "make it work": a place to
   enter login credentials, and that per-project rate control. Before
   writing any code, three genuinely open design questions were resolved
   with the user via `AskUserQuestion` (not guessed at, since MinuteDock's
   API only supports Bearer-token auth, not literal username/password):
   - **Auth**: a MinuteDock **Personal Access Token** (an OAuth access
     token the user generates once from their own MinuteDock profile →
     "Manage Access Tokens", ready to use immediately, no
     application-registration/authorization-code flow needed) - not a
     literal username/password, which the API doesn't support at all.
   - **Trigger**: automatic, inside the same "Create" click that already
     makes folders and fills Word docs - no separate "submit to website"
     step/button. This matches what `main_window.py`'s own module
     docstring already said was the intended design before Step 3 existed.
   - **Contact resolution**: match an existing MinuteDock Contact by the
     wizard's "Client info" field against `Contact.name`; create one
     automatically if no match.
   A full implementation plan (this exact breakdown) was written and
   approved via plan mode before any file was touched - see
   `C:\Users\NoahZ\.claude\plans\shimmering-popping-charm.md` for the
   original plan document if it's still around; its content is folded into
   this handoff entry.
2. **New `app/core/minutedock_client.py`** - a thin, business-logic-free
   wrapper around `https://minutedock.com/api/v1`. Every call sends
   `Authorization: Bearer <token>`. `find_or_create_contact`/
   `find_or_create_project` are genuinely **find-or-create**, not
   create-only: `_on_create` in `review_step.py` can plausibly run twice
   for the same job (e.g. retrying after an earlier Word-doc-fill failure
   left folders already created - see existing "Partial success" handling),
   and find-or-create means a retry never creates a duplicate Contact or
   Project. Matching is **exact, case-insensitive, trimmed** - deliberately
   not substring/"contains" matching, since e.g. "Smith" fuzzy-matching
   "Smith Family Trust" would silently attach a job to the wrong client.
   No pagination for `GET /contacts`/`GET /projects` in this version (a
   single small engineering firm's account is assumed to fit in one
   unpaginated page) - documented as a known v1 limitation in the module
   docstring rather than guessed at.
   **A real discrepancy between the OpenAPI spec and the live API was
   caught by actually calling it**, not just trusting the spec: the spec's
   documented error shape is `{"error": "...", "status": ...}`, but a real
   403 response (tested with a deliberately bogus token, a safe read-only
   call) came back as `{"status": "error", "message": "..."}` instead -
   `_request`'s error-message extraction checks both `error` and `message`
   keys for exactly this reason. Also note: MinuteDock's own "New Project"
   UI has a "Reference" text field with **no equivalent in the `Project`
   schema** (that's an Invoice-level field instead) - intentionally not
   sent anywhere, flagged in a comment so it isn't "fixed" into the wrong
   field later.
3. **`app/core/web_filler.py`'s long-standing `NotImplementedError` stub is
   gone** - `sync_to_minutedock()` is the business-logic layer on top of
   the client: find-or-create the Contact, then find-or-create the Project
   under it, return both.
4. **New "MinuteDock" wizard step** (`app/gui/steps/minutedock_step.py`,
   `MinuteDockStepMixin`) - a "Project is billable" checkbutton plus a
   "Use contact rates"/"Set a standard rate for this project" radio gating
   a `$/hour` entry (same enable/disable-and-clear gating idiom as
   `waivers_step.py`'s `_on_waivers_required_change`). **Only appended to
   `self.steps` in `main_window.py`'s `_build_step_list()` when a
   MinuteDock token is configured** (`if
   self.settings.get("minutedock_access_token", "").strip():` - same
   conditional-step precedent as the first-run Settings step), so Step 3
   stays entirely invisible/optional for anyone who hasn't opted in.
   `_validate_minutedock_step()` also normalizes the rate to MinuteDock's
   required `CurrencyString` format (exactly 2 decimals, e.g. `"125.00"`)
   at validation time, so `review_step.py` never has to reformat it before
   sending.
5. **MinuteDock token field + "Test connection" button added to the
   Settings dialog** (`app/gui/steps/settings_step.py`'s
   `_open_settings_dialog` - the always-reachable header button, not the
   first-run-only step) - a masked (`show="*"`) `Entry` plus a button that
   calls `minutedock_client.test_connection` (`GET /accounts/current`) and
   shows success/error via `messagebox`, so a bad/mistyped token is caught
   immediately instead of silently failing at the very end of a Create
   click. **The header button itself was renamed "File path" → "Settings"**
   (`main_window.py`) once the dialog it opens covered more than drive
   paths - caught by the user after running the app for real ("I don't see
   where to set the API") - "File path" gave no hint an API token lived in
   there too. Persisted via the same
   `_save_drive_settings()`/`save_settings()` path as the drive paths (a
   harmless no-op write on the first-run step, which doesn't render this
   field at all).
6. **`review_step.py`'s `_on_create` syncs to MinuteDock last**, after
   folders and all six Word documents already succeeded, and only if a
   token is configured - skipped entirely otherwise. The MinuteDock
   Project's `name` reuses `folder_creator.build_project_folder_name(job_number,
   street)` verbatim (the exact same `"{job_number} - {street}"` string
   used for the folder name), so the same identifier ties folders/docs/
   MinuteDock together. **On `MinuteDockError`, this deliberately mirrors
   the existing per-document failure handling** (`messagebox.showwarning`
   with a "Partial success" title, `create_result_var` shows everything
   that *did* succeed, early `return` without calling
   `_reset_for_new_project()`) rather than inventing a new retry-button/
   pending-state mechanism - re-clicking Create for the same job already
   can't fully retry cleanly today (folder creation raises `FileExistsError`
   once folders exist), a known pre-existing limitation this feature
   doesn't attempt to solve, so a bespoke MinuteDock-only retry affordance
   would have been inconsistent with - and more complex than - what
   Word-doc failures already do. `_reset_for_new_project()` also resets the
   three MinuteDock vars back to their defaults (billable=True, rate
   mode="contact", rate="").
7. **`app/config/settings.py`**: added `minutedock_access_token` (default
   `""`); removed the long-dead `website_url` key (nothing read it, and
   MinuteDock's API has a fixed base URL - there's no "website URL" concept
   to configure). Old saved JSON with a stray `website_url` key is
   harmlessly ignored by `load_settings()`'s merge-over-defaults, no
   migration needed.
8. **`requirements.txt`**: uncommented `requests>=2.31.0` (already
   installed in the dev environment, confirmed via `python -c "import
   requests"` before relying on it) and dropped the `selenium` line
   entirely - browser automation was the alternative the user's decision
   ruled out, not a "maybe later" option worth leaving commented.
9. **Two bugs found by the user actually running the app**, both fixed:
   the header's "File path" button was renamed **"Settings"** (it opens a
   dialog that now covers more than drive paths, but nothing hinted the
   MinuteDock token lived in there too - see "What Didn't Work" for the
   full "我没有看到setting api的地方" story); and a **recurrence of the
   stale-`self.steps` bug** from an earlier handoff - saving a MinuteDock
   token via the Settings dialog persisted it correctly but didn't rebuild
   the step list the user was already looking at, so the new "MinuteDock"
   step didn't appear until a restart. Fixed with
   `_refresh_step_list_preserving_position()` (`settings_step.py`) - see
   "What Didn't Work" for why this is a second instance of a *documented*
   mistake, not a new one.
10. **Packaging** (PyInstaller onedir + Inno Setup) - the app is now a real
    installable `Setup.exe`, not just something run via `python main.py`.
    See "Packaging" below for the full writeup.
11. **PS1 Input's Council name row nudged right** (`ps1_step.py`) - the
    dropdown + "Add Council..."/"Edit Council..." buttons had a lot of
    empty space to their right (the row is only as wide as its own
    content, sitting left-aligned in a much wider input column shared with
    the full-width Description/Legal description/Site verification `Text`
    boxes below it). First tried `sticky="e"` (snap the whole row to the
    right edge of its grid cell) but that's an edge-anchor, not a nudge -
    the user wanted a small rightward shift, not full-right alignment, so
    it's `sticky="w"` (unchanged) plus `padx=8` on the row's own `grid()`
    call instead - the same fixed-offset idiom already used for the
    Description/Legal description/Site verification rows just below it.
    (A `padx=(0, 16)` → `padx=(0, 20)` tweak on the Scope-of-statement
    radio buttons' own spacing, a few lines down, rode along in the same
    diff - minor, unrelated spacing polish, not a functional change.)

`f538915`'s own changes (historical record, already pushed):

1. **The Inspection Schedule step's "Other" item is no longer limited to
   one - the user can Add/Remove any number of them.** Previously a
   single checkbox gated one fixed pair of Description/Time-frame
   entries; now an "Add Other" button appends a new entry (its own
   Description/Time-frame `ttk.Entry` pair plus a "Remove" button) to a
   dynamically-growing list, each entry getting a generated id
   (`other_1`, `other_2`, ...) that participates in `self.inspection_order`
   exactly like a fixed item's key - Other entries can be freely
   interleaved with fixed items in the Move Up/Down order, not just
   appended at the end. `self.inspection_other_items_by_id: dict[str,
   dict[str, tk.StringVar]]` replaces the old single
   `inspection_other_var`/`_description_var`/`_time_frame_var` trio (see
   [inspection_step.py](app/gui/steps/inspection_step.py)).
2. **The PS1 template needed no changes for this** - its existing single
   "Other" row already serves as a reusable *cloning prototype* rather
   than a single fixed slot: `word_filler.py` gained
   `_find_and_remove_table_row_template` (captures a deep copy of the row
   matching a literal token label, then removes the original
   unconditionally - it's never "kept" as-is anymore) and
   `_insert_dynamic_table_rows` (walks a full order list mixing existing
   rows' labels with new keys, cloning the captured template and setting
   its cells' text *directly* - no `{{token}}`s - for every new key,
   inserting each one at the right spot among the already-correctly-
   ordered fixed rows). Wired into `fill_docx_template` as three new
   parameters: `dynamic_table_row_templates`/`_order`/`_values` (all
   `dict[int, ...]`, keyed by table index, mirroring the existing
   `keep_table_rows`/`table_row_order` convention). See "Word filling"
   for the full mechanism and why fixed items still use the older
   token-based approach unchanged (no need to touch what already works).
3. **`review_step.py`'s `_on_create` documents list changed from
   positional tuples to dicts** (`{"template": ..., "output": ...,
   "keep_table_rows": ..., ...}`, read with `.get()`) - the PS1 entry
   alone now needs 6 of `fill_docx_template`'s optional table-editing
   parameters, all `None` for every other document; a 6-element
   all-`None`-except-one-row tuple was already unreadable before this
   handoff added 3 more fields on top. New `_build_inspection_table_data()`
   replaces `_inspection_row_order_labels()`, returning everything
   `_on_create` needs in one pass: which fixed rows survive, their
   relative order, the full interleaved order (fixed + Other), and each
   Other id's resolved `[No, description, time frame]` values.

4. **`Specifications.docx`'s "Grout" field (Specification step, MASONRY
   BLOCKWORK section) is now a fixed 3-option dropdown, not free-text
   MPa entry.** `grout_strength_var` used to be a plain `ttk.Entry`
   sharing the same rendering code as every other
   `SPECIFICATION_NUMERIC_FIELDS` entry; the field's label changed from
   "Grout, Zone C (MPa):" to "Grout strength:" and the template's own
   sentence used to hardcode " MPa (Zone C)" right after the token, so a
   plain number like "20" read as "...strength of 20 MPa (Zone C)...".
   The user wants the *whole* value (number + unit + zone) picked from a
   short list instead: `17.5 MPa (Zone B)`, `20 MPa (Zone C)`, `25 MPa
   (Zone D)` (the middle option's zone letter was corrected by the user
   directly in `constants.py` after an initial guess of "Zone B" for both
   the first two options). New `SPECIFICATION_DROPDOWN_FIELDS: dict[str,
   list[str]]` in `constants.py` maps a numeric field's `StringVar`
   attribute name to its option list; `specification_step.py` checks this
   dict when building each field and renders a `state="readonly"`
   `ttk.Combobox` instead of a `ttk.Entry` for any name present in it
   (falling back to `"disabled"` when its section is unchecked, matching
   the existing Entry gating idiom - Combobox just uses
   `"readonly"`/`"disabled"` instead of `"normal"`/`"disabled"`). The
   template itself needed a one-off migration (same copy-verify-then-
   real-file workflow as every other template surgery here): the run
   holding literal " MPa (Zone C), " right after `{{grout_strength}}` had
   its text changed to just ", ", since the dropdown's own value now
   supplies the unit and zone. No other `SPECIFICATION_NUMERIC_FIELDS`
   entry changed - they're all still plain numeric `Entry` fields, this
   was purely additive (one new dict, checked before falling back to the
   existing behavior).
5. **B2 Letter.docx gained `{{street}}`, `{{suburb}}`, `{{town}}` tokens
   (typed directly into the template in Word by the user, not by a
   migration script) - and they weren't substituting.** All three values
   were already flowing into the shared `replacements` dict from a much
   earlier handoff (see "Address → Street/Suburb/Town split" below) - the
   *dict* side needed zero changes. The actual bug was structural: Word's
   autocomplete/spellcheck had glued runs unevenly while the user typed
   `{{street}}, {{suburb}}, {{town}}`, leaving one run reading `"{{street}}, {{"`
   (a full token *plus* the next token's opening braces, all in one run)
   instead of a clean break after `}}`. `_run_range_for_span` requires a
   token's span to land exactly on run boundaries so only whole runs ever
   get spliced (see "Word filling" below); `{{street}}` sat at the *start*
   of that run but ended mid-run, so it silently fell into the "doesn't
   align, leaving as-is" branch and stayed as literal text in every
   generated `.docx`.
6. **Fixed generally in `word_filler.py`, not patched just for this one
   paragraph** - three new helpers (`_run_is_splittable`, `_split_run`,
   `_ensure_run_boundary`) let `_replace_in_paragraph` split a straddling
   run into two sibling runs with identical formatting (`rPr` deep-copied)
   right at the point a token needs a boundary, before re-checking
   alignment - a no-op wherever alignment already holds (i.e. every
   template/token that worked before this change still takes the exact
   same code path, confirmed by a full six-document regression run
   producing zero new warnings). Splitting only ever happens on a run
   that's provably safe to reconstruct through python-docx's own
   `Run.text` getter/setter round-trip (plain text plus
   tab/break/carriage-return/non-breaking-hyphen children only, checked by
   `_run_is_splittable`) - a run holding a drawing, field code, or
   anything else `Run.text` doesn't fully capture is left alone and still
   falls through to the "doesn't align" warning rather than risk silently
   dropping content. See "Word filling" for where this plugs into the
   existing right-to-left processing loop.

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
`.docx` with python-docx - see "What Worked". **Step 3 is now implemented**
against MinuteDock's REST API (find-or-create Contact/Project, synced on
the same Create click) - see "Feature 3: MinuteDock sync" below. The
failure path (bad/missing token) was verified end-to-end against the real
MinuteDock API this handoff; the success path (an actual Contact/Project
getting created/matched) has only been read-verified in code, not run
against a real account, since no real MinuteDock token was available while
building this - **still needs the user to run it once for real with their
own token** before considering it fully done. As of this handoff,
MinuteDock sync (and the drive paths) are required, not optional - see
the working-tree entry near the top of this file.

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
│       ├── inspection_step.py
│       ├── waivers_step.py
│       ├── specification_step.py
│       ├── b2_letter_step.py
│       ├── minutedock_step.py
│       └── review_step.py
├── core/
│   ├── folder_creator.py    # Step 1 — IMPLEMENTED
│   ├── word_filler.py       # Step 2 — IMPLEMENTED
│   ├── web_filler.py        # Step 3 — IMPLEMENTED (business logic: what to sync, in what order)
│   └── minutedock_client.py # Step 3 — thin MinuteDock REST API wrapper (no business logic)
├── config/settings.py    # settings persisted to %APPDATA%\AutomaticProcess\user_settings.json
└── utils/logger.py       # logs to console + %APPDATA%\AutomaticProcess\logs\app.log

resources/
├── automation.png    # source image for app_icon.ico (a personal photo, confirmed intentional - see "What Worked")
├── app_icon.ico       # generated from automation.png - see "Packaging"
└── templates/        # six working templates, no untouched-"original" copies anymore
    ├── Project register.docx
    ├── PS1 Producer Statement.docx
    ├── LBP form.docx             # checkboxes/cells migrated in place (see Word filling)
    ├── Calculation Statement.docx  # no tokens/tables - copied through as-is
    ├── Specifications.docx       # section-selectable (see Word filling)
    └── B2 Letter.docx            # table-row-selectable (see Word filling)

build_scripts/   # PyInstaller spec + Inno Setup script - see "Packaging"
├── automaticprocess.spec  # PyInstaller: onedir, windowed, bundles templates/icon
├── installer.iss          # Inno Setup: wraps the onedir build into Setup.exe
└── output/                # gitignored - AutomaticProcess-Setup.exe lands here
tests/           # empty — no automated tests, everything verified via ad hoc scripts
main.py          # root entry script: `python main.py`
requirements.txt # python-docx, pyinstaller, requests (MinuteDock API)
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
  Ps1StepMixin, InspectionStepMixin, WaiversStepMixin,
  SpecificationStepMixin, B2LetterStepMixin, ReviewStepMixin, tk.Tk)`
  composes every mixin via
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
   drive paths (`engineer_drive`/`drafting_drive`/`admin_drive`) *or* the
   MinuteDock token is unconfigured at launch (`_settings_configured()`,
   this handoff — all four are now required, not just the drives; see the
   working-tree entry near the top of this file). Always reachable
   afterwards via the **"Settings"** button (top-right of the header row —
   deliberately a plain `ttk.Button`, *not* a native OS menu bar; a menu
   bar was tried first and looked like an unclickable white strip on the
   user's machine).
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
4. **Inspection Schedule** (previous handoff `2f19aec`; unlimited "Other"
   items added this handoff) — PS1's "Schedule 3 - Schedule of
   Inspections" table. A checkbox per typical inspection item
   (`INSPECTION_ITEMS`, 7 items), at least one item required overall.
   **"Other" items are unbounded** - an "Add Other" button appends a new
   Description/Time-frame `ttk.Entry` pair (each with its own "Remove"
   button) to `self.inspection_other_items_by_id`, every entry's fields
   required once added. Selected fixed items and every Other entry all
   appear together in one `tk.Listbox` (`self.inspection_order`, the
   single source of truth for both inclusion and sequence, mixing fixed
   item keys with Other ids) with Move Up/Move Down buttons re-sorting it
   - Other items can be freely interleaved with fixed ones, not just
   appended at the end - that final order becomes the table's No. column
   and physical row order. See "Word filling" for the template mechanism.
5. **Waivers and Modifications** (previous handoff, `4814414`) — a step dedicated to the
   LBP form's "WAIVERS AND MODIFICATIONS" section: a Yes/No radio
   (`waivers_required_var`) for "Are waivers or modifications of the
   Building Code required?", gating a Building Code Clause `ttk.Entry`
   and a Waiver/modification-required `tk.Text` — both required and
   enabled only when "Yes" is chosen, disabled+cleared under "No" (same
   gating idiom as PS1's Compliance/Alternative fields:
   `_on_waivers_required_change` mirrors `_on_compliance_alt_change`).
   Reuses `LABEL_WIDTH`/the 3:7 column split from PS1 Input for visual
   consistency.
6. **Specification** — no longer a stub. One checkbox per top-level
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
7. **B2 Letter** — no longer a stub either. Three checkboxes
   (`B2_LETTER_MATERIALS`: Reinforced concrete, Structural timber, Mild
   steel structure), at least one required - controls which rows survive
   in B2 Letter.docx's Material/Means of Compliance/Notes table. Row
   *content* is fixed (the user said so explicitly - "内容不用变"); this
   step only toggles which rows appear. See "Word filling" for the
   removal mechanism.
8. **MinuteDock** — always appears in `self.steps` now (a previous
   handoff's conditional append on a configured token is gone - see the
   working-tree entry near the top of this file; MinuteDock sync is
   required, not optional, so its step can't be skipped either). A "Use
   contact rates"/"Set a standard rate for this project" radio gating a
   `$/hour` entry (same gating idiom as Waivers/Specification). No
   "Project is billable" toggle (this handoff removed it - every project
   is created billable=True unconditionally, since unchecking it on
   MinuteDock's own web UI stops time entries from being logged against
   that project at all, confirmed by the user against a real account).
   The rate controls mirror MinuteDock's own "New Project" web page, which
   the user screenshotted while requesting this feature originally. See
   "Feature 3: MinuteDock sync" below for what this data actually drives.
9. **Review & Create** — the Next button becomes "Create" on the last
   step. Runs `folder_creator.create_project_folders`, then
   `word_filler.fill_docx_template` for each of the **six** templates
   (Project register, PS1, LBP form, Calculation Statement,
   Specifications, B2 Letter — skipped individually if its template file
   is missing), then `web_filler.sync_to_minutedock` unconditionally (this
   handoff - previously only if a token happened to be configured; see
   "Feature 3: MinuteDock sync"), then shows a success dialog (see "Success dialog"
   below), then calls `_reset_for_new_project()` which blanks every
   *project* field (job number, street/suburb/town, scope, PS1 fields,
   inspection schedule selections/order, waivers fields,
   Specification/B2 Letter/MinuteDock selections, date, etc.),
   **rebuilds `self.steps`** (an earlier handoff - see the Repo note
   above; picks up Settings dropping out of the list if it was just
   completed this session, and MinuteDock dropping in/out if the token was
   just configured/cleared), and jumps back to the General step — but
   leaves drive settings, the saved council list, and the MinuteDock token
   alone, since those are machine config, not project data.

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
   **This handoff:** exact run-boundary alignment isn't guaranteed just
   because a token is hand-typed directly into Word (as opposed to
   migrated in by a script) - Word's autocomplete can leave a token
   sharing a run with unrelated neighboring text (see "B2 Letter.docx's
   street/suburb/town tokens" below). When `_run_range_for_span` first
   comes back `None`, `_replace_in_paragraph` now calls
   `_ensure_run_boundary` (which calls `_split_run` when the straddling
   run is safe to split - `_run_is_splittable` checks it holds only
   plain-text/tab/break content, nothing `Run.text` can't losslessly
   round-trip) for both the token's start and end position, then re-checks
   alignment once before giving up and logging the same "doesn't align"
   warning as before. A no-op for every already-aligned token - the fast
   path nothing else changed.
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

**B2 Letter.docx's `{{street}}`/`{{suburb}}`/`{{town}}` tokens (this
handoff):** the user typed these three tokens directly into the template
in Word themselves (no migration script involved, unlike every other
token addition in this project) as one run of text, `{{street}}, {{suburb}}, {{town}}`.
No `word_filler.py`/`review_step.py` change was needed for the *values* -
`street`/`suburb`/`town` were already in the shared `replacements` dict
since the earlier Address→Street/Suburb/Town split, and every document
gets the same dict. The tokens silently weren't substituting, though: a
token scan first (see "What Worked" for why this is always the first
move on a "should just work" report) found `{{street}}` sitting in a run
that also held the *next* token's opening braces (`'{{street}}, {{'`, one
run - Word's autocomplete evidently didn't break the run cleanly after
`}}`), so `_run_range_for_span` saw the token's end position landing
mid-run rather than on a boundary and silently left it as literal text.
Fixed generally, not just for this paragraph - see mechanism 1 in "Word
filling" above (`_ensure_run_boundary`/`_split_run`/`_run_is_splittable`).
Confirmed end-to-end against a real generated B2 Letter document: the
paragraph reads `"123 Main St, Riccarton, Christchurch"` with every run's
original bold formatting intact.

**Specifications.docx's Grout field is now a 3-option dropdown, not free
numeric entry (this handoff):** previously `grout_strength_var` was a
plain `Entry` like every other `SPECIFICATION_NUMERIC_FIELDS` field, and
the template's own sentence hardcoded " MPa (Zone C)" right after the
token. The user wants the whole value (number + unit + zone) chosen from
`17.5 MPa (Zone B)` / `20 MPa (Zone C)` / `25 MPa (Zone D)` instead - so
the template's hardcoded " MPa (Zone C), " text (a single run, confirmed
via a raw-run dump before touching it) was migrated down to just ", ",
and a new `SPECIFICATION_DROPDOWN_FIELDS: dict[str, list[str]]` constant
lets `specification_step.py` render a `readonly` `ttk.Combobox` instead
of an `Entry` for any field name present in it - one dict lookup added to
the existing field-building loop, every other numeric field is untouched.
Confirmed against a real generated Specifications document: "...minimum
28-day compressive strength of 20 MPa (Zone B), using coarse
aggregate..." (tested before the user's own follow-up edit corrected the
middle option's zone letter from B to C in `constants.py` - the mechanism
itself doesn't care what the option strings say, so this remains valid).

**PS1's "Schedule 3 - Schedule of Inspections" table (this handoff) - the
same row-removal idea, but matched on a *different* column, plus a
per-row order token:** the table only had 2 of the 7 typical inspection
items hardcoded as plain text (no tokens at all) before this handoff - the
other 5, plus a new free-text "Other" row, were added by a one-off
migration script (same copy-verify-then-real-file workflow as every other
template surgery here), each row a deep-copy of the existing Subsurface
row so its Verdana/8pt/shaded-No.-cell formatting carries over exactly.
Every row's No. cell is now a per-item token (`{{inspection_<key>_no}}`)
instead of the old hardcoded "1"/"2" - **`_remove_unselected_table_rows`
gained a `label_column` parameter (default 0, so B2 Letter's call site is
unaffected)** because this table's *first* column is the one thing that's
never stable (it's the order the user picks), so row-selection has to
match on the **Item of inspection** column (`label_column=1`) instead -
wired through `fill_docx_template` as a new
`keep_table_row_label_columns: dict[int, int] | None` parameter, applied
alongside the existing `keep_table_rows` dict. The "Other" row's Item
cell holds the literal text `{{inspection_other_description}}` in the
template - since row-matching runs *before* token replacement, that's
still exactly what the cell reads at match time, so `INSPECTION_OTHER_LABEL`
(in constants.py) is set to that same literal string rather than a plain
word like "Other" - **a first attempt used the plain word "Other" as a
match-only sentinel, assuming the token substitution would separately
overwrite it, but nothing ever put the token there in the first place, so
the literal word "Other" silently survived into real output instead of
the user's typed description** (caught by the end-to-end headless test
before this shipped, not by inspection - see "What Didn't Work"). Order
numbers themselves come from `_build_inspection_replacements()` in
review_step.py, one `str(position)` per key in `self.inspection_order`
(1-based, in the user's chosen order) - deliberately not derived from
`self.inspection_vars` at replacement time, since only `inspection_order`
(built and reordered by the new step's Move Up/Down buttons) records the
user's actual chosen sequence.

**Assigning the right number to a row is not the same as the row being in
that position** - the first version stopped there, and the user's own
click-through immediately caught it: numbers were correct but the table's
physical row order stayed exactly as the template laid it out (Subsurface,
Waffle, Floor diaphragm, ... Other), since `_remove_unselected_table_rows`
only ever deletes, never reorders. A new `_reorder_table_rows` (same file)
walks a table's surviving `<w:tr>` elements, builds a `label → <w:tr>` map
(same `label_column` idea as removal), then re-parents each one via
`.addnext()` in the order given, right after `_remove_unselected_table_rows`
and before token replacement - `.addnext()` on an *existing* element
moves it (lxml elements only ever have one parent) rather than creating a
duplicate, so no new mechanism was needed beyond what `_insert_bullet_
paragraph_after` already relies on for the same reason. Wired through
`fill_docx_template` as `table_row_order: dict[int, list[str]] | None`,
using `keep_table_row_label_columns` for the column exactly like
`keep_table_rows` does. (`review_step.py`'s translation point for this
was `_inspection_row_order_labels()` at the time - see below for what
replaced it once "Other" stopped being a single fixed row.)

**"Other" items are unlimited (this handoff) - the fixed-item mechanism
above is unchanged, dynamic rows are a separate, additional mechanism
layered next to it:** rather than extend the token-per-slot approach to
some arbitrary N "Other" tokens, the template's existing single "Other"
row (Item cell still holding the literal text
`{{inspection_other_description}}`) is now treated purely as a **cloning
prototype**. `_find_and_remove_table_row_template` runs *before* any other
row surgery - finds the row matching a literal label, deep-copies it, and
unconditionally removes the original (it's never "kept" as one of the
survivors anymore, unlike the fixed items). `_insert_dynamic_table_rows`
then runs *after* `_remove_unselected_table_rows`/`_reorder_table_rows`
have settled the fixed rows into their correct relative order: it walks a
full `order` list that mixes existing rows' labels (fixed items - just
skipped past, already correctly positioned) with brand-new keys (Other ids
- not skipped, since they were never a row) that only exist in a `values`
dict, cloning the captured template and writing each new key's `[No,
description, time frame]` **directly into the cells as literal text - no
{{token}}s at all**, immediately after whichever row currently precedes
it. This is what makes Other items able to sit *anywhere* in the final
order, including between two fixed items, rather than only ever being
appended at the end. `fill_docx_template` gained three more parameters for
this - `dynamic_table_row_templates`/`_order`/`_values`, all
`dict[int, ...]` keyed by table index like the existing table parameters.
`review_step.py`'s `_build_inspection_table_data()` replaced
`_inspection_row_order_labels()`, computing all four pieces
`_on_create` needs in one pass over `self.inspection_order`: which fixed
items' labels survive (`keep_table_rows`), their relative order
(`table_row_order`), the full interleaved order mixing fixed labels with
Other ids (`dynamic_table_row_order`), and each Other id's resolved
`[No, description, time frame]` (`dynamic_table_row_values`) - since a
`str(position)` No. value is computed once, in the same loop, for
*every* selected item regardless of whether it's fixed (goes into a
`{{token}}`) or Other (goes directly into `values`), there's no risk of
the two numbering schemes drifting apart.

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

### Feature 3: MinuteDock sync ([app/core/minutedock_client.py](app/core/minutedock_client.py), [app/core/web_filler.py](app/core/web_filler.py))

Two layers, same split as Step 2's `word_filler.py`/`review_step.py`:
`minutedock_client.py` is a thin, dependency-free wrapper around
`https://minutedock.com/api/v1` with **no business logic** (auth header,
JSON in/out, error handling only); `web_filler.py`'s `sync_to_minutedock()`
is the business logic on top of it (what to find-or-create, in what
order). Authenticates with a **Personal Access Token** the user generates
once from their own MinuteDock profile ("Manage Access Tokens") and pastes
into Settings - sent as `Authorization: Bearer <token>` on every request.
`_on_create` in `review_step.py` attempts this *after* folders and all six
Word documents already succeeded, unconditionally - the token is a
required Settings field (see the working-tree entry near the top of this
file), so by the time this step is reachable at all one is guaranteed to
be present; there's no longer a skip-if-not-configured branch here (there
was, before this handoff).

**Find-or-create, not create-only**, for both the Contact and the
Project - `find_or_create_contact`/`find_or_create_project` each do a
`GET` first and only `POST` on a miss (via the shared `_find_by_field`
helper). This matters because `_on_create` can plausibly run twice for
the same job (the existing "Partial success" pattern for a Word-doc-fill
failure leaves the wizard state as-is rather than resetting, so a user
could very reasonably click Create again) - without find-or-create, a
retry would create duplicate MinuteDock records every time.

**Contact** matches on `name` (exact, case-insensitive, trimmed - not
substring, since e.g. "Smith" fuzzy-matching "Smith Family Trust" would
silently attach a job to the wrong client), fed straight from the General
step's `client_info_var` (free text, already existed - no new field
needed).

**Project** matches on `short_code`, *not* `name` (fixed after a
follow-up bug report - see `09cfacc`'s own section above for the full
story): `name` = street only, `short_code` = job
number only - previously both were smashed into one combined string
(`folder_creator.build_project_folder_name(job_number, street)`,
e.g. `"1234 - 211 Ferry Rd"`) sent only as `name`, with nothing ever sent
for `short_code` - MinuteDock's own UI then auto-slugified that entire
combined name into the short code field on its own, which is not what
either field is supposed to contain. The job number, not the street, is
the real stable unique identifier for a project (two unrelated jobs could
plausibly share a street name over the years), so matching find-or-create
on `short_code` is more correct, not just a side effect of the field
being available now. `folder_creator.build_project_folder_name` is still
used as-is for the actual folder name and the Word `{{address}}` token,
which legitimately do want the combined form - only the MinuteDock call
site changed.

**Billable is always `True`, not user-facing** (this handoff - see the
working-tree entry near the top of this file for why). **Rate** comes
from the MinuteDock wizard step's two remaining controls (see "GUI:
wizard steps" above); `standard_rate_dollars` is only sent when the user
picked "Set a standard rate" - never sent when they picked "Use contact
rates", so MinuteDock's own contact-level default isn't overridden by
accident.

**No pagination** for `GET /contacts`/`GET /projects` in this version - a
single small engineering firm's account is assumed to fit in the API's
default page size (500). Documented as a known limitation in
`minutedock_client.py`'s module docstring rather than guessed at; would
need a real pagination loop added to a future `_get_all`-style helper if a
firm's contact/project list ever grows past that.

**No "Reference" field** - MinuteDock's own "New Project" web UI (which
the user screenshotted) has a "Reference" text box, but the `Project`
schema has no equivalent (that's an Invoice-level field instead in the
OpenAPI spec) - there's nothing to send it to, so it's intentionally
omitted, with a comment in `minutedock_client.py` explaining why, so a
future reader doesn't go looking for where it "should" be wired up.

**No budget support** - the screenshot's "Set a budget" section (type/
frequency/target) is deliberately not implemented. Asked explicitly after
the first version shipped ("the UI doesn't have a place for me to fill in
budget") and confirmed with the user via `AskUserQuestion` that it's not
wanted for now - not an oversight, a confirmed scope decision. If it's
ever wanted, `Project`'s schema already has `budget_type`/
`budget_frequency`/`budget_target` (see `_BudgetProperties` in the OpenAPI
spec) ready to wire into `find_or_create_project`.

**On failure** (`MinuteDockError` - network issue, bad token, 4xx/5xx),
`_on_create` shows the exact same "Partial success" `messagebox.showwarning`
+ early-`return`-without-reset pattern already used for a Word-doc-fill
failure, rather than a bespoke MinuteDock-specific retry mechanism. This
was a deliberate simplicity choice: re-clicking Create for the same job
already can't cleanly retry today regardless of *which* step failed
(`folder_creator.create_project_folders` raises `FileExistsError` once
folders exist), so a special retry-button/pending-state system just for
MinuteDock would have been inconsistent with - and more complex than -
what every other failure in this same method already does. If proper
retry-without-recreating-folders is ever wanted, it's a single
cross-cutting improvement that would help every step in `_on_create`, not
a MinuteDock-only fix.

**A real discrepancy between the OpenAPI spec and the live API was caught
by actually calling it, not by re-reading the spec harder**: the spec
documents the error response shape as `{"error": "...", "status": ...}`,
but a real 403 response (from `test_connection` with a deliberately bogus
token - a safe, read-only smoke test) actually came back as `{"status":
"error", "message": "..."}` instead. `_request`'s error-message extraction
checks both `error` and `message` keys for exactly this reason - trusting
the spec alone would have produced a raw-JSON-text error message instead
of the human-readable one. See "What Worked" for why this generalizes into
a standing lesson about API integrations.

### Packaging ([build_scripts/](build_scripts/))

Two tools, two build steps, documented in full in
[build_scripts/README.md](build_scripts/README.md) (build commands,
one-time setup) - this section covers the *why* behind the choices.

**PyInstaller (`automaticprocess.spec`) → Inno Setup (`installer.iss`).**
PyInstaller alone only produces an exe or a folder, never a real
installer (Start Menu shortcut, "Apps & features" uninstall entry) - Inno
Setup wraps whatever PyInstaller produces into a proper `Setup.exe`. The
user explicitly asked whether a `.msi` was possible; the honest answer is
PyInstaller can't produce one directly either way, and the real choice is
between WiX (produces a literal `.msi`, more config) and Inno Setup
(produces a `Setup.exe` that behaves identically for the end user -
wizard, shortcuts, uninstall entry). The user confirmed they don't need a
literal `.msi` specifically, just the installer *experience* - Inno Setup
chosen for that reason, discussed and confirmed via `AskUserQuestion`
before any build config was written.

**Onedir, not onefile, once Inno Setup is doing the "one file to
distribute" job.** PyInstaller's onefile mode exists specifically so you
can hand someone a single exe - but once that exe is going to be
permanently installed to `Program Files` by a real installer anyway,
onefile's self-extract-to-a-temp-folder-on-every-launch behavior only
costs startup time and antivirus-false-positive risk, with no upside left
to offset it. Onedir starts faster and is easier to debug (an actual
folder of files, not a runtime-extracted temp directory). This trade-off
was explained to the user (see chat) before picking onedir, not assumed.

**`app/gui/constants.py`'s `TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent
/ "resources" / "templates"` needed zero code changes to keep working
frozen** - confirmed empirically, not just reasoned about, since PyInstaller
patches `__file__` for frozen modules to a synthetic-but-consistent path
under `sys._MEIPASS` specifically so this common pattern keeps working.
Verified with a small standalone diagnostic script/build (imported
`app.gui.constants`, printed `TEMPLATES_DIR`/`.exists()`/directory
listing, built as its own tiny onedir exe with the same `--add-data`
mapping, ran it, read the output, then deleted the whole throwaway
build) - see "What Worked" for why this was worth doing instead of
trusting the reasoning alone.

**`app/utils/logger.py` needed one real code change**:
`StreamHandler(sys.stdout)` would raise the moment anything got logged in
a windowed (`console=False`) build, since `sys.stdout` is `None` (not
just closed/redirected) when there's no console attached - now guarded
with `if sys.stdout is not None:`. Found by reasoning about the
`--windowed` flag's known implications *before* building (not by hitting
the crash first) - the file-handler logging (`%APPDATA%\AutomaticProcess\logs\app.log`)
was always going to be the real log destination for a windowed build
anyway, so the console handler is now simply skipped rather than
attempted-and-crashing when there's nothing to write to.

**`resources/app_icon.ico`** was generated from a user-supplied PNG
(`resources/automation.png`) via Pillow: padded to a square canvas (the
source was 125×130, not square), then **upscaled to 256×256 before
saving** - Pillow's ICO writer only emits requested sizes that are `<=`
the source image's own size, so skipping the upscale silently dropped the
256×256 frame Windows uses for large-icon views, leaving 128×128 as the
largest available size. Caught by inspecting the saved `.ico`'s own
`.info["sizes"]` after the first attempt, not assumed correct - see "What
Worked" for the "the source photo is a personal photo of two people, not
a logo" confirmation that came before any of this.

**Testing the packaged build for real, not just trusting the build logs said "Successful compile."**
The exe was actually launched (via a screenshot, confirming the window
opens, no console flashes behind it, and the file log shows
`Application starting` with no crash) and the installer was actually run
end-to-end - install (non-elevated throwaway variant, to avoid needing an
interactive UAC approval this session couldn't provide), confirm the exe
launches from the installed location, then uninstall and verify zero
leftover files/shortcuts/registry keys. The *real* `installer.iss`
(admin-required, installs to `Program Files`, as a normal Windows
installer should) was deliberately **not** run by this session - UAC
elevation exists specifically to require a human, so the final real-world
verification of `AutomaticProcess-Setup.exe` is left for the user to run
themselves (see "Next Steps").

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
- **`_remove_unselected_table_rows`'s "match on a stable column before
  replacement" idea generalized to a table whose *first* column isn't
  stable** (PS1's Inspection Schedule - the No. column is exactly the
  thing the user controls, via reordering). Adding one `label_column`
  parameter (default 0, so B2 Letter's existing call site needed no
  change) was enough - didn't need a new mechanism, just matching on
  column 1 instead of 0 for this one table. Worth checking for this same
  shape (first column unstable, another column isn't) before reaching for
  something heavier if a future table needs row-selection.
- **The end-to-end headless test caught a real bug that template
  inspection alone would have missed** - see "What Didn't Work" for the
  Inspection Schedule "Other" row's literal-"Other"-never-replaced bug.
  Worth repeating: build the actual `.docx` and read back the specific
  cell that was supposed to change, not just confirm the migration script
  ran without error.
- **The user's own click-through caught a bug the headless test's own
  scripted reordering didn't surface** (numbers assigned correctly but
  table rows never physically moved - see "What Didn't Work"). The
  headless test *did* exercise `_move_inspection_item` and reordering
  logic, but only checked the final `self.inspection_order` list and the
  No. token values, never the physical row sequence in the generated
  `.docx` - so it verified the *input* side of the reorder feature
  thoroughly but not the *output* rendering, which is exactly the kind of
  gap a real user looking at the real table catches immediately and a
  script checking data structures doesn't. Confirms the standing "keep
  having the user click through" lesson from earlier handoffs, but this
  time the gap was in what the automated test bothered to *assert*, not
  in what state it was willing to *set up* - worth designing table/order
  verification specifically around "does the Nth physical row equal the
  Nth expected item," not just "is the right value stored somewhere."
- **Re-checking a "just replace the token" report against the actual raw
  XML before believing it's simple.** The B2 Letter street/suburb/town
  request sounded like it needed nothing beyond adding three keys to a
  dict that already existed - dumping the paragraph's actual runs first
  (instead of assuming it would just work) found the real, structural
  cause (a run straddling two tokens) in one step, the same "inspect the
  XML, don't guess" instinct from the original PS1 checkbox/bullet work
  paying off again on a much smaller case.
- **A full six-document regression run (not just the one changed
  template) is the right bar for any change to `_replace_in_paragraph`
  specifically**, since it's the one mechanism every template and nearly
  every token goes through - ran the real `MainWindow` end to end with
  every field populated after adding the run-splitting fallback and
  confirmed zero new "does not align"/other warnings anywhere, not just
  that the B2 Letter paragraph in question now reads correctly.
- **Using plan mode for a genuinely multi-file, multi-decision feature
  (MinuteDock sync) instead of just starting to code.** Three real design
  questions (auth method, when to trigger the sync, how to resolve a
  Contact) were resolved with the user via `AskUserQuestion` *before* the
  plan was even drafted, then a full file-by-file plan was written and
  approved via `ExitPlanMode` before any file was touched. Caught scope
  creep before it happened, not after: the plan's own first draft (from a
  delegated Plan agent) proposed a bespoke retry-button/pending-state
  mechanism for MinuteDock failures, which got simplified back down to
  mirroring the *existing* Word-doc-failure pattern once it was clear the
  same "can't retry without recreating folders" limitation already existed
  and wasn't being solved for Word docs either - catching that during
  planning was far cheaper than catching it after writing a whole
  parallel retry system.
- **Testing an API integration against the real, live endpoint - even
  before writing any GUI code - caught a real spec-vs-reality mismatch
  that no amount of re-reading the OpenAPI spec would have.** A one-line,
  safe, read-only smoke test (`test_connection` with a deliberately bogus
  token) revealed the actual 403 error body used `{"status": "error",
  "message": ...}`, not the spec-documented `{"error": "...", "status":
  ...}`. Fixed by checking both keys in `_request`'s error extraction.
  **When integrating a third-party API, exercise at least one real call
  (a safe, side-effect-free one like a bad-auth check) as part of building
  the client, don't just trust the spec document.**
- **Find-or-create (not create-only) for both records synced to
  MinuteDock, decided during planning rather than added reactively after
  a duplicate-creation bug report.** The project's own existing "Partial
  success" pattern (leaves wizard state as-is on failure, doesn't force a
  reset) already made a same-job re-Create a realistic scenario before this
  feature existed - recognizing that during planning (not after someone
  hit it) meant find-or-create was designed in from the start instead of
  patched on later.
- **Actually opening the icon source file before packaging it, instead of
  assuming a file named `automation.png` was a logo.** It turned out to be
  a personal photo of two people - rendered a preview and asked the user
  to confirm before it got baked into `resources/app_icon.ico` and shipped
  in every build. They confirmed it was intentional, but the check itself
  cost nothing and would have caught a real mistake (wrong file path, a
  private photo accidentally in the wrong folder) if the answer had been
  different.
- **Verifying a "should just work because of how PyInstaller handles
  `__file__`" claim with an actual frozen build, before trusting it for
  the real app.** Built a tiny throwaway diagnostic script into its own
  onedir exe (same `--add-data` mapping as the real spec), ran it, read
  back `TEMPLATES_DIR`/`.exists()`/the actual file listing, *then* deleted
  the whole throwaway build once confirmed - cheaper and more conclusive
  than either assuming the reasoning was right or debugging a "why can't
  the packaged app find its templates" report after the fact.
- **Recognizing when an OS security prompt (UAC) is the actual point,
  not an obstacle to script around.** The real `installer.iss` requires
  admin rights by design (a normal Windows installer experience) - rather
  than trying to suppress/bypass that to get a fully-automated test, a
  throwaway `PrivilegesRequired=lowest` variant was built just to verify
  the Inno Setup *script's own logic* (Files/Icons/uninstall sections)
  non-interactively, and the real admin-required installer was explicitly
  left for the user to run themselves (see "Next Steps") - the two have
  different jobs: one verifies the script doesn't have a bug, the other is
  the actual real-world acceptance test only a human can give.
- **Even a real, admin-free non-interactive install/uninstall cycle is
  worth actually running, not just skimming the Inno Setup docs.** The
  first attempt at running the test installer via the Bash tool's `&`-style
  background launch returned immediately with no log file - Inno Setup
  installers can re-launch themselves as a child process, so the shell's
  "it exited" wasn't the same as "the install finished." Switched to
  PowerShell's `Start-Process -Wait` (blocks until the *actual* install
  process, not just the launcher, completes) and got a real log
  confirming success. Then ran the generated uninstaller and checked
  `Test-Path` on every artifact (install dir, Start Menu shortcut, Desktop
  shortcut, registry uninstall key) - all four, not just the obvious one -
  before considering the round-trip verified.
- **Actually running the threaded Create flow headlessly (not just eyeballing
  the diff) caught a real `RuntimeError` the first version would have hit on
  every single MinuteDock-enabled Create.** The test drove the exact real
  path: called `app._on_create()`, confirmed the button disabled/dialog
  shown/result-var-still-empty *immediately* (proving the call itself
  doesn't block), then looped `app.update()` until the background thread's
  outcome landed, then checked the final state (button re-enabled, dialog
  gone, files actually on disk, wizard reset on success / left alone on
  partial failure). That immediate-return check specifically is what a
  "does the final state look right" test would have skipped straight past -
  it's the difference between "eventually correct" and "actually
  non-blocking," which was the entire point of the feature.

## What Didn't Work / Avoid Repeating

- **Calling `self.after(0, callback)` directly from a background thread to
  hand a result back to tkinter.** This is widely cited as *the* standard
  cross-thread signaling idiom for tkinter, and the first version of the
  Create-threading fix used it - it raises `RuntimeError: main thread is
  not in main loop` on this project's Python version (3.13) the moment the
  worker thread calls it, because `Widget.after()` internally calls
  `self.tk.createcommand(...)` to register the callback, and CPython's
  tkinter added a same-thread check around that call. **Confirmed by
  actually running the threaded flow**, not by re-reading tkinter's docs
  harder - the failure only showed up mid-test, as an exception logged
  from the background thread while the main test loop kept polling
  (`app.update()`) for a result var that would now never arrive without
  the fix. The actually-safe pattern: the worker thread only ever touches
  a `queue.Queue` (`.put()`, genuinely thread-safe, no Tk/Tcl call
  involved at all); `self.after` itself is only ever invoked by code
  already running on the main thread, polling that queue on a short
  interval and rescheduling itself. **If a future feature needs a
  background thread to report back to tkinter, reach for `queue.Queue` +
  a main-thread `self.after` poll loop directly - don't reach for
  `widget.after()` from the thread itself, even though it's the pattern
  most commonly recommended online.**
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
- **The exact same class of bug recurred for the MinuteDock step's
  conditional inclusion, in a new spot the earlier fix didn't cover.**
  `_open_settings_dialog`'s `on_save()` persisted a newly-entered
  MinuteDock token correctly, but never rebuilt `self.steps` - so the
  "MinuteDock" step didn't appear until the app was restarted, even though
  `_build_step_list()`'s conditional (`if
  self.settings.get("minutedock_access_token", "").strip():`) was
  correctly written and the earlier `_reset_for_new_project()` fix for
  this exact issue already existed in the codebase as a *known pattern to
  apply*. Caught immediately by the user actually running the app
  ("我没有看到这一步" after saving a token, on a real "Step 7 of 7" Review
  & Create screenshot with no MinuteDock step in sight) - a second
  reminder that this specific mistake (state derived from settings,
  computed once, not re-derived when settings change mid-session) is easy
  to reintroduce even with the earlier instance documented right here in
  this file. Fixed with a new `_refresh_step_list_preserving_position()`
  (`settings_step.py`), called from `on_save()`: unlike
  `_reset_for_new_project()` (which always lands back on a fixed step,
  "General"), the Settings dialog can be opened from *any* step, so this
  rebuilds `self.steps` and then finds the *same step by title* in the
  rebuilt list (falling back to clamping the index if that title
  vanished) rather than assuming a fixed destination or a stable index -
  confirmed by a headless test that opens the dialog equivalent while
  sitting on "Review & Create" with no token, saves one, and checks both
  that "MinuteDock" now appears in `self.steps` *and* that the user is
  still looking at "Review & Create" (now correctly numbered), not
  silently bounced elsewhere. **Any future step made conditional on a
  Settings value needs to double-check every place that value can be
  changed - not just the one call site an earlier bug happened to get
  fixed at - triggers a rebuild.**
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
- **A row-matching "sentinel" that isn't literally the token it's meant to
  be replaced by.** First version of the Inspection Schedule's "Other" row
  put the plain word "Other" in the template's Item-of-inspection cell,
  intending for the later token-replacement pass to overwrite it with
  `{{inspection_other_description}}`'s value - except nothing ever put
  that token *in* the cell, so "Other" just stayed as literal, permanent
  text in every generated PS1 document regardless of what the user typed.
  Caught by the end-to-end headless test (read back the actual cell text
  after a real `fill_docx_template` run), not by re-reading the migration
  script, which looked correct in isolation. Fixed by making the cell's
  literal template text the token itself
  (`{{inspection_other_description}}`) and matching rows on that exact
  string - row-matching runs *before* replacement, so the token text is
  still what's there to match on. **If a row/cell needs to be both
  "matched on" (before replacement) and "replaced" (after), the match
  target and the token must be the same string** - a separate
  human-readable sentinel that a later pass is "supposed to" overwrite is
  a trap unless something concrete actually wires that overwrite up.
- **A toggle handler that assumed every selectable key lives in the same
  `dict[str, tk.BooleanVar]`.** `_on_inspection_toggle(key)` originally
  read `self.inspection_vars[key].get()` to decide whether to add/remove
  from the order list - crashed with `KeyError: 'other'` the moment the
  Other checkbox (which uses its own separate `inspection_other_var`, not
  an entry in `inspection_vars`) called it. Fixed by having callers pass
  the resolved `selected: bool` in directly instead of the handler
  re-deriving it from a dict that doesn't cover every key. Caught
  immediately by the headless test (first thing exercised), before it
  ever reached the user.
- **Assuming a per-row token value is enough to represent row order,
  without physically reordering the rows.** First version of the
  Inspection Schedule feature computed the right `{{inspection_<key>_no}}`
  value for every selected item based on `self.inspection_order`, but
  `_remove_unselected_table_rows` only ever deletes non-surviving rows -
  it never touches the surviving ones' relative order, which stays
  exactly as laid out in the template. Result: reordering items in the
  GUI changed the *numbers* shown in a real generated PS1 document but not
  which row those numbers sat next to, e.g. "No. 1" next to Subsurface,
  "No. 4" next to Floor diaphragm, "No. 2" next to Hold down brackets -
  correct values, visibly wrong table. **The user caught this by actually
  looking at a generated document** (see "What Worked") - it slipped past
  the headless test because that test asserted on `self.inspection_order`
  and the token dict, never on the physical row sequence of the output
  `.docx`. Fixed with `_reorder_table_rows` (see "Word filling"). **A
  "user picks the order" feature needs the *rendered* order verified, not
  just the order value stored somewhere** - a plausible-looking correct
  token is not proof the visual result is correct when position and value
  are two separate things that both have to move together.
- **A headless test script's `module.load_settings = lambda: {...}`
  monkeypatch silently did nothing, and the test wrote real files to the
  user's actual configured NAS drive as a result.** `main_window.py` does
  `from app.config.settings import load_settings` at import time, which
  binds the *function object itself* into `main_window`'s own namespace -
  patching `app.config.settings.load_settings` afterward (the module the
  name was imported *from*) doesn't change what `main_window.py` calls,
  since it already holds its own separate reference. The fix is to patch
  the name where it's actually looked up - `app.gui.main_window.load_settings
  = lambda: {...}` (i.e. patch the *importing* module, not the *defining*
  one) - a standard `unittest.mock.patch` gotcha, but there's no mocking
  framework in this project's ad hoc test scripts to catch it by
  convention. The mistake wasn't caught until a second `MainWindow()` run
  raised `FileExistsError` for a folder that "shouldn't" have existed yet
  (see the B2 Letter/grout dropdown work above) - the first run had
  already silently created a real `"J123 - 123 Main St"` project (folders
  plus all six documents) on `D:\automaticeng\...`, the user's real
  configured Engineer/Drafting/Admin drives. Caught via
  `Test-Path`/`Get-ChildItem` against the real drive paths (read from
  `app.config.settings.load_settings()` directly, not assumed), confirmed
  it was exactly the test's synthetic data (job number `J123`, "Client
  X", etc. - nothing a real user would have entered) before deleting it
  with `Remove-Item -Recurse -Force`, then re-verified with `Test-Path`
  that all three drive locations were clean. **Any test script for this
  app must patch `load_settings` on the module that imported it
  (`app.gui.main_window.load_settings`), and should print/assert
  `app.settings.get("engineer_drive")` right after constructing
  `MainWindow` and *before* calling `_on_create()`, to confirm a temp
  directory is actually in play before anything gets written** - the cost
  of skipping that check is real writes to the user's real project
  drives, not just a wrong assertion in a throwaway script.

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
   own click-through over more coordinate-based automation. The
   Inspection Schedule step's Move Up/Move Down/single-"Other" flow was
   confirmed by the user's own click-through (`2f19aec`) - **this
   handoff's unlimited-"Other" Add/Remove buttons have only been driven
   programmatically so far** (calling `_add_inspection_other_item()`/
   `_remove_inspection_other_item()` directly), never actually clicked -
   worth another real pass, especially the visual layout once several
   Other rows stack up under the fixed checkboxes. **Also unclicked so
   far:** the Specification step's new Grout dropdown (readonly
   `ttk.Combobox` - confirmed programmatically that it builds/enables/
   disables correctly, never actually opened and picked from in a running
   window) and the B2 Letter street/suburb/town fix (confirmed via the
   generated `.docx`, not by looking at the document in Word itself). **Also
   unclicked:** the new MinuteDock step's checkbox/radio/rate-entry UI -
   only verified programmatically (see below). **Also unclicked:** the new
   "please wait" progress dialog for Create - headless testing confirmed
   the *mechanism* works (non-blocking, correct end state), but nobody has
   looked at whether the dialog is positioned sensibly over the main
   window, whether the indeterminate bar animates smoothly, or how it
   feels for a real multi-second MinuteDock network call.
2. **Consent Document folder** (`06 Consent Document`) now gets PS1, LBP
   form, Calculation Statement, Specifications, and B2 Letter - probably
   everything the user meant by "other documents belong there too" when
   that was mentioned in passing early on, but worth a quick
   confirmation now that the folder is this full rather than assuming.
3. **The user *did* run Step 3 against a real MinuteDock account since the
   last handoff, and it already caught a real bug**: Project Name and
   Short Code were both getting the combined "job number - street"
   string, since nothing was ever sent for `short_code` (see the
   working-tree entry near the top of this file, and "Feature 3:
   MinuteDock sync"). Fixed - `name` is now street only, `short_code` is
   now job number only, and find-or-create matches on `short_code`
   instead of `name`. **Still needs**: one more real Create against a real
   account to confirm the Project now shows up in MinuteDock's web UI
   with a clean Name ("217 Armagh Street") and Short Code ("23432")
   instead of the smashed-together version, and that a second Create for
   the same job number correctly finds/reuses that Project rather than
   creating a duplicate (the find-or-create match key changed, so this is
   worth re-confirming specifically, not just assuming the earlier
   find-or-create testing still covers it).
4. **Packaging is implemented but the real installer needs the user's own
   run.** `build_scripts/output/AutomaticProcess-Setup.exe` exists and its
   Inno Setup mechanics were verified via a throwaway non-admin variant
   (install → launch → uninstall → confirm zero leftovers - see
   "Packaging"), but the *real* installer requires admin/UAC, which this
   session couldn't approve non-interactively. **The user needs to
   actually run `AutomaticProcess-Setup.exe` once**, approve UAC, confirm
   it installs to `Program Files`, launches, has a working Start Menu/
   optional desktop shortcut, and uninstalls cleanly via "Apps &
   features." Also worth deciding: **code signing** - an unsigned exe/
   installer will very likely trigger a Windows SmartScreen "unrecognized
   publisher" warning on first run on someone else's machine (not tested
   here, since this was run locally where the file was just built, which
   Windows treats differently than a freshly-downloaded/copied file from
   another machine) - acceptable for now for an internal single-firm tool,
   but worth flagging before wider distribution. **Version bumps**:
   `MyAppVersion` in `installer.iss` is hardcoded `"1.0.0"` - bump it by
   hand for each new release for now; nothing currently ties it to a git
   tag or `constants.py`.
5. No automated tests exist (`tests/` is empty aside from `__init__.py`).
   Everything so far was verified via ad hoc scripts run through the Bash
   tool, not committed as reusable tests. `word_filler.py` in particular
   now has four structural mechanisms (token replace, checkbox toggle,
   bullet-list splice, section/row removal) intricate enough to benefit
   from real pytest regression coverage, and the headless `MainWindow`
   walkthrough scripts written this handoff would be a reasonable
   starting point to adapt into actual test cases, if the user wants
   that investment.
6. **This handoff's required-Settings/no-billable-toggle changes are only
   verified headlessly, not clicked through.** Confirmed programmatically:
   `_save_settings()` refuses to save with the token blank, the rebuilt
   step list always includes "MinuteDock" once configured, and the
   MinuteDock step's widget tree has no "Project is billable" control
   anywhere. **Not yet confirmed in a real running window**: that the
   first-run Settings step's new token field/Test connection button look
   right laid out under the three drive rows, that trying to click past an
   incomplete Settings step shows a sensible error (not just that the
   function returns `False`), and a full real Create against a real
   MinuteDock account with a project actually coming through billable with
   no way to have set it otherwise. Also: `build_scripts/output/`'s
   installer/zip/PDF were rebuilt from this handoff's code (see the
   working-tree entry near the top of this file) but not reinstalled/
   re-run by a human this session - same standing item as #4 above,
   worth combining into one real end-to-end pass rather than two separate
   ones.
7. **No script in the repo reproduces `build_scripts/output/USER_GUIDE.pdf`
   from `USER_GUIDE.md`** - it was regenerated this handoff by converting
   the Markdown to styled HTML (`python-markdown`) and printing that to
   PDF with a headless `msedge.exe --print-to-pdf`, run ad hoc through the
   Bash tool, the same way the previous session that first produced this
   PDF apparently did (no record of *that* process either - the file
   simply existed, gitignored, with no generating script committed
   anywhere). If this PDF needs regenerating again on a regular basis (not
   just after occasional `USER_GUIDE.md` edits), worth turning that ad hoc
   conversion into a real `build_scripts/make_user_guide_pdf.py` so it's
   reproducible instead of re-improvised each time.

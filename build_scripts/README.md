# Build scripts

Packages the app into a Windows installer: PyInstaller bundles the Python
app into a onedir (folder) build, then Inno Setup wraps that folder into a
single `Setup.exe` installer (Start Menu shortcut, optional desktop
shortcut, proper "Apps & features" uninstall entry).

## One-time setup

- PyInstaller: `pip install -r requirements.txt` (from the repo root).
- Inno Setup: https://jrsoftware.org/isdl.php (or `winget install
  JRSoftware.InnoSetup`). Installs `ISCC.exe` (the command-line compiler)
  to `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`.

## Release (what users get from "Check for updates")

Releases are built and published by GitHub Actions
(`.github/workflows/release.yml`, on a Windows runner) - nothing is
published from a local machine.

1. Bump `__version__` in `app/version.py` (e.g. `1.0.2` -> `1.0.3`), commit
   and push. The app only offers a release whose tag is newer than its own
   version.
2. Start the workflow, either:
   - push a tag whose message is the notes:
     `git tag -a v1.0.3 -m "What changed, for users"` then
     `git push origin v1.0.3` (the tag must be `v` + `__version__`), or
   - on GitHub: Actions -> Release -> Run workflow, type the notes (the tag
     is created from `__version__`).
3. The workflow builds (PyInstaller + Inno Setup, stamped with the
   version), makes `USER_GUIDE.pdf` (`make_user_guide_pdf.py`) and the zip,
   and publishes release `v<version>` with `AutomaticProcess-Setup.exe` +
   `AutomaticProcess-v<version>.zip`. It fails if the release already
   exists or the tag doesn't match the version. Progress/errors: the
   repository's Actions tab.

`AutomaticProcess-Setup.exe` is the asset name the app looks for
(`updater.SETUP_ASSET_NAME`) - don't rename it. The notes are shown to users
in the "Update available" prompt as plain text - write them for users and
don't use Markdown.

## Build only (local)

From the repo root (the version must be passed - the script refuses to
compile without it):

```
pyinstaller build_scripts/automaticprocess.spec
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" /DMyAppVersion=1.0.2 build_scripts\installer.iss
python build_scripts/make_user_guide_pdf.py      # optional: USER_GUIDE.pdf (pip install markdown)
```

Output: `build_scripts/output/AutomaticProcess-Setup.exe` - hand this one
file to whoever needs to install the app. It requires admin rights (installs
to `Program Files` by default) since that's the standard, expected
Windows-installer experience.

`build/`, `dist/`, and `build_scripts/output/` are all gitignored -
regenerate them from source, don't rely on stale binaries in these
folders being up to date with the current code.

## Notes

- **`automaticprocess.spec`**: onedir (not onefile) - see HANDOFF.md's
  "Packaging" section for why onedir was chosen once Inno Setup is doing
  the "one file to distribute" job instead of PyInstaller's self-extraction.
  Windowed (`console=False`, no console window), bundles
  `resources/templates/` and `resources/app_icon.ico`.
- **`installer.iss`**: `AppId` is a fixed GUID, not the app name - re-running
  the installer for a future version upgrades the existing install rather
  than creating a duplicate "Apps & features" entry. Never change it once
  real installs exist. `CloseApplications=force` plus a second `[Run]`
  entry (`Check: WizardSilent`, `runasoriginaluser`) make the in-app
  updater's silent install close the running app and reopen it afterwards
  as the signed-in user.
- **`resources/app_icon.ico`** / **`app_icon.png`**: drawn by
  `python build_scripts/make_icon.py` (folder + document + green check on
  a blue rounded square; colours at the top of the script). Each ICO size
  (16-256px) is drawn at 4x and scaled down so small sizes stay crisp. The
  .ico is the exe, installer and window title-bar icon (bundled into the
  build for the latter).

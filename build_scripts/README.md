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

## Build

From the repo root:

```
pyinstaller build_scripts/automaticprocess.spec
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" build_scripts\installer.iss
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
  real installs exist.
- **`resources/app_icon.ico`**: generated from `resources/automation.png`
  (padded to a square canvas, upscaled to 256x256 before Pillow's ICO
  writer runs, since it only emits sizes <= the source image - see git
  history for the exact commands if it ever needs regenerating from a
  different source image).

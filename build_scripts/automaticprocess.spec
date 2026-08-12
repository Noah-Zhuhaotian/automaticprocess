# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec - onedir (folder), windowed (no console popup),
bundles the six Word templates and the app icon.

Build from the repo root:
    pyinstaller build_scripts/automaticprocess.spec

Output lands in dist/AutomaticProcess/ (the whole folder is what gets
distributed - see build_scripts/installer.iss, which wraps this folder
into a single Setup.exe via Inno Setup).

Paths below are resolved relative to this spec file's own location via
SPECPATH (a name PyInstaller injects when exec'ing the spec), not the
current working directory, so this also works if `pyinstaller` is invoked
from somewhere other than the repo root.
"""

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    # Bundled at the same relative path ("resources/templates") that
    # app/gui/constants.py's TEMPLATES_DIR expects, since it's derived
    # from __file__ - PyInstaller keeps that layout intact under the
    # onedir root, so no code changes were needed for template lookup to
    # keep working in the packaged build.
    datas=[(str(ROOT / "resources" / "templates"), "resources/templates")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutomaticProcess",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "resources" / "app_icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="AutomaticProcess",
)

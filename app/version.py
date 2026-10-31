"""The app's version - the single source of truth.

build_scripts/release.ps1 reads it to stamp the installer (ISCC
/DMyAppVersion=...) and to name the GitHub release tag ("v" + version).
app/core/updater.py compares it with the latest release's tag, so bump it
for every release - an installer built with an old number is never offered
as an update.
"""

__version__ = "1.0.2"

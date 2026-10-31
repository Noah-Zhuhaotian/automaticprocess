"""The app's version - the single source of truth.

The release workflow (.github/workflows/release.yml) reads it to stamp the
installer (ISCC /DMyAppVersion=...) and to name the GitHub release tag
("v" + version).
app/core/updater.py compares it with the latest release's tag, so bump it
for every release - an installer built with an old number is never offered
as an update.
"""

__version__ = "1.0.3"

"""USER_GUIDE.md -> build_scripts/output/USER_GUIDE.pdf (styled HTML via
python-markdown, printed to PDF by headless Microsoft Edge).

Run from anywhere: python build_scripts/make_user_guide_pdf.py
Used by .github/workflows/release.yml; needs `pip install markdown`.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build_scripts" / "output" / "USER_GUIDE.pdf"
EDGE_PATHS = [
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microsoft/Edge/Application/msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #222; }
h1 { font-size: 20pt; color: #1F4E79; border-bottom: 2px solid #1F4E79; padding-bottom: 4px; }
h2 { font-size: 14pt; color: #1F4E79; margin-top: 22px; border-bottom: 1px solid #ccd; padding-bottom: 2px; }
h3 { font-size: 11.5pt; color: #2E5C8A; margin-top: 16px; }
h2, h3 { page-break-after: avoid; }
code { font-family: Consolas, monospace; background: #f2f4f7; padding: 0 3px; border-radius: 3px; font-size: 9.5pt; }
table { border-collapse: collapse; margin: 8px 0; }
th, td { border: 1px solid #c8ccd4; padding: 4px 8px; text-align: left; vertical-align: top; }
th { background: #e9eef5; }
li { margin: 2px 0; }
"""


def main() -> None:
    edge = next((path for path in EDGE_PATHS if path.exists()), None)
    if edge is None:
        sys.exit("Microsoft Edge not found - can't print the PDF.")

    body = markdown.markdown(
        (ROOT / "USER_GUIDE.md").read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"]
    )
    html = (
        f'<!doctype html><html><head><meta charset="utf-8"><title>User Guide</title><style>{CSS}</style>'
        f"</head><body>{body}</body></html>"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "guide.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                str(edge),
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--user-data-dir={Path(tmp) / 'edge'}",
                f"--print-to-pdf={OUTPUT}",
                page.as_uri(),
            ],
            check=True,
            timeout=120,
        )
    if not OUTPUT.exists():
        sys.exit("Edge didn't write the PDF.")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

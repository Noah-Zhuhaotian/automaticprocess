"""Excel (.xlsx) template filling - the openpyxl counterpart of word_filler.

The Excel template has no {{tokens}}: values go into fixed cells, given as
{sheet title: {cell: value}}. Writing a cell's value keeps its style (font,
borders, wrap); openpyxl also keeps the sheets' data validations (the
YES/NO and Low/Medium/High drop-downs).

Excel doesn't re-fit an explicitly set row height when the file is opened,
so a cell that now holds several lines gets its row grown to fit
(_fit_row_height) - otherwise only its first lines would show.
"""

from __future__ import annotations

import copy
import datetime
import math
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Points per text line for the templates' 10pt Arial, plus cell padding.
LINE_HEIGHT = 12.75
ROW_PADDING = 3.0


def fill_xlsx_template(
    template_path: str,
    output_path: str,
    cells: dict[str, dict[str, Any]],
    number_formats: dict[str, dict[str, str]] | None = None,
) -> str:
    """Copy template_path to output_path with `cells` filled in. A date
    value can be given an Excel number format via number_formats (same
    shape as cells), e.g. "dd/mm/yy". Raises FileNotFoundError for a
    missing template, KeyError for an unknown sheet, and FileExistsError if
    output_path already exists (never overwrites)."""
    template = Path(template_path)
    output = Path(output_path)
    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template}")
    if output.exists():
        raise FileExistsError(f"Output file already exists, not overwriting: {output}")

    workbook = openpyxl.load_workbook(template)
    for sheet_title, values in cells.items():
        sheet = workbook[sheet_title]
        formats = (number_formats or {}).get(sheet_title, {})
        for coordinate, value in values.items():
            cell = sheet[coordinate]
            cell.value = value
            if coordinate in formats:
                cell.number_format = formats[coordinate]
            if isinstance(value, datetime.date) and cell.alignment.horizontal is None:
                # Excel right-aligns dates by default; keep it where the
                # placeholder text it replaces sat.
                alignment = copy.copy(cell.alignment)
                alignment.horizontal = "left"
                cell.alignment = alignment
            if isinstance(value, str) and "\n" in value:
                _fit_row_height(sheet, coordinate)

    output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output)
    logger.info("Filled %s -> %s", template, output)
    return str(output)


def _fit_row_height(sheet: Worksheet, coordinate: str) -> None:
    """Grow (never shrink) the cell's row to show all its lines, counting
    lines that wrap at the column width (about one character per unit)."""
    cell = sheet[coordinate]
    width = sheet.column_dimensions[cell.column_letter].width or 8.43
    lines = sum(max(1, math.ceil(len(line) / width)) for line in str(cell.value).split("\n"))
    needed = lines * LINE_HEIGHT + ROW_PADDING
    row = sheet.row_dimensions[cell.row]
    if row.height is None or row.height < needed:
        row.height = needed

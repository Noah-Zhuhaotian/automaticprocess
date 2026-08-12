"""Shared constants for the wizard's steps.

Kept separate from main_window.py and the individual step modules
(app/gui/steps/) so every step can import from here without risking a
circular import back into main_window.py, which composes all the step
mixins into MainWindow.
"""

from __future__ import annotations

from pathlib import Path

SCOPE_ITEMS = ["Foundation", "Retaining", "Beams", "Portal", "Bracing", "Others"]
ROLE_OPTIONS = ["Carried out", "Supervised"]
ALL_PART_OPTIONS = ["All", "Part only"]
YES_NO_OPTIONS = ["Yes", "No"]
CM_ITEMS = ["CM1", "CM2", "CM3", "CM4", "CM5"]
B1_OPTIONS = ["B1/VM1", "B1/MV4", "B1/AS1"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Top-level "Title 1" section headings in Specifications.docx, in document
# order - must match that document's heading text exactly (see word_filler's
# SECTION_HEADING_STYLE / remove_unselected_sections).
SPECIFICATION_SECTIONS = [
    "GENERAL STRUCTURAL CONSTRUCTION",
    "EXCAVATION AND HARDFILL",
    "CONCRETE - GENERAL",
    "REINFORCING STEEL",
    "STRUCTURAL STEELWORK",
    "STRUCTURAL TIMBER",
    "MASONRY BLOCKWORK",
]

# Numeric {{token}} fields embedded in specific Specification sections, keyed
# by the section that gates them: (StringVar attribute name, field label).
# Only relevant/required when that section is selected - the paragraphs that
# contain these tokens are deleted along with the rest of the section
# otherwise, so an empty value in that case is harmless.
SPECIFICATION_NUMERIC_FIELDS: dict[str, list[tuple[str, str]]] = {
    "EXCAVATION AND HARDFILL": [
        ("capacity_var", "Ultimate bearing capacity (kPa):"),
    ],
    "CONCRETE - GENERAL": [
        ("precast_strength_var", "Precast elements (MPa):"),
        ("foundation_plain_strength_var", "Foundations - Plain Concrete (MPa):"),
        ("foundation_fibre_strength_var", "Foundations - Fibre Concrete (MPa):"),
        ("metal_deck_topping_strength_var", "Metal deck topping (MPa):"),
    ],
    "MASONRY BLOCKWORK": [
        ("grout_strength_var", "Grout strength:"),
    ],
}

# grout_strength_var (above) is a dropdown, not a free-text numeric entry -
# its chosen value is substituted whole into Specifications.docx's
# "...compressive strength of {{grout_strength}}, using..." sentence (the
# template used to hardcode " MPa (Zone C)" after the token; that literal
# text was removed from the template since each option below already spells
# out its own unit + zone). Keyed by StringVar attribute name so
# specification_step.py can tell which numeric fields need a Combobox
# instead of a plain Entry.
SPECIFICATION_DROPDOWN_FIELDS: dict[str, list[str]] = {
    "grout_strength_var": ["17.5 MPa (Zone B)", "20 MPa (Zone C)", "25 MPa (Zone D)"],
}

# Symbols used for tick-box placeholders in the Word templates.
CHECKED = "☒"
UNCHECKED = "☐"

DRIVE_KEYS = ("engineer_drive", "drafting_drive", "admin_drive")

# Fixed label width (characters) on the PS1/Waivers steps so every input
# widget starts at the same x position, regardless of label text length.
LABEL_WIDTH = 20

# Templates live in the repo (versioned), not in per-machine settings.
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "templates"
PROJECT_REGISTER_TEMPLATE = TEMPLATES_DIR / "Project register.docx"
PS1_TEMPLATE = TEMPLATES_DIR / "PS1 Producer Statement.docx"
LBP_TEMPLATE = TEMPLATES_DIR / "LBP form.docx"
CALCULATION_STATEMENT_TEMPLATE = TEMPLATES_DIR / "Calculation Statement.docx"
SPECIFICATION_TEMPLATE = TEMPLATES_DIR / "Specifications.docx"
B2_LETTER_TEMPLATE = TEMPLATES_DIR / "B2 Letter.docx"

# Row labels (first cell) in B2 Letter.docx's Material/Means of
# Compliance/Notes table, in document order - must match that document's
# text exactly (see word_filler's _remove_unselected_table_rows).
B2_LETTER_MATERIALS = ["Reinforced concrete", "Structural timber", "Mild steel structure"]

# PS1's "Schedule 3 - Schedule of Inspections" table (see word_filler's
# _remove_unselected_table_rows, called with label_column=1 since the
# Item-of-inspection column - unlike the No. column - has fixed,
# known-in-advance text to match rows on before the No. tokens get filled
# with the user's chosen order). (key, item text, time frame text) - item
# and time frame text must match that table's text exactly.
INSPECTION_ITEMS: list[tuple[str, str, str]] = [
    ("subsurface", "Subsurface and bearing condition.", "Cut inspection. To be confirmed on site."),
    ("waffle", "Waffle foundation.", "Pre-pour inspection."),
    (
        "floor_diaphragm",
        "Floor diaphragm",
        "After erection and prior to installation of first floor framing.",
    ),
    (
        "mid_floor_joist",
        "Mid floor joist and all associated beams and lintels and steelwork.",
        "Pre roof inspection. After erection and prior to lining/insulation/cladding.",
    ),
    (
        "hold_down_brackets",
        "Hold down brackets and bracing wall length to wall sheet bracing.",
        "Pre-line inspection. After erection and prior to lining/insulation/cladding.",
    ),
    (
        "ceiling_roof_strap",
        "Ceiling/roof strap braces",
        "Pre-line inspection. After erection and prior to lining/insulation/cladding.",
    ),
    (
        "wall_lining",
        "Wall lining and associated fixing schedule.",
        "Post line inspection. After lining and prior to stop",
    ),
]

# The template's single "Other" row's Item-of-inspection cell holds this
# literal token text - it's used to find and remove that row as a cloning
# prototype (see word_filler's _find_and_remove_table_row_template), since
# the user can add any number of Other items, not just one. Matching runs
# before token replacement, so this is exactly what the cell's text still
# reads at match time.
INSPECTION_OTHER_LABEL = "{{inspection_other_description}}"
INSPECTION_ITEM_LABELS: dict[str, str] = {key: item_text for key, item_text, _time_frame in INSPECTION_ITEMS}

# document.tables index of PS1's Schedule of Inspections table.
PS1_INSPECTION_TABLE_INDEX = 2

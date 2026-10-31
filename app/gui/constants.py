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
B1_OPTIONS = ["B1/VM1", "B1/VM2", "B1/AS1"]
# PS1's "Alternative solution" is always this fixed text when Alternative is
# ticked - not free-text input (and "N/A" when it isn't).
ALTERNATIVE_SOLUTION_TEXT = (
    "Repairing and rebuilding houses affected by the Canterbury Earthquake December 2012."
)
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
        ("concrete_other_strength_var", "Others (MPa):"),
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
# Numeric fields that each have their own tickbox: only ticked ones are
# filled and kept in Specifications.docx - an unticked one's whole line is
# deleted (word_filler.remove_paragraphs_with_tokens). These are CONCRETE -
# GENERAL's 28-day strengths; a selected section needs at least one ticked.
# Plain and Fibre foundations share one line ("Foundations: ..."), built in
# specification_step.py from whichever of the two is ticked (only one can
# be - SPECIFICATION_EXCLUSIVE_FIELDS).
SPECIFICATION_TICKABLE_FIELDS = (
    "precast_strength_var",
    "foundation_plain_strength_var",
    "foundation_fibre_strength_var",
    "metal_deck_topping_strength_var",
    "concrete_other_strength_var",
)
# Tickable fields that rule each other out: the foundations are either
# Plain or Fibre concrete, never both. Ticking one unticks (and clears) the
# other.
SPECIFICATION_EXCLUSIVE_FIELDS = {
    "foundation_plain_strength_var": "foundation_fibre_strength_var",
    "foundation_fibre_strength_var": "foundation_plain_strength_var",
}

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
# Window/title-bar icon (also the exe/installer icon - see build_scripts/make_icon.py).
APP_ICON = TEMPLATES_DIR.parent / "app_icon.ico"
PROJECT_REGISTER_TEMPLATE = TEMPLATES_DIR / "Project register.docx"
PS1_TEMPLATE = TEMPLATES_DIR / "PS1 Producer Statement.docx"
LBP_TEMPLATE = TEMPLATES_DIR / "LBP form.docx"
CALCULATION_STATEMENT_TEMPLATE = TEMPLATES_DIR / "Calculation Statement.docx"
SPECIFICATION_TEMPLATE = TEMPLATES_DIR / "Specifications.docx"
B2_LETTER_TEMPLATE = TEMPLATES_DIR / "B2 Letter.docx"
QA_SID_TEMPLATE = TEMPLATES_DIR / "Engsolution_Post_Interactive_QA_and_SiD_Simple.xlsx"

# Cells filled in the QA / Safety in Design workbook (excel_filler): the
# scope goes into the QA Process sheet's "Scope" row, under the "Scope"
# label, as " - item" lines (the sheet's own list style); the Safety in
# Design sheet gets the project name (= folder name) and the PS1 date.
QA_SHEET = "QA Process"
QA_SCOPE_CELL = "B5"
QA_SCOPE_LABEL = "Scope"
SID_SHEET = "Safety in Design"
SID_PROJECT_CELL = "B4"
SID_DATE_CELL = "B5"
SID_DATE_FORMAT = "dd/mm/yy"

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

# Review summary of an update run (reopening a project whose documents were
# already generated): the "Changes" section's heading, and the suffix marking
# a changed row in the other sections (both rendered highlighted).
CHANGES_HEADING = "Changes"
UPDATED_SUFFIX = " (updated)"

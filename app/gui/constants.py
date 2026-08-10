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
        ("grout_strength_var", "Grout, Zone C (MPa):"),
    ],
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

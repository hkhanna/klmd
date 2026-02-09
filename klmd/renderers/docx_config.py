"""
KLMD Docx Renderer Configuration

Configuration dataclasses for the docx renderer.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .markdown import NumberingScheme


@dataclass
class StyleMapping:
    """Maps AST node types to Word paragraph style names."""

    document_title: str = "Title"
    attachment_title: str = "Title"
    attachment_subtitle: str = "Subtitle"
    section_level_1: str = "Heading 1"
    section_level_2: str = "Heading 2"
    section_level_3: str = "Heading 3"
    section_level_4: str = "Heading 4"
    section_level_5: str = "Heading 5"
    paragraph: str = "Normal"
    signature_party_name: str = "Normal"
    signature_line: str = "Normal"
    signature_field: str = "Normal"
    comment_text: str = "Quote"

    def get_section_style(self, level: int) -> str:
        """Get style for section level 1-5 (clamped)."""
        clamped_level = max(1, min(5, level))
        style: str = getattr(self, f"section_level_{clamped_level}")
        return style


@dataclass
class DocxConfig:
    """Main configuration for docx renderer."""

    template_path: Path | None = None
    paragraph_styles: StyleMapping = field(default_factory=StyleMapping)
    section_numbering: NumberingScheme = field(
        default_factory=lambda: NumberingScheme.from_preset("decimal")
    )
    attachment_numbering: NumberingScheme = field(
        default_factory=lambda: NumberingScheme.from_preset("letters")
    )
    cross_ref_template: str = "Section {number}"
    generate_bookmarks: bool = True
    generate_hyperlinks: bool = True
    include_comments: bool = False  # Comments excluded by default
    defined_term_bold: bool = True
    signature_line_width_inches: float = 3.0
    uppercase_entity_names: bool = True

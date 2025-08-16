"""
KLMD Markdown Renderer

Converts KLMD AST to standard Markdown with resolved numbering.
Serves as baseline renderer and reference implementation.
"""

import re
from dataclasses import dataclass, field
from enum import Enum

from ..parser import (
    CommentNode,
    CrossReferenceNode,
    DefinedTermNode,
    DocumentNode,
    Node,
    ParagraphNode,
    SectionNode,
    SignatureBlockNode,
    TextNode,
    TitleNode,
)


class TextStyle(Enum):
    """Text styling options for markdown output."""

    PLAIN = "plain"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    CODE = "code"
    UNDERLINE = "underline"


class NumberStyle(Enum):
    """Numbering style options."""

    ARABIC = "arabic"
    ALPHA_LOWER = "alpha_lower"
    ALPHA_UPPER = "alpha_upper"
    ROMAN_LOWER = "roman_lower"
    ROMAN_UPPER = "roman_upper"


class CommentStyle(Enum):
    """Comment rendering options."""

    EXCLUDE = "exclude"
    BLOCKQUOTE = "blockquote"
    HTML_COMMENT = "html_comment"


@dataclass
class LevelNumbering:
    """Configuration for a single numbering level."""

    style: NumberStyle
    prefix: str = ""
    suffix: str = ""
    include_parent: bool = True
    title_style: TextStyle = TextStyle.BOLD

    def format_value(self, value: int) -> str:
        """Convert integer to styled representation."""
        if self.style == NumberStyle.ARABIC:
            return str(value)
        elif self.style == NumberStyle.ALPHA_LOWER:
            return chr(ord("a") + value - 1)
        elif self.style == NumberStyle.ALPHA_UPPER:
            return chr(ord("A") + value - 1)
        elif self.style == NumberStyle.ROMAN_LOWER:
            return self._to_roman(value).lower()
        elif self.style == NumberStyle.ROMAN_UPPER:
            return self._to_roman(value)
        else:
            raise ValueError(f"Unknown NumberStyle: {self.style}")

    def _to_roman(self, num: int) -> str:
        """Convert integer to Roman numeral."""
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        literals = [
            "M",
            "CM",
            "D",
            "CD",
            "C",
            "XC",
            "L",
            "XL",
            "X",
            "IX",
            "V",
            "IV",
            "I",
        ]

        result = ""
        for i, value in enumerate(values):
            count = num // value
            if count:
                result += literals[i] * count
                num -= value * count
        return result


@dataclass
class NumberingScheme:
    """Complete numbering configuration for sections or attachments."""

    levels: list[LevelNumbering]

    @classmethod
    def from_preset(cls, preset: str) -> "NumberingScheme":
        """Create numbering scheme from preset name."""
        presets = {
            "decimal": cls(
                levels=[
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix=".",
                        include_parent=False,
                        title_style=TextStyle.BOLD,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix=".",
                        include_parent=True,
                        title_style=TextStyle.ITALIC,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix=".",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix=".",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix=".",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                ]
            ),
            "legal": cls(
                levels=[
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.BOLD,
                    ),
                    LevelNumbering(
                        NumberStyle.ALPHA_LOWER,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.ITALIC,
                    ),
                    LevelNumbering(
                        NumberStyle.ROMAN_LOWER,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ALPHA_UPPER,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                ]
            ),
            "outline": cls(
                levels=[
                    LevelNumbering(
                        NumberStyle.ROMAN_UPPER,
                        suffix=".",
                        include_parent=False,
                        title_style=TextStyle.BOLD,
                    ),
                    LevelNumbering(
                        NumberStyle.ALPHA_UPPER,
                        suffix=".",
                        include_parent=False,
                        title_style=TextStyle.ITALIC,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix=".",
                        include_parent=False,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ALPHA_LOWER,
                        suffix=".",
                        include_parent=False,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ROMAN_LOWER,
                        suffix=".",
                        include_parent=False,
                        title_style=TextStyle.PLAIN,
                    ),
                ]
            ),
            "simple": cls(
                levels=[
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.BOLD,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.ITALIC,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.PLAIN,
                    ),
                ]
            ),
            "alpha_parens": cls(
                levels=[
                    LevelNumbering(
                        NumberStyle.ALPHA_LOWER,
                        prefix="(",
                        suffix=")",
                        include_parent=False,
                        title_style=TextStyle.BOLD,
                    ),
                    LevelNumbering(
                        NumberStyle.ROMAN_LOWER,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.ITALIC,
                    ),
                    LevelNumbering(
                        NumberStyle.ARABIC,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ALPHA_UPPER,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                    LevelNumbering(
                        NumberStyle.ROMAN_UPPER,
                        prefix="(",
                        suffix=")",
                        include_parent=True,
                        title_style=TextStyle.PLAIN,
                    ),
                ]
            ),
            "letters": cls(
                levels=[
                    LevelNumbering(
                        NumberStyle.ALPHA_UPPER,
                        suffix="",
                        include_parent=False,
                        title_style=TextStyle.BOLD,
                    ),
                ]
            ),
        }

        if preset not in presets:
            raise ValueError(
                f"Unknown preset: {preset}. Available presets: {list(presets.keys())}"
            )

        return presets[preset]

    def customize_level(self, level: int, config: LevelNumbering) -> None:
        """Override specific level while keeping rest of scheme."""
        if level < 0:
            raise ValueError("Level must be non-negative")

        # Extend levels list if necessary
        while len(self.levels) <= level:
            # Copy the last level configuration as default
            last_config = (
                self.levels[-1] if self.levels else LevelNumbering(NumberStyle.ARABIC)
            )
            self.levels.append(last_config)

        self.levels[level] = config

    def format_number(self, position: list[int]) -> str:
        """Generate formatted number string for given position."""
        if not position:
            return ""

        level = len(position) - 1
        if level >= len(self.levels):
            # Use last level configuration for deeper levels
            level_config = self.levels[-1]
        else:
            level_config = self.levels[level]

        if level_config.include_parent and level > 0:
            # Include parent numbering
            parent_position = position[:-1]
            parent_number = self.format_number(parent_position)
            current_value = level_config.format_value(position[-1])
            return (
                f"{parent_number}{level_config.prefix}{current_value}"
                f"{level_config.suffix}"
            )
        else:
            # No parent numbering
            current_value = level_config.format_value(position[-1])
            return f"{level_config.prefix}{current_value}{level_config.suffix}"


@dataclass
class CrossReferenceConfig:
    """Configuration for cross-reference rendering."""

    template: str = "Section {number}"
    generate_links: bool = True


@dataclass
class MarkdownConfig:
    """Main configuration for markdown renderer."""

    section_numbering: NumberingScheme = field(
        default_factory=lambda: NumberingScheme.from_preset("decimal")
    )
    attachment_numbering: NumberingScheme = field(
        default_factory=lambda: NumberingScheme.from_preset("letters")
    )
    defined_term_style: TextStyle = TextStyle.BOLD
    cross_references: CrossReferenceConfig = field(default_factory=CrossReferenceConfig)
    include_comments: CommentStyle = CommentStyle.EXCLUDE
    heading_base_level: int = 2


class NumberingTracker:
    """Tracks current position at each hierarchy level."""

    def __init__(self) -> None:
        self.section_position: list[int] = []
        self.attachment_position: int = 0
        self.in_attachment: bool = False

    def enter_section(self, level: int) -> None:
        """Enter a section at the given level (1-indexed)."""
        level_index = level - 1  # Convert to 0-indexed

        # Adjust position list to match level
        if level_index >= len(self.section_position):
            # Extend to reach this level
            while len(self.section_position) <= level_index:
                self.section_position.append(0)
        else:
            # Truncate deeper levels
            self.section_position = self.section_position[: level_index + 1]

        # Increment current level
        self.section_position[level_index] += 1

    def enter_attachment(self) -> None:
        """Enter an attachment."""
        self.attachment_position += 1
        self.in_attachment = True
        # Reset section numbering within attachment
        self.section_position = []

    def exit_attachment(self) -> None:
        """Exit attachment scope."""
        self.in_attachment = False

    def get_section_number(self, scheme: NumberingScheme) -> str:
        """Get formatted section number."""
        return scheme.format_number(self.section_position)

    def get_attachment_number(self, scheme: NumberingScheme) -> str:
        """Get formatted attachment number."""
        return scheme.format_number([self.attachment_position])


class NumberingResolver:
    """First-pass traversal to assign numbers to all sections and attachments."""

    def __init__(self, config: MarkdownConfig):
        self.config = config
        self.tracker = NumberingTracker()
        self.section_numbers: dict[int, str] = {}  # node id -> number
        self.attachment_numbers: dict[int, str] = {}  # node id -> number
        self.title_to_number: dict[str, str] = {}
        self.title_to_anchor: dict[str, str] = {}

    def resolve(self, document: DocumentNode) -> None:
        """Traverse document and assign all numbers."""
        self._traverse_node(document)

    def _traverse_node(self, node: Node) -> None:
        """Recursively traverse and number nodes."""
        if isinstance(node, TitleNode):
            if node.has_attachment_placeholder:
                self.tracker.enter_attachment()
                number = self.tracker.get_attachment_number(
                    self.config.attachment_numbering
                )
                self.attachment_numbers[id(node)] = number
                # Register title for cross-references
                title_key = self._normalize_title(node.title)
                self.title_to_number[title_key] = number
                self.title_to_anchor[title_key] = self._generate_anchor(node.title)
            else:
                # Regular document title - no numbering but register for references
                title_key = self._normalize_title(node.title)
                self.title_to_anchor[title_key] = self._generate_anchor(node.title)

            # Process children
            for child in node.children:
                self._traverse_node(child)

            if node.has_attachment_placeholder:
                self.tracker.exit_attachment()

        elif isinstance(node, SectionNode):
            self.tracker.enter_section(node.level)
            number = self.tracker.get_section_number(self.config.section_numbering)
            self.section_numbers[id(node)] = number

            # Register title for cross-references if it has one
            if node.title:
                title_key = self._normalize_title(node.title)
                self.title_to_number[title_key] = number
                self.title_to_anchor[title_key] = self._generate_anchor(node.title)

            # Process children
            for child in node.children:
                self._traverse_node(child)

        elif hasattr(node, "children"):
            # Process children for other node types
            for child in node.children:
                self._traverse_node(child)

    def _normalize_title(self, title: str) -> str:
        """Normalize title for cross-reference lookup."""
        return title.lower().replace(" ", "-")

    def _generate_anchor(self, title: str) -> str:
        """Generate markdown anchor ID from title."""
        # Convert to lowercase, replace spaces and special chars with hyphens
        anchor = re.sub(r"[^\w\s-]", "", title).strip()
        anchor = re.sub(r"[-\s]+", "-", anchor)
        return anchor.lower()


class StyleFormatter:
    """Applies markdown text styling."""

    @staticmethod
    def apply_style(text: str, style: TextStyle) -> str:
        """Apply text styling to markdown output."""
        if style == TextStyle.PLAIN:
            return text
        elif style == TextStyle.BOLD:
            return f"**{text}**"
        elif style == TextStyle.ITALIC:
            return f"*{text}*"
        elif style == TextStyle.BOLD_ITALIC:
            return f"***{text}***"
        elif style == TextStyle.CODE:
            return f"`{text}`"
        elif style == TextStyle.UNDERLINE:
            return f"<u>{text}</u>"
        else:
            raise ValueError(f"Unknown TextStyle: {style}")


class MarkdownRenderer:
    """Main markdown renderer class."""

    def __init__(self, config: MarkdownConfig | None = None) -> None:
        self.config = config or MarkdownConfig()
        self.resolver: NumberingResolver

    def render(self, document: DocumentNode) -> str:
        """Render document to markdown string."""
        # First pass: resolve all numbering
        self.resolver = NumberingResolver(self.config)
        self.resolver.resolve(document)

        # Second pass: render with resolved numbers
        return self._render_node(document).strip()

    def _render_node(self, node: Node) -> str:
        """Render a single node to markdown."""
        if isinstance(node, DocumentNode):
            return self._render_document(node)
        elif isinstance(node, TitleNode):
            return self._render_title(node)
        elif isinstance(node, SectionNode):
            return self._render_section(node)
        elif isinstance(node, ParagraphNode):
            return self._render_paragraph(node)
        elif isinstance(node, TextNode):
            return self._render_text(node)
        elif isinstance(node, CrossReferenceNode):
            return self._render_cross_reference(node)
        elif isinstance(node, DefinedTermNode):
            return self._render_defined_term(node)
        elif isinstance(node, CommentNode):
            return self._render_comment(node)
        elif isinstance(node, SignatureBlockNode):
            return self._render_signature_block(node)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    def _render_document(self, node: DocumentNode) -> str:
        """Render document node."""
        parts = []
        for child in node.children:
            rendered = self._render_node(child)
            if rendered.strip():
                parts.append(rendered)
        return "\n\n".join(parts)

    def _render_title(self, node: TitleNode) -> str:
        """Render title node."""
        if node.has_attachment_placeholder:
            # Attachment title with number
            number = self.resolver.attachment_numbers[id(node)]
            title_text = f"{node.title} {number}"
            if node.subtitle:
                title_text = f"{node.title} {number}\n{node.subtitle}"
        else:
            # Regular document title
            title_text = node.title

        parts = [f"# {title_text}"]

        # Render children
        for child in node.children:
            rendered = self._render_node(child)
            if rendered.strip():
                parts.append(rendered)

        return "\n\n".join(parts)

    def _render_section(self, node: SectionNode) -> str:
        """Render section node."""
        number = self.resolver.section_numbers[id(node)]

        # Determine heading level
        heading_level = self.config.heading_base_level + node.level - 1
        heading_level = min(heading_level, 6)  # Cap at H6
        heading_prefix = "#" * heading_level

        # Build section heading
        if node.title:
            # Get title styling for this level
            level_index = node.level - 1
            if level_index < len(self.config.section_numbering.levels):
                level_config = self.config.section_numbering.levels[level_index]
            else:
                level_config = self.config.section_numbering.levels[-1]

            styled_title = StyleFormatter.apply_style(
                node.title, level_config.title_style
            )
            # Don't add extra period if number already has suffix
            if number.endswith(".") or number.endswith(")"):
                heading_text = f"{number} {styled_title}"
            else:
                heading_text = f"{number}. {styled_title}"

            # Generate anchor
            anchor = self.resolver.title_to_anchor.get(
                self.resolver._normalize_title(node.title), ""
            )
            if anchor:
                section_line = f"{heading_prefix} {heading_text} {{#{anchor}}}"
            else:
                section_line = f"{heading_prefix} {heading_text}"
        else:
            # Section without title
            if number.endswith(".") or number.endswith(")"):
                section_line = f"{heading_prefix} {number}"
            else:
                section_line = f"{heading_prefix} {number}."

        parts = [section_line]

        # Render children
        for child in node.children:
            rendered = self._render_node(child)
            if rendered.strip():
                parts.append(rendered)

        return "\n\n".join(parts)

    def _render_paragraph(self, node: ParagraphNode) -> str:
        """Render paragraph node."""
        parts = []
        for child in node.children:
            rendered = self._render_node(child)
            parts.append(rendered)
        return "".join(parts)

    def _render_text(self, node: TextNode) -> str:
        """Render text node."""
        return node.text

    def _render_cross_reference(self, node: CrossReferenceNode) -> str:
        """Render cross-reference node."""
        # Look up number and anchor
        number = self.resolver.title_to_number.get(node.reference_key)
        anchor = self.resolver.title_to_anchor.get(node.reference_key)

        if number is None:
            # Missing reference - return original text
            return node.original_text

        # Apply template
        ref_text = self.config.cross_references.template.format(number=number)

        if self.config.cross_references.generate_links and anchor:
            return f"[{ref_text}](#{anchor})"
        else:
            return ref_text

    def _render_defined_term(self, node: DefinedTermNode) -> str:
        """Render defined term node."""
        styled_term = StyleFormatter.apply_style(
            node.term, self.config.defined_term_style
        )

        if node.descriptor:
            return f"({styled_term})"
        else:
            return f"({styled_term})"

    def _render_comment(self, node: CommentNode) -> str:
        """Render comment node."""
        if self.config.include_comments == CommentStyle.EXCLUDE:
            return ""
        elif self.config.include_comments == CommentStyle.BLOCKQUOTE:
            if node.is_inline:
                return f"> {node.content}"
            else:
                # Multi-line blockquote
                lines = node.content.split("\n")
                quoted_lines = [f"> {line}" for line in lines]
                return "\n".join(quoted_lines)
        elif self.config.include_comments == CommentStyle.HTML_COMMENT:
            if node.is_inline:
                return f"<!-- {node.content} -->"
            else:
                return f"<!-- \n{node.content}\n-->"
        else:
            raise ValueError(f"Unknown CommentStyle: {self.config.include_comments}")

    def _render_signature_block(self, node: SignatureBlockNode) -> str:
        """Render signature block node."""
        parts = []

        if node.is_entity:
            # Entity signature
            party_name = node.party_name.upper()
            parts.append(party_name)

            # Add By Entity chain
            for by_entity in node.by_entities:
                parts.append(f"By: {by_entity}")

            # Add signature line and human signatory
            parts.append("")  # Blank line
            parts.append("By: " + "_" * 20)
            if node.signatory:
                parts.append(f"Name: {node.signatory}")

            # Add other fields
            for field_name, field_value in node.fields.items():
                if field_name.lower() not in ["by", "by entity"]:
                    parts.append(f"{field_name}: {field_value}")

        else:
            # Individual signature
            parts.append("_" * 20)
            parts.append(node.party_name)

            # Add fields
            for field_name, field_value in node.fields.items():
                parts.append(f"{field_name}: {field_value}")

        return "\n".join(parts)

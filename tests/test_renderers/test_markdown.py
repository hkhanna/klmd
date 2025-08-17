"""
Tests for KLMD Markdown Renderer
"""

import pytest

from klmd.parser import (
    CommentNode,
    CrossReferenceNode,
    DefinedTermNode,
    DocumentNode,
    ParagraphNode,
    SectionNode,
    SignatureBlockNode,
    TextNode,
    TitleNode,
)
from klmd.renderers.markdown import (
    AnchorGeneration,
    CommentStyle,
    CrossReferenceConfig,
    LevelNumbering,
    MarkdownConfig,
    MarkdownRenderer,
    NumberingResolver,
    NumberingScheme,
    NumberingTracker,
    NumberStyle,
    SectionContentPlacement,
    StyleFormatter,
    TextStyle,
)


class TestTextStyle:
    """Test TextStyle enum and formatting."""

    def test_style_formatter(self) -> None:
        """Test StyleFormatter applies correct markdown formatting."""
        assert StyleFormatter.apply_style("Test", TextStyle.PLAIN) == "Test"
        assert StyleFormatter.apply_style("Test", TextStyle.BOLD) == "**Test**"
        assert StyleFormatter.apply_style("Test", TextStyle.ITALIC) == "*Test*"
        assert StyleFormatter.apply_style("Test", TextStyle.BOLD_ITALIC) == "***Test***"
        assert StyleFormatter.apply_style("Test", TextStyle.CODE) == "`Test`"
        assert StyleFormatter.apply_style("Test", TextStyle.UNDERLINE) == "<u>Test</u>"


class TestNumberStyle:
    """Test NumberStyle and LevelNumbering."""

    def test_arabic_formatting(self) -> None:
        """Test Arabic number formatting."""
        level = LevelNumbering(NumberStyle.ARABIC)
        assert level.format_value(1) == "1"
        assert level.format_value(42) == "42"

    def test_alpha_lower_formatting(self) -> None:
        """Test lowercase alphabetic formatting."""
        level = LevelNumbering(NumberStyle.ALPHA_LOWER)
        assert level.format_value(1) == "a"
        assert level.format_value(26) == "z"

    def test_alpha_upper_formatting(self) -> None:
        """Test uppercase alphabetic formatting."""
        level = LevelNumbering(NumberStyle.ALPHA_UPPER)
        assert level.format_value(1) == "A"
        assert level.format_value(26) == "Z"

    def test_roman_formatting(self) -> None:
        """Test Roman numeral formatting."""
        level_lower = LevelNumbering(NumberStyle.ROMAN_LOWER)
        level_upper = LevelNumbering(NumberStyle.ROMAN_UPPER)

        assert level_lower.format_value(1) == "i"
        assert level_lower.format_value(4) == "iv"
        assert level_lower.format_value(9) == "ix"
        assert level_lower.format_value(2023) == "mmxxiii"

        assert level_upper.format_value(1) == "I"
        assert level_upper.format_value(4) == "IV"
        assert level_upper.format_value(9) == "IX"
        assert level_upper.format_value(2023) == "MMXXIII"


class TestLevelNumbering:
    """Test LevelNumbering configuration."""

    def test_prefix_suffix(self) -> None:
        """Test prefix and suffix application."""
        level = LevelNumbering(NumberStyle.ARABIC, prefix="(", suffix=")")
        assert (
            level.format_value(5) == "5"
        )  # format_value doesn't include prefix/suffix

    def test_title_style_default(self) -> None:
        """Test default title style."""
        level = LevelNumbering(NumberStyle.ARABIC)
        assert level.title_style == TextStyle.BOLD


class TestNumberingScheme:
    """Test NumberingScheme configuration and presets."""

    def test_decimal_preset(self) -> None:
        """Test decimal preset configuration."""
        scheme = NumberingScheme.from_preset("decimal")
        assert len(scheme.levels) == 5
        assert scheme.levels[0].style == NumberStyle.ARABIC
        assert scheme.levels[0].suffix == "."
        assert not scheme.levels[0].include_parent
        assert scheme.levels[1].include_parent

    def test_legal_preset(self) -> None:
        """Test legal preset configuration."""
        scheme = NumberingScheme.from_preset("legal")
        assert len(scheme.levels) == 5
        assert scheme.levels[0].style == NumberStyle.ARABIC
        assert scheme.levels[1].style == NumberStyle.ALPHA_LOWER
        assert scheme.levels[1].prefix == "("
        assert scheme.levels[1].suffix == ")"
        assert scheme.levels[1].include_parent

    def test_outline_preset(self) -> None:
        """Test outline preset configuration."""
        scheme = NumberingScheme.from_preset("outline")
        assert scheme.levels[0].style == NumberStyle.ROMAN_UPPER
        assert scheme.levels[1].style == NumberStyle.ALPHA_UPPER
        assert scheme.levels[2].style == NumberStyle.ARABIC
        assert not scheme.levels[0].include_parent  # Outline doesn't include parent

    def test_letters_preset(self) -> None:
        """Test letters preset for attachments."""
        scheme = NumberingScheme.from_preset("letters")
        assert len(scheme.levels) == 1
        assert scheme.levels[0].style == NumberStyle.ALPHA_UPPER
        assert not scheme.levels[0].include_parent

    def test_unknown_preset_error(self) -> None:
        """Test error on unknown preset."""
        with pytest.raises(ValueError, match="Unknown preset"):
            NumberingScheme.from_preset("nonexistent")

    def test_customize_level(self) -> None:
        """Test level customization."""
        scheme = NumberingScheme.from_preset("decimal")

        # Customize level 1 (0-indexed)
        new_config = LevelNumbering(NumberStyle.ROMAN_LOWER, prefix="[", suffix="]")
        scheme.customize_level(1, new_config)

        assert scheme.levels[1].style == NumberStyle.ROMAN_LOWER
        assert scheme.levels[1].prefix == "["
        assert scheme.levels[1].suffix == "]"
        # Other levels unchanged
        assert scheme.levels[0].style == NumberStyle.ARABIC
        assert scheme.levels[2].style == NumberStyle.ARABIC

    def test_format_number_without_parent(self) -> None:
        """Test number formatting without parent inclusion."""
        scheme = NumberingScheme(
            levels=[
                LevelNumbering(NumberStyle.ARABIC, suffix=".", include_parent=False),
                LevelNumbering(
                    NumberStyle.ALPHA_LOWER,
                    prefix="(",
                    suffix=")",
                    include_parent=False,
                ),
            ]
        )

        assert scheme.format_number([1]) == "1."
        assert scheme.format_number([1, 2]) == "(b)"  # Second alpha letter

    def test_format_number_with_parent(self) -> None:
        """Test number formatting with parent inclusion."""
        scheme = NumberingScheme(
            levels=[
                LevelNumbering(NumberStyle.ARABIC, suffix="", include_parent=False),
                LevelNumbering(
                    NumberStyle.ALPHA_LOWER, prefix="(", suffix=")", include_parent=True
                ),
            ]
        )

        assert scheme.format_number([1]) == "1"
        assert scheme.format_number([1, 2]) == "1(b)"

    def test_format_number_empty(self) -> None:
        """Test formatting empty position."""
        scheme = NumberingScheme.from_preset("decimal")
        assert scheme.format_number([]) == ""


class TestNumberingTracker:
    """Test NumberingTracker functionality."""

    def test_section_numbering(self) -> None:
        """Test section position tracking."""
        tracker = NumberingTracker()

        # First section
        tracker.enter_section(1)
        assert tracker.section_position == [1]

        # Subsection
        tracker.enter_section(2)
        assert tracker.section_position == [1, 1]

        # Another subsection at same level
        tracker.enter_section(2)
        assert tracker.section_position == [1, 2]

        # Back to top level
        tracker.enter_section(1)
        assert tracker.section_position == [2]

    def test_attachment_numbering(self) -> None:
        """Test attachment numbering and section reset."""
        tracker = NumberingTracker()
        NumberingScheme.from_preset("letters")

        # Add some sections first
        tracker.enter_section(1)
        tracker.enter_section(2)
        assert tracker.section_position == [1, 1]

        # Enter attachment
        tracker.enter_attachment()
        assert tracker.attachment_position == 1
        assert tracker.in_attachment
        assert tracker.section_position == []  # Reset in attachment

        # Add section within attachment
        tracker.enter_section(1)
        assert tracker.section_position == [1]

        # Another attachment
        tracker.enter_attachment()
        assert tracker.attachment_position == 2

    def test_get_formatted_numbers(self) -> None:
        """Test getting formatted numbers."""
        tracker = NumberingTracker()
        section_scheme = NumberingScheme.from_preset("legal")
        attachment_scheme = NumberingScheme.from_preset("letters")

        tracker.enter_section(1)
        tracker.enter_section(2)
        assert tracker.get_section_number(section_scheme) == "1(a)"

        tracker.enter_attachment()
        assert tracker.get_attachment_number(attachment_scheme) == "A"


class TestNumberingResolver:
    """Test NumberingResolver functionality."""

    def test_section_resolution(self) -> None:
        """Test section number resolution."""
        # Create test document
        document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="First Section",
                    children=[ParagraphNode(children=[TextNode("Content 1")])],
                ),
                SectionNode(
                    level=2,
                    title="Subsection",
                    children=[ParagraphNode(children=[TextNode("Content 2")])],
                ),
                SectionNode(
                    level=1,
                    title="Second Section",
                    children=[ParagraphNode(children=[TextNode("Content 3")])],
                ),
            ]
        )

        config = MarkdownConfig(section_numbering=NumberingScheme.from_preset("legal"))
        resolver = NumberingResolver(config)
        resolver.resolve(document)

        # Check section numbers
        sections = [
            child for child in document.children if isinstance(child, SectionNode)
        ]
        assert resolver.section_numbers[id(sections[0])] == "1"
        assert resolver.section_numbers[id(sections[1])] == "1(a)"
        assert resolver.section_numbers[id(sections[2])] == "2"

        # Check title mappings
        assert resolver.title_to_number["first-section"] == "1"
        assert resolver.title_to_number["subsection"] == "1(a)"
        assert resolver.title_to_number["second-section"] == "2"

    def test_attachment_resolution(self) -> None:
        """Test attachment number resolution."""
        document = DocumentNode(
            children=[
                TitleNode(
                    title="Exhibit",
                    is_document_title=False,
                    has_attachment_placeholder=True,
                    subtitle=None,
                    children=[
                        SectionNode(level=1, title="Attachment Section", children=[])
                    ],
                )
            ]
        )

        config = MarkdownConfig(
            attachment_numbering=NumberingScheme.from_preset("letters")
        )
        resolver = NumberingResolver(config)
        resolver.resolve(document)

        # Check attachment number
        title_node = document.children[0]
        assert resolver.attachment_numbers[id(title_node)] == "A"
        assert resolver.title_to_number["exhibit"] == "A"


class TestMarkdownRenderer:
    """Test main MarkdownRenderer functionality."""

    def test_basic_document_rendering(self) -> None:
        """Test rendering a basic document."""
        document = DocumentNode(
            children=[
                TitleNode(
                    title="Test Document",
                    is_document_title=True,
                    has_attachment_placeholder=False,
                    subtitle=None,
                    children=[ParagraphNode(children=[TextNode("Document content.")])],
                )
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        assert "# Test Document" in output
        assert "Document content." in output

    def test_section_rendering(self) -> None:
        """Test section rendering with numbering."""
        document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="Payment Terms",
                    children=[
                        ParagraphNode(
                            children=[TextNode("Payment is due within 30 days.")]
                        )
                    ],
                ),
                SectionNode(
                    level=2,
                    title="Late Fees",
                    children=[
                        ParagraphNode(
                            children=[TextNode("Interest accrues at 1.5% per month.")]
                        )
                    ],
                ),
            ]
        )

        config = MarkdownConfig(
            section_numbering=NumberingScheme.from_preset("legal"),
            anchor_generation=AnchorGeneration.ALL,
        )
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "1. **Payment Terms** {#payment-terms}" in output
        assert "    1(a) *Late Fees* {#late-fees}" in output
        assert "Payment is due within 30 days." in output
        assert "Interest accrues at 1.5% per month." in output

    def test_cross_reference_rendering(self) -> None:
        """Test cross-reference rendering."""
        document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="Payment Terms",
                    children=[ParagraphNode(children=[TextNode("Payment details.")])],
                ),
                ParagraphNode(
                    children=[
                        TextNode("See "),
                        CrossReferenceNode(
                            reference_key="payment-terms",
                            original_text="[#payment-terms]",
                        ),
                        TextNode(" for details."),
                    ]
                ),
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        assert "[Section 1](#payment-terms)" in output
        assert "See [Section 1](#payment-terms) for details." in output

    def test_defined_term_rendering(self) -> None:
        """Test defined term rendering."""
        document = DocumentNode(
            children=[
                ParagraphNode(
                    children=[
                        TextNode("Big Company LLC "),
                        DefinedTermNode(term="Company", descriptor="the"),
                        TextNode(" provides services."),
                    ]
                )
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        assert "Big Company LLC (the **Company**) provides services." in output

    def test_comment_rendering_exclude(self) -> None:
        """Test comment rendering with EXCLUDE style."""
        document = DocumentNode(
            children=[
                ParagraphNode(
                    children=[
                        TextNode("Some text."),
                        CommentNode(content="This is a comment", is_inline=True),
                    ]
                )
            ]
        )

        config = MarkdownConfig(include_comments=CommentStyle.EXCLUDE)
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "Some text." in output
        assert "This is a comment" not in output

    def test_comment_rendering_blockquote(self) -> None:
        """Test comment rendering with BLOCKQUOTE style."""
        document = DocumentNode(
            children=[
                ParagraphNode(
                    children=[
                        TextNode("Some text."),
                        CommentNode(content="This is a comment", is_inline=True),
                    ]
                )
            ]
        )

        config = MarkdownConfig(include_comments=CommentStyle.BLOCKQUOTE)
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "Some text." in output
        assert "> This is a comment" in output

    def test_comment_rendering_html(self) -> None:
        """Test comment rendering with HTML_COMMENT style."""
        document = DocumentNode(
            children=[
                ParagraphNode(
                    children=[
                        TextNode("Some text."),
                        CommentNode(content="This is a comment", is_inline=True),
                    ]
                )
            ]
        )

        config = MarkdownConfig(include_comments=CommentStyle.HTML_COMMENT)
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "Some text." in output
        assert "<!-- This is a comment -->" in output

    def test_individual_signature_rendering(self) -> None:
        """Test individual signature block rendering."""
        document = DocumentNode(
            children=[
                SignatureBlockNode(
                    party_name="John Smith",
                    is_entity=False,
                    by_entities=[],
                    signatory=None,
                    fields={"Address": "123 Main St", "Email": "john@example.com"},
                )
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        assert "____________________" in output
        assert "John Smith" in output
        assert "Address: 123 Main St" in output
        assert "Email: john@example.com" in output

    def test_entity_signature_rendering(self) -> None:
        """Test entity signature block rendering."""
        document = DocumentNode(
            children=[
                SignatureBlockNode(
                    party_name="ABC Corporation",
                    is_entity=True,
                    by_entities=[],
                    signatory="John Smith",
                    fields={"Title": "CEO"},
                )
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        assert "ABC CORPORATION" in output
        assert "By: ____________________" in output
        assert "Name: John Smith" in output
        assert "Title: CEO" in output

    def test_nested_entity_signature_rendering(self) -> None:
        """Test nested entity signature rendering."""
        document = DocumentNode(
            children=[
                SignatureBlockNode(
                    party_name="Investment Fund LP",
                    is_entity=True,
                    by_entities=["ABC Management LLC, its General Partner"],
                    signatory="John Smith",
                    fields={"Title": "President"},
                )
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        assert "INVESTMENT FUND LP" in output
        assert "By: ABC Management LLC, its General Partner" in output
        assert "By: ____________________" in output
        assert "Name: John Smith" in output
        assert "Title: President" in output

    def test_complete_document_rendering(self) -> None:
        """Test rendering a complete document with multiple features."""
        document = DocumentNode(
            children=[
                TitleNode(
                    title="Master Services Agreement",
                    is_document_title=True,
                    has_attachment_placeholder=False,
                    subtitle=None,
                    children=[
                        SectionNode(
                            level=1,
                            title="Definitions",
                            children=[
                                ParagraphNode(
                                    children=[
                                        TextNode("Big Company LLC "),
                                        DefinedTermNode(
                                            term="Company", descriptor="the"
                                        ),
                                        TextNode(" is the service provider."),
                                    ]
                                )
                            ],
                        ),
                        SectionNode(
                            level=1,
                            title="Payment",
                            children=[
                                ParagraphNode(
                                    children=[
                                        TextNode("Payment terms are in "),
                                        CrossReferenceNode(
                                            reference_key="definitions",
                                            original_text="[#definitions]",
                                        ),
                                        TextNode("."),
                                    ]
                                )
                            ],
                        ),
                    ],
                ),
                TitleNode(
                    title="Exhibit",
                    is_document_title=False,
                    has_attachment_placeholder=True,
                    subtitle="Statement of Work",
                    children=[
                        ParagraphNode(children=[TextNode("Work description here.")])
                    ],
                ),
            ]
        )

        renderer = MarkdownRenderer()
        output = renderer.render(document)

        # Check document structure
        assert "# Master Services Agreement" in output
        assert "1. **Definitions** {#definitions}" in output  # Has anchor
        assert "2. **Payment**\n" in output  # No anchor (not cross-referenced)
        assert "# Exhibit A" in output
        assert "Statement of Work" in output

        # Check defined term
        assert "(the **Company**)" in output

        # Check cross-reference
        assert "[Section 1](#definitions)" in output


class TestConfigurationIntegration:
    """Test various configuration combinations."""

    def test_custom_cross_reference_config(self) -> None:
        """Test custom cross-reference configuration."""
        document = DocumentNode(
            children=[
                SectionNode(level=1, title="Test Section", children=[]),
                ParagraphNode(
                    children=[
                        CrossReferenceNode(
                            reference_key="test-section",
                            original_text="[#test-section]",
                        )
                    ]
                ),
            ]
        )

        config = MarkdownConfig(
            cross_references=CrossReferenceConfig(
                template="({number})", generate_links=False
            )
        )
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "(1)" in output
        assert "[" not in output  # No links generated

    def test_custom_defined_term_style(self) -> None:
        """Test custom defined term styling."""
        document = DocumentNode(
            children=[
                ParagraphNode(
                    children=[
                        TextNode("Company "),
                        DefinedTermNode(term="ABC Corp", descriptor=None),
                    ]
                )
            ]
        )

        config = MarkdownConfig(defined_term_style=TextStyle.CODE)
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "(`ABC Corp`)" in output

    def test_heading_base_level_config(self) -> None:
        """Test custom heading base level (no longer used but config still exists)."""
        document = DocumentNode(
            children=[SectionNode(level=1, title="Test", children=[])]
        )

        config = MarkdownConfig(
            heading_base_level=3, anchor_generation=AnchorGeneration.ALL
        )
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "1. **Test** {#test}" in output  # Plain format regardless of base level

    def test_section_indent_config(self) -> None:
        """Test custom section indentation."""
        document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="First",
                    children=[
                        SectionNode(
                            level=2,
                            title="Second",
                            children=[SectionNode(level=3, title="Third", children=[])],
                        )
                    ],
                )
            ]
        )

        # Test default indentation (4 spaces)
        config = MarkdownConfig(anchor_generation=AnchorGeneration.ALL)
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        assert "1. **First** {#first}" in output
        assert "    1.1. *Second* {#second}" in output  # Level 2 uses italic
        assert "        1.1.1. Third {#third}" in output  # Level 3 uses plain

        # Test tab indentation
        config_tab = MarkdownConfig(
            section_indent="\t", anchor_generation=AnchorGeneration.ALL
        )
        renderer_tab = MarkdownRenderer(config_tab)
        output_tab = renderer_tab.render(document)

        assert "1. **First** {#first}" in output_tab
        assert "\t1.1. *Second* {#second}" in output_tab
        assert "\t\t1.1.1. Third {#third}" in output_tab

        # Test 2-space indentation
        config_2space = MarkdownConfig(
            section_indent="  ", anchor_generation=AnchorGeneration.ALL
        )
        renderer_2space = MarkdownRenderer(config_2space)
        output_2space = renderer_2space.render(document)

        assert "1. **First** {#first}" in output_2space
        assert "  1.1. *Second* {#second}" in output_2space
        assert "    1.1.1. Third {#third}" in output_2space

    def test_section_content_placement_config(self) -> None:
        """Test section content placement options."""
        # Test with titled section
        titled_document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="Payment Terms",
                    children=[
                        ParagraphNode(
                            children=[TextNode("Payment is due within 30 days.")]
                        ),
                        ParagraphNode(
                            children=[TextNode("Late fees apply after grace period.")]
                        ),
                    ],
                )
            ]
        )

        # Test NEWLINE placement (default)
        config_newline = MarkdownConfig(
            section_content_placement=SectionContentPlacement.NEWLINE,
            anchor_generation=AnchorGeneration.ALL,
        )
        renderer_newline = MarkdownRenderer(config_newline)
        output_newline = renderer_newline.render(titled_document)

        assert "1. **Payment Terms** {#payment-terms}" in output_newline
        assert "Payment is due within 30 days." in output_newline
        # Content should be on separate lines
        lines = output_newline.split("\n")
        title_line_idx = next(
            i for i, line in enumerate(lines) if "Payment Terms" in line
        )
        assert lines[title_line_idx + 1] == ""  # Empty line after title
        assert "Payment is due within 30 days." in lines[title_line_idx + 2]

        # Test INLINE placement
        config_inline = MarkdownConfig(
            section_content_placement=SectionContentPlacement.INLINE,
            anchor_generation=AnchorGeneration.ALL,
        )
        renderer_inline = MarkdownRenderer(config_inline)
        output_inline = renderer_inline.render(titled_document)

        # First content should be on same line as title, with period after title
        expected_inline = (
            "1. **Payment Terms**. {#payment-terms} Payment is due within 30 days."
        )
        assert expected_inline in output_inline
        # Second paragraph should be on separate line
        assert "Late fees apply after grace period." in output_inline

    def test_untitled_section_content_placement(self) -> None:
        """Test that untitled sections always have inline content."""
        untitled_document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title=None,
                    children=[
                        ParagraphNode(
                            children=[TextNode("Payment is due within 30 days.")]
                        ),
                        ParagraphNode(
                            children=[TextNode("Late fees apply after grace period.")]
                        ),
                    ],
                )
            ]
        )

        # Test with NEWLINE config - should still be inline for untitled sections
        config_newline = MarkdownConfig(
            section_content_placement=SectionContentPlacement.NEWLINE
        )
        renderer_newline = MarkdownRenderer(config_newline)
        output_newline = renderer_newline.render(untitled_document)

        # Content should start immediately after number
        assert "1. Payment is due within 30 days." in output_newline
        assert "Late fees apply after grace period." in output_newline

        # Test with INLINE config - should also be inline
        config_inline = MarkdownConfig(
            section_content_placement=SectionContentPlacement.INLINE
        )
        renderer_inline = MarkdownRenderer(config_inline)
        output_inline = renderer_inline.render(untitled_document)

        # Should be identical behavior
        assert "1. Payment is due within 30 days." in output_inline
        assert "Late fees apply after grace period." in output_inline

    def test_anchor_generation_config(self) -> None:
        """Test different anchor generation modes."""
        document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="Payment Terms",
                    children=[
                        ParagraphNode(
                            children=[TextNode("Payment is due within 30 days.")]
                        )
                    ],
                ),
                SectionNode(
                    level=1,
                    title="Definitions",
                    children=[
                        ParagraphNode(children=[TextNode("Terms are defined here.")])
                    ],
                ),
                ParagraphNode(
                    children=[
                        TextNode("See "),
                        CrossReferenceNode(
                            reference_key="payment-terms",
                            original_text="[#payment-terms]",
                        ),
                        TextNode(" for details."),
                    ]
                ),
            ]
        )

        # Test CROSS_REFERENCED mode (default) - only Payment Terms should have anchor
        config_cross_ref = MarkdownConfig(
            anchor_generation=AnchorGeneration.CROSS_REFERENCED
        )
        renderer_cross_ref = MarkdownRenderer(config_cross_ref)
        output_cross_ref = renderer_cross_ref.render(document)

        assert "1. **Payment Terms** {#payment-terms}" in output_cross_ref
        assert "2. **Definitions**\n" in output_cross_ref  # No anchor
        assert "[Section 1](#payment-terms)" in output_cross_ref

        # Test ALL mode - both sections should have anchors
        config_all = MarkdownConfig(anchor_generation=AnchorGeneration.ALL)
        renderer_all = MarkdownRenderer(config_all)
        output_all = renderer_all.render(document)

        assert "1. **Payment Terms** {#payment-terms}" in output_all
        assert "2. **Definitions** {#definitions}" in output_all
        assert "[Section 1](#payment-terms)" in output_all

        # Test NONE mode - no anchors should be generated
        config_none = MarkdownConfig(anchor_generation=AnchorGeneration.NONE)
        renderer_none = MarkdownRenderer(config_none)
        output_none = renderer_none.render(document)

        assert "1. **Payment Terms**\n" in output_none  # No anchor
        assert "2. **Definitions**\n" in output_none  # No anchor
        # Cross-reference still works but without links
        assert "Section 1" in output_none  # No link generated since no anchor

    def test_anchor_generation_with_multiple_references(self) -> None:
        """Test anchor generation when multiple sections reference the same section."""
        document = DocumentNode(
            children=[
                SectionNode(
                    level=1,
                    title="Payment Terms",
                    children=[ParagraphNode(children=[TextNode("Payment details.")])],
                ),
                SectionNode(
                    level=1,
                    title="Late Fees",
                    children=[ParagraphNode(children=[TextNode("Late fee details.")])],
                ),
                SectionNode(
                    level=1,
                    title="Summary",
                    children=[
                        ParagraphNode(
                            children=[
                                TextNode("See "),
                                CrossReferenceNode(
                                    reference_key="payment-terms",
                                    original_text="[#payment-terms]",
                                ),
                                TextNode(" and "),
                                CrossReferenceNode(
                                    reference_key="payment-terms",
                                    original_text="[#payment-terms]",
                                ),
                                TextNode(" again."),
                            ]
                        )
                    ],
                ),
            ]
        )

        config = MarkdownConfig(anchor_generation=AnchorGeneration.CROSS_REFERENCED)
        renderer = MarkdownRenderer(config)
        output = renderer.render(document)

        # Payment Terms should have anchor (referenced twice)
        assert "1. **Payment Terms** {#payment-terms}" in output
        # Late Fees should not have anchor (not referenced)
        assert "2. **Late Fees**\n" in output
        # Summary should not have anchor (not referenced)
        assert "3. **Summary**\n" in output

    def test_cross_reference_formatting_strips_periods(self) -> None:
        """Test cross-references strip trailing periods but preserve parentheses."""
        document = DocumentNode(
            children=[
                # Section with decimal numbering (has period suffix)
                SectionNode(
                    level=1,
                    title="Payment Terms",
                    children=[ParagraphNode(children=[TextNode("Payment details.")])],
                ),
                # Subsection with legal numbering (has parentheses, no trailing period)
                SectionNode(
                    level=2,
                    title="Late Fees",
                    children=[ParagraphNode(children=[TextNode("Late fee details.")])],
                ),
                # Cross-references to both
                ParagraphNode(
                    children=[
                        TextNode("See "),
                        CrossReferenceNode(
                            reference_key="payment-terms",
                            original_text="[#payment-terms]",
                        ),
                        TextNode(" and "),
                        CrossReferenceNode(
                            reference_key="late-fees",
                            original_text="[#late-fees]",
                        ),
                        TextNode("."),
                    ]
                ),
            ]
        )

        # Test with decimal preset (has period suffixes)
        config_decimal = MarkdownConfig(
            section_numbering=NumberingScheme.from_preset("decimal"),
            anchor_generation=AnchorGeneration.ALL,
        )
        renderer_decimal = MarkdownRenderer(config_decimal)
        output_decimal = renderer_decimal.render(document)

        # Cross-references should strip trailing periods
        assert "[Section 1](#payment-terms)" in output_decimal  # Not "Section 1."
        assert "[Section 1.1](#late-fees)" in output_decimal    # Not "Section 1.1."

        # Test with legal preset (has parentheses but no trailing periods)
        config_legal = MarkdownConfig(
            section_numbering=NumberingScheme.from_preset("legal"),
            anchor_generation=AnchorGeneration.ALL,
        )
        renderer_legal = MarkdownRenderer(config_legal)
        output_legal = renderer_legal.render(document)

        # Cross-references should preserve parentheses
        assert "[Section 1](#payment-terms)" in output_legal    # No period to strip
        assert "[Section 1(a)](#late-fees)" in output_legal    # Parentheses preserved


if __name__ == "__main__":
    pytest.main([__file__])

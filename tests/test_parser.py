"""
Tests for KLMD parser and AST nodes.
"""

from klmd.parser import (
    CrossReferenceNode,
    DocumentNode,
    KLMDParser,
    ParagraphNode,
    SectionNode,
    TextNode,
    TitleNode,
    TitleRegistry,
)


class TestTitleRegistry:
    """Test the TitleRegistry helper class."""

    def test_basic_registration_and_existence(self) -> None:
        """Test basic title registration and existence checking."""
        registry = TitleRegistry()
        
        registry.register("Payment Terms")
        registry.register("Confidentiality")
        
        assert registry.exists("payment-terms") is True
        assert registry.exists("confidentiality") is True
        assert registry.exists("nonexistent") is False

    def test_case_insensitive_matching(self) -> None:
        """Test case-insensitive title matching."""
        registry = TitleRegistry()
        
        registry.register("Payment Terms")
        
        # All these should match the same title
        assert registry.exists("payment-terms") is True
        assert registry.exists("Payment-Terms") is True
        assert registry.exists("PAYMENT-TERMS") is True

    def test_duplicate_detection(self) -> None:
        """Test duplicate title detection."""
        registry = TitleRegistry()
        
        registry.register("Terms")
        registry.register("Terms")  # Duplicate
        
        errors = registry.get_duplicate_errors()
        assert len(errors) == 1
        assert "Terms" in errors[0]

    def test_normalization(self) -> None:
        """Test title normalization."""
        registry = TitleRegistry()
        
        # Spaces should become hyphens
        normalized = registry._normalize_title("Payment Terms")
        assert normalized == "payment-terms"
        
        # Mixed case should become lowercase
        normalized = registry._normalize_title("PAYMENT TERMS")
        assert normalized == "payment-terms"


class TestKLMDParser:
    """Test the KLMD parser."""

    def test_simple_text_line(self) -> None:
        """Test parsing a single line of text."""
        parser = KLMDParser()
        text = "This is just a simple line of text."

        doc = parser.parse(text)

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ParagraphNode)

        paragraph = doc.children[0]
        assert len(paragraph.children) == 1
        text_node = paragraph.children[0]
        assert isinstance(text_node, TextNode)
        assert text_node.text == "This is just a simple line of text."

    def test_two_lines_of_text(self) -> None:
        """Test parsing two lines of text that form one paragraph."""
        parser = KLMDParser()
        text = """First line of text.
Second line of text."""

        doc = parser.parse(text)

        assert len(doc.children) == 1
        assert isinstance(doc.children[0], ParagraphNode)

        paragraph = doc.children[0]
        assert len(paragraph.children) == 1
        text_node = paragraph.children[0]
        assert isinstance(text_node, TextNode)
        assert text_node.text == "First line of text. Second line of text."

    def test_paragraph_creation(self) -> None:
        """Test paragraph creation from multiple lines."""
        parser = KLMDParser()
        text = """First line of paragraph.
Second line of paragraph.

Another paragraph starts here.
With another line."""

        doc = parser.parse(text)

        assert len(doc.children) == 2
        assert all(isinstance(child, ParagraphNode) for child in doc.children)

        # First paragraph should combine two lines
        first_para = doc.children[0]
        assert isinstance(first_para, ParagraphNode)
        assert len(first_para.children) == 1
        first_text = first_para.children[0]
        assert isinstance(first_text, TextNode)
        assert first_text.text == "First line of paragraph. Second line of paragraph."

        # Second paragraph
        second_para = doc.children[1]
        assert isinstance(second_para, ParagraphNode)
        second_text = second_para.children[0]
        assert isinstance(second_text, TextNode)
        assert second_text.text == "Another paragraph starts here. With another line."

    def test_parse_simple_section(self) -> None:
        """Test parsing a simple section."""
        parser = KLMDParser()
        text = "[#] This is Section 1."

        doc = parser.parse(text)

        assert isinstance(doc, DocumentNode)
        assert len(doc.children) == 1

        section = doc.children[0]
        assert isinstance(section, SectionNode)
        assert section.level == 1
        assert section.title is None
        assert len(section.children) == 1
        assert isinstance(section.children[0], TextNode)
        content_node = section.children[0]
        assert isinstance(content_node, TextNode)
        assert content_node.text == "This is Section 1."

    def test_parse_section_with_title(self) -> None:
        """Test parsing a section with a title."""
        parser = KLMDParser()
        text = (
            "[# Definitions] The following terms shall have the meanings "
            "set forth below."
        )

        doc = parser.parse(text)
        section = doc.children[0]

        assert isinstance(section, SectionNode)
        assert section.level == 1
        assert section.title == "Definitions"
        content_node = section.children[0]
        assert isinstance(content_node, TextNode)
        expected_text = "The following terms shall have the meanings set forth below."
        assert content_node.text == expected_text

    def test_parse_hierarchical_sections(self) -> None:
        """Test parsing the hierarchical example from the spec."""
        parser = KLMDParser()
        text = """[#] This is Section 1.
   [##] This is Section 1.1.
      [###] This is Section 1.1.1.
   [##] This is Section 1.2.
[#] This is Section 2.
   [##] This is Section 2.1."""

        doc = parser.parse(text)

        # Should have 6 sections
        sections = [child for child in doc.children if isinstance(child, SectionNode)]
        assert len(sections) == 6

        # Check section levels
        assert sections[0].level == 1
        assert sections[1].level == 2
        assert sections[2].level == 3
        assert sections[3].level == 2
        assert sections[4].level == 1
        assert sections[5].level == 2

    def test_parse_titled_sections_example(self) -> None:
        """Test parsing the titled sections example from the spec."""
        parser = KLMDParser()
        text = """[# Definitions] The following terms shall have the meanings \
set forth below.
[##] "Agreement" means this Master Services Agreement.
[##] "Services" means the services described in each Statement of Work.
[# Payment Terms] Client shall pay all fees within thirty (30) days.
[## Late Payments] Interest accrues at 1.5% per month on overdue amounts."""

        doc = parser.parse(text)
        sections = [child for child in doc.children if isinstance(child, SectionNode)]

        assert len(sections) == 5

        # Check titles and levels
        assert sections[0].title == "Definitions"
        assert sections[0].level == 1

        assert sections[1].title is None
        assert sections[1].level == 2

        assert sections[2].title is None
        assert sections[2].level == 2

        assert sections[3].title == "Payment Terms"
        assert sections[3].level == 1

        assert sections[4].title == "Late Payments"
        assert sections[4].level == 2

    def test_parse_mixed_content(self) -> None:
        """Test parsing mixed sections and paragraphs."""
        parser = KLMDParser()
        text = """This is a paragraph before sections.

[#] First Section
This is content under the first section.

[##] Subsection
More content here.

This is another paragraph."""

        doc = parser.parse(text)

        # Should have: paragraph, section, paragraph, section, paragraph, paragraph
        assert len(doc.children) == 6

        assert isinstance(doc.children[0], ParagraphNode)  # "This is a paragraph..."
        assert isinstance(doc.children[1], SectionNode)  # "[#] First Section"
        assert isinstance(doc.children[2], ParagraphNode)  # "This is content under..."
        assert isinstance(doc.children[3], SectionNode)  # "[##] Subsection"
        assert isinstance(doc.children[4], ParagraphNode)  # "More content here."
        assert isinstance(
            doc.children[5], ParagraphNode
        )  # "This is another paragraph."

        # Check section content (content on same line as section marker)
        section1 = doc.children[1]
        assert isinstance(section1, SectionNode)
        assert section1.level == 1
        content1 = section1.children[0]
        assert isinstance(content1, TextNode)
        assert content1.text == "First Section"

        section2 = doc.children[3]
        assert isinstance(section2, SectionNode)
        assert section2.level == 2
        content2 = section2.children[0]
        assert isinstance(content2, TextNode)
        assert content2.text == "Subsection"

    def test_empty_section_content(self) -> None:
        """Test sections with no content after the bracket."""
        parser = KLMDParser()
        text = "[#] "

        doc = parser.parse(text)
        section = doc.children[0]

        assert isinstance(section, SectionNode)
        assert len(section.children) == 0  # No content should be added for empty string

    def test_whitespace_handling(self) -> None:
        """Test that whitespace is handled correctly."""
        parser = KLMDParser()
        text = "   [#]    This has extra whitespace.   "

        doc = parser.parse(text)
        section = doc.children[0]

        assert isinstance(section, SectionNode)
        content_node = section.children[0]
        assert isinstance(content_node, TextNode)
        assert content_node.text == "This has extra whitespace."

    def test_parse_basic_document_title(self) -> None:
        """Test parsing a basic document title."""
        parser = KLMDParser()
        text = """Document Title
==============

Some content after the title."""

        doc = parser.parse(text)
        
        assert len(doc.children) == 2
        assert isinstance(doc.children[0], TitleNode)
        assert isinstance(doc.children[1], ParagraphNode)
        
        title = doc.children[0]
        assert title.title == "Document Title"
        assert title.is_document_title is True
        assert title.has_attachment_placeholder is False
        assert title.subtitle is None
        assert len(title.children) == 0

    def test_parse_attachment_title_without_number(self) -> None:
        """Test parsing an attachment title without [#]."""
        parser = KLMDParser()
        text = """Document Title
==============

[#] Section 1

Statement of Work
=================

[#] Attachment section."""

        doc = parser.parse(text)
        
        # Should have: doc title, section, attachment title, section
        assert len(doc.children) == 4
        
        doc_title = doc.children[0]
        assert isinstance(doc_title, TitleNode)
        assert doc_title.title == "Document Title"
        assert doc_title.is_document_title is True
        
        attachment_title = doc.children[2]
        assert isinstance(attachment_title, TitleNode)
        assert attachment_title.title == "Statement of Work"
        assert attachment_title.is_document_title is False
        assert attachment_title.has_attachment_placeholder is False
        assert attachment_title.subtitle is None

    def test_parse_attachment_with_number_placeholder(self) -> None:
        """Test parsing an attachment with [#] placeholder."""
        parser = KLMDParser()
        text = """Document Title
==============

Exhibit [#]
===========

[#] Section in exhibit."""

        doc = parser.parse(text)
        
        assert len(doc.children) == 3
        
        attachment_title = doc.children[1]
        assert isinstance(attachment_title, TitleNode)
        assert attachment_title.title == "Exhibit"
        assert attachment_title.is_document_title is False
        assert attachment_title.has_attachment_placeholder is True
        assert attachment_title.subtitle is None

    def test_parse_attachment_with_subtitle(self) -> None:
        """Test parsing an attachment with [# subtitle]."""
        parser = KLMDParser()
        text = """Schedule [# Pricing Terms]
==========================

[#] Base fees."""

        doc = parser.parse(text)
        
        assert len(doc.children) == 2
        
        attachment_title = doc.children[0]
        assert isinstance(attachment_title, TitleNode)
        assert attachment_title.title == "Schedule"
        assert attachment_title.is_document_title is True  # First title
        assert attachment_title.has_attachment_placeholder is True
        assert attachment_title.subtitle == "Pricing Terms"

    def test_multiple_attachments_numbering(self) -> None:
        """Test that multiple attachments get sequential numbers."""
        parser = KLMDParser()
        text = """Document
========

Exhibit [#]
===========

Schedule [#]
============

Appendix [# Additional Terms]
=============================="""

        doc = parser.parse(text)
        
        assert len(doc.children) == 4
        
        # First attachment
        exhibit = doc.children[1]
        assert isinstance(exhibit, TitleNode)
        assert exhibit.title == "Exhibit"
        assert exhibit.has_attachment_placeholder is True
        
        # Second attachment  
        schedule = doc.children[2]
        assert isinstance(schedule, TitleNode)
        assert schedule.title == "Schedule"
        assert schedule.has_attachment_placeholder is True
        
        # Third attachment
        appendix = doc.children[3]
        assert isinstance(appendix, TitleNode)
        assert appendix.title == "Appendix"
        assert appendix.has_attachment_placeholder is True
        assert appendix.subtitle == "Additional Terms"

    def test_section_counter_resets_in_attachments(self) -> None:
        """Test that section numbering resets within attachments."""
        parser = KLMDParser()
        text = """Main Document
=============

[#] Section 1 in main
[##] Section 1.1 in main

Statement of Work
=================

[#] Section 1 in SOW (reset)
[##] Section 1.1 in SOW

Exhibit [#]
===========

[#] Section 1 in exhibit (reset)"""

        doc = parser.parse(text)
        
        # Extract all section nodes
        sections = [child for child in doc.children if isinstance(child, SectionNode)]
        
        assert len(sections) == 5
        
        # Check section structure (numbering will be handled by renderer)
        assert sections[0].level == 1  # Main doc section
        assert sections[1].level == 2  # Main doc subsection
        assert sections[2].level == 1  # SOW section
        assert sections[3].level == 2  # SOW subsection
        assert sections[4].level == 1  # Exhibit section

    def test_title_with_minimum_equals(self) -> None:
        """Test title with exactly 3 equals signs."""
        parser = KLMDParser()
        text = """Title
===

Content after."""

        doc = parser.parse(text)
        
        assert len(doc.children) == 2
        title = doc.children[0]
        assert isinstance(title, TitleNode)
        assert title.title == "Title"

    def test_title_with_many_equals(self) -> None:
        """Test title with many equals signs."""
        parser = KLMDParser()
        text = """Title
===================

Content after."""

        doc = parser.parse(text)
        
        assert len(doc.children) == 2
        title = doc.children[0]
        assert isinstance(title, TitleNode)
        assert title.title == "Title"

    def test_title_at_end_of_document(self) -> None:
        """Test title at the end of document with no content after."""
        parser = KLMDParser()
        text = """Final Title
==========="""

        doc = parser.parse(text)
        
        assert len(doc.children) == 1
        title = doc.children[0]
        assert isinstance(title, TitleNode)
        assert title.title == "Final Title"
        assert len(title.children) == 0

    def test_empty_attachment_placeholder(self) -> None:
        """Test attachment with empty [#] placeholder."""
        parser = KLMDParser()
        text = """Document
========

Exhibit [#]
==========="""

        doc = parser.parse(text)
        
        exhibit = doc.children[1]
        assert isinstance(exhibit, TitleNode)
        assert exhibit.title == "Exhibit"
        assert exhibit.has_attachment_placeholder is True
        assert exhibit.subtitle is None

    def test_whitespace_in_attachment_subtitle(self) -> None:
        """Test attachment with whitespace in subtitle."""
        parser = KLMDParser()
        text = """Schedule [#  Terms and Conditions  ]
====================================="""

        doc = parser.parse(text)
        
        schedule = doc.children[0]
        assert isinstance(schedule, TitleNode)
        assert schedule.title == "Schedule"
        assert schedule.has_attachment_placeholder is True
        assert schedule.subtitle == "Terms and Conditions"

    def test_basic_cross_reference_to_section(self) -> None:
        """Test basic cross-reference to a section title."""
        parser = KLMDParser()
        text = """[# Payment Terms] Payment is due within 30 days.

Please refer to Section [#payment-terms] for details."""

        doc = parser.parse(text)
        
        # Should have: section, paragraph
        assert len(doc.children) == 2
        
        # Check the paragraph contains cross-reference
        paragraph = doc.children[1]
        assert isinstance(paragraph, ParagraphNode)
        assert len(paragraph.children) == 3  # Text, CrossRef, Text
        
        # Check cross-reference node
        cross_ref = paragraph.children[1]
        assert isinstance(cross_ref, CrossReferenceNode)
        assert cross_ref.reference_key == "payment-terms"
        assert cross_ref.original_text == "[#payment-terms]"

    def test_cross_reference_to_attachment(self) -> None:
        """Test cross-reference to an attachment title."""
        parser = KLMDParser()
        text = """Main Document
=============

Exhibit [# Terms]
=================

Please see Exhibit [#terms] for details."""

        doc = parser.parse(text)
        
        # Find the paragraph with the cross-reference
        paragraph = doc.children[2]
        assert isinstance(paragraph, ParagraphNode)
        
        # Check cross-reference
        cross_ref = paragraph.children[1]
        assert isinstance(cross_ref, CrossReferenceNode)
        assert cross_ref.reference_key == "terms"

    def test_multiple_cross_references_in_paragraph(self) -> None:
        """Test multiple cross-references in the same paragraph."""
        parser = KLMDParser()
        text = """[# Terms] General terms and conditions.
[# Privacy] Privacy policy details.

See Section [#terms] and Section [#privacy] for more info."""

        doc = parser.parse(text)
        
        # Check the paragraph with references
        paragraph = doc.children[2]
        assert isinstance(paragraph, ParagraphNode)
        assert len(paragraph.children) == 5  # Text, Ref, Text, Ref, Text
        
        # First cross-reference
        ref1 = paragraph.children[1]
        assert isinstance(ref1, CrossReferenceNode)
        assert ref1.reference_key == "terms"
        
        # Second cross-reference
        ref2 = paragraph.children[3]
        assert isinstance(ref2, CrossReferenceNode)
        assert ref2.reference_key == "privacy"

    def test_forward_reference(self) -> None:
        """Test forward reference (reference before definition)."""
        parser = KLMDParser()
        text = """See Section [#conclusion] for final thoughts.

[# Conclusion] This is the end of the document."""

        doc = parser.parse(text)
        
        # Check forward reference
        paragraph = doc.children[0]
        assert isinstance(paragraph, ParagraphNode)
        cross_ref = paragraph.children[1]
        assert isinstance(cross_ref, CrossReferenceNode)
        assert cross_ref.reference_key == "conclusion"

    def test_case_insensitive_cross_references(self) -> None:
        """Test case-insensitive cross-reference matching."""
        parser = KLMDParser()
        text = """[# Payment Terms] Payment details here.

Both [#payment-terms] and [#Payment-Terms] should work."""

        doc = parser.parse(text)
        
        paragraph = doc.children[1]
        assert isinstance(paragraph, ParagraphNode)
        
        # Both references should be parsed correctly
        ref1 = paragraph.children[1]
        ref2 = paragraph.children[3]
        assert isinstance(ref1, CrossReferenceNode)
        assert isinstance(ref2, CrossReferenceNode)
        assert ref1.reference_key == "payment-terms"
        assert ref2.reference_key == "payment-terms"

    def test_unresolved_cross_reference(self) -> None:
        """Test cross-reference that doesn't resolve to anything."""
        parser = KLMDParser()
        text = """[# Payment Terms] Payment details here.

Please see Section [#nonexistent-section] for more info."""

        doc = parser.parse(text)
        
        paragraph = doc.children[1]
        assert isinstance(paragraph, ParagraphNode)
        cross_ref = paragraph.children[1]
        assert isinstance(cross_ref, CrossReferenceNode)
        assert cross_ref.reference_key == "nonexistent-section"

    def test_duplicate_title_error(self) -> None:
        """Test that duplicate titles raise an error."""
        parser = KLMDParser()
        text = """[# Payment Terms] First definition.
[# Payment Terms] Duplicate definition."""

        # Should raise ValueError for duplicate titles
        try:
            parser.parse(text)
            raise AssertionError("Expected ValueError for duplicate titles")
        except ValueError as e:
            assert "Duplicate titles found" in str(e)
            assert "Payment Terms" in str(e)

    def test_cross_reference_in_section_content(self) -> None:
        """Test cross-reference within section content."""
        parser = KLMDParser()
        text = """[# Terms] General terms apply.
[# Privacy] See Section [#terms] for general provisions."""

        doc = parser.parse(text)
        
        # Second section should have cross-reference in its content
        section2 = doc.children[1]
        assert isinstance(section2, SectionNode)
        
        # Section content should have the cross-reference
        cross_ref = section2.children[1]  # Content has: Text, CrossRef, Text
        assert isinstance(cross_ref, CrossReferenceNode)
        assert cross_ref.reference_key == "terms"

"""
Tests for KLMD parser and AST nodes.
"""

from klmd.parser import (
    DocumentNode,
    KLMDParser,
    ParagraphNode,
    SectionCounter,
    SectionNode,
    TextNode,
)


class TestSectionCounter:
    """Test the SectionCounter helper class."""

    def test_basic_numbering(self) -> None:
        """Test basic sequential numbering."""
        counter = SectionCounter()

        counter.increment(1)
        assert counter.get_number(1) == "1"

        counter.increment(1)
        assert counter.get_number(1) == "2"

        counter.increment(1)
        assert counter.get_number(1) == "3"

    def test_hierarchical_numbering(self) -> None:
        """Test hierarchical section numbering."""
        counter = SectionCounter()

        # Level 1 sections
        counter.increment(1)
        assert counter.get_number(1) == "1"

        # Level 2 subsections
        counter.increment(2)
        assert counter.get_number(2) == "1.1"

        counter.increment(2)
        assert counter.get_number(2) == "1.2"

        # Level 3 subsection
        counter.increment(3)
        assert counter.get_number(3) == "1.2.1"

        # Back to level 2
        counter.increment(2)
        assert counter.get_number(2) == "1.3"

        # New level 1 section (resets deeper levels)
        counter.increment(1)
        assert counter.get_number(1) == "2"

        counter.increment(2)
        assert counter.get_number(2) == "2.1"

    def test_reset(self) -> None:
        """Test counter reset functionality."""
        counter = SectionCounter()

        counter.increment(1)
        counter.increment(2)
        assert counter.get_number(2) == "1.1"

        counter.reset()
        counter.increment(1)
        assert counter.get_number(1) == "1"


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
        assert section.number == "1"
        assert len(section.content) == 1
        assert isinstance(section.content[0], TextNode)
        content_node = section.content[0]
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
        assert section.number == "1"
        content_node = section.content[0]
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

        # Should have 5 sections
        sections = [child for child in doc.children if isinstance(child, SectionNode)]
        assert len(sections) == 6

        # Check section numbers
        assert sections[0].number == "1"
        assert sections[0].level == 1

        assert sections[1].number == "1.1"
        assert sections[1].level == 2

        assert sections[2].number == "1.1.1"
        assert sections[2].level == 3

        assert sections[3].number == "1.2"
        assert sections[3].level == 2

        assert sections[4].number == "2"
        assert sections[4].level == 1

        assert sections[5].number == "2.1"
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

        # Check titles and numbers
        assert sections[0].title == "Definitions"
        assert sections[0].number == "1"

        assert sections[1].title is None
        assert sections[1].number == "1.1"

        assert sections[2].title is None
        assert sections[2].number == "1.2"

        assert sections[3].title == "Payment Terms"
        assert sections[3].number == "2"

        assert sections[4].title == "Late Payments"
        assert sections[4].number == "2.1"

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

        # Check section numbering
        assert doc.children[1].number == "1"
        assert doc.children[3].number == "1.1"

        # Check section content (content on same line as section marker)
        section1 = doc.children[1]
        assert isinstance(section1, SectionNode)
        content1 = section1.content[0]
        assert isinstance(content1, TextNode)
        assert content1.text == "First Section"

        section2 = doc.children[3]
        assert isinstance(section2, SectionNode)
        content2 = section2.content[0]
        assert isinstance(content2, TextNode)
        assert content2.text == "Subsection"

    def test_empty_section_content(self) -> None:
        """Test sections with no content after the bracket."""
        parser = KLMDParser()
        text = "[#] "

        doc = parser.parse(text)
        section = doc.children[0]

        assert isinstance(section, SectionNode)
        assert len(section.content) == 0  # No content should be added for empty string

    def test_whitespace_handling(self) -> None:
        """Test that whitespace is handled correctly."""
        parser = KLMDParser()
        text = "   [#]    This has extra whitespace.   "

        doc = parser.parse(text)
        section = doc.children[0]

        assert isinstance(section, SectionNode)
        content_node = section.content[0]
        assert isinstance(content_node, TextNode)
        assert content_node.text == "This has extra whitespace."

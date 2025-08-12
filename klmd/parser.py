"""
KLMD Parser and AST Node Definitions

This module defines the Abstract Syntax Tree (AST) nodes for KLMD documents
and implements the parser for converting KLMD text into an AST.
"""

import re
from dataclasses import dataclass


class Node:
    """Base class for all AST nodes."""
    pass


@dataclass
class TextNode(Node):
    """Represents plain text content."""
    text: str


@dataclass
class ParagraphNode(Node):
    """Container for paragraph-level content."""
    children: list[Node]


@dataclass
class SectionNode(Node):
    """Represents a numbered section with optional title."""
    level: int  # 1 for [#], 2 for [##], etc.
    title: str | None  # Optional title text from within brackets
    content: list[Node]  # Child nodes containing section content
    number: str | None = None  # Generated section number, populated during rendering


@dataclass
class DocumentNode(Node):
    """Root container for the entire document."""
    children: list[Node]


class SectionCounter:
    """Manages hierarchical section numbering."""
    
    def __init__(self) -> None:
        self.counters: list[int] = []
    
    def reset(self) -> None:
        """Reset all counters (needed for attachments)."""
        self.counters = []
    
    def increment(self, level: int) -> None:
        """Increment counter at specified level."""
        # Ensure we have enough counter levels
        while len(self.counters) < level:
            self.counters.append(0)
        
        # Increment the counter at this level
        self.counters[level - 1] += 1
        
        # Reset deeper level counters
        if level < len(self.counters):
            self.counters = self.counters[:level]
    
    def get_number(self, level: int) -> str:
        """Get current formatted number (e.g., '1.2.3')."""
        if level > len(self.counters):
            return ""
        
        numbers = [str(counter) for counter in self.counters[:level]]
        return ".".join(numbers)


class KLMDParser:
    """Parser for KLMD syntax."""
    
    SECTION_PATTERN = re.compile(r'^(\s*)\[([#]+)([^\]]*)\]\s*(.*)$')
    
    def __init__(self) -> None:
        self.section_counter = SectionCounter()
    
    def parse(self, text: str) -> DocumentNode:
        """Parse KLMD text into an AST."""
        lines = text.split('\n')
        children: list[Node] = []
        current_paragraph_lines: list[str] = []
        
        for line in lines:
            section_match = self.SECTION_PATTERN.match(line)
            
            if section_match:
                # Finish any pending paragraph
                if current_paragraph_lines:
                    paragraph = self._create_paragraph(current_paragraph_lines)
                    if paragraph:
                        children.append(paragraph)
                    current_paragraph_lines = []
                
                # Parse section
                section = self._parse_section(section_match)
                children.append(section)
            else:
                # Regular line - add to current paragraph
                if line.strip():  # Only add non-empty lines
                    current_paragraph_lines.append(line)
                elif current_paragraph_lines:
                    # Empty line ends paragraph
                    paragraph = self._create_paragraph(current_paragraph_lines)
                    if paragraph:
                        children.append(paragraph)
                    current_paragraph_lines = []
        
        # Finish any remaining paragraph
        if current_paragraph_lines:
            paragraph = self._create_paragraph(current_paragraph_lines)
            if paragraph:
                children.append(paragraph)
        
        return DocumentNode(children=children)
    
    def _parse_section(self, match: re.Match[str]) -> SectionNode:
        """Parse a section from regex match."""
        _, hashes, title_text, content = match.groups()
        
        level = len(hashes)
        title = title_text.strip() if title_text.strip() else None
        
        # Increment section counter and get number
        self.section_counter.increment(level)
        number = self.section_counter.get_number(level)
        
        # For now, treat content as a single text node
        content_nodes: list[Node] = (
            [TextNode(text=content.strip())] if content.strip() else []
        )
        
        return SectionNode(
            level=level,
            title=title,
            content=content_nodes,
            number=number
        )
    
    def _create_paragraph(self, lines: list[str]) -> ParagraphNode | None:
        """Create a paragraph node from lines of text."""
        if not lines:
            return None
        
        # Join lines with spaces and create a single text node
        text = ' '.join(line.strip() for line in lines if line.strip())
        if not text:
            return None
        
        return ParagraphNode(children=[TextNode(text=text)])
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


@dataclass
class TitleNode(Node):
    """Represents a document or attachment title."""
    title: str  # Main title text (with [#] removed if present)
    is_document_title: bool  # True only for first title in document
    attachment_number: int | None  # Set ONLY if original had [#], None otherwise
    subtitle: str | None  # Optional text after [#] (e.g., "Pricing Terms")
    children: list[Node]  # Content that follows this title


@dataclass
class CrossReferenceNode(Node):
    """Represents an inline cross-reference to a section or attachment."""
    reference_key: str  # Normalized title (lowercase, spaces→hyphens)
    original_text: str  # Original text for error messages
    resolved_number: str | None = None  # Filled during resolution


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


class AttachmentCounter:
    """Manages attachment numbering."""
    
    def __init__(self) -> None:
        self.counter: int = 0
    
    def increment(self) -> int:
        """Increment counter and return new value."""
        self.counter += 1
        return self.counter


class TitleRegistry:
    """Tracks all section and attachment titles for cross-reference resolution."""
    
    def __init__(self) -> None:
        self.titles: dict[str, str] = {}  # normalized_title → number
        self.duplicates: list[str] = []  # Track duplicates for error reporting
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for case-insensitive matching."""
        return title.lower().replace(' ', '-')
    
    def register(self, title: str, number: str) -> None:
        """Register a title with its number. Detects duplicates."""
        if not title:
            return
        
        normalized = self._normalize_title(title)
        if normalized in self.titles:
            self.duplicates.append(title)
        else:
            self.titles[normalized] = number
    
    def resolve(self, reference_key: str) -> str | None:
        """Resolve a reference key to its number."""
        return self.titles.get(reference_key.lower())
    
    def get_duplicate_errors(self) -> list[str]:
        """Get list of duplicate title errors."""
        return [f"Duplicate title: '{title}'" for title in self.duplicates]


class KLMDParser:
    """Parser for KLMD syntax."""
    
    SECTION_PATTERN = re.compile(r'^(\s*)\[([#]+)([^\]]*)\]\s*(.*)$')
    ATTACHMENT_PATTERN = re.compile(r'\[#\s*([^\]]*)\]')
    CROSS_REF_PATTERN = re.compile(r'\[#([^\]]+)\]')
    
    def __init__(self) -> None:
        self.section_counter = SectionCounter()
        self.attachment_counter = AttachmentCounter()
        self.title_registry = TitleRegistry()
        self.has_document_title = False
    
    def parse(self, text: str) -> DocumentNode:
        """Parse KLMD text into an AST."""
        lines = text.split('\n')
        children: list[Node] = []
        current_paragraph_lines: list[str] = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for title pattern (line followed by equals)
            if (i + 1 < len(lines) and 
                line.strip() and 
                self._is_equals_line(lines[i + 1])):
                
                # Finish any pending paragraph
                if current_paragraph_lines:
                    paragraph = self._create_paragraph(current_paragraph_lines)
                    if paragraph:
                        children.append(paragraph)
                    current_paragraph_lines = []
                
                # Parse title
                title = self._parse_title_block(line)
                children.append(title)
                
                # Skip the equals line
                i += 2
                continue
            
            # Check for section pattern
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
            
            i += 1
        
        # Finish any remaining paragraph
        if current_paragraph_lines:
            paragraph = self._create_paragraph(current_paragraph_lines)
            if paragraph:
                children.append(paragraph)
        
        # Create document node
        document = DocumentNode(children=children)
        
        # Resolve all cross-references
        for child in document.children:
            self._resolve_cross_references(child)
        
        # Check for duplicate title errors
        duplicate_errors = self.title_registry.get_duplicate_errors()
        if duplicate_errors:
            raise ValueError(f"Duplicate titles found: {'; '.join(duplicate_errors)}")
        
        return document
    
    def _parse_section(self, match: re.Match[str]) -> SectionNode:
        """Parse a section from regex match."""
        _, hashes, title_text, content = match.groups()
        
        level = len(hashes)
        title = title_text.strip() if title_text.strip() else None
        
        # Increment section counter and get number
        self.section_counter.increment(level)
        number = self.section_counter.get_number(level)
        
        # Register title for cross-references (if title exists)
        if title:
            self.title_registry.register(title, number)
        
        # Parse content to handle cross-references
        content_nodes: list[Node] = (
            self._parse_text_with_refs(content.strip()) if content.strip() else []
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
        
        # Join lines with spaces and parse for cross-references
        text = ' '.join(line.strip() for line in lines if line.strip())
        if not text:
            return None
        
        # Parse text to handle cross-references
        children = self._parse_text_with_refs(text)
        if not children:
            return None
        
        return ParagraphNode(children=children)
    
    def _parse_title_block(self, title_line: str) -> TitleNode:
        """Parse a title line into a TitleNode."""
        # Check if this is the first title
        is_document_title = not self.has_document_title
        if is_document_title:
            self.has_document_title = True
        
        # Look for [#] pattern in title
        attachment_match = self.ATTACHMENT_PATTERN.search(title_line)
        attachment_number = None
        subtitle = None
        
        if attachment_match:
            subtitle_text = attachment_match.group(1).strip()
            subtitle = subtitle_text if subtitle_text else None
            
            # Remove the [#] pattern from title
            title = self.ATTACHMENT_PATTERN.sub('', title_line).strip()
            
            # Only assign attachment number if this is not a document title
            if not is_document_title:
                attachment_number = self.attachment_counter.increment()
        else:
            title = title_line.strip()
        
        # Reset section counter for all non-document titles
        if not is_document_title:
            self.section_counter.reset()
        
        # Register title for cross-references (for attachments with numbers)
        if attachment_number is not None:
            # For now, register with numeric attachment number
            # Renderer will decide format (A, B, C vs 1, 2, 3)
            attachment_ref = f"{title} {attachment_number}"
            self.title_registry.register(title, attachment_ref)
            
            # Also register with subtitle if present
            if subtitle:
                self.title_registry.register(subtitle, attachment_ref)
        
        return TitleNode(
            title=title,
            is_document_title=is_document_title,
            attachment_number=attachment_number,
            subtitle=subtitle,
            children=[]
        )
    
    def _is_equals_line(self, line: str) -> bool:
        """Check if line is an equals line (3+ equals signs)."""
        stripped = line.strip()
        return len(stripped) >= 3 and all(c == '=' for c in stripped)
    
    def _parse_text_with_refs(self, text: str) -> list[Node]:
        """Parse text content, splitting into TextNode and CrossReferenceNode parts."""
        if not text.strip():
            return []
        
        nodes: list[Node] = []
        last_end = 0
        
        # Find all cross-reference patterns
        for match in self.CROSS_REF_PATTERN.finditer(text):
            start, end = match.span()
            
            # Add text before the reference as TextNode
            if start > last_end:
                text_content = text[last_end:start]
                if text_content:
                    nodes.append(TextNode(text=text_content))
            
            # Add the cross-reference as CrossReferenceNode
            reference_text = match.group(1).strip()
            reference_key = reference_text.lower().replace(' ', '-')
            original_text = match.group(0)
            
            nodes.append(CrossReferenceNode(
                reference_key=reference_key,
                original_text=original_text
            ))
            
            last_end = end
        
        # Add remaining text after last reference
        if last_end < len(text):
            text_content = text[last_end:]
            if text_content:
                nodes.append(TextNode(text=text_content))
        
        # If no references found, return single TextNode
        if not nodes:
            nodes.append(TextNode(text=text))
        
        return nodes
    
    def _resolve_cross_references(self, node: Node) -> None:
        """Recursively resolve all cross-references in the AST."""
        if isinstance(node, CrossReferenceNode):
            # Resolve this cross-reference
            resolved = self.title_registry.resolve(node.reference_key)
            if resolved:
                node.resolved_number = resolved
        
        # Recursively process children
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                self._resolve_cross_references(child)
        
        # Handle SectionNode content
        if isinstance(node, SectionNode) and node.content:
            for content_node in node.content:
                self._resolve_cross_references(content_node)
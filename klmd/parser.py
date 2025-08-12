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
    children: list[Node]  # Child nodes containing section content


@dataclass
class DocumentNode(Node):
    """Root container for the entire document."""
    children: list[Node]


@dataclass
class TitleNode(Node):
    """Represents a document or attachment title."""
    title: str  # Main title text (with [#] removed if present)
    is_document_title: bool  # True only for first title in document
    has_attachment_placeholder: bool  # True if original had [#] pattern
    subtitle: str | None  # Optional text after [#] (e.g., "Pricing Terms")
    children: list[Node]  # Content that follows this title


@dataclass
class CrossReferenceNode(Node):
    """Represents an inline cross-reference to a section or attachment."""
    reference_key: str  # Normalized title (lowercase, spaces→hyphens)
    original_text: str  # Original text for error messages



class TitleRegistry:
    """Tracks all section and attachment titles for cross-reference validation."""
    
    def __init__(self) -> None:
        self.titles: set[str] = set()  # Set of normalized titles
        self.duplicates: list[str] = []  # Track duplicates for error reporting
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for case-insensitive matching."""
        return title.lower().replace(' ', '-')
    
    def register(self, title: str) -> None:
        """Register that a title exists. Detects duplicates."""
        if not title:
            return
        
        normalized = self._normalize_title(title)
        if normalized in self.titles:
            self.duplicates.append(title)
        else:
            self.titles.add(normalized)
    
    def exists(self, reference_key: str) -> bool:
        """Check if a reference key exists."""
        return reference_key.lower() in self.titles
    
    def get_duplicate_errors(self) -> list[str]:
        """Get list of duplicate title errors."""
        return [f"Duplicate title: '{title}'" for title in self.duplicates]


class KLMDParser:
    """Parser for KLMD syntax."""
    
    SECTION_PATTERN = re.compile(r'^(\s*)\[([#]+)([^\]]*)\]\s*(.*)$')
    ATTACHMENT_PATTERN = re.compile(r'\[#\s*([^\]]*)\]')
    CROSS_REF_PATTERN = re.compile(r'\[#([^\]]+)\]')
    
    def __init__(self) -> None:
        self.title_registry = TitleRegistry()
        self.has_document_title = False
        self.attachment_count = 0  # Track count for TitleNode metadata
    
    def parse(self, text: str) -> DocumentNode:
        """Parse KLMD text into an AST."""
        lines = text.split('\n')
        
        # Phase 1: Build AST
        children = self._parse_lines(lines)
        document = DocumentNode(children=children)
        
        # Phase 2: Validate cross-references
        self._validate_cross_references(document)
        
        # Phase 3: Check for errors
        self._check_for_errors()
        
        return document
    
    def _validate_cross_references(self, document: DocumentNode) -> None:
        """Validate all cross-references in the document."""
        validator = CrossReferenceValidator(self.title_registry)
        for child in document.children:
            validator.visit(child)
        
        # Collect unresolved reference errors
        ref_errors = validator.get_errors()
        if ref_errors:
            # For now, just warn about unresolved references
            # In the future, this could be configurable
            pass  # TODO: Add warning mechanism
    
    def _check_for_errors(self) -> None:
        """Check for parsing errors and raise if any found."""
        duplicate_errors = self.title_registry.get_duplicate_errors()
        if duplicate_errors:
            error_msg = f"Duplicate titles found: {'; '.join(duplicate_errors)}"
            raise ValueError(error_msg)
    
    def _parse_lines(self, lines: list[str]) -> list[Node]:
        """Parse lines into a list of nodes."""
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
                self._finish_paragraph(current_paragraph_lines, children)
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
                self._finish_paragraph(current_paragraph_lines, children)
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
                    self._finish_paragraph(current_paragraph_lines, children)
                    current_paragraph_lines = []
            
            i += 1
        
        # Finish any remaining paragraph
        self._finish_paragraph(current_paragraph_lines, children)
        
        return children
    
    def _finish_paragraph(
        self, paragraph_lines: list[str], children: list[Node]
    ) -> None:
        """Create paragraph from accumulated lines and add to children if non-empty."""
        if paragraph_lines:
            paragraph = self._create_paragraph(paragraph_lines)
            if paragraph:
                children.append(paragraph)
    
    def _parse_section(self, match: re.Match[str]) -> SectionNode:
        """Parse a section from regex match."""
        _, hashes, title_text, content = match.groups()
        
        level = len(hashes)
        title = title_text.strip() if title_text.strip() else None
        
        # Register title for cross-reference validation (if title exists)
        if title:
            self.title_registry.register(title)
        
        # Parse content to handle cross-references
        content_nodes: list[Node] = (
            self._parse_text_with_refs(content.strip()) if content.strip() else []
        )
        
        return SectionNode(
            level=level,
            title=title,
            children=content_nodes
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
        has_attachment_placeholder = attachment_match is not None
        subtitle = None
        
        if attachment_match:
            subtitle_text = attachment_match.group(1).strip()
            subtitle = subtitle_text if subtitle_text else None
            
            # Remove the [#] pattern from title
            title = self.ATTACHMENT_PATTERN.sub('', title_line).strip()
        else:
            title = title_line.strip()
        
        # Register title for cross-reference validation
        if title:
            self.title_registry.register(title)
        
        # Also register subtitle if present
        if subtitle:
            self.title_registry.register(subtitle)
        
        return TitleNode(
            title=title,
            is_document_title=is_document_title,
            has_attachment_placeholder=has_attachment_placeholder,
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
    
class CrossReferenceValidator:
    """Visitor for validating cross-references in the AST."""
    
    def __init__(self, title_registry: TitleRegistry) -> None:
        self.title_registry = title_registry
        self.unresolved_refs: list[str] = []
    
    def visit(self, node: Node) -> None:
        """Visit a node and all its children."""
        if (isinstance(node, CrossReferenceNode) 
            and not self.title_registry.exists(node.reference_key)):
            error_msg = f"Unresolved reference: {node.original_text}"
            self.unresolved_refs.append(error_msg)
        
        # Visit children
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                self.visit(child)
    
    def get_errors(self) -> list[str]:
        """Get list of unresolved reference errors."""
        return self.unresolved_refs.copy()
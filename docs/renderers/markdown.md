# Markdown Renderer

The Markdown renderer is KLMD's baseline renderer that converts the parsed AST to standard Markdown with resolved numbering. It serves as both a functional output format and a reference implementation for developers building other renderers (HTML, docx, etc.).

## Purpose and Design

The Markdown renderer demonstrates core rendering concepts:
- Resolving section and attachment numbering
- Configurable text styling for semantic elements
- Handling cross-references and defined terms
- Managing complex structures like signature blocks

This simple, configurable approach provides a foundation that other renderers can build upon.

## Overview

The markdown renderer is configured through the `MarkdownConfig` class, which controls how each KLMD element is processed and styled.

### Complete Configuration Example

```python
# Create custom numbering with per-level styling
section_numbering = NumberingScheme(
    levels=[
        LevelNumbering(ARABIC, suffix="", include_parent=False, title_style=TextStyle.BOLD),
        LevelNumbering(ALPHA_LOWER, prefix="(", suffix=")", include_parent=True, title_style=TextStyle.ITALIC),
        LevelNumbering(ARABIC, prefix=".", suffix="", include_parent=True, title_style=TextStyle.PLAIN)
    ]
)

# Attachment numbering (simpler, single-level)
attachment_numbering = NumberingScheme(
    levels=[LevelNumbering(ALPHA_UPPER, include_parent=False, title_style=TextStyle.BOLD)]
)

# Overall renderer configuration
config = MarkdownConfig(
    section_numbering=section_numbering,
    attachment_numbering=attachment_numbering,
    defined_term_style=TextStyle.BOLD,
    cross_references=CrossReferenceConfig(template="Section {number}", generate_links=True),
    include_comments=CommentStyle.EXCLUDE,
    heading_base_level=2
)

renderer = MarkdownRenderer(config)
```

This configuration produces:
- **Section 1** with bold titles, subsections like **1(a)** with italic titles, sub-subsections like **1(a).1** with plain titles
- **Attachment A**, **Attachment B** etc. with bold titles
- Defined terms rendered as **bold text**
- Comments excluded from output
- Cross-references as clickable links
- Sections start at H2 level in markdown

## Section Numbering

Section numbering is the most complex aspect of the renderer, supporting flexible per-level configuration through presets and custom specifications.

### Configuration System

The numbering system allows you to specify the format for each hierarchy level independently, enabling complex patterns like `1(a).1` or `I.A.1.a`.

```python
@dataclass
class LevelNumbering:
    style: NumberStyle      # ARABIC, ALPHA_LOWER, ALPHA_UPPER, ROMAN_LOWER, ROMAN_UPPER
    prefix: str = ""        # Text before number, e.g., "(" or "."
    suffix: str = ""        # Text after number, e.g., ")" or "."
    include_parent: bool = True  # Whether to include parent number at this level
    title_style: TextStyle = TextStyle.BOLD  # How to style the section title
    
@dataclass
class NumberingScheme:
    levels: List[LevelNumbering]
```

### Available Presets

- **decimal**: `1.1.1.1` (hierarchical Arabic with dots) - Good for technical documents
- **legal**: `1(a)(i)(A)` (mixed with parentheses) - Standard legal document format
- **outline**: `I.A.1.a` (traditional outline format) - Academic and formal documents
- **simple**: `1, 2, 3` (non-hierarchical Arabic) - Simple numbered lists
- **alpha_parens**: `(a)(i)(1)` (alphabetic with parentheses) - Alternative legal format
- **letters**: `A, B, C` (single-level letters) - Used for attachments/exhibits

Each preset includes appropriate default title styling:
- Top levels typically use **bold** titles
- Mid levels use *italic* titles  
- Deeper levels use plain titles
- Can be overridden with `customize_level()`

### Configuration Examples

#### Using Presets
```python
# Quick setup with legal numbering
config = MarkdownConfig(
    section_numbering=NumberingScheme.from_preset("legal"),
    attachment_numbering=NumberingScheme.from_preset("letters")
)
```

#### Custom Configuration
```python
# Legal Style (1(a)(i))
NumberingScheme(
    levels=[
        LevelNumbering(ARABIC, suffix="", include_parent=False, title_style=TextStyle.BOLD),
        LevelNumbering(ALPHA_LOWER, prefix="(", suffix=")", include_parent=True, title_style=TextStyle.ITALIC),
        LevelNumbering(ROMAN_LOWER, prefix="(", suffix=")", include_parent=True, title_style=TextStyle.PLAIN)
    ]
)

# Mixed Format (1(a).1)
NumberingScheme(
    levels=[
        LevelNumbering(ARABIC, suffix="", include_parent=False, title_style=TextStyle.BOLD),
        LevelNumbering(ALPHA_LOWER, prefix="(", suffix=")", include_parent=True, title_style=TextStyle.ITALIC),
        LevelNumbering(ARABIC, prefix=".", suffix="", include_parent=True, title_style=TextStyle.PLAIN)
    ]
)
```

#### Attachment Numbering
Attachments use simpler numbering since they don't support hierarchy:

```python
# Letters: A, B, C
attachment_numbering = NumberingScheme(
    levels=[LevelNumbering(ALPHA_UPPER, include_parent=False)]
)

# Numbers with periods: 1., 2., 3.
attachment_numbering = NumberingScheme(
    levels=[LevelNumbering(ARABIC, suffix=".", include_parent=False)]
)
```

### Rendering Behavior

#### Section Output Format
```markdown
## 1. Payment Terms
```

- **Number calculation**: Track hierarchical position in document
- **Title formatting**: Apply configured text styling from `title_style`
- **Anchor generation**: `{#payment-terms}` for cross-reference targets
- **Heading hierarchy**: Section levels 1-5 map to H2-H6 headings
- **Number placement**: `## 1. Title` format with number before title

#### Document and Attachment Titles
- **Heading level**: Document and attachment titles use H1 (`#`)
- **Numbering placeholder**: Resolve `[#]` to actual attachment number
- **Underline handling**: Convert `===` to heading or preserve as text decoration

#### Hierarchical Examples

##### Legal Preset (1(a)(i))
```klmd
[# First Section]
[## Subsection]
[## Another Subsection]
[### Sub-subsection]
[# Second Section]
```

**Renders to:**
```markdown
## 1. First Section
### 1(a). Subsection
### 1(b). Another Subsection
#### 1(b)(i). Sub-subsection
## 2. Second Section
```

##### Custom Format (1(a).1)
**Renders to:**
```markdown
## 1. First Section
### 1(a). Subsection
### 1(b). Another Subsection
#### 1(b).1. Sub-subsection
## 2. Second Section
```

## Cross-References

Cross-references allow linking to sections and attachments by title. The renderer resolves these references and formats them according to your configuration.

### Configuration

```python
@dataclass
class CrossReferenceConfig:
    template: str = "Section {number}"     # Format template for resolved references
    generate_links: bool = True            # Whether to create markdown links
```

#### Template Options
The `template` field supports these placeholders:
- `{number}` - The resolved section/attachment number
- `{title}` - The target section title (optional)

Common templates:
- `"Section {number}"` → "Section 1.2" 
- `"{number}"` → "1.2"
- `"({number})"` → "(1.2)"
- `"§{number}"` → "§1.2"
- `"Section {number}: {title}"` → "Section 1.2: Payment Terms"

#### Configuration Examples
```python
# Standard legal style with links
cross_ref_config = CrossReferenceConfig(
    template="Section {number}",
    generate_links=True
)

# Simple numbering without "Section" prefix
cross_ref_config = CrossReferenceConfig(
    template="({number})",
    generate_links=True
)

# Plain text references (no links)
cross_ref_config = CrossReferenceConfig(
    template="Section {number}",
    generate_links=False
)
```

### Rendering Behavior

#### Resolution Process
- **Resolution**: Look up target section number from title
- **Template application**: Apply configured format template
- **Link generation**: Create markdown links to section anchors when enabled

#### Output Examples
```markdown
# Input: [#payment-terms]

# With generate_links=True:
[Section 2](#payment-terms)

# With generate_links=False:
Section 2

# With template="({number})":
[(2)](#payment-terms)

# With template="§{number}":
[§2](#payment-terms)
```

## Defined Terms

Defined terms control how the extracted term appears in the rendered output using the same `TextStyle` system as section titles.

### Configuration

```python
class TextStyle(Enum):
    PLAIN = "plain"           # No formatting
    BOLD = "bold"             # **Title**
    ITALIC = "italic"         # *Title*
    BOLD_ITALIC = "bold_italic"  # ***Title***
    CODE = "code"             # `Title`
    UNDERLINE = "underline"   # <u>Title</u> (HTML in markdown)
```

#### Configuration Examples
```python
# Bold defined terms (default for legal emphasis)
config = MarkdownConfig(defined_term_style=TextStyle.BOLD)

# Code-style defined terms
config = MarkdownConfig(defined_term_style=TextStyle.CODE)

# Plain defined terms (no special formatting)
config = MarkdownConfig(defined_term_style=TextStyle.PLAIN)
```

### Rendering Behavior

#### Processing
- **Term extraction**: Pull quoted term from DTI syntax
- **Referent identification**: Extract preceding text that term defines
- **Styling application**: Apply configured text formatting
- **Descriptor handling**: Include/exclude descriptors like "the", "any"

#### Output Examples
```markdown
# Input: Big Company LLC (defined as the "Company")

# Bold styling (default):
Big Company LLC (**Company**)

# Code styling:
Big Company LLC (`Company`)

# Plain styling:
Big Company LLC (Company)

# Italic styling:
Big Company LLC (*Company*)
```

## Comments

Comments in KLMD documents can be handled in several ways during rendering, from complete exclusion to various inclusion styles that preserve the comment content while adapting it to markdown format.

### Configuration

```python
class CommentStyle(Enum):
    EXCLUDE = "exclude"           # Remove comments entirely (default)
    BLOCKQUOTE = "blockquote"     # Render as markdown blockquotes
    HTML_COMMENT = "html_comment" # Render as HTML comments in markdown
```

#### Configuration Examples
```python
# Exclude comments from output (default)
config = MarkdownConfig(include_comments=CommentStyle.EXCLUDE)

# Include comments as blockquotes
config = MarkdownConfig(include_comments=CommentStyle.BLOCKQUOTE)

# Include as HTML comments (visible in source but not rendered)
config = MarkdownConfig(include_comments=CommentStyle.HTML_COMMENT)
```

### Rendering Behavior

#### Comment Positioning
Comments are rendered at their original position in the document flow:
- **Inline comments**: Appear immediately after the content they follow
- **Standalone comments**: Appear as separate elements in the document structure
- **Block comments**: Maintain their block-level positioning

#### Output Examples

##### Line Comments
```markdown
# Input KLMD:
[# Payment Terms] Client pays within 30 days.
// Note: Add late payment penalties

# EXCLUDE (default):
## 1. Payment Terms
Client pays within 30 days.

# BLOCKQUOTE:
## 1. Payment Terms
Client pays within 30 days.
> Note: Add late payment penalties

# HTML_COMMENT:
## 1. Payment Terms
Client pays within 30 days.
<!-- Note: Add late payment penalties -->
```

##### Block Comments
```markdown
# Input KLMD:
[# Payment Terms] Client pays within 30 days.
/* 
This section needs review:
- Check late fees
- Verify payment methods
*/

# EXCLUDE (default):
## 1. Payment Terms
Client pays within 30 days.

# BLOCKQUOTE:
## 1. Payment Terms
Client pays within 30 days.
> This section needs review:
> - Check late fees
> - Verify payment methods

# HTML_COMMENT:
## 1. Payment Terms
Client pays within 30 days.
<!-- 
This section needs review:
- Check late fees
- Verify payment methods
-->
```

## Signature Blocks

Signature blocks have no configuration options - they are rendered consistently based on their structure (individual vs entity signatures).

### Rendering Behavior

#### Individual Signatures
Individual signatures render with a signature line (20 underscores) above the party name.

```markdown
# Input:
---
John Smith
Address: 123 Main St

# Output:
____________________
John Smith

Address: 123 Main St
```

#### Entity Signatures
Entity signatures render the entity name in UPPERCASE, convert the "By:" field to "Name:", and add a signature line with 20 underscores after "By:".

```markdown
# Input:
-----
ABC Corporation
By: John Smith
Title: CEO

# Output:
ABC CORPORATION

By: ____________________
Name: John Smith  
Title: CEO
```

#### Nested Entity Signatures
For nested entities, only the primary entity name is rendered in UPPERCASE. Chain of authority entities remain as "By:" fields, while the final human signatory gets converted to "Name:" with a signature line.

```markdown
# Input:
--------------------
Investment Fund LP
By Entity: ABC Management LLC, its General Partner
  By Entity: XYZ Holdings Inc., its Managing Member
    By: John Smith
    Title: President

# Output:
INVESTMENT FUND LP
By: ABC Management LLC, its General Partner  
By: XYZ Holdings Inc., its Managing Member  

By: ____________________
Name: John Smith
Title: President
```

## Implementation Architecture

### Core Classes

#### MarkdownRenderer
```python
class MarkdownRenderer:
    def __init__(self, config: MarkdownConfig = None)
    def render(self, document: DocumentNode) -> str
    def render_node(self, node: Node) -> str
    def resolve_numbering(self, document: DocumentNode)
```

#### MarkdownConfig
```python
@dataclass
class MarkdownConfig:
    section_numbering: NumberingScheme = NumberingScheme.from_preset("decimal")
    attachment_numbering: NumberingScheme = NumberingScheme.from_preset("letters")
    defined_term_style: TextStyle = TextStyle.BOLD
    cross_references: CrossReferenceConfig = CrossReferenceConfig()
    include_comments: CommentStyle = CommentStyle.EXCLUDE
    heading_base_level: int = 2
```

#### NumberingScheme
```python
@dataclass
class NumberingScheme:
    levels: List[LevelNumbering]
    
    @classmethod
    def from_preset(cls, preset: str) -> 'NumberingScheme':
        """Create numbering scheme from preset name"""
        
    def customize_level(self, level: int, config: LevelNumbering):
        """Override specific level while keeping rest of scheme"""
        
    def format_number(self, position: List[int]) -> str:
        """Generate formatted number string for given position"""
```

#### LevelNumbering
```python
@dataclass
class LevelNumbering:
    style: NumberStyle
    prefix: str = ""
    suffix: str = ""
    include_parent: bool = True
    title_style: TextStyle = TextStyle.BOLD
    
    def format_value(self, value: int) -> str:
        """Convert integer to styled representation"""
```

### Helper Classes

#### NumberingTracker
- Track current position at each hierarchy level
- Apply NumberingScheme configuration to generate formatted numbers
- Handle attachment numbering across document
- Reset section numbering within attachments
- Support for non-contiguous numbering (skipping levels)

#### NumberingResolver
- Traverse document AST and assign numbers to sections
- Build cross-reference mapping from titles to numbers
- Handle complex cases like forward references
- Validate numbering consistency

#### StyleFormatter
- Apply text styling (bold, italic, etc.)
- Generate markdown formatting codes
- Handle edge cases like nested formatting

## Usage Examples

### Basic Usage
```python
from klmd.renderers.markdown import MarkdownRenderer
from klmd.parser import KLMDParser

# Parse KLMD document
parser = KLMDParser()
document = parser.parse(klmd_text)

# Render to markdown
renderer = MarkdownRenderer()
markdown_output = renderer.render(document)
```

### Configuration with Presets
```python
# Use a preset numbering scheme (presets include default title styling)
config = MarkdownConfig(
    section_numbering=NumberingScheme.from_preset("legal"),
    defined_term_style=TextStyle.CODE,
    include_comments=CommentStyle.BLOCKQUOTE,
    cross_references=CrossReferenceConfig(template="({number})", generate_links=False)
)
renderer = MarkdownRenderer(config)
```

### Custom Numbering Configuration
```python
# Create custom numbering scheme for 1(a).1 format with title styling
custom_scheme = NumberingScheme(
    levels=[
        LevelNumbering(NumberStyle.ARABIC, suffix="", include_parent=False, title_style=TextStyle.BOLD),
        LevelNumbering(NumberStyle.ALPHA_LOWER, prefix="(", suffix=")", include_parent=True, title_style=TextStyle.ITALIC),
        LevelNumbering(NumberStyle.ARABIC, prefix=".", suffix="", include_parent=True, title_style=TextStyle.PLAIN)
    ]
)

config = MarkdownConfig(section_numbering=custom_scheme)
renderer = MarkdownRenderer(config)
```

### Preset with Level Customization
```python
# Start with legal preset, but customize level 2
scheme = NumberingScheme.from_preset("legal")
scheme.customize_level(2, LevelNumbering(
    NumberStyle.ROMAN_LOWER, 
    prefix="[", 
    suffix="]",
    title_style=TextStyle.CODE
))

config = MarkdownConfig(section_numbering=scheme)
renderer = MarkdownRenderer(config)
```

### Complete Example

#### Input KLMD
```klmd
Master Services Agreement
=========================

[# Definitions] The following terms are defined:
[##] Big Company LLC (defined as the "Company") is the service provider.
[##] Services means the work described in Exhibit [#statement-of-work].

// Note: Add more definitions

[# Payment] Client pays within 30 days.

Exhibit [#]
===========

Statement of Work description here.
```

#### Output Markdown
```markdown
# Master Services Agreement

## 1. Definitions
The following terms are defined:
### 1.1. 
Big Company LLC (**Company**) is the service provider.
### 1.2. 
Services means the work described in [Exhibit A](#exhibit-a).

## 2. Payment
Client pays within 30 days.

# Exhibit A

Statement of Work description here.
```

## Implementation Notes

Key requirements for the renderer implementation:

1. **Two-phase processing**: First pass assigns numbers to all sections and attachments, second pass renders with resolved cross-references
2. **AST traversal**: Process document tree depth-first to maintain proper hierarchical numbering
3. **Title normalization**: Convert section titles to anchor IDs using lowercase and hyphens for cross-reference targets
4. **Error handling**: Gracefully handle missing cross-reference targets and malformed signature blocks
5. **Markdown compliance**: Generate valid CommonMark output that renders correctly in standard markdown processors


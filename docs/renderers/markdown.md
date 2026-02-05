# Markdown Renderer

The Markdown renderer converts the parsed KLMD AST to standard Markdown with resolved numbering. It serves as both a functional output format and a reference implementation for developers building other renderers (HTML, docx, etc.).

## Configuration Overview

The renderer is configured through `MarkdownConfig`, which controls how each KLMD element is processed and styled.

```python
from klmd.renderers.markdown import (
    MarkdownRenderer,
    MarkdownConfig,
    NumberingScheme,
    LevelNumbering,
    CrossReferenceConfig,
    TextStyle,
    CommentStyle,
    SectionContentPlacement,
    AnchorGeneration,
)
from klmd.renderers.markdown import NumberStyle

# Complete configuration example
config = MarkdownConfig(
    section_numbering=NumberingScheme.from_preset("legal"),
    attachment_numbering=NumberingScheme.from_preset("letters"),
    defined_term_style=TextStyle.BOLD,
    cross_references=CrossReferenceConfig(template="Section {number}", generate_links=True),
    include_comments=CommentStyle.EXCLUDE,
    heading_base_level=2,
    section_indent="    ",
    section_content_placement=SectionContentPlacement.INLINE,
    anchor_generation=AnchorGeneration.CROSS_REFERENCED,
)

renderer = MarkdownRenderer(config)
```

### MarkdownConfig Reference

```python
@dataclass
class MarkdownConfig:
    section_numbering: NumberingScheme = NumberingScheme.from_preset("decimal")
    attachment_numbering: NumberingScheme = NumberingScheme.from_preset("letters")
    defined_term_style: TextStyle = TextStyle.BOLD
    cross_references: CrossReferenceConfig = CrossReferenceConfig()
    include_comments: CommentStyle = CommentStyle.EXCLUDE
    heading_base_level: int = 2
    section_indent: str = "    "  # 4 spaces by default, can be "\t" for tab
    section_content_placement: SectionContentPlacement = SectionContentPlacement.NEWLINE
    anchor_generation: AnchorGeneration = AnchorGeneration.CROSS_REFERENCED
```

## Section Numbering

*Syntax: [spec.md § Section Numbers](../spec.md#2-section-numbers)*

Section numbering is the most complex aspect of the renderer, supporting flexible per-level configuration through presets and custom specifications.

### LevelNumbering

Each hierarchy level is configured independently:

```python
@dataclass
class LevelNumbering:
    style: NumberStyle      # ARABIC, ALPHA_LOWER, ALPHA_UPPER, ROMAN_LOWER, ROMAN_UPPER
    prefix: str = ""        # Text before number, e.g., "(" or "."
    suffix: str = ""        # Text after number, e.g., ")" or "."
    include_parent: bool = True  # Whether to include parent number at this level
    title_style: TextStyle = TextStyle.BOLD  # How to style the section title
```

### Available Presets

| Preset | Format | Use case |
|--------|--------|----------|
| `decimal` | `1.1.1.1` | Technical documents |
| `legal` | `1(a)(i)(A)` | Standard legal format |
| `outline` | `I.A.1.a` | Academic and formal documents |
| `simple` | `1, 2, 3` | Simple numbered lists |
| `alpha_parens` | `(a)(i)(1)` | Alternative legal format |
| `letters` | `A, B, C` | Attachments/exhibits |

Each preset includes appropriate default title styling (bold for top levels, italic for mid levels, plain for deeper levels). These can be overridden with `customize_level()`.

### Configuration Examples

#### Using Presets
```python
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

#### Preset with Level Customization
```python
scheme = NumberingScheme.from_preset("legal")
scheme.customize_level(2, LevelNumbering(
    NumberStyle.ROMAN_LOWER,
    prefix="[",
    suffix="]",
    title_style=TextStyle.CODE
))

config = MarkdownConfig(section_numbering=scheme)
```

### Indentation

Sections are indented according to their hierarchy level using `section_indent` (default: 4 spaces). Set to `"\t"` for tab indentation.

### Section Content Placement

Controls where section body text appears relative to the title:

**NEWLINE (default)**: Content starts on the next line after the title
```markdown
1. Payment Terms
Payment is due within 30 days.
```

**INLINE**: Content starts on the same line, separated by a period and space
```markdown
1. Payment Terms. Payment is due within 30 days.
```

Untitled sections always place content immediately after the number, regardless of this setting:
```markdown
1. Payment is due within 30 days.
```

```python
config = MarkdownConfig(section_content_placement=SectionContentPlacement.INLINE)
```

### Anchor Generation

Section anchors enable linking to specific sections. Three modes are available:

| Mode | Behavior |
|------|----------|
| `CROSS_REFERENCED` (default) | Anchors only for sections referenced elsewhere |
| `ALL` | Anchors for every section |
| `NONE` | No anchors |

```python
config = MarkdownConfig(anchor_generation=AnchorGeneration.CROSS_REFERENCED)
```

### Rendered Examples

#### Legal Preset (1(a)(i))
```klmd
[# First Section]
[## Subsection]
[## Another Subsection]
[### Sub-subsection]
[# Second Section]
```

Renders to:
```markdown
1. First Section
    1(a). Subsection
    1(b). Another Subsection
        1(b)(i). Sub-subsection
2. Second Section
```

## Document and Attachment Titles

*Syntax: [spec.md § Document and Attachment Titles](../spec.md#3-document-and-attachment-titles)*

- **Heading level**: Document and attachment titles render as H1 (`#`)
- **Numbering placeholder**: `[#]` in titles resolves to the actual attachment number
- **Underline handling**: `===` underlines are converted to heading syntax

## Attachment Numbering

*Syntax: [spec.md § Attachment Numbering](../spec.md#4-attachment-numbering)*

Attachments use simpler, single-level numbering:

```python
# Letters: A, B, C (default)
attachment_numbering = NumberingScheme.from_preset("letters")

# Numbers with periods: 1., 2., 3.
attachment_numbering = NumberingScheme(
    levels=[LevelNumbering(ARABIC, suffix=".", include_parent=False)]
)
```

## Cross-References

*Syntax: [spec.md § Cross References](../spec.md#5-cross-references)*

### Configuration

```python
@dataclass
class CrossReferenceConfig:
    template: str = "Section {number}"     # Format template for resolved references
    generate_links: bool = True            # Whether to create markdown links
```

### Template Variables

- `{number}` — The resolved section/attachment number
- `{title}` — The target section title

Common templates:

| Template | Output |
|----------|--------|
| `"Section {number}"` | Section 1.2 |
| `"§{number}"` | §1.2 |
| `"({number})"` | (1.2) |
| `"{number}"` | 1.2 |
| `"Section {number}: {title}"` | Section 1.2: Payment Terms |

### Output Examples

```markdown
# Input: [#payment-terms]

# With generate_links=True:
[Section 2](#payment-terms)

# With generate_links=False:
Section 2

# With template="§{number}":
[§2](#payment-terms)
```

### Period Stripping

Cross-references automatically strip trailing periods from section numbers to avoid awkward constructions like "Section 3.":

- Section numbered "3." renders as "Section 3" in cross-references
- Section numbered "3(a)" preserves the suffix: "Section 3(a)"

## Defined Terms

*Syntax: [spec.md § Defined Terms](../spec.md#6-defined-terms)*

### Configuration

```python
class TextStyle(Enum):
    PLAIN = "plain"           # No formatting
    BOLD = "bold"             # **Term**
    ITALIC = "italic"         # *Term*
    BOLD_ITALIC = "bold_italic"  # ***Term***
    CODE = "code"             # `Term`
    UNDERLINE = "underline"   # <u>Term</u>
```

```python
config = MarkdownConfig(defined_term_style=TextStyle.BOLD)
```

### Output Examples

```markdown
# Input: Big Company LLC (defined as the "Company")

# Bold (default):  Big Company LLC (the **Company**)
# Code:            Big Company LLC (the `Company`)
# Italic:          Big Company LLC (the *Company*)
# Plain:           Big Company LLC (the Company)
```

## Comments

*Syntax: [spec.md § Comments](../spec.md#7-comments)*

### Configuration

```python
class CommentStyle(Enum):
    EXCLUDE = "exclude"           # Remove comments entirely (default)
    BLOCKQUOTE = "blockquote"     # Render as markdown blockquotes
    HTML_COMMENT = "html_comment" # Render as HTML comments
```

```python
config = MarkdownConfig(include_comments=CommentStyle.BLOCKQUOTE)
```

### Output Examples

#### Line Comments
```markdown
# Input:
[# Payment Terms] Client pays within 30 days.
// Note: Add late payment penalties

# EXCLUDE:     (comment removed)
# BLOCKQUOTE:  > Note: Add late payment penalties
# HTML:        <!-- Note: Add late payment penalties -->
```

#### Block Comments
```markdown
# Input:
/*
This section needs review:
- Check late fees
- Verify payment methods
*/

# BLOCKQUOTE:
> This section needs review:
> - Check late fees
> - Verify payment methods

# HTML:
<!--
This section needs review:
- Check late fees
- Verify payment methods
-->
```

Comments are rendered at their original position in the document flow (inline, standalone, or block-level).

## Signature Blocks

*Syntax: [spec.md § Signature Blocks](../spec.md#8-signature-blocks)*

Signature blocks have no configuration options—they are rendered consistently based on their structure.

### Individual Signatures

Rendered with a signature line (20 underscores) above the party name.

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

### Entity Signatures

Entity name in UPPERCASE, `By:` field converted to `Name:`, signature line added.

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

### Nested Entity Signatures

Primary entity in UPPERCASE. Chain of authority entities as `By:` fields. Final human signatory gets `Name:` with signature line.

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

## Python API

### Basic Usage

```python
from klmd.parser import KLMDParser
from klmd.renderers.markdown import MarkdownRenderer

parser = KLMDParser()
document = parser.parse(klmd_text)

renderer = MarkdownRenderer()
markdown_output = renderer.render(document)
```

### Configuration with Presets

```python
from klmd.renderers.markdown import (
    MarkdownRenderer,
    MarkdownConfig,
    NumberingScheme,
    TextStyle,
    CommentStyle,
    CrossReferenceConfig,
)

config = MarkdownConfig(
    section_numbering=NumberingScheme.from_preset("legal"),
    defined_term_style=TextStyle.CODE,
    include_comments=CommentStyle.BLOCKQUOTE,
    cross_references=CrossReferenceConfig(template="({number})", generate_links=False)
)
renderer = MarkdownRenderer(config)
output = renderer.render(document)
```

### Custom Numbering

```python
from klmd.renderers.markdown import NumberingScheme, LevelNumbering, NumberStyle

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

### Jinja2 Integration

```python
from jinja2 import Template
from klmd.parser import KLMDParser
from klmd.renderers.markdown import MarkdownRenderer

template_text = """
{{ client_name }} Services Agreement
{{ "=" * (client_name|length + 18) }}

[# Definitions]
[##] {{ client_name }} (defined as "Client") shall mean the contracting party.
[##] Services means {{ service_description }}.

[# Payment] Client pays ${{ amount }} within {{ payment_days }} days.
"""

template = Template(template_text)
klmd_text = template.render(
    client_name="Acme Corp",
    service_description="software development services",
    amount="50,000",
    payment_days=30
)

parser = KLMDParser()
document = parser.parse(klmd_text)
renderer = MarkdownRenderer()
final_output = renderer.render(document)
```

### Batch Processing

```python
from pathlib import Path
from klmd.parser import KLMDParser
from klmd.renderers.markdown import MarkdownRenderer

def process_klmd_directory(input_dir: str, output_dir: str):
    """Convert all KLMD files in a directory to markdown."""
    parser = KLMDParser()
    renderer = MarkdownRenderer()

    for klmd_file in Path(input_dir).glob("*.klmd"):
        with open(klmd_file, 'r') as f:
            document = parser.parse(f.read())

        markdown = renderer.render(document)

        output_file = Path(output_dir) / f"{klmd_file.stem}.md"
        with open(output_file, 'w') as f:
            f.write(markdown)

        print(f"Converted {klmd_file} -> {output_file}")
```

## CLI

For command-line usage and options, see the [CLI Reference](../cli.md).

## Implementation Architecture

### Core Classes

- **MarkdownRenderer** — Main renderer; `render(document)` returns markdown string
- **MarkdownConfig** — Configuration dataclass controlling all rendering behaviors
- **NumberingScheme** — Hierarchical numbering with preset support and `from_preset()` / `customize_level()` / `format_number()` methods
- **LevelNumbering** — Per-level numbering configuration with `format_value()`

### Helper Classes

- **NumberingTracker** — Tracks current position at each hierarchy level, applies numbering scheme, handles attachment numbering and section resets
- **NumberingResolver** — First-pass AST traversal to assign numbers and build cross-reference mapping
- **StyleFormatter** — Applies text styling (bold, italic, etc.) and generates markdown formatting

### Rendering Process

1. **First pass (NumberingResolver)**: Traverse the AST to assign numbers to all sections and attachments, and build the cross-reference mapping
2. **Second pass (MarkdownRenderer)**: Render each node with resolved numbering and cross-references
3. **Title normalization**: Section titles are converted to anchor IDs using lowercase and hyphens
4. **Output**: Valid CommonMark that renders correctly in standard markdown processors

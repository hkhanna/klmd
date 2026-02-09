# Docx Renderer

The docx renderer converts KLMD documents to Microsoft Word format (.docx). It supports Word templates for custom styling and generates working internal hyperlinks for cross-references.

## CLI Usage

Basic conversion:

```bash
klmd document.klmd -f docx -o document.docx
```

With a template:

```bash
klmd document.klmd -f docx --template firm-style.docx -o document.docx
```

With numbering presets:

```bash
klmd document.klmd -f docx -p legal -o document.docx
```

## Python API

### Basic Usage

```python
from klmd.parser import KLMDParser
from klmd.renderers.docx import DocxRenderer

parser = KLMDParser()
document = parser.parse(open("contract.klmd").read())

renderer = DocxRenderer()
with open("contract.docx", "wb") as f:
    f.write(renderer.render(document))
```

### With Configuration

```python
from pathlib import Path
from klmd.renderers.docx import DocxRenderer
from klmd.renderers.docx_config import DocxConfig, StyleMapping
from klmd.renderers.markdown import NumberingScheme

config = DocxConfig(
    template_path=Path("template.docx"),
    section_numbering=NumberingScheme.from_preset("legal"),
    cross_ref_template="Clause {number}",
    defined_term_bold=True,
    uppercase_entity_names=True,
)

renderer = DocxRenderer(config)
output_bytes = renderer.render(document)
```

## Configuration Options

### DocxConfig

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `template_path` | `Path \| None` | `None` | Word template file for styling |
| `paragraph_styles` | `StyleMapping` | (see below) | Maps AST nodes to Word styles |
| `section_numbering` | `NumberingScheme` | `"decimal"` | Section numbering format |
| `attachment_numbering` | `NumberingScheme` | `"letters"` | Attachment numbering format |
| `cross_ref_template` | `str` | `"Section {number}"` | Template for cross-reference text |
| `generate_bookmarks` | `bool` | `True` | Create Word bookmarks for sections |
| `generate_hyperlinks` | `bool` | `True` | Make cross-references clickable |
| `include_comments` | `bool` | `False` | Include KLMD comments in output |
| `defined_term_bold` | `bool` | `True` | Bold defined terms |
| `uppercase_entity_names` | `bool` | `True` | Uppercase entity names in signatures |

### StyleMapping

The `StyleMapping` class maps KLMD elements to Word paragraph styles:

| Property | Default Style | Used For |
|----------|---------------|----------|
| `document_title` | `"Title"` | Main document title |
| `attachment_title` | `"Title"` | Attachment/exhibit titles |
| `attachment_subtitle` | `"Subtitle"` | Attachment subtitles |
| `section_level_1` | `"Heading 1"` | Top-level sections |
| `section_level_2` | `"Heading 2"` | Second-level sections |
| `section_level_3` | `"Heading 3"` | Third-level sections |
| `section_level_4` | `"Heading 4"` | Fourth-level sections |
| `section_level_5` | `"Heading 5"` | Fifth-level sections |
| `paragraph` | `"Normal"` | Body text |
| `signature_party_name` | `"Normal"` | Party names in signature blocks |
| `signature_line` | `"Normal"` | Signature lines |
| `signature_field` | `"Normal"` | Signature metadata fields |
| `comment_text` | `"Quote"` | Comments (when included) |

Custom style mapping:

```python
from klmd.renderers.docx_config import DocxConfig, StyleMapping

styles = StyleMapping(
    document_title="Contract Title",
    section_level_1="Article Heading",
    section_level_2="Section Heading",
    paragraph="Body Text",
)

config = DocxConfig(paragraph_styles=styles)
```

## Templates

Templates let you control the visual appearance of generated documents. The renderer applies Word styles to content, so your template defines how those styles look.

### Creating a Template

1. Create a new Word document
2. Define styles (Title, Heading 1, Heading 2, Normal, etc.)
3. Set fonts, sizes, spacing, and other formatting for each style
4. Save as `.docx` or `.dotx`

### Using a Template

```python
from pathlib import Path
from klmd.renderers.docx_config import DocxConfig

config = DocxConfig(template_path=Path("firm-template.docx"))
```

Or via CLI:

```bash
klmd document.klmd -f docx --template firm-template.docx -o output.docx
```

## Numbering Schemes

The renderer supports the same numbering presets as the markdown renderer:

| Preset | Example Output |
|--------|----------------|
| `decimal` | 1., 1.1., 1.1.1. |
| `legal` | 1, 1(a), 1(a)(i) |
| `outline` | I., A., 1. |
| `simple` | 1, 2, 3 (no hierarchy) |
| `alpha_parens` | (a), (a)(i), (a)(i)(1) |
| `letters` | A, B, C (for attachments) |

```python
from klmd.renderers.markdown import NumberingScheme

config = DocxConfig(
    section_numbering=NumberingScheme.from_preset("legal"),
    attachment_numbering=NumberingScheme.from_preset("letters"),
)
```

## Cross-References

Cross-references are rendered as clickable hyperlinks that navigate to bookmarks within the document.

### Bookmark Generation

Bookmarks are created for:
- Document and attachment titles
- Titled sections
- Attachment subtitles

Bookmark names are normalized: lowercase, spaces become underscores, special characters removed, truncated to 40 characters.

### Hyperlink Format

The `cross_ref_template` option controls how cross-references appear:

```python
# Default: "Section 1"
config = DocxConfig(cross_ref_template="Section {number}")

# Alternative: "Clause 1"
config = DocxConfig(cross_ref_template="Clause {number}")

# Minimal: just the number
config = DocxConfig(cross_ref_template="{number}")
```

### Disabling Links

```python
config = DocxConfig(
    generate_bookmarks=False,  # No bookmarks
    generate_hyperlinks=False,  # Plain text cross-references
)
```

## Signature Blocks

Signature blocks are rendered as a series of paragraphs:

**Entity signatures:**
- Party name (bold, uppercase by default)
- "By Entity:" lines for nested entities
- Signature line with underscores
- Name, title, and other fields

**Individual signatures:**
- Signature line with underscores
- Party name
- Additional fields

### Configuration

```python
config = DocxConfig(
    uppercase_entity_names=True,  # "ACME CORP" vs "Acme Corp"
)
```

## Comments

KLMD comments are excluded from output by default. To include them:

```python
config = DocxConfig(include_comments=True)
```

When included, standalone comments use the `comment_text` style (default: "Quote"), and inline comments appear in brackets: `[comment text]`.

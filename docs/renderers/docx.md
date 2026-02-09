# Docx Renderer

The docx renderer converts KLMD documents to Microsoft Word format (.docx). A Word template is required and controls all styling, including fonts, spacing, and numbering.

## CLI Usage

Basic conversion (template required):

```bash
klmd document.klmd -f docx --template firm-style.docx -o document.docx
```

## Python API

### Basic Usage

```python
from pathlib import Path
from klmd.parser import KLMDParser
from klmd.renderers.docx import DocxRenderer
from klmd.renderers.docx_config import DocxConfig

parser = KLMDParser()
document = parser.parse(open("contract.klmd").read())

config = DocxConfig(template_path=Path("template.docx"))
renderer = DocxRenderer(config)
with open("contract.docx", "wb") as f:
    f.write(renderer.render(document))
```

### With Configuration

```python
from pathlib import Path
from klmd.renderers.docx import DocxRenderer
from klmd.renderers.docx_config import DocxConfig, StyleMapping

config = DocxConfig(
    template_path=Path("template.docx"),
    defined_term_bold=True,
    uppercase_entity_names=True,
    generate_hyperlinks=True,
)

renderer = DocxRenderer(config)
output_bytes = renderer.render(document)
```

## Configuration Options

### DocxConfig

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `template_path` | `Path` | (required) | Word template file for styling |
| `paragraph_styles` | `StyleMapping` | (see below) | Maps AST nodes to Word styles |
| `generate_bookmarks` | `bool` | `True` | Create Word bookmarks for sections |
| `generate_hyperlinks` | `bool` | `True` | Make cross-references clickable |
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

Custom style mapping:

```python
from klmd.renderers.docx_config import DocxConfig, StyleMapping

styles = StyleMapping(
    document_title="Contract Title",
    section_level_1="Article Heading",
    section_level_2="Section Heading",
    paragraph="Body Text",
)

config = DocxConfig(
    template_path=Path("template.docx"),
    paragraph_styles=styles,
)
```

## Templates

Templates control the visual appearance of generated documents. The renderer applies Word styles to content, so your template defines how those styles look.

### Creating a Template

1. Create a new Word document
2. Define styles (Title, Heading 1, Heading 2, Normal, etc.)
3. Set fonts, sizes, spacing, and other formatting for each style
4. **For automatic numbering**: Configure heading styles with Word's multilevel list numbering
5. Save as `.docx` or `.dotx`

### Numbering

The renderer does not generate section numbers. Instead, numbering is controlled by the template:

- If your template's Heading 1, Heading 2, etc. styles are linked to a multilevel list, Word applies numbering automatically
- This gives you full control over numbering format (1., 1.1 vs Article I, Section 1(a), etc.)
- If your template has no numbering defined, sections appear without numbers

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

## Cross-References

Cross-references are rendered as the title text with optional hyperlinks to bookmarks within the document.

### How It Works

1. The renderer collects all titles (document title, section titles, attachment titles/subtitles)
2. Cross-references like `[#definitions]` resolve to the matching title text ("Definitions")
3. If hyperlinks are enabled, the text links to a bookmark at that section

### Bookmark Generation

Bookmarks are created for:
- Document and attachment titles
- Titled sections
- Attachment subtitles

Bookmark names are normalized: lowercase, spaces become underscores, special characters removed, truncated to 40 characters.

### Disabling Links

```python
config = DocxConfig(
    template_path=Path("template.docx"),
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
    template_path=Path("template.docx"),
    uppercase_entity_names=True,  # "ACME CORP" vs "Acme Corp"
)
```

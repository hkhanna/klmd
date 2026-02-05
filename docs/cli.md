# KLMD Command Line Interface

Complete reference for the KLMD command-line interface.

For KLMD syntax details, see the [Specification](spec.md). For renderer-specific configuration and Python API usage, see the [Markdown Renderer](renderers/markdown.md).

## Synopsis

```bash
klmd [OPTIONS] [INPUT] [OUTPUT]
```

**Input:** KLMD file path or `-` for stdin (default: stdin)  
**Output:** Output file path or omit for stdout

## Global Options

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `-h, --help` | Show help message and exit | |
| `--version` | Show version number and exit | |
| `-o, --output FILE` | Output file (alternative to positional argument) | stdout |
| `-f, --format FORMAT` | Output format: `markdown`, `html`, `docx`, `pdf` | `markdown` |
| `-c, --config FILE` | Configuration file (YAML or JSON) | |

### General Options

| Option | Description | Default |
|--------|-------------|---------|
| `--validate` | Parse and validate only, do not generate output | |
| `-v, --verbose` | Show progress information | |
| `--debug` | Show AST and configuration details | |

## Configuration Options

### Quick Presets

| Option | Description | Available Values |
|--------|-------------|------------------|
| `-p, --preset PRESET` | Apply numbering preset to sections | `decimal`, `legal`, `outline`, `simple`, `alpha_parens`, `letters` |

**Preset Examples:**
- `decimal`: 1.1.1.1 (hierarchical)
- `legal`: 1(a)(i)(A) (legal style)
- `outline`: I.A.1.a (formal outline)
- `simple`: 1, 2, 3 (non-hierarchical)

### Section Numbering

| Option | Description | Available Values |
|--------|-------------|------------------|
| `--section-preset PRESET` | Section numbering preset | `decimal`, `legal`, `outline`, `simple`, `alpha_parens` |
| `--section-style-1 STYLE` | Title style for level 1 sections | `plain`, `bold`, `italic`, `bold_italic`, `code`, `underline` |
| `--section-style-2 STYLE` | Title style for level 2 sections | Same as above |
| `--section-style-3 STYLE` | Title style for level 3 sections | Same as above |

### Attachment Numbering

| Option | Description | Available Values |
|--------|-------------|------------------|
| `--attachment-preset PRESET` | Attachment numbering preset | `letters`, `decimal`, `simple` |
| `--attachment-style STYLE` | Title style for attachments | `plain`, `bold`, `italic`, `bold_italic`, `code`, `underline` |

### Defined Terms

| Option | Description | Available Values |
|--------|-------------|------------------|
| `--terms STYLE` | Style for defined terms | `plain`, `bold`, `italic`, `bold_italic`, `code`, `underline` |

**Examples:**
- `bold`: **Company** (default)
- `code`: `Company`
- `italic`: *Company*
- `plain`: Company

### Cross-References

| Option | Description | Default |
|--------|-------------|---------|
| `--xref-template TEMPLATE` | Template for cross-reference text | `"Section {number}"` |
| `--xref-links` | Generate markdown links for cross-references | enabled |
| `--no-xref-links` | Disable markdown links for cross-references | |

**Template Variables:**
- `{number}`: The resolved section/attachment number
- `{title}`: The target section title (optional)

**Template Examples:**
- `"Section {number}"`: Section 1.2
- `"§{number}"`: §1.2
- `"({number})"`: (1.2)
- `"{number}"`: 1.2

### Comments

| Option | Description | Available Values |
|--------|-------------|------------------|
| `--comments STYLE` | How to handle comments in output | `exclude`, `blockquote`, `html` |

**Comment Styles:**
- `exclude`: Remove comments entirely (default)
- `blockquote`: Render as markdown blockquotes (`> comment`)
- `html`: Render as HTML comments (`<!-- comment -->`)

## Configuration Files

### YAML Configuration

```yaml
section_numbering:
  preset: legal
  customize:
    2:
      style: roman_lower
      title_style: italic
      prefix: "["
      suffix: "]"
      
attachment_numbering:
  preset: letters
  
defined_terms: bold

cross_references:
  template: "Section {number}"
  links: true
  
comments: exclude
```

### JSON Configuration

```json
{
  "section_numbering": {
    "preset": "legal",
    "customize": {
      "2": {
        "style": "roman_lower", 
        "title_style": "italic"
      }
    }
  },
  "attachment_numbering": {
    "preset": "letters"
  },
  "defined_terms": "bold",
  "cross_references": {
    "template": "Section {number}",
    "links": true
  },
  "comments": "exclude"
}
```

### Configuration Precedence

1. **Default values** (lowest priority)
2. **Configuration file** settings (if specified with `-c`)
3. **CLI arguments** (highest priority)

## Usage Examples

### Basic Usage

```bash
# Convert KLMD to markdown
uv run python -m klmd document.klmd -o document.md

# Pipe input/output
cat contract.klmd | uv run python -m klmd - > contract.md

# Validate syntax only
uv run python -m klmd --validate document.klmd
```

### Using Presets

```bash
# Legal document formatting
uv run python -m klmd contract.klmd -p legal

# Technical manual formatting
uv run python -m klmd manual.klmd -p decimal

# Formal document formatting
uv run python -m klmd policy.klmd -p outline
```

### Custom Formatting

```bash
# Custom section styles
uv run python -m klmd doc.klmd \
  --section-preset legal \
  --section-style-1 bold \
  --section-style-2 italic

# Custom defined terms and cross-references
uv run python -m klmd doc.klmd \
  --terms code \
  --xref-template "§{number}" \
  --no-xref-links

# Include comments as blockquotes
uv run python -m klmd doc.klmd \
  --comments blockquote
```

### Configuration Files

```bash
# Using YAML configuration
uv run python -m klmd document.klmd -c config.yaml

# Configuration with CLI overrides
uv run python -m klmd document.klmd \
  -c base-config.yaml \
  --terms code \
  --verbose
```

### Development and Debugging

```bash
# Verbose output
uv run python -m klmd document.klmd -v

# Debug with AST information
uv run python -m klmd document.klmd --debug

# Validate and debug
uv run python -m klmd --validate --debug document.klmd
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Input file not found` | File doesn't exist | Check file path |
| `Permission denied reading file` | No read permission | Check file permissions |
| `Permission denied writing file` | No write permission | Check output directory permissions |
| `Error parsing configuration file` | Invalid YAML/JSON | Validate configuration syntax |
| `Parse error` | Invalid KLMD syntax | Use `--debug` to see detailed error |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (file not found, parse error, etc.) |
| 130 | Interrupted (Ctrl+C) |

## Integration Examples

### Git Hooks

Convert KLMD files to markdown on commit:

```bash
#!/bin/bash
# .git/hooks/pre-commit
for file in *.klmd; do
    if [ -f "$file" ]; then
        uv run python -m klmd "$file" -o "${file%.klmd}.md"
        git add "${file%.klmd}.md"
    fi
done
```

### Makefile Integration

```makefile
%.md: %.klmd
	uv run python -m klmd $< -o $@

all: contract.md policy.md manual.md

clean:
	rm -f *.md
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Convert KLMD to Markdown
  run: |
    for file in docs/*.klmd; do
      uv run python -m klmd "$file" -o "${file%.klmd}.md"
    done
```

## Related Documentation

- **[Specification](spec.md)** — KLMD syntax reference
- **[Markdown Renderer](renderers/markdown.md)** — Renderer configuration, Python API, and output examples
- Future renderers: HTML, DOCX, PDF
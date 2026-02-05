# Khanna Law Markdown (KLMD)
A flavor of markdown designed for legal drafting.

## Introduction

The Khanna Law Markdown (KLMD) specification provides a lightweight, human-readable syntax for drafting legal documents such as contracts, legislation, and agreements. KLMD extends standard Markdown with specialized features for legal drafting without losing the portability and simplicity of plain text.

### Why KLMD?

For most lawyers, Microsoft Word remains the default tool. Not because it's pleasant to use, but because it handles things that plain text traditionally can't, like:

- **Automatic multi-level numbering** that updates when sections are reorganized
- **Live cross-references** that always reference the right section numbers after edits
- **Consistent attachment numbering** for exhibits, schedules, and annexes

Replicating these capabilities in standard Markdown or plain text is tedious and usually not worth the hassle, so lawyers stay in Word, even when it makes version control painful and produces documents that are harder to automate.

KLMD bridges this gap. It brings the core automation and semantic structure lawyers rely on into a Markdown-based format, combining the ease of plain text with the professional polish of modern legal drafting tools without the overhead of a full legislative management system.

Although KLMD was designed to be rendered into Word's docx format, is not bound to any specific rendering engine, making it flexible enough to integrate into a wide range of legal drafting processes. You can render KLMD to HTML, PDF, or even directly back to plain text with all the numbering generated and filled in.

### Use Cases

- Draft and collaborate entirely in plain text while keeping advanced features like cross-references and automatic section numbering usually reserved for word processors.
- Convert to Word (.docx) for work with other lawyers.
- Plain text is durable, portable, and well-suited to version control.
- Large language models (LLMs) can revise plain-text drafts without dealing with formatting issues or the complexity of Word's docx format.
- Combine KLMD with a templating engine like Jinja2 to drive contract generation without needing to write custom extensions for section numbering and cross references.

### Design Philosophy

KLMD's markup is designed to encode *what* the text is, not *how* it should look. The goal is to capture the semantic structure of a legal document—clauses, sections, references, definitions without prescribing formatting choices such as font size, bolding, or alignment. Those are presentation concerns and should be handled in a separate styling or rendering layer.

A practical test: if the feature could be expressed as a Word style (e.g., "Heading 2" or "Block Quote"), it's a presentation element. If it changes the legal meaning or logical structure of the document (e.g., turning a word into a defined term or inserting a cross-reference), it's content.

This separation allows KLMD to be rendered in a lawyer's custom style. Fonts, page breaks, numbering style can be customized from lawyer to lawyer to match a firm's style guide.

Another important design choice is to avoid implementing features that templating engines are better suited for. For example, variable substitution is intentionally excluded; use a templating tool like Jinja2 for that.

## Quick Start

### Installation

```bash
uv sync
```

### Example

Given a KLMD source file:

```markdown
Master Services Agreement
=========================

[# Definitions] The following terms are defined:
[##] Big Company LLC (defined as the "Company") is the service provider.
[##] Services means the work described in Exhibit [#statement-of-work].

[# Payment] Client pays within 30 days of invoice.

Exhibit [# Statement of Work]
==============================

Description of services goes here.
```

Parse and render with Python:

```python
from klmd.parser import KLMDParser
from klmd.renderers.markdown import MarkdownRenderer

parser = KLMDParser()
document = parser.parse(open("contract.klmd").read())

renderer = MarkdownRenderer()
print(renderer.render(document))
```

Or use the CLI:

```bash
uv run python -m klmd contract.klmd -o contract.md
```

## Documentation

- **[Specification](docs/spec.md)** — KLMD syntax reference (sections, cross-references, defined terms, comments, signature blocks)
- **[CLI Reference](docs/cli.md)** — Command-line interface options, presets, and configuration files
- **[Markdown Renderer](docs/renderers/markdown.md)** — Renderer configuration, Python API, and output examples
- **[Future Work](FUTURE.md)** — Planned features not yet specified or implemented

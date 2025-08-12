# Khanna Law Markdown (KLMD)
A flavor of markdown designed for legal drafting.

## Introduction

The Khanna Law Markdown (KLMD) specification provides a lightweight, human-readable syntax for drafting legal documents such as contracts, legislation, and agreements. KLMD extends standard Markdown with specialized features for legal drafting without losing the portability and simplicity of plain text.

### Why KLMD?

For most lawyers, Microsoft Word remains the default tool. Not because it’s pleasant to use, but because it handles things that plain text traditionally can’t, like:

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

### Design philosophy

KLMD’s markup is designed to encode *what* the text is, not *how* it should look. The goal is to capture the semantic structure of a legal document—clauses, sections, references, definitions without prescribing formatting choices such as font size, bolding, or alignment. Those are presentation concerns and should be handled in a separate styling or rendering layer.

A practical test: if the feature could be expressed as a Word style (e.g., "Heading 2" or "Block Quote"), it’s a presentation element. If it changes the legal meaning or logical structure of the document (e.g., turning a word into a defined term or inserting a cross-reference), it’s content.

This separation allows KLMD to be rendered in a lawyer's custom style. Fonts, page breaks, numbering style can be customized from lawyer to lawyer to match a firm's style guide.

Another important design choice is to avoid implementing features that templating engines are better suited for. For example, variable substitution is intentionally excluded; use a templating tool like Jinja2 for that.

## Usage

```bash
# Install dependencies and sync environment
uv sync

# Render a klmd file to html
# (not implemented yet)
klmd examples/simple.klmd simple.html
```

## Specification

_The specification is a work in progress._

### 1. Text and paragraphs

KLMD follows standard Markdown conventions for text formatting and paragraph breaks.

#### 1.1. Paragraphs

Consecutive lines of text are joined into a single paragraph. Paragraphs are separated by one or more blank lines.

```markdown
This is the first paragraph.
This line is part of the same paragraph.

This is a second paragraph.
```

**Rendered output:**
```
This is the first paragraph. This line is part of the same paragraph.

This is a second paragraph.
```

This convention allows for natural line wrapping in source documents while maintaining semantic paragraph structure—essential for legal documents where paragraph breaks often have substantive meaning.

### 2. Section numbers

Automatic hierarchical section numbering with optional titles. Square brackets indicate placeholder content that will be replaced with actual numbers during rendering.

#### 2.1. Hierarchical numbering

Section depth is indicated by the number of hash marks. The hash must be the first non-whitespace character on the line, with at least one space after the closing bracket.

```markdown
[#] This is Section 1.
   [##] This is Section 1.1.
      [###] This is Section 1.1.1.
   [##] This is Section 1.2.
[#] This is Section 2.
   [##] This is Section 2.1.
```

**Example rendered output:**
```
1. This is Section 1.
   1.1. This is Section 1.1.
      1.1.1. This is Section 1.1.1.
   1.2. This is Section 1.2.
2. This is Section 2.
   2.1. This is Section 2.1.
```

Note: Indentation is optional and has no effect on numbering—it's purely for readability in the source.

#### 2.2. Section titles

Titles appear within the square brackets after the hash marks. Renderers typically format these in bold or underlined.

```markdown
[# Definitions] The following terms shall have the meanings set forth below.
[##] "Agreement" means this Master Services Agreement.
[##] "Services" means the services described in each Statement of Work.
[# Payment Terms] Client shall pay all fees within thirty (30) days.
[## Late Payments] Interest accrues at 1.5% per month on overdue amounts.
```

**Example rendered output:**
```
1. Definitions. The following terms shall have the meanings set forth below.
   1.1. "Agreement" means this Master Services Agreement.
   1.2. "Services" means the services described in each Statement of Work.
2. Payment Terms. Client shall pay all fees within thirty (30) days.
   2.1. Late Payments. Interest accrues at 1.5% per month on overdue amounts.
```

### 3. Document and attachment titles

Titles for main documents or attachments, marked by a line of equal signs. Renderers typically center the titles and add page breaks before these titles (except at document start).

**Syntax:** Title text followed by a line of at least 3 equal signs.

```markdown
Master Services Agreement
=========================

This Agreement is entered into as of [DATE] by and between...

[Later in document...]

Statement of Work
=================

The Vendor shall provide the following services...
```

**Common use cases:**
- Main agreement titles
- Exhibit or schedule titles within a document
- Appendix titles
- Standalone document titles

### 4. Attachment numbering

Automatic lettering for exhibits, schedules, and appendices. Note that section numbering resets within each attachment.

#### 4.1. Basic attachment

```markdown
Exhibit [#]
===========

[#] Scope of Work. The Consultant shall...
[#] Deliverables. The following deliverables...
```

**Rendered output:**
```
Exhibit A

1. Scope of Work. The Consultant shall...
2. Deliverables. The following deliverables...
```

#### 4.2. Attachment with title

```markdown
Schedule [# Pricing Terms]
==========================

[#] Base Fees. Monthly retainer of...
[#] Additional Services. Hourly rates...
```

**Example rendered output:**
```
Schedule A
Pricing Terms

1. Base Fees. Monthly retainer of...
2. Additional Services. Hourly rates...
```

**Notes:**
- Renderers may support alternate schemes (numbers, Roman numerals)

### 5. Cross references

Automatically updated references to sections, exhibits, or other numbered elements by their title.

#### 5.1. Syntax

- Format: `[#title-with-dashes]`
- Replace spaces with hyphens
- Case-insensitive matching
- No whitespace inside brackets

#### 5.2. Examples

```markdown
[# Confidentiality] Each party shall maintain strict confidentiality...
[# Payment Terms] Payment is due within 30 days...
[# Termination] Either party may terminate...

The confidentiality obligations in Section [#confidentiality] shall survive termination.
Subject to Section [#payment-terms], all fees are non-refundable.
Termination procedures are detailed in Section [#termination].
```

**Example rendered output:**
```
The confidentiality obligations in Section 1 shall survive termination.
Subject to Section 2, all fees are non-refundable.
Termination procedures are detailed in Section 3.
```

#### 5.3. Attachment references

```markdown
See Exhibit [#statement-of-work] for project details.
Pricing is set forth in Schedule [#pricing-terms].
```

#### 5.4. Error handling

- **Duplicate titles**: Parser throws error when multiple sections share the same title
- **Missing references**: Parser warns when referenced title doesn't exist
- **Case variations**: Both `[#payment-terms]` and `[#Payment-Terms]` resolve to the same section


**Notes:**
- Default format: lowercase letters in parentheses (a), (b), (c)
- Numbering resets with each paragraph
- Titles not allowed (unlike section numbers)
- Renderers may support alternate formats: (i), (ii), (iii) or (1), (2), (3)


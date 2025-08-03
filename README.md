# Khanna Law Markdown (KLMD)
A flavor of markdown designed for legal drafting.

## Introduction
The Khanna Law Markdown (KLMD) specification provides a lightweight, human-readable syntax for drafting legal documents such as contracts, legislation, and agreements. 

Existing solutions for structuring legal documents are either incomplete, unmaintained, or overly complex (e.g., full-fledged legislative management systems). KLMD aims to fill this gap by offering a practical, markdown-based approach that balances simplicity with the semantic richness needed for legal drafting. It is designed to:

1. Enable authors to focus on content, not formatting.
1. Generate outputs like Word documents, PDFs, or HTML.
1. Integrate with templating engines for automation.

KLMD is not tied to any specific rendering engine or workflow, making it adaptable to a wide range of legal drafting needs.

Why is this useful?
- Draft and collaborate on documents with plain text tooling while keeping the functionality of cross refs and automatic section numbering provided by word processors
- And easy conversion to Word docx so that you can generate it from, say, a bank of your own contract templates and then start working it from there.
- Plain text is so much better suited to legal documents
- LLMs can more easily update the drafts and not have to worry about formatting
- Can be combined with a templating engine and not need to worry about things like numbering changes and crossrefernces.

What's out of scope?
- Variable substitution. Use a templating engine like Jinja2 for that.

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

### 1. Defined term introductions

Legal documents often define parties, concepts, or other phrases for later reuse. KLMD marks such definitions with a short inline construct that is readable in plain text yet recognisable by software.

A Defined-Term Introduction (DTI) appears inside parentheses, starts with the keyword `defined as`, and binds a quoted term to text that normally precedes it (the referent). 

A renderer MUST NOT display the words `defined as` in the final output.

#### 1.1. Syntax

```markdown
( ... defined as <descriptor> "<term>" ... )
```
- **descriptor** (optional): a single word article or qualifier (e.g., `the`, `a`, `any`, `this`).
- **"term"**: the defined term, enclosed in straight ASCII double quotes
- whitespace: at least one space MUST appear after `defined as` and after any descriptor.

Multiple DTIs MAY appear inside a single pair of parentheses.

#### 1.2. Example

```markdown
This Agreement is by and between Joe Smith (defined as "Joe") and Big Company LLC (defined as the "Company" and, together with Joe, defined as the "Parties").  
```

This example introduces three defined terms: **Joe**, **Company**, and **Parties**. 

#### 1.3. Processing notes

- **Uniqueness**: Each term MUST be unique within the document. Redefinition SHOULD raise a warning.
- **Escaping**: Prefix `defined as` with a backslash to prevent parsing as a DTI. The backslash is removed during rendering:
```markdown
This is a test (this is \defined as "for example").  
```
- **Referent identification**: Not yet standardised. Parsers MAY assume the referent is the text immediately preceding the opening parenthesis until a future revision specifies an explicit rule. 

### 2. Section numbers
Section numbering. Sections can be with or without titles. 

### 2.1. Hierarchical numbering

The hash must be the first non-whitespace character on the line. There must be at least 1 space between the closing square bracket and the rest of the line.

```code
[#] This is Section 1.
[##] This is Section 1.1.
[#] This is Section 2.
[##] This is Section 2.1.
```

Indentation has no effect, so the above is equivalent to: 

```code
[#] This is Section 1.
    [##] This is Section 1.1.
[#] This is Section 2.
    [##] This is Section 2.1.
```

Square brackets are familiar to lawyers as text that will not go in the final draft.

### 2.2. Section titles

A section can contain a title. These are often rendered in bold or with an underline.

The title goes within the square brackets after the hash marks.

```code
[# Section 1 Title] This is Section 1.
    [##] This is Section 1.1. It does not have a title.
[#] This is Section 2. It does not have a title.
    [## Section 2.1 Title] This is Section 2.1.
```

## Not yet specified

The below portions of the spec have not yet been specified or implemented. They are placeholders for now.

### 2. Titles
Document/exhibit titles
top level atx with automatic page break?

### 4. Attachment numbers
Numbering exhibits and schedules: Exhibit #exhibit / Schedule #schedule

### 5. Mid-prose numbers
Mid-paragraph numbering [\#]

### 6. Scoped numbers
Context isolation with Section numbering. E.g., restart numbering in an exhibit.

### 7. Cross references

### 8. Comments
comments - initially free standing
myst-directive style syntax
Comments can eventually tie to specific sections of text, perhaps using the cross reference syntax.

### 9. Signature blocks
myst-directive style syntax

### 10. Recitals (e.g., WHEREAS)

### 11. Tracked changes syntax

### 12. Footnotes
# KLMD Specification

_The specification is a work in progress._

## 1. Text and Paragraphs

KLMD follows standard Markdown conventions for text formatting and paragraph breaks.

### 1.1. Paragraphs

Consecutive lines of text are joined into a single paragraph. Paragraphs are separated by one or more blank lines.

```markdown
This is the first paragraph.
This line is part of the same paragraph.

This is a second paragraph.
```

This convention allows for natural line wrapping in source documents while maintaining semantic paragraph structure—essential for legal documents where paragraph breaks often have substantive meaning.

## 2. Section Numbers

Automatic hierarchical section numbering with optional titles. Square brackets indicate placeholder content that will be replaced with actual numbers during rendering.

### 2.1. Hierarchical numbering

Section depth is indicated by the number of hash marks. The hash must be the first non-whitespace character on the line, with at least one space after the closing bracket.

```markdown
[#] This is Section 1.
   [##] This is Section 1.1.
      [###] This is Section 1.1.1.
   [##] This is Section 1.2.
[#] This is Section 2.
   [##] This is Section 2.1.
```

Note: Indentation is optional and has no effect on numbering—it's purely for readability in the source.

### 2.2. Section titles

Titles appear within the square brackets after the hash marks.

```markdown
[# Definitions] The following terms shall have the meanings set forth below.
[##] "Agreement" means this Master Services Agreement.
[##] "Services" means the services described in each Statement of Work.
[# Payment Terms] Client shall pay all fees within thirty (30) days.
[## Late Payments] Interest accrues at 1.5% per month on overdue amounts.
```

**Renderer options:** [Markdown](renderers/markdown.md#section-numbering)

## 3. Document and Attachment Titles

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

**Renderer options:** [Markdown](renderers/markdown.md#document-and-attachment-titles)

## 4. Attachment Numbering

Automatic lettering for exhibits, schedules, and appendices. Note that section numbering resets within each attachment.

### 4.1. Basic attachment

```markdown
Exhibit [#]
===========

[#] Scope of Work. The Consultant shall...
[#] Deliverables. The following deliverables...
```

### 4.2. Attachment with title

```markdown
Schedule [# Pricing Terms]
==========================

[#] Base Fees. Monthly retainer of...
[#] Additional Services. Hourly rates...
```

**Notes:**
- Renderers may support alternate schemes (numbers, Roman numerals)

**Renderer options:** [Markdown](renderers/markdown.md#attachment-numbering)

## 5. Cross References

Automatically updated references to sections, exhibits, or other numbered elements by their title.

### 5.1. Syntax

- Format: `[#title-with-dashes]`
- Replace spaces with hyphens
- Case-insensitive matching
- No whitespace inside brackets

### 5.2. Examples

```markdown
[# Confidentiality] Each party shall maintain strict confidentiality...
[# Payment Terms] Payment is due within 30 days...
[# Termination] Either party may terminate...

The confidentiality obligations in [#confidentiality] shall survive termination.
Subject to [#payment-terms], all fees are non-refundable.
Termination procedures are detailed in [#termination].
```

### 5.3. Attachment references

```markdown
See Exhibit [#statement-of-work] for project details.
Pricing is set forth in Schedule [#pricing-terms].
```

### 5.4. Error handling

- **Duplicate titles**: Parser throws error when multiple sections share the same title
- **Missing references**: Parser warns when referenced title doesn't exist
- **Case variations**: Both `[#payment-terms]` and `[#Payment-Terms]` resolve to the same section

**Renderer options:** [Markdown](renderers/markdown.md#cross-references)

## 6. Defined Terms

Legal documents often define parties, concepts, or other phrases for later reuse. KLMD marks such definitions with a short inline construct that is readable in plain text yet recognizable by software.

A Defined-Term Introduction (DTI) appears inside parentheses, starts with the keyword `defined as`, and binds a quoted term to text that normally precedes it (the referent).

A renderer MUST NOT display the words `defined as` in the final output.

### 6.1. Syntax

```markdown
( ... defined as <descriptor> "term" ... )
```
- **descriptor** (optional): a single word article or qualifier (e.g., `the`, `a`, `any`, `this`)
- **"term"**: the defined term, enclosed in straight ASCII double quotes
- whitespace: at least one space MUST appear after `defined as` and after any descriptor

Multiple DTIs MAY appear inside a single pair of parentheses.

### 6.2. Example

```markdown
This Agreement is by and between Joe Smith (defined as "Joe") and Big Company LLC (defined as the "Company" and, together with Joe, defined as the "Parties").
```

This example introduces three defined terms: **Joe**, **Company**, and **Parties**.

### 6.3. Processing notes

- **Uniqueness**: Each term MUST be unique within the document. Redefinition SHOULD raise a warning
- **Escaping**: Prefix `defined as` with a backslash to prevent parsing as a DTI. The backslash is removed during rendering:
```markdown
This is a test (this is \defined as "for example").
```
- **Referent identification**: Not yet standardized. Parsers MAY assume the referent is the text immediately preceding the opening parenthesis until a future revision specifies an explicit rule

**Renderer options:** [Markdown](renderers/markdown.md#defined-terms)

## 7. Comments

KLMD supports inline annotations and comments that can be included during drafting but may be excluded from final output. Comments use C-style syntax familiar to many users.

### 7.1. Line comments

Line comments start with `//` and continue to the end of the line. These are useful for notes, reminders, or section-level annotations.

```markdown
// This is a line comment
[# Payment Terms] Payment is due within 30 days.
// Note: Check with client about net-30 vs net-45

[# Termination] Either party may terminate this Agreement.
// Need to add notice period requirements
```

### 7.2. Block and inline comments

Block comments are enclosed in `/*` and `*/` and can span multiple lines or appear inline within text. These are useful for detailed notes or inline clarifications.

**Inline usage:**
```markdown
The Vendor /*ABC Corp or subsidiary*/ shall deliver by /*confirm date*/ December 31.

Payment of /*$10,000 or $15,000?*/ shall be made within thirty days.
```

**Multi-line usage:**
```markdown
/*
Multi-line comment for longer discussions:
- Need to verify payment terms with finance
- Check currency for international transactions
- Consider late payment penalties
*/

[# Warranties] The Vendor warrants that...
```

### 7.3. Processing notes

- **Rendering flexibility**: Comments may be completely omitted, converted to marginal notes, or transformed into document comments depending on the output format
- **Placement**: Comments can appear anywhere in the document - before titles, within sections, or inline within paragraphs
- **Nesting**: Block comments (`/* */`) cannot be nested within each other

**Renderer options:** [Markdown](renderers/markdown.md#comments)

## 8. Signature Blocks

Legal documents require signature blocks that identify the signing parties and their capacity. KLMD provides structured syntax for both individual and entity signatures, including nested entity relationships.

### 8.1. Syntax

Signature blocks are delimited by horizontal rules with at least three dashes, preceded by a blank line. The party name appears immediately after the horizontal rule, followed by optional metadata fields. The `By:` metadata field has special meaning described below and is case insensitive.

Indentation within signature blocks is optional and ignored by the parser—it serves only to improve readability in the source document.

```markdown

-------------------
Party Name
Field Name: Field Value
Another Field: Another Value
```

### 8.2. Individual signatures

Individual signatories require no additional fields beyond the party name. Individual signatories MUST NOT have a `By:` field.

```markdown

-------------------
John Smith

-------------------
Jane Doe
Address: 123 Main Street, New York, NY 10001
Email: jane@example.com
```

### 8.3. Entity signatures

Entity signatures are identified by the presence of a `By:` field, which specifies the human signatory acting on behalf of the entity. Entity signatures MUST contain at least the `By:` field.

```markdown

-------------------
ABC Corporation
By: John Smith
Title: Chief Executive Officer

-------------------
XYZ LLC
By: Jane Doe
Title: Managing Member
Entity Type: Delaware limited liability company
Address: 456 Corporate Boulevard, Wilmington, DE 19801
```

### 8.4. Nested entity signatures

When an entity signs on behalf of another entity, use multiple `By Entity:` fields to establish the chain of authority. Only one `By:` field is permitted per signature block, identifying the ultimate human signatory.

```markdown

-------------------
Investment Fund LP
  By Entity: ABC Management LLC, its General Partner
    By Entity: XYZ Holdings Inc., its Managing Member
      By: John Smith
      Title: President
Address: 789 Finance Street, New York, NY 10005

-------------------
Subsidiary Corp
By Entity: Parent LLC, its sole member
  By: Jane Doe
  Title: Manager
Phone: (555) 123-4567
```

The indentation in the above example is optional and purely for readability—both indented and non-indented versions are parsed identically.

### 8.5. Processing notes

- **Entity detection**: A signature block is treated as an entity signature if it contains a `By:` field
- **Required fields**: Entity signatures must contain at least one field; individual signatures may have zero fields
- **Field flexibility**: Any field names may be used beyond the specified `By:` and `By Entity:` fields
- **Chain validation**: Each `By Entity:` field should specify the relationship (e.g., "its General Partner", "its Managing Member")
- **Single human signatory**: Only one `By:` field is permitted per signature block

**Renderer options:** [Markdown](renderers/markdown.md#signature-blocks)

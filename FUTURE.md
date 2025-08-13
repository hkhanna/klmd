# Future work

The below portions of the spec have not yet been specified or implemented. They are placeholders for now.

### Signature blocks
myst-directive style syntax?

### Reference by Id

Section or document numbers can have an `id` to avoid title conflicts and to allow cross references to numbering with no associated title (e.g., mid-prose numbers).

### Reset numbering

Useful if, e.g., we're doing multiple groups of mid-prose numbers in a section. Need to find a way to specify the first group is (a) (b) (c) and the second group is (x) (y) (z) for example.

### Scoped numbers
Context isolation with Section numbering. E.g., restart numbering in an exhibit.

### Recitals (e.g., WHEREAS)

Do these need a separate syntax?

### Mid-prose numbers

Inline numbering or lettering within paragraphs, commonly used for listing obligations, conditions, or steps.

#### Basic usage

```markdown
The Consultant shall: [#] provide weekly status reports; [#] attend all project meetings; and [#] maintain complete documentation.
```

**Example rendered output:**
```
The Consultant shall: (a) provide weekly status reports; (b) attend all project meetings; and (c) maintain complete documentation.
```

#### Common patterns

```markdown
# Conditions precedent
Closing is subject to: [#] completion of due diligence, [#] receipt of regulatory approval, and [#] execution of ancillary agreements.

# Step-by-step processes
To submit a claim: [#] complete the claim form, [#] attach supporting documentation, [#] submit within 30 days, and [#] await confirmation.

# Multiple obligations
Each party shall [#] act in good faith, [#] provide reasonable cooperation, and [#] maintain confidentiality.
```
### Mid-prose numbers with automatic conjunctions

The last element will often need a conjunction before the final element (like "and" or "or").  Sometimes we'll want to automatically add a conjunction before the last element rather than writing it in the sentence itself. This is often really useful in combination with a templating engine.

One possible syntax is colons. But we can't just put the colon on the last element because a templating engine might omit that last element.

```code
The parties shall [#] negotiate in good faith, [#] be available to one other to consult, [and:#] have a great time.
```
### Footnotes

### Tying comments to specific parts of the text
Possibly using cross-reference syntax


### Tracked changes syntax

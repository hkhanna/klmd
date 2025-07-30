"""DTI (Defined Term Introduction) feature implementation for KLMD."""

import re
from typing import Any

from markdown_it import MarkdownIt


def process_dti_in_text(text: str) -> str:
    """Process DTI syntax in text content.

    Args:
        text: The text content to process

    Returns:
        The text with DTI syntax converted to HTML
    """
    # Pattern to match DTI syntax: (defined as [descriptor] "term")
    # But exclude cases where "defined as" is escaped with backslash
    dti_pattern = r"\(([^)]*(?<!\\)defined\s+as[^)]*)\)"

    def replace_dti(match: re.Match[str]) -> str:
        content = match.group(1)

        # Check if content contains valid DTI patterns (not escaped)
        if "defined as" not in content:
            return match.group(0)  # Return original if no DTI found

        # Find all DTI patterns within the parentheses
        term_pattern = r'(?<!\\)defined\s+as\s+(?:(the|a|any|this)\s+)?"([^"]+)"'
        term_matches = list(re.finditer(term_pattern, content))

        if not term_matches:
            return match.group(0)  # Return original if no valid DTI patterns

        # Process the content, replacing DTI patterns
        result = content
        offset = 0

        for term_match in term_matches:
            descriptor = term_match.group(1)  # Optional descriptor
            term = term_match.group(2)  # The defined term

            # Build replacement
            replacement = ""
            if descriptor:
                replacement += descriptor + " "
            replacement += f'"<strong>{term}</strong>"'

            # Replace in result string
            start = term_match.start() + offset
            end = term_match.end() + offset
            old_text = result[start:end]
            result = result[:start] + replacement + result[end:]
            offset += len(replacement) - len(old_text)

        return f"({result})"

    # Handle escaped "defined as" after DTI processing
    result = re.sub(dti_pattern, replace_dti, text)
    result = re.sub(r"\\defined\s+as", "defined as", result)

    return result


def dti_plugin(md: MarkdownIt) -> None:
    """Register DTI processing plugin with markdown-it-py.

    Args:
        md: The MarkdownIt instance to register the plugin with
    """
    # Store the original text renderer
    original_text_renderer = md.renderer.rules.get("text", None)  # type: ignore

    def render_text_with_dti(tokens: Any, idx: int, options: Any, env: Any) -> str:
        """Render text tokens with DTI processing."""
        token = tokens[idx]
        content: str = str(token.content)

        # Process DTI syntax in the content
        processed_content = process_dti_in_text(content)

        # If content changed, return the processed HTML directly
        if processed_content != content:
            return processed_content

        # Otherwise, use the original text renderer if it exists
        if original_text_renderer:
            result: Any = original_text_renderer(tokens, idx, options, env)
            return str(result)  # type: ignore[no-any-return]
        else:
            # Default text rendering - escape HTML
            return (
                content.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )  # type: ignore[no-any-return]

    # Override the text renderer
    md.renderer.rules["text"] = render_text_with_dti  # type: ignore

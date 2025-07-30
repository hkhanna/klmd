"""Utility functions for KLMD parser."""

from markdown_it import MarkdownIt


def render(text: str) -> str:
    """Render KLMD text to HTML.

    Args:
        text: The KLMD markdown text to render.

    Returns:
        The rendered HTML string.
    """
    md = MarkdownIt("zero")
    result: str = md.render(text)
    return result

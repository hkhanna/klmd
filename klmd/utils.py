"""Utility functions for KLMD parser."""

from markdown_it import MarkdownIt

from .features.dti import dti_plugin


def render(text: str) -> str:
    """Render KLMD text to HTML.

    Args:
        text: The KLMD markdown text to render.

    Returns:
        The rendered HTML string.
    """
    md = MarkdownIt("commonmark").use(dti_plugin)
    result: str = md.render(text)
    return result

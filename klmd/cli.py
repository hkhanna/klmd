"""
KLMD Command Line Interface

Converts KLMD documents to various formats with configurable rendering options.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .parser import KLMDParser
from .renderers.docx import DocxRenderer
from .renderers.docx_config import DocxConfig
from .renderers.markdown import (
    CommentStyle,
    CrossReferenceConfig,
    MarkdownConfig,
    MarkdownRenderer,
    NumberingScheme,
    NumberStyle,
    TextStyle,
)


class CLIError(Exception):
    """Exception raised for CLI-specific errors."""

    pass


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="klmd",
        description="Convert KLMD documents to various formats",
        epilog="""
Examples:
  klmd document.klmd -o document.md
  klmd contract.klmd -p legal --terms bold
  klmd -c config.yaml input.klmd
  klmd --validate document.klmd
  cat input.klmd | klmd - > output.md
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional arguments
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input KLMD file (use '-' for stdin, default: stdin)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output file (default: stdout)",
    )

    # Output options
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Output file (alternative to positional argument)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "html", "docx", "pdf"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    # Configuration file
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file (YAML or JSON)",
    )

    # Template file (for docx output)
    parser.add_argument(
        "--template",
        help="Word template file (.docx or .dotx) for docx output",
    )

    # Quick presets
    parser.add_argument(
        "-p",
        "--preset",
        choices=["decimal", "legal", "outline", "simple", "alpha_parens", "letters"],
        help="Quick preset for section numbering",
    )

    # Section numbering options
    section_group = parser.add_argument_group("Section Numbering")
    section_group.add_argument(
        "--section-preset",
        choices=["decimal", "legal", "outline", "simple", "alpha_parens"],
        help="Preset for section numbering",
    )
    section_group.add_argument(
        "--section-style-1",
        choices=["plain", "bold", "italic", "bold_italic", "code", "underline"],
        help="Title style for level 1 sections",
    )
    section_group.add_argument(
        "--section-style-2",
        choices=["plain", "bold", "italic", "bold_italic", "code", "underline"],
        help="Title style for level 2 sections",
    )
    section_group.add_argument(
        "--section-style-3",
        choices=["plain", "bold", "italic", "bold_italic", "code", "underline"],
        help="Title style for level 3 sections",
    )

    # Attachment numbering options
    attachment_group = parser.add_argument_group("Attachment Numbering")
    attachment_group.add_argument(
        "--attachment-preset",
        choices=["letters", "decimal", "simple"],
        help="Preset for attachment numbering",
    )
    attachment_group.add_argument(
        "--attachment-style",
        choices=["plain", "bold", "italic", "bold_italic", "code", "underline"],
        help="Title style for attachments",
    )

    # Defined terms
    parser.add_argument(
        "--terms",
        choices=["plain", "bold", "italic", "bold_italic", "code", "underline"],
        help="Style for defined terms",
    )

    # Cross-references
    xref_group = parser.add_argument_group("Cross-References")
    xref_group.add_argument(
        "--xref-template",
        help="Template for cross-references (e.g., 'Section {number}')",
    )
    xref_group.add_argument(
        "--xref-links",
        action="store_true",
        help="Generate markdown links for cross-references",
    )
    xref_group.add_argument(
        "--no-xref-links",
        action="store_true",
        help="Disable markdown links for cross-references",
    )

    # Comments
    parser.add_argument(
        "--comments",
        choices=["exclude", "blockquote", "html"],
        help="How to handle comments in output",
    )

    # Additional options
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate input only, do not generate output",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug output with AST information",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="klmd 0.0.1",
    )

    return parser


def load_config_file(config_path: str) -> dict[str, Any]:
    """Load configuration from YAML or JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise CLIError(f"Configuration file not found: {config_path}")

    try:
        with open(path) as f:
            if path.suffix.lower() in [".yaml", ".yml"]:
                if not YAML_AVAILABLE:
                    raise CLIError("PyYAML is required for YAML configuration files")
                result = yaml.safe_load(f)
                return result if result is not None else {}
            elif path.suffix.lower() == ".json":
                result = json.load(f)
                return result if isinstance(result, dict) else {}
            else:
                # Try to detect format from content
                content = f.read()
                f.seek(0)
                if content.strip().startswith("{"):
                    result = json.load(f)
                    return result if isinstance(result, dict) else {}
                else:
                    if not YAML_AVAILABLE:
                        raise CLIError(
                            "PyYAML is required for YAML configuration files"
                        )
                    result = yaml.safe_load(f)
                    return result if result is not None else {}
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise CLIError(f"Error parsing configuration file: {e}") from e


def text_style_from_string(style_str: str) -> TextStyle:
    """Convert string to TextStyle enum."""
    style_map = {
        "plain": TextStyle.PLAIN,
        "bold": TextStyle.BOLD,
        "italic": TextStyle.ITALIC,
        "bold_italic": TextStyle.BOLD_ITALIC,
        "code": TextStyle.CODE,
        "underline": TextStyle.UNDERLINE,
    }
    return style_map[style_str]


def comment_style_from_string(style_str: str) -> CommentStyle:
    """Convert string to CommentStyle enum."""
    style_map = {
        "exclude": CommentStyle.EXCLUDE,
        "blockquote": CommentStyle.BLOCKQUOTE,
        "html": CommentStyle.HTML_COMMENT,
    }
    return style_map[style_str]


def create_docx_config_from_args(
    args: argparse.Namespace, config_dict: dict[str, Any]
) -> DocxConfig:
    """Create DocxConfig from command line arguments and config file."""
    # Template is required for docx output
    if not args.template:
        raise CLIError("--template is required for docx output")

    template_path = Path(args.template)
    if not template_path.exists():
        raise CLIError(f"Template file not found: {args.template}")

    # Start with required template
    generate_hyperlinks = True
    generate_bookmarks = True
    defined_term_bold = True

    # Apply config file settings
    if "cross_references" in config_dict:
        xref_config = config_dict["cross_references"]
        if "links" in xref_config:
            generate_hyperlinks = xref_config["links"]
            generate_bookmarks = xref_config["links"]

    if "defined_terms" in config_dict:
        defined_term_bold = config_dict["defined_terms"] == "bold"

    # Apply command line arguments (these override config file)
    if args.xref_links:
        generate_hyperlinks = True
        generate_bookmarks = True
    elif args.no_xref_links:
        generate_hyperlinks = False

    if args.terms:
        defined_term_bold = args.terms == "bold"

    return DocxConfig(
        template_path=template_path,
        generate_hyperlinks=generate_hyperlinks,
        generate_bookmarks=generate_bookmarks,
        defined_term_bold=defined_term_bold,
    )


def create_config_from_args(
    args: argparse.Namespace, config_dict: dict[str, Any]
) -> MarkdownConfig:
    """Create MarkdownConfig from command line arguments and config file."""
    # Start with defaults
    config = MarkdownConfig()

    # Apply config file settings
    if "section_numbering" in config_dict:
        section_config = config_dict["section_numbering"]
        if "preset" in section_config:
            config.section_numbering = NumberingScheme.from_preset(
                section_config["preset"]
            )

        # Apply customizations
        if "customize" in section_config:
            for level_str, level_config in section_config["customize"].items():
                level = int(level_str) - 1  # Convert to 0-based index
                if level < len(config.section_numbering.levels):
                    current = config.section_numbering.levels[level]
                    if "style" in level_config:
                        style_map = {
                            "arabic": NumberStyle.ARABIC,
                            "alpha_lower": NumberStyle.ALPHA_LOWER,
                            "alpha_upper": NumberStyle.ALPHA_UPPER,
                            "roman_lower": NumberStyle.ROMAN_LOWER,
                            "roman_upper": NumberStyle.ROMAN_UPPER,
                        }
                        current.style = style_map[level_config["style"]]
                    if "title_style" in level_config:
                        current.title_style = text_style_from_string(
                            level_config["title_style"]
                        )
                    if "prefix" in level_config:
                        current.prefix = level_config["prefix"]
                    if "suffix" in level_config:
                        current.suffix = level_config["suffix"]
                    if "include_parent" in level_config:
                        current.include_parent = level_config["include_parent"]

    if "attachment_numbering" in config_dict:
        attach_config = config_dict["attachment_numbering"]
        if "preset" in attach_config:
            config.attachment_numbering = NumberingScheme.from_preset(
                attach_config["preset"]
            )

    if "defined_terms" in config_dict:
        config.defined_term_style = text_style_from_string(config_dict["defined_terms"])

    if "cross_references" in config_dict:
        xref_config = config_dict["cross_references"]
        config.cross_references = CrossReferenceConfig(
            template=xref_config.get("template", config.cross_references.template),
            generate_links=xref_config.get(
                "links", config.cross_references.generate_links
            ),
        )

    if "comments" in config_dict:
        config.include_comments = comment_style_from_string(config_dict["comments"])

    # Apply command line arguments (these override config file)
    if args.preset:
        config.section_numbering = NumberingScheme.from_preset(args.preset)

    if args.section_preset:
        config.section_numbering = NumberingScheme.from_preset(args.section_preset)

    # Apply individual section style overrides
    if args.section_style_1 and len(config.section_numbering.levels) > 0:
        config.section_numbering.levels[0].title_style = text_style_from_string(
            args.section_style_1
        )
    if args.section_style_2 and len(config.section_numbering.levels) > 1:
        config.section_numbering.levels[1].title_style = text_style_from_string(
            args.section_style_2
        )
    if args.section_style_3 and len(config.section_numbering.levels) > 2:
        config.section_numbering.levels[2].title_style = text_style_from_string(
            args.section_style_3
        )

    if args.attachment_preset:
        config.attachment_numbering = NumberingScheme.from_preset(
            args.attachment_preset
        )

    if args.attachment_style and len(config.attachment_numbering.levels) > 0:
        config.attachment_numbering.levels[0].title_style = text_style_from_string(
            args.attachment_style
        )

    if args.terms:
        config.defined_term_style = text_style_from_string(args.terms)

    if args.xref_template:
        config.cross_references.template = args.xref_template

    if args.xref_links:
        config.cross_references.generate_links = True
    elif args.no_xref_links:
        config.cross_references.generate_links = False

    if args.comments:
        config.include_comments = comment_style_from_string(args.comments)

    return config


def open_input_file(filename: str) -> TextIO:
    """Open input file or return stdin."""
    if filename == "-":
        return sys.stdin
    try:
        return open(filename, encoding="utf-8")
    except FileNotFoundError as e:
        raise CLIError(f"Input file not found: {filename}") from e
    except PermissionError as e:
        raise CLIError(f"Permission denied reading file: {filename}") from e


def open_output_file(filename: str) -> TextIO:
    """Open output file or return stdout."""
    if filename is None:
        return sys.stdout
    try:
        return open(filename, "w", encoding="utf-8")
    except PermissionError as e:
        raise CLIError(f"Permission denied writing file: {filename}") from e


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load configuration file if specified
        config_dict = {}
        if args.config:
            config_dict = load_config_file(args.config)

        # Determine output file
        output_file = args.output_file or args.output

        # Read input
        with open_input_file(args.input) as f:
            input_text = f.read()

        if args.verbose:
            input_desc = "stdin" if args.input == "-" else args.input
            print(f"Reading from: {input_desc}", file=sys.stderr)
            if output_file:
                print(f"Writing to: {output_file}", file=sys.stderr)
            else:
                print("Writing to: stdout", file=sys.stderr)

        # Parse the document
        parser_instance = KLMDParser()
        try:
            document = parser_instance.parse(input_text)
        except Exception as e:
            if args.debug:
                raise
            raise CLIError(f"Parse error: {e}") from e

        if args.debug:
            print("=== AST Debug Output ===", file=sys.stderr)
            print(f"Document: {document}", file=sys.stderr)
            print("======================", file=sys.stderr)

        # Validation mode - just parse and exit
        if args.validate:
            if args.verbose:
                print("Document validation successful", file=sys.stderr)
            return 0

        # Create renderer configuration
        config = create_config_from_args(args, config_dict)

        if args.debug:
            print("=== Renderer Config ===", file=sys.stderr)
            print(f"Config: {config}", file=sys.stderr)
            print("======================", file=sys.stderr)

        # Render the document
        if args.format == "markdown":
            renderer = MarkdownRenderer(config)
            output_text = renderer.render(document)

            # Write output
            with open_output_file(output_file) as f:
                f.write(output_text)

        elif args.format == "docx":
            docx_config = create_docx_config_from_args(args, config_dict)
            docx_renderer = DocxRenderer(docx_config)
            output_bytes = docx_renderer.render(document)

            if output_file:
                Path(output_file).write_bytes(output_bytes)
            else:
                sys.stdout.buffer.write(output_bytes)

        else:
            raise CLIError(f"Format '{args.format}' not yet implemented")

        if args.verbose and output_file:
            print("Conversion completed successfully", file=sys.stderr)

        return 0

    except CLIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        if args.debug if "args" in locals() else False:
            raise
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

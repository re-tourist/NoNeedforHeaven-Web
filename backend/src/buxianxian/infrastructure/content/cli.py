"""Standard-library command line for content validation and compilation."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from buxianxian.infrastructure.content.compiler import compile_content, validate_content
from buxianxian.infrastructure.content.errors import ContentCompilationError

DEFAULT_SOURCE = Path("../authoring/published/documents")
DEFAULT_OUTPUT = Path("../runtime-content/buxianxian-content.json")


def main(argv: Sequence[str] | None = None) -> int:
    """Validate CLI arguments, execute one command, and return a process status."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    command_value: object = arguments.command
    source_value: object = arguments.source
    output_value: object = arguments.output
    if not isinstance(command_value, str) or not isinstance(source_value, Path):
        raise RuntimeError("content CLI produced an invalid parsed command")
    if output_value is not None and not isinstance(output_value, Path):
        raise RuntimeError("content CLI produced an invalid output path")

    try:
        if command_value == "validate":
            package = validate_content(source_value)
            print(f"Validated {len(package.entries)} content entries.")
            return 0
        if command_value == "compile":
            output_file = output_value or DEFAULT_OUTPUT
            package = compile_content(source_value, output_file)
            print(f"Compiled {len(package.entries)} content entries to {output_file}.")
            return 0
    except ContentCompilationError as error:
        for issue in error.issues:
            print(issue.describe(), file=sys.stderr)
        return 1

    raise RuntimeError(f"unsupported parsed content command {command_value!r}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate or compile 不羡仙 published content.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate without writing a package")
    validate_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    validate_parser.set_defaults(output=None)

    compile_parser = subparsers.add_parser("compile", help="validate and write a runtime package")
    compile_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    compile_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    return parser

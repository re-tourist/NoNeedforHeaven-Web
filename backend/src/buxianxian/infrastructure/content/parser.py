"""Restricted frontmatter parsing and read-only document validation."""

import json
import re
from pathlib import Path
from typing import Never

from buxianxian.infrastructure.content.errors import (
    ContentCompilationError,
    ContentIssue,
    ContentIssueCode,
)
from buxianxian.infrastructure.content.model import (
    READ_ONLY_DOCUMENT_SCHEMA_VERSION,
    ContentType,
    ReadOnlyDocument,
)

_FRONTMATTER_DELIMITER = "---"
_EXPECTED_FIELDS = frozenset({"schema_version", "id", "type", "title"})
_KEY_PATTERN = re.compile(r"[a-z_][a-z0-9_]*")
_CONTENT_ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")
_INTEGER_PATTERN = re.compile(r"0|[1-9][0-9]*")
_COMPLEX_VALUE_PREFIXES = frozenset("[{>|&*!@`")

type _Scalar = str | int
type _MetadataValue = tuple[_Scalar, int]


def parse_read_only_document(source: Path) -> ReadOnlyDocument:
    """Read, parse, and validate one dedicated publication source file."""

    text = _read_utf8(source)
    lines = text.splitlines(keepends=True)
    if not lines or _line_content(lines[0]) != _FRONTMATTER_DELIMITER:
        _raise_issue(
            ContentIssueCode.MISSING_FRONTMATTER,
            source,
            "file must begin with a frontmatter delimiter",
            line=1,
        )

    closing_index = _find_closing_delimiter(lines)
    if closing_index is None:
        _raise_issue(
            ContentIssueCode.INVALID_FRONTMATTER,
            source,
            "frontmatter closing delimiter is missing",
            line=1,
        )

    metadata = _parse_metadata(lines[1:closing_index], source)
    missing_fields = sorted(_EXPECTED_FIELDS.difference(metadata))
    if missing_fields:
        _raise_issue(
            ContentIssueCode.MISSING_FIELD,
            source,
            f"required field {missing_fields[0]!r} is missing",
            line=1,
        )

    schema_version, schema_line = metadata["schema_version"]
    if not isinstance(schema_version, int):
        _raise_issue(
            ContentIssueCode.INVALID_FIELD,
            source,
            "schema_version must be a non-negative integer",
            line=schema_line,
        )
    if schema_version != READ_ONLY_DOCUMENT_SCHEMA_VERSION:
        _raise_issue(
            ContentIssueCode.UNSUPPORTED_SCHEMA_VERSION,
            source,
            f"document schema version {schema_version} is not supported",
            line=schema_line,
        )

    content_id, id_line = _require_string_field(metadata, "id", source)
    if len(content_id) > 128 or _CONTENT_ID_PATTERN.fullmatch(content_id) is None:
        _raise_issue(
            ContentIssueCode.INVALID_CONTENT_ID,
            source,
            "id must be 1-128 lowercase ASCII characters in stable machine-id form",
            line=id_line,
        )

    raw_content_type, type_line = _require_string_field(metadata, "type", source)
    if raw_content_type != ContentType.READ_ONLY_DOCUMENT:
        _raise_issue(
            ContentIssueCode.UNSUPPORTED_CONTENT_TYPE,
            source,
            f"content type {raw_content_type!r} is not supported",
            line=type_line,
        )

    title, title_line = _require_string_field(metadata, "title", source)
    if not title.strip():
        _raise_issue(
            ContentIssueCode.EMPTY_TITLE,
            source,
            "title cannot be empty",
            line=title_line,
        )

    markdown = "".join(lines[closing_index + 1 :])
    if not markdown.strip():
        _raise_issue(
            ContentIssueCode.EMPTY_BODY,
            source,
            "Markdown body cannot be empty",
            line=closing_index + 2,
        )

    return ReadOnlyDocument(
        schema_version=schema_version,
        content_id=content_id,
        content_type=ContentType.READ_ONLY_DOCUMENT,
        title=title,
        markdown=markdown,
    )


def _read_utf8(source: Path) -> str:
    try:
        return source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        _raise_issue(
            ContentIssueCode.INVALID_ENCODING,
            source,
            "source must be valid UTF-8",
        )
    except OSError:
        _raise_issue(
            ContentIssueCode.SOURCE_READ_ERROR,
            source,
            "source file could not be read",
        )


def _find_closing_delimiter(lines: list[str]) -> int | None:
    for index, line in enumerate(lines[1:], start=1):
        if _line_content(line) == _FRONTMATTER_DELIMITER:
            return index
    return None


def _parse_metadata(lines: list[str], source: Path) -> dict[str, _MetadataValue]:
    metadata: dict[str, _MetadataValue] = {}
    for offset, line in enumerate(lines, start=2):
        raw_line = _line_content(line)
        if not raw_line.strip():
            continue
        if raw_line.lstrip().startswith("#") or ":" not in raw_line:
            _raise_issue(
                ContentIssueCode.INVALID_FRONTMATTER,
                source,
                "frontmatter lines must use simple key: value scalars",
                line=offset,
            )

        raw_key, raw_value = raw_line.split(":", maxsplit=1)
        key = raw_key.strip()
        if key != raw_key or _KEY_PATTERN.fullmatch(key) is None:
            _raise_issue(
                ContentIssueCode.INVALID_FRONTMATTER,
                source,
                "frontmatter key is invalid",
                line=offset,
            )
        if key not in _EXPECTED_FIELDS:
            _raise_issue(
                ContentIssueCode.INVALID_FRONTMATTER,
                source,
                f"frontmatter field {key!r} is not supported",
                line=offset,
            )
        if key in metadata:
            _raise_issue(
                ContentIssueCode.INVALID_FRONTMATTER,
                source,
                f"frontmatter field {key!r} is duplicated",
                line=offset,
            )

        metadata[key] = (_parse_scalar(raw_value.strip(), source, offset), offset)

    return metadata


def _require_string_field(
    metadata: dict[str, _MetadataValue],
    key: str,
    source: Path,
) -> tuple[str, int]:
    value, line = metadata[key]
    if not isinstance(value, str):
        _raise_issue(
            ContentIssueCode.INVALID_FIELD,
            source,
            f"{key} must be a string",
            line=line,
        )
    return value, line


def _parse_scalar(value: str, source: Path, line: int) -> _Scalar:
    if not value:
        return ""
    if value.startswith('"'):
        try:
            parsed_value: object = json.loads(value)
        except json.JSONDecodeError:
            _raise_issue(
                ContentIssueCode.INVALID_FRONTMATTER,
                source,
                "double-quoted scalar is invalid",
                line=line,
            )
        if not isinstance(parsed_value, str):
            _raise_issue(
                ContentIssueCode.INVALID_FRONTMATTER,
                source,
                "frontmatter values must be strings or the schema version integer",
                line=line,
            )
        return parsed_value

    if value.startswith("'") or value[0] in _COMPLEX_VALUE_PREFIXES or " #" in value:
        _raise_issue(
            ContentIssueCode.INVALID_FRONTMATTER,
            source,
            "complex YAML and comments are not supported in frontmatter",
            line=line,
        )
    if _INTEGER_PATTERN.fullmatch(value) is not None:
        return int(value)
    return value


def _line_content(line: str) -> str:
    return line.rstrip("\r\n")


def _raise_issue(
    code: ContentIssueCode,
    source: Path,
    detail: str,
    *,
    line: int | None = None,
) -> Never:
    raise ContentCompilationError((ContentIssue(code, source, detail, line),))

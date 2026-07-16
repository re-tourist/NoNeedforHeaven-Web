"""Deterministic content discovery, validation, serialization, and atomic output."""

import json
import os
import tempfile
from pathlib import Path

from buxianxian.infrastructure.content.errors import (
    ContentCompilationError,
    ContentIssue,
    ContentIssueCode,
)
from buxianxian.infrastructure.content.model import (
    CONTENT_FORMAT,
    CONTENT_PACKAGE_SCHEMA_VERSION,
    ContentPackage,
    ReadOnlyDocument,
)
from buxianxian.infrastructure.content.parser import parse_read_only_document

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]


def validate_content(source_directory: Path) -> ContentPackage:
    """Validate all dedicated publication sources and return a deterministic package."""

    source_files, discovery_issues = _discover_source_files(source_directory)
    documents: list[ReadOnlyDocument] = []
    issues = list(discovery_issues)
    id_sources: dict[str, Path] = {}

    for source in source_files:
        try:
            document = parse_read_only_document(source)
        except ContentCompilationError as error:
            issues.extend(error.issues)
            continue

        previous_source = id_sources.get(document.content_id)
        if previous_source is not None:
            issues.append(
                ContentIssue(
                    ContentIssueCode.DUPLICATE_CONTENT_ID,
                    source,
                    (
                        f"id {document.content_id!r} duplicates source "
                        f"{previous_source.as_posix()!r}"
                    ),
                )
            )
            continue

        id_sources[document.content_id] = source
        documents.append(document)

    if issues:
        raise ContentCompilationError(_sort_issues(issues))

    return ContentPackage(
        format=CONTENT_FORMAT,
        schema_version=CONTENT_PACKAGE_SCHEMA_VERSION,
        entries=tuple(sorted(documents, key=lambda document: document.content_id)),
    )


def compile_content(source_directory: Path, output_file: Path) -> ContentPackage:
    """Validate completely, then atomically write one deterministic runtime package."""

    package = validate_content(source_directory)
    serialized = serialize_content_package(package)
    _atomic_write_text(output_file, serialized)
    return package


def serialize_content_package(package: ContentPackage) -> str:
    """Return the canonical UTF-8 JSON text for a compiled package."""

    entries: list[JsonValue] = []
    for document in sorted(package.entries, key=lambda entry: entry.content_id):
        entries.append(
            {
                "schema_version": document.schema_version,
                "id": document.content_id,
                "type": document.content_type.value,
                "title": document.title,
                "markdown": document.markdown,
            }
        )

    payload: dict[str, JsonValue] = {
        "format": package.format,
        "schema_version": package.schema_version,
        "entries": entries,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _discover_source_files(
    source_directory: Path,
) -> tuple[tuple[Path, ...], tuple[ContentIssue, ...]]:
    if not source_directory.is_dir():
        issue = ContentIssue(
            ContentIssueCode.SOURCE_DIRECTORY_NOT_FOUND,
            source_directory,
            "published source directory does not exist or is not a directory",
        )
        return (), (issue,)

    source_files: list[Path] = []
    issues: list[ContentIssue] = []
    try:
        candidates = tuple(source_directory.rglob("*.md"))
    except OSError:
        issue = ContentIssue(
            ContentIssueCode.SOURCE_READ_ERROR,
            source_directory,
            "published source directory could not be scanned",
        )
        return (), (issue,)

    for candidate in candidates:
        try:
            is_symlink = candidate.is_symlink()
            is_file = candidate.is_file()
        except OSError:
            issues.append(
                ContentIssue(
                    ContentIssueCode.SOURCE_READ_ERROR,
                    candidate,
                    "source file metadata could not be read",
                )
            )
            continue

        if is_symlink:
            issues.append(
                ContentIssue(
                    ContentIssueCode.SOURCE_SYMLINK,
                    candidate,
                    "symbolic-link sources are not allowed",
                )
            )
        elif is_file:
            source_files.append(candidate)

    source_files.sort(key=lambda path: path.relative_to(source_directory).as_posix())
    return tuple(source_files), _sort_issues(issues)


def _sort_issues(issues: list[ContentIssue]) -> tuple[ContentIssue, ...]:
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.source.as_posix(),
                issue.line if issue.line is not None else 0,
                issue.code.value,
            ),
        )
    )


def _atomic_write_text(output_file: Path, serialized: str) -> None:
    temporary_path: Path | None = None
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output_file.name}.",
            suffix=".tmp",
            dir=output_file.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        _replace_file(temporary_path, output_file)
        temporary_path = None
    except OSError:
        issue = ContentIssue(
            ContentIssueCode.OUTPUT_WRITE_ERROR,
            output_file,
            "runtime content package could not be written atomically",
        )
        raise ContentCompilationError((issue,)) from None
    finally:
        if temporary_path is not None:
            _remove_temporary_file(temporary_path)


def _replace_file(source: Path, target: Path) -> None:
    os.replace(source, target)


def _remove_temporary_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return

"""Structured, source-aware failures for content validation and output."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ContentIssueCode(StrEnum):
    """Stable categories for expected content compilation failures."""

    SOURCE_DIRECTORY_NOT_FOUND = "source_directory_not_found"
    SOURCE_SYMLINK = "source_symlink"
    SOURCE_READ_ERROR = "source_read_error"
    INVALID_ENCODING = "invalid_encoding"
    MISSING_FRONTMATTER = "missing_frontmatter"
    INVALID_FRONTMATTER = "invalid_frontmatter"
    MISSING_FIELD = "missing_field"
    INVALID_FIELD = "invalid_field"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
    INVALID_CONTENT_ID = "invalid_content_id"
    DUPLICATE_CONTENT_ID = "duplicate_content_id"
    EMPTY_TITLE = "empty_title"
    EMPTY_BODY = "empty_body"
    OUTPUT_WRITE_ERROR = "output_write_error"


@dataclass(frozen=True, slots=True)
class ContentIssue:
    """One validation or output issue tied to a relevant file and optional line."""

    code: ContentIssueCode
    source: Path
    detail: str
    line: int | None = None

    def describe(self) -> str:
        """Return a stable human-readable diagnostic with source context."""

        location = str(self.source)
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{location}: {self.code.value}: {self.detail}"


class ContentCompilationError(Exception):
    """Expected failure containing one or more ordered structured issues."""

    issues: tuple[ContentIssue, ...]

    def __init__(self, issues: tuple[ContentIssue, ...]) -> None:
        if not issues:
            raise ValueError("content compilation error requires at least one issue")
        self.issues = issues
        super().__init__("\n".join(issue.describe() for issue in issues))

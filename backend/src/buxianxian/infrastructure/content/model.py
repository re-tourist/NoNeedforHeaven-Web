"""Versioned runtime content contracts for compiled read-only documents."""

from dataclasses import dataclass
from enum import StrEnum

CONTENT_FORMAT = "buxianxian-content"
CONTENT_PACKAGE_SCHEMA_VERSION = 1
READ_ONLY_DOCUMENT_SCHEMA_VERSION = 1


class ContentType(StrEnum):
    """Content kinds supported by the current package schema."""

    READ_ONLY_DOCUMENT = "read_only_document"


@dataclass(frozen=True, slots=True)
class ReadOnlyDocument:
    """Compiled Markdown document independent from its authoring file path."""

    schema_version: int
    content_id: str
    content_type: ContentType
    title: str
    markdown: str


@dataclass(frozen=True, slots=True)
class ContentPackage:
    """Complete deterministic runtime content package."""

    format: str
    schema_version: int
    entries: tuple[ReadOnlyDocument, ...]

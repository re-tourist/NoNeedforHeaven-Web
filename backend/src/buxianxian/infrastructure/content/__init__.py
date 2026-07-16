"""Public contracts for read-only document validation and compilation."""

from buxianxian.infrastructure.content.compiler import (
    compile_content,
    serialize_content_package,
    validate_content,
)
from buxianxian.infrastructure.content.errors import (
    ContentCompilationError,
    ContentIssue,
    ContentIssueCode,
)
from buxianxian.infrastructure.content.model import (
    CONTENT_FORMAT,
    CONTENT_PACKAGE_SCHEMA_VERSION,
    READ_ONLY_DOCUMENT_SCHEMA_VERSION,
    ContentPackage,
    ContentType,
    ReadOnlyDocument,
)
from buxianxian.infrastructure.content.parser import parse_read_only_document

__all__ = [
    "CONTENT_FORMAT",
    "CONTENT_PACKAGE_SCHEMA_VERSION",
    "READ_ONLY_DOCUMENT_SCHEMA_VERSION",
    "ContentCompilationError",
    "ContentIssue",
    "ContentIssueCode",
    "ContentPackage",
    "ContentType",
    "ReadOnlyDocument",
    "compile_content",
    "parse_read_only_document",
    "serialize_content_package",
    "validate_content",
]

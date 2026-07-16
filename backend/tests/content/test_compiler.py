"""Read-only publication validation and deterministic compilation tests."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

import buxianxian.infrastructure.content.compiler as compiler_module
from buxianxian.infrastructure.content import (
    CONTENT_FORMAT,
    CONTENT_PACKAGE_SCHEMA_VERSION,
    ContentCompilationError,
    ContentIssueCode,
    compile_content,
    serialize_content_package,
    validate_content,
)
from buxianxian.infrastructure.content.cli import main

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "published"


def _document(
    *,
    content_id: str = "document.example",
    content_type: str = "read_only_document",
    schema_version: str = "1",
    title: str = '"Example Document"',
    body: str = "# Example\n\nNeutral body.\n",
) -> str:
    return (
        "---\n"
        f"schema_version: {schema_version}\n"
        f"id: {content_id}\n"
        f"type: {content_type}\n"
        f"title: {title}\n"
        "---\n"
        f"{body}"
    )


def _write_document(source_root: Path, relative_path: str, text: str) -> Path:
    path = source_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _assert_single_issue(source_root: Path, code: ContentIssueCode) -> ContentCompilationError:
    with pytest.raises(ContentCompilationError) as captured:
        validate_content(source_root)
    assert captured.value.issues[0].code is code
    return captured.value


def test_valid_document_preserves_contract_fields_and_markdown() -> None:
    package = validate_content(FIXTURE_ROOT)

    assert package.format == CONTENT_FORMAT == "buxianxian-content"
    assert package.schema_version == CONTENT_PACKAGE_SCHEMA_VERSION == 1
    assert len(package.entries) == 1
    entry = package.entries[0]
    assert entry.content_id == "document.alpha"
    assert entry.content_type.value == "read_only_document"
    assert entry.title == "中性文档"
    assert entry.markdown == "# Alpha\n\nNeutral fixture body.\n"


def test_multiple_documents_are_sorted_by_stable_id(tmp_path: Path) -> None:
    source_root = tmp_path / "published" / "documents"
    _write_document(source_root, "z-last.md", _document(content_id="document.zulu"))
    _write_document(source_root, "nested/a-first.md", _document(content_id="document.alpha"))

    package = validate_content(source_root)

    assert [entry.content_id for entry in package.entries] == [
        "document.alpha",
        "document.zulu",
    ]


def test_repeated_compilation_is_byte_identical_and_contains_no_source_path(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "published" / "documents"
    _write_document(source_root, "entry.md", _document(title='"中性标题"'))
    first_output = tmp_path / "first.json"
    second_output = tmp_path / "second.json"

    first_package = compile_content(source_root, first_output)
    second_package = compile_content(source_root, second_output)
    first_bytes = first_output.read_bytes()

    assert first_package == second_package
    assert first_bytes == second_output.read_bytes()
    serialized = first_bytes.decode("utf-8")
    assert str(tmp_path) not in serialized
    assert "published" not in serialized
    assert "author" not in serialized.lower()
    decoded: dict[str, object] = json.loads(serialized)
    assert decoded["format"] == "buxianxian-content"
    assert decoded["schema_version"] == 1


def test_private_sibling_is_not_scanned(tmp_path: Path) -> None:
    authoring_root = tmp_path / "authoring"
    source_root = authoring_root / "published" / "documents"
    private_root = authoring_root / "private"
    _write_document(source_root, "valid.md", _document())
    _write_document(private_root, "invalid.md", "private material without frontmatter")

    package = validate_content(source_root)

    assert len(package.entries) == 1
    assert "private material" not in serialize_content_package(package)


def test_duplicate_id_is_rejected_with_source_context(tmp_path: Path) -> None:
    source_root = tmp_path / "documents"
    _write_document(source_root, "one.md", _document(content_id="duplicate.id"))
    duplicate = _write_document(
        source_root,
        "two.md",
        _document(content_id="duplicate.id"),
    )

    error = _assert_single_issue(source_root, ContentIssueCode.DUPLICATE_CONTENT_ID)

    assert error.issues[0].source == duplicate
    assert "one.md" in error.issues[0].detail


@pytest.mark.parametrize(
    ("source_bytes", "expected_code"),
    [
        (b"# No frontmatter\n", ContentIssueCode.MISSING_FRONTMATTER),
        (
            b"---\nschema_version: 1\nid: document.example\ntitle: Example\n---\nBody\n",
            ContentIssueCode.MISSING_FIELD,
        ),
        (
            _document(content_type="scene").encode(),
            ContentIssueCode.UNSUPPORTED_CONTENT_TYPE,
        ),
        (
            _document(schema_version="2").encode(),
            ContentIssueCode.UNSUPPORTED_SCHEMA_VERSION,
        ),
        (_document(schema_version='"1"').encode(), ContentIssueCode.INVALID_FIELD),
        (_document(title="123").encode(), ContentIssueCode.INVALID_FIELD),
        (_document(content_id="Invalid ID").encode(), ContentIssueCode.INVALID_CONTENT_ID),
        (_document(title='""').encode(), ContentIssueCode.EMPTY_TITLE),
        (_document(body=" \n").encode(), ContentIssueCode.EMPTY_BODY),
        (
            b"---\nschema_version: [1]\nid: document.example\n"
            b"type: read_only_document\ntitle: Example\n---\nBody\n",
            ContentIssueCode.INVALID_FRONTMATTER,
        ),
        (b"\xff\xfe\x00", ContentIssueCode.INVALID_ENCODING),
    ],
)
def test_invalid_sources_are_rejected_with_structured_file_and_line_context(
    tmp_path: Path,
    source_bytes: bytes,
    expected_code: ContentIssueCode,
) -> None:
    source_root = tmp_path / "documents"
    source_root.mkdir()
    source = source_root / "invalid.md"
    source.write_bytes(source_bytes)

    error = _assert_single_issue(source_root, expected_code)

    assert error.issues[0].source == source
    assert str(source) in error.issues[0].describe()
    if expected_code is not ContentIssueCode.INVALID_ENCODING:
        assert error.issues[0].line is not None


def test_invalid_source_does_not_create_or_replace_a_formal_package(tmp_path: Path) -> None:
    source_root = tmp_path / "documents"
    source = _write_document(source_root, "entry.md", _document())
    output = tmp_path / "runtime" / "content.json"
    compile_content(source_root, output)
    old_bytes = output.read_bytes()
    source.write_text("invalid", encoding="utf-8")

    with pytest.raises(ContentCompilationError):
        compile_content(source_root, output)

    assert output.read_bytes() == old_bytes


def test_replace_failure_preserves_old_package_and_cleans_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "documents"
    _write_document(source_root, "entry.md", _document())
    output = tmp_path / "runtime" / "content.json"
    output.parent.mkdir()
    output.write_text("previous-valid-package", encoding="utf-8")

    def fail_replace(source: Path, target: Path) -> None:
        del source, target
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(compiler_module, "_replace_file", fail_replace)

    with pytest.raises(ContentCompilationError) as captured:
        compile_content(source_root, output)

    assert captured.value.issues[0].code is ContentIssueCode.OUTPUT_WRITE_ERROR
    assert output.read_text(encoding="utf-8") == "previous-valid-package"
    assert list(output.parent.glob("*.tmp")) == []


@pytest.mark.parametrize("command", ["validate", "compile"])
def test_cli_provides_cross_platform_validate_and_compile_entries(
    tmp_path: Path,
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_root = tmp_path / "documents"
    _write_document(source_root, "entry.md", _document())
    output = tmp_path / "content.json"
    arguments = [command, "--source", str(source_root)]
    if command == "compile":
        arguments.extend(("--output", str(output)))

    result = main(arguments)

    captured = capsys.readouterr()
    assert result == 0
    assert "1 content entries" in captured.out
    assert captured.err == ""
    assert output.exists() is (command == "compile")


def test_cli_reports_structured_validation_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_root = tmp_path / "documents"
    invalid = _write_document(source_root, "invalid.md", "invalid")

    result = main(["validate", "--source", str(source_root)])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert str(invalid) in captured.err
    assert ContentIssueCode.MISSING_FRONTMATTER.value in captured.err


def test_missing_source_directory_is_structured(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    error = _assert_single_issue(missing, ContentIssueCode.SOURCE_DIRECTORY_NOT_FOUND)

    assert error.issues[0].source == missing


def test_serialization_is_independent_of_input_entry_order(tmp_path: Path) -> None:
    source_root = tmp_path / "documents"
    _write_document(source_root, "a.md", _document(content_id="document.alpha"))
    _write_document(source_root, "z.md", _document(content_id="document.zulu"))
    package = validate_content(source_root)
    reverse_package = type(package)(
        format=package.format,
        schema_version=package.schema_version,
        entries=tuple(reversed(package.entries)),
    )

    serializers: tuple[Callable[[], str], ...] = (
        lambda: serialize_content_package(package),
        lambda: serialize_content_package(reverse_package),
    )
    assert serializers[0]() == serializers[1]()

"""Isolation checks for the authoring compiler and existing runtime layers."""

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).parents[2]
SOURCE_ROOT = BACKEND_ROOT / "src" / "buxianxian"
CONTENT_ROOT = SOURCE_ROOT / "infrastructure" / "content"
PROTECTED_ROOTS = (
    SOURCE_ROOT / "domain",
    SOURCE_ROOT / "application",
)
PROTECTED_FILES = (
    SOURCE_ROOT / "infrastructure" / "save_repository.py",
    SOURCE_ROOT / "api" / "app.py",
)


def _imports_in(source_file: Path) -> set[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    imports: set[str] = set()
    for node in ast.walk(tree):
        match node:
            case ast.Import(names=names):
                imports.update(alias.name for alias in names)
            case ast.ImportFrom(module=module) if module is not None:
                imports.add(module)
            case _:
                continue
    return imports


def test_content_compiler_does_not_import_domain_application_api_or_save_modules() -> None:
    forbidden = (
        "buxianxian.domain",
        "buxianxian.application",
        "buxianxian.api",
        "buxianxian.infrastructure.save_repository",
    )
    for source_file in CONTENT_ROOT.glob("*.py"):
        for imported_module in _imports_in(source_file):
            assert not imported_module.startswith(forbidden), (
                f"{source_file.name} imports protected runtime module {imported_module}"
            )


def test_existing_runtime_layers_do_not_import_the_content_compiler() -> None:
    protected_sources = [
        *(source for root in PROTECTED_ROOTS for source in root.glob("*.py")),
        *PROTECTED_FILES,
    ]
    for source_file in protected_sources:
        assert all(
            not imported_module.startswith("buxianxian.infrastructure.content")
            for imported_module in _imports_in(source_file)
        ), f"{source_file} imports the authoring compiler"

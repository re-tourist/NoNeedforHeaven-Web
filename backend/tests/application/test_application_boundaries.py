"""Static dependency-boundary tests for the application layer."""

import ast
import sys
from pathlib import Path

APPLICATION_ROOT = Path(__file__).parents[2] / "src" / "buxianxian" / "application"


def _imports_in(source_file: Path) -> set[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        match node:
            case ast.Import(names=names):
                imported_modules.update(alias.name for alias in names)
            case ast.ImportFrom(module=module) if module is not None:
                imported_modules.add(module)
            case _:
                continue

    return imported_modules


def test_application_imports_only_standard_library_application_and_domain() -> None:
    for source_file in APPLICATION_ROOT.glob("*.py"):
        for imported_module in _imports_in(source_file):
            root_module = imported_module.partition(".")[0]
            allowed_project_import = imported_module.startswith(
                ("buxianxian.application", "buxianxian.domain")
            )
            assert root_module in sys.stdlib_module_names or allowed_project_import, (
                f"{source_file.name} imports forbidden dependency {imported_module}"
            )


def test_application_has_no_transport_or_frontend_dependency() -> None:
    forbidden_roots = frozenset({"fastapi", "httpx", "pydantic", "starlette"})
    for source_file in APPLICATION_ROOT.glob("*.py"):
        imported_roots = {
            imported_module.partition(".")[0] for imported_module in _imports_in(source_file)
        }
        assert imported_roots.isdisjoint(forbidden_roots)

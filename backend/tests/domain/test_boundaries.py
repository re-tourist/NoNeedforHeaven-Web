"""Static import-boundary checks for the standard-library-only domain package."""

import ast
import sys
from pathlib import Path

DOMAIN_ROOT = Path(__file__).parents[2] / "src" / "buxianxian" / "domain"
FILESYSTEM_MODULES = frozenset({"os", "pathlib", "shutil", "sqlite3", "tempfile"})


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


def test_domain_imports_only_standard_library_and_domain_modules() -> None:
    for source_file in DOMAIN_ROOT.glob("*.py"):
        for imported_module in _imports_in(source_file):
            root_module = imported_module.partition(".")[0]
            assert root_module in sys.stdlib_module_names or imported_module.startswith(
                "buxianxian.domain"
            ), f"{source_file.name} imports non-domain dependency {imported_module}"


def test_domain_does_not_import_filesystem_modules() -> None:
    for source_file in DOMAIN_ROOT.glob("*.py"):
        imported_roots = {
            imported_module.partition(".")[0] for imported_module in _imports_in(source_file)
        }
        assert imported_roots.isdisjoint(FILESYSTEM_MODULES), (
            f"{source_file.name} imports a filesystem module"
        )

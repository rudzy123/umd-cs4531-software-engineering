"""Import rules that keep the layers from collapsing into one package."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "task_api"


def test_domain_does_not_import_outer_layers() -> None:
    forbidden = (
        "task_api.application",
        "task_api.infrastructure",
        "task_api.api",
        "fastapi",
        "sqlalchemy",
        "pydantic",
    )
    assert _violations(ROOT / "domain", forbidden) == []


def test_application_depends_only_on_the_domain() -> None:
    forbidden = ("task_api.infrastructure", "task_api.api", "fastapi", "sqlalchemy", "pydantic")
    assert _violations(ROOT / "application", forbidden) == []


def test_routes_do_not_import_infrastructure() -> None:
    forbidden = ("task_api.infrastructure", "sqlalchemy")
    violations: list[str] = []
    for path in (ROOT / "api").rglob("*.py"):
        if path.name == "dependencies.py":
            continue
        violations.extend(_violations(path, forbidden))
    assert violations == []


def test_composition_root_wires_the_sqlite_adapter() -> None:
    modules = _imported(ROOT / "api" / "dependencies.py")
    assert "task_api.infrastructure.repositories" in modules
    assert "task_api.infrastructure.database" in modules


def _violations(path: Path, forbidden: tuple[str, ...]) -> list[str]:
    files = [path] if path.is_file() else sorted(path.rglob("*.py"))
    found: list[str] = []
    for file in files:
        for module in _imported(file):
            if _matches(module, forbidden):
                found.append(f"{file.relative_to(ROOT)} imports {module}")
    return found


def _imported(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _matches(module: str, forbidden: tuple[str, ...]) -> bool:
    return any(module == item or module.startswith(f"{item}.") for item in forbidden)

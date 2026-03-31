import tomllib
from pathlib import Path


def test_pyproject_declares_console_scripts_and_mcp_dependency() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml should exist for package distribution"

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data["project"]
    scripts = project["scripts"]
    dependencies = project["dependencies"]

    assert project["name"] == "codescan"
    assert scripts["codescan"] == "codescan.__main__:main"
    assert scripts["codescan-mcp"] == "codescan.mcp_server:main"
    assert any(dependency.startswith("mcp") for dependency in dependencies)

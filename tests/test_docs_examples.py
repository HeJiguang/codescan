from pathlib import Path


def test_codex_docs_and_assets_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = repo_root / "README.md"
    codex_doc = repo_root / "docs" / "codex.md"
    codex_asset = repo_root / "docs" / "assets" / "codex-workflow.svg"

    assert codex_doc.exists(), "Codex usage guide should exist"
    assert codex_asset.exists(), "Codex workflow asset should exist"

    readme_text = readme.read_text(encoding="utf-8")
    assert "[Use With Codex](docs/codex.md)" in readme_text
    assert "codex-workflow.svg" in codex_doc.read_text(encoding="utf-8")

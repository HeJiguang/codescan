import json
from pathlib import Path


def test_sample_output_assets_exist_and_are_well_formed() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_app = repo_root / "examples" / "demo-vulnerable-app" / "app.py"
    fixture_template = repo_root / "examples" / "demo-vulnerable-app" / "templates" / "profile.html"
    sample_result = repo_root / "examples" / "sample-mcp-result.json"
    example_doc = repo_root / "docs" / "example-output.md"
    preview_asset = repo_root / "docs" / "assets" / "sample-findings.svg"

    assert fixture_app.exists(), "Example vulnerable app should exist"
    assert fixture_template.exists(), "Example vulnerable template should exist"
    assert sample_result.exists(), "Sample MCP result should exist"
    assert example_doc.exists(), "Example output guide should exist"
    assert preview_asset.exists(), "Example preview asset should exist"

    data = json.loads(sample_result.read_text(encoding="utf-8"))
    assert data["scan_type"] == "directory"
    assert data["scan_model"] == "demo-model"
    assert data["total_issues"] >= 3
    assert "issues_by_severity" in data
    assert data["issues"][0]["title"]
    assert data["issues"][0]["location"]

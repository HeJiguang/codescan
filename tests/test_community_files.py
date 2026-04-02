from pathlib import Path


def test_readme_highlights_adoption_and_contribution_paths() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "## Who This Is For" in readme
    assert "## Try It In 5 Minutes" in readme
    assert "## Get Involved" in readme
    assert "docs/CONTRIBUTING.md" in readme
    assert "docs/good-first-issues.md" in readme
    assert "good first issues" in readme.lower()


def test_bilingual_readme_entrypoints_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme_en = (repo_root / "README.md").read_text(encoding="utf-8")
    readme_zh_path = repo_root / "README.zh-CN.md"
    docs_index = (repo_root / "docs" / "README.md").read_text(encoding="utf-8")

    assert readme_zh_path.exists(), "Chinese README should exist at the repository root"

    readme_zh = readme_zh_path.read_text(encoding="utf-8")

    assert "[简体中文](README.zh-CN.md)" in readme_en
    assert "[English](README.md)" in readme_zh
    assert "Project README (Simplified Chinese)" in docs_index


def test_issue_templates_and_pr_template_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    bug_report = repo_root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
    feature_request = repo_root / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml"
    config = repo_root / ".github" / "ISSUE_TEMPLATE" / "config.yml"
    pr_template = repo_root / ".github" / "pull_request_template.md"

    assert bug_report.exists(), "Bug report template should exist"
    assert feature_request.exists(), "Feature request template should exist"
    assert config.exists(), "Issue template config should exist"
    assert pr_template.exists(), "PR template should exist"


def test_contributing_doc_is_modernized_for_current_repo() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    contributing = (repo_root / "docs" / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "pip install -e .[dev]" in contributing
    assert "python -m pytest tests -q" in contributing
    assert "python -m compileall codescan" in contributing
    assert "good first contribution" in contributing.lower()


def test_user_facing_docs_avoid_local_asset_paths_and_overly_meta_copy() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    codex_doc = (repo_root / "docs" / "codex.md").read_text(encoding="utf-8")
    example_doc = (repo_root / "docs" / "example-output.md").read_text(encoding="utf-8")

    assert "/D:/Project/CodeScan" not in codex_doc
    assert "/D:/Project/CodeScan" not in example_doc
    assert "(assets/codex-workflow.svg)" in codex_doc
    assert "(assets/sample-findings.svg)" in example_doc

    assert "The next growth comes from contributors." not in readme
    assert "That path is short on purpose." not in readme


def test_security_support_and_good_first_issue_docs_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    security = repo_root / "SECURITY.md"
    support = repo_root / "SUPPORT.md"
    good_first_issues = repo_root / "docs" / "good-first-issues.md"
    community = repo_root / "docs" / "community.md"

    assert security.exists(), "Security policy should exist"
    assert support.exists(), "Support guide should exist"
    assert good_first_issues.exists(), "Good first issues guide should exist"
    assert community.exists(), "Community guide should exist"

    security_text = security.read_text(encoding="utf-8")
    support_text = support.read_text(encoding="utf-8")
    issues_text = good_first_issues.read_text(encoding="utf-8")
    community_text = community.read_text(encoding="utf-8")

    assert "Reporting a Vulnerability" in security_text
    assert "Questions And Setup Help" in support_text
    assert "good first issue" in issues_text.lower()
    assert "High-Value Feedback" in community_text

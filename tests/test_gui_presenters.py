from codescan.scanner import ScanResult, VulnerabilityIssue


def build_issue(
    **overrides,
) -> VulnerabilityIssue:
    data = {
        "title": "Hardcoded Secret",
        "severity": "high",
        "file_path": "src/demo.py",
        "line_number": 12,
        "description": "A hardcoded secret was found.",
        "recommendation": "Move the secret into environment configuration.",
        "confidence": "high",
        "cwe_id": "CWE-798",
    }
    data.update(overrides)
    return VulnerabilityIssue(**data)


def test_issue_title_prefers_title_then_description() -> None:
    from codescan.gui_presenters import issue_title

    assert issue_title(build_issue()) == "Hardcoded Secret"
    assert issue_title(build_issue(title="")) == "A hardcoded secret was found."
    assert issue_title(build_issue(title="", description="")) == "未命名问题"


def test_vulnerability_type_counts_group_long_tail() -> None:
    from codescan.gui_presenters import vulnerability_type_counts

    issues = [build_issue(cwe_id=f"CWE-{100+i}", title=f"Issue {i}", description=f"Desc {i}") for i in range(9)]

    counts = vulnerability_type_counts(issues)

    assert len(counts) == 8
    assert "其他" in counts
    assert counts["其他"] == 2


def test_issue_details_markdown_includes_core_fields() -> None:
    from codescan.gui_presenters import issue_details_markdown

    content = issue_details_markdown(
        build_issue(owasp_category="A02", vulnerability_type="secrets")
    )

    assert "# Hardcoded Secret" in content
    assert "**严重程度:** 高危" in content
    assert "**OWASP 类别:** A02" in content
    assert "**漏洞类型:** secrets" in content
    assert "## 修复建议" in content


def test_scan_summary_markdown_renders_issue_counts() -> None:
    from codescan.gui_presenters import scan_summary_markdown

    result = ScanResult(
        scan_id="scan-1",
        scan_path="demo",
        scan_type="directory",
        scan_model="deepseek-chat",
        timestamp=0.0,
        issues=[
            build_issue(severity="critical"),
            build_issue(severity="low", title="Minor"),
        ],
    )

    content = scan_summary_markdown(result)

    assert "# 扫描结果摘要" in content
    assert "- **总计**: 2个问题" in content
    assert "**严重**" in content
    assert "**低危**" in content

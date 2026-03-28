import json

from codescan.report import HTMLReportGenerator, JSONReportGenerator, TextReportGenerator
from codescan.scanner import ScanResult, VulnerabilityIssue


def build_scan_result() -> ScanResult:
    return ScanResult(
        scan_id="scan-1",
        scan_path="demo.py",
        scan_type="file",
        scan_model="deepseek-chat",
        timestamp=0.0,
        issues=[
            VulnerabilityIssue(
                title="Hardcoded Secret",
                severity="high",
                file_path="demo.py",
                line_number=12,
                description="A hardcoded secret was found.",
                recommendation="Move the secret to environment configuration.",
                confidence="high",
            )
        ],
        stats={"total_files": 1, "total_lines_of_code": 20},
        project_info={"project_type": "python-file"},
    )


def test_json_report_uses_real_scan_result_fields() -> None:
    content = JSONReportGenerator().generate_report(build_scan_result())
    data = json.loads(content)

    assert data["scan_model"] == "deepseek-chat"
    assert data["issues"][0]["title"] == "Hardcoded Secret"
    assert data["issues"][0]["line_number"] == 12


def test_text_report_renders_issue_title_and_recommendation() -> None:
    content = TextReportGenerator().generate_report(build_scan_result())

    assert "Hardcoded Secret" in content
    assert "A hardcoded secret was found." in content
    assert "Move the secret to environment configuration." in content


def test_html_report_prefers_issue_title_for_heading() -> None:
    content = HTMLReportGenerator().generate_report(build_scan_result())

    assert "Hardcoded Secret" in content
    assert "<h3>Hardcoded Secret</h3>" in content

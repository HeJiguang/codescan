from codescan.scanner import ScanResult, VulnerabilityIssue


def test_vulnerability_issue_supports_gui_metadata_fields() -> None:
    issue = VulnerabilityIssue(
        title="SQL Injection",
        severity="high",
        file_path="demo.py",
        description="Dynamic SQL execution detected.",
        owasp_category="A03:2021 Injection",
        vulnerability_type="injection",
    )

    assert issue.owasp_category == "A03:2021 Injection"
    assert issue.vulnerability_type == "injection"


def test_scan_result_json_round_trip_preserves_optional_issue_metadata() -> None:
    result = ScanResult(
        scan_id="scan-compat",
        scan_path="demo.py",
        scan_type="file",
        scan_model="deepseek-chat",
        timestamp=0.0,
        issues=[
            VulnerabilityIssue(
                title="SQL Injection",
                severity="high",
                file_path="demo.py",
                description="Dynamic SQL execution detected.",
                owasp_category="A03:2021 Injection",
                vulnerability_type="injection",
            )
        ],
    )

    round_tripped = ScanResult.from_json(result.to_json())

    assert round_tripped.issues[0].owasp_category == "A03:2021 Injection"
    assert round_tripped.issues[0].vulnerability_type == "injection"

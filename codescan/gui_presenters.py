"""Pure presentation helpers extracted from the GUI module."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable

from .scanner import ScanResult, VulnerabilityIssue


SEVERITY_LABELS = {
    "critical": "严重",
    "high": "高危",
    "medium": "中危",
    "low": "低危",
    "info": "提示",
}


def severity_label(severity: str) -> str:
    """Return the localized label for a severity level."""

    return SEVERITY_LABELS.get(severity, severity)


def issue_title(issue: VulnerabilityIssue) -> str:
    """Choose the best display title for an issue."""

    return issue.title or issue.description or "未命名问题"


def vulnerability_type_counts(
    issues: Iterable[VulnerabilityIssue], max_categories: int = 8
) -> Dict[str, int]:
    """Build chart-friendly vulnerability type counts."""

    type_counts: Dict[str, int] = {}

    for issue in issues:
        if issue.cwe_id:
            type_name = f"CWE-{issue.cwe_id}"
        else:
            desc = issue.description.strip()
            type_name = desc[:15] + "..." if len(desc) > 15 else desc or issue_title(issue)

        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    if len(type_counts) > max_categories:
        sorted_types = sorted(type_counts.items(), key=lambda item: item[1], reverse=True)
        top_types = sorted_types[: max_categories - 1]
        other_count = sum(count for _, count in sorted_types[max_categories - 1 :])
        type_counts = {name: count for name, count in top_types}
        if other_count > 0:
            type_counts["其他"] = other_count

    return type_counts


def issue_details_markdown(issue: VulnerabilityIssue) -> str:
    """Render a single issue to markdown."""

    details = f"# {issue_title(issue)}\n\n"

    if issue.severity:
        details += f"**严重程度:** {severity_label(issue.severity)}\n\n"

    if issue.location:
        details += f"**位置:** `{issue.location}`\n\n"

    if issue.description:
        details += f"## 问题描述\n{issue.description}\n\n"

    if issue.cwe_id:
        cwe_value = issue.cwe_id.replace("CWE-", "")
        details += (
            f"**CWE ID:** [{issue.cwe_id}]"
            f"(https://cwe.mitre.org/data/definitions/{cwe_value}.html)\n\n"
        )

    if issue.owasp_category:
        details += f"**OWASP 类别:** {issue.owasp_category}\n\n"

    if issue.vulnerability_type:
        details += f"**漏洞类型:** {issue.vulnerability_type}\n\n"

    if issue.code_snippet:
        details += f"\n## 代码片段\n```\n{issue.code_snippet}\n```\n"

    if issue.recommendation:
        details += f"\n## 修复建议\n{issue.recommendation}\n"

    return details


def scan_summary_markdown(result: ScanResult) -> str:
    """Render the top-level scan summary."""

    severity_counts = result.issues_by_severity
    formatted_time = datetime.fromtimestamp(result.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 扫描结果摘要

- **扫描路径**: {result.scan_path}
- **扫描类型**: {result.scan_type}
- **扫描时间**: {formatted_time}
- **扫描ID**: {result.scan_id}

## 问题统计
- **总计**: {result.total_issues}个问题
- **严重**: {severity_counts.get('critical', 0)}
- **高危**: {severity_counts.get('high', 0)}
- **中危**: {severity_counts.get('medium', 0)}
- **低危**: {severity_counts.get('low', 0)}
- **提示**: {severity_counts.get('info', 0)}
"""

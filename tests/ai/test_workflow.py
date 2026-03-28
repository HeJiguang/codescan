from codescan.ai.schemas import AIFileIssue, AIFileScanResult
from codescan.ai.workflow import build_file_analysis_workflow


def test_file_analysis_workflow_merges_rule_and_llm_findings() -> None:
    def fake_file_analyzer(state: dict) -> AIFileScanResult:
        return AIFileScanResult(
            summary="LLM analysis complete",
            issues=[
                AIFileIssue(
                    title="LLM Issue",
                    severity="medium",
                    description="Found by the LLM layer.",
                    recommendation="Use safer construction.",
                    confidence="medium",
                    line_number=18,
                )
            ],
        )

    graph = build_file_analysis_workflow(fake_file_analyzer)
    result = graph.invoke(
        {
            "file_path": "demo.py",
            "language": "python",
            "content": "print('demo')",
            "rule_issues": [
                AIFileIssue(
                    title="Rule Issue",
                    severity="high",
                    description="Matched by regex rule.",
                    recommendation="Remove the unsafe pattern.",
                    confidence="high",
                    line_number=8,
                )
            ],
        }
    )

    issues = result["issues"]

    assert len(issues) == 2
    assert {issue.title for issue in issues} == {"Rule Issue", "LLM Issue"}
    assert result["summary"] == "LLM analysis complete"

"""LangGraph workflows used by the AI runtime."""

from __future__ import annotations

from typing import Callable, Dict, List

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .schemas import AIFileIssue, AIFileScanResult


class FileAnalysisState(TypedDict, total=False):
    file_path: str
    language: str
    content: str
    rule_issues: List[AIFileIssue]
    llm_result: AIFileScanResult
    issues: List[AIFileIssue]
    summary: str


def build_file_analysis_workflow(
    file_analyzer: Callable[[Dict], AIFileScanResult]
):
    """Build the file-analysis workflow."""

    def rule_scan(state: FileAnalysisState) -> Dict[str, List[AIFileIssue]]:
        return {"rule_issues": list(state.get("rule_issues", []))}

    def llm_scan(state: FileAnalysisState) -> Dict[str, AIFileScanResult]:
        return {"llm_result": file_analyzer(state)}

    def merge_and_finalize(state: FileAnalysisState) -> Dict[str, object]:
        llm_result = state.get("llm_result", AIFileScanResult())
        merged: List[AIFileIssue] = []
        seen = set()
        for issue in list(state.get("rule_issues", [])) + list(llm_result.issues):
            issue_key = (issue.title, issue.line_number, issue.description)
            if issue_key in seen:
                continue
            seen.add(issue_key)
            merged.append(issue)
        return {
            "issues": merged,
            "summary": llm_result.summary,
        }

    graph = StateGraph(FileAnalysisState)
    graph.add_node("rule_scan", rule_scan)
    graph.add_node("llm_scan", llm_scan)
    graph.add_node("merge_and_finalize", merge_and_finalize)
    graph.add_edge(START, "rule_scan")
    graph.add_edge("rule_scan", "llm_scan")
    graph.add_edge("llm_scan", "merge_and_finalize")
    graph.add_edge("merge_and_finalize", END)
    return graph.compile()

"""High-level AI service used by scanner orchestration."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from .chains import (
    build_file_analysis_chain,
    build_file_summary_chain,
    build_project_summary_chain,
)
from .prompts import (
    build_file_analysis_prompt,
    build_file_summary_prompt,
    build_project_summary_prompt,
)
from .providers import create_chat_model
from .workflow import build_file_analysis_workflow


class AIAnalysisService:
    """Facade over providers, chains, and workflows."""

    def __init__(self, model_config: Dict[str, Any]):
        self.chat_model = create_chat_model(model_config)
        self.file_analysis_chain = build_file_analysis_chain(self.chat_model)
        self.project_summary_chain = build_project_summary_chain(self.chat_model)
        self.file_summary_chain = build_file_summary_chain(self.chat_model)
        self.file_workflow = build_file_analysis_workflow(self._analyze_file_state)

    def _analyze_file_state(self, state: Dict[str, Any]):
        return self.file_analysis_chain.invoke(
            {
                "prompt": build_file_analysis_prompt(
                    file_path=state["file_path"],
                    language=state["language"],
                    content=state["content"],
                )
            }
        )

    def analyze_file(
        self,
        file_path: str,
        language: str,
        content: str,
        rule_issues: Iterable,
    ) -> Dict[str, Any]:
        """Analyze a file with the workflow."""

        return self.file_workflow.invoke(
            {
                "file_path": file_path,
                "language": language,
                "content": content,
                "rule_issues": list(rule_issues),
            }
        )

    def summarize_project(self, dir_path: str, stats: Dict[str, Any], structure: Dict[str, Any]):
        """Generate a structured project summary."""

        return self.project_summary_chain.invoke(
            {
                "prompt": build_project_summary_prompt(
                    dir_path=dir_path,
                    stats=stats,
                    structure=structure,
                )
            }
        )

    def summarize_file(self, file_path: str, language: str, stats: Dict[str, Any], content: str):
        """Generate a structured file summary."""

        return self.file_summary_chain.invoke(
            {
                "prompt": build_file_summary_prompt(
                    file_path=file_path,
                    language=language,
                    stats=stats,
                    content=content,
                )
            }
        )

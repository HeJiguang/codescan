"""Structured AI output schemas."""

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


Severity = Literal["critical", "high", "medium", "low", "info"]
Confidence = Literal["high", "medium", "low"]


class AIFileIssue(BaseModel):
    """Normalized issue produced by AI workflows."""

    title: str = Field(default="未命名问题")
    severity: Severity = Field(default="medium")
    description: str = Field(default="")
    recommendation: str = Field(default="")
    confidence: Confidence = Field(default="medium")
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None


class AIFileScanResult(BaseModel):
    """Structured output for file-level security analysis."""

    summary: str = Field(default="")
    issues: List[AIFileIssue] = Field(default_factory=list)


class AIProjectSummary(BaseModel):
    """Structured output for project-level summary generation."""

    project_type: str = Field(default="未能自动分析")
    main_functionality: str = Field(default="未能自动分析")
    components: List[str] = Field(default_factory=list)
    architecture: str = Field(default="未能自动分析")
    use_cases: List[str] = Field(default_factory=list)


class AIFileSummary(BaseModel):
    """Structured output for file-level explanation."""

    file_purpose: str = Field(default="未能自动分析")
    main_components: List[str] = Field(default_factory=list)
    possible_role: str = Field(default="未能自动分析")
    code_quality: Any = Field(default="未能自动分析")
    suggested_improvements: List[str] = Field(default_factory=list)

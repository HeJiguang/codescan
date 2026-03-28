"""Prompt builders for structured AI analysis."""

from __future__ import annotations

import json
from typing import Any, Dict


def build_file_analysis_prompt(file_path: str, language: str, content: str) -> str:
    """Build the prompt for file-level security analysis."""

    return f"""
你是一个严格的软件安全分析器。请分析下面的 {language} 文件，找出高价值的安全问题、实现缺陷和明显的不良实践。

文件路径: {file_path}

要求:
1. 只输出有明确依据的问题
2. 如果没有问题，返回空问题列表
3. 问题标题要简洁
4. 建议要可执行

代码:
```
{content}
```
""".strip()


def build_project_summary_prompt(dir_path: str, stats: Dict[str, Any], structure: Dict[str, Any]) -> str:
    """Build the prompt for project summary."""

    return f"""
请根据下面的项目信息，总结项目类型、主要功能、主要组件、架构和使用场景。

项目路径: {dir_path}
统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}
目录结构: {json.dumps(structure, ensure_ascii=False, indent=2)}
""".strip()


def build_file_summary_prompt(file_path: str, language: str, stats: Dict[str, Any], content: str) -> str:
    """Build the prompt for file summary."""

    return f"""
请根据以下文件信息总结它的主要用途、主要组件、在项目中的角色、代码质量和改进建议。

文件路径: {file_path}
语言: {language}
统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}

代码片段:
```
{content[:3000]}
```
""".strip()

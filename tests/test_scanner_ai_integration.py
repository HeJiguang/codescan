from pathlib import Path

from codescan.ai.schemas import AIFileIssue, AIFileSummary, AIProjectSummary
from codescan.scanner import CodeScanner


class FakeAIService:
    def analyze_file(self, file_path, language, content, rule_issues):
        merged = list(rule_issues)
        merged.append(
            AIFileIssue(
                title="Injected Issue",
                severity="medium",
                description=f"AI analyzed {Path(file_path).name}",
                recommendation="Review the injected issue.",
                confidence="high",
                line_number=3,
            )
        )
        return {"summary": "analysis complete", "issues": merged}

    def summarize_project(self, dir_path, stats, structure):
        return AIProjectSummary(
            project_type="Demo Project",
            main_functionality="Directory summary",
            components=["scanner", "report"],
            architecture="layered",
            use_cases=["testing"],
        )

    def summarize_file(self, file_path, language, stats, content):
        return AIFileSummary(
            file_purpose="Fake file summary",
            main_components=["main"],
            possible_role="demo module",
            code_quality="good",
            suggested_improvements=["add more tests"],
        )


def test_scan_file_uses_injected_ai_service(tmp_path) -> None:
    file_path = tmp_path / "demo.py"
    file_path.write_text("print('demo')\n", encoding="utf-8")

    scanner = CodeScanner(model_name="default", ai_service=FakeAIService())
    result = scanner.scan_file(str(file_path))

    assert result.scan_model == "default"
    assert result.total_issues == 1
    assert result.issues[0].title == "Injected Issue"
    assert result.project_info["main_functionality"] == "Fake file summary"


def test_scan_directory_uses_ai_service_for_project_summary(tmp_path) -> None:
    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('b')\n", encoding="utf-8")

    scanner = CodeScanner(model_name="default", ai_service=FakeAIService())
    result = scanner.scan_directory(str(tmp_path), max_workers=1)

    assert result.scan_model == "default"
    assert result.stats["total_files"] == 2
    assert result.project_info["project_type"] == "Demo Project"
    assert result.total_issues == 2

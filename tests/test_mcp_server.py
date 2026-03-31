import asyncio
from pathlib import Path

import git
from mcp.shared.memory import create_connected_server_and_client_session

from codescan.scanner import ScanResult, VulnerabilityIssue


class FakeScanner:
    def __init__(self, model_name: str, calls: list[tuple[str, object]]) -> None:
        self.model_name = model_name
        self.calls = calls

    def scan_file(self, file_path: str) -> ScanResult:
        self.calls.append(("scan_file", file_path))
        return ScanResult(
            scan_id="file_scan",
            scan_path=file_path,
            scan_type="file",
            scan_model=self.model_name,
            timestamp=1.0,
            issues=[
                VulnerabilityIssue(
                    title="Hardcoded secret",
                    severity="high",
                    file_path=file_path,
                    line_number=2,
                    description="Detected by fake scanner",
                    recommendation="Remove the secret.",
                    confidence="high",
                )
            ],
            stats={"total_files": 1},
            project_info={"file_purpose": "test fixture"},
        )

    def scan_directory(self, dir_path: str, max_workers: int = 5, progress_callback=None) -> ScanResult:
        self.calls.append(("scan_directory", (dir_path, max_workers)))
        return ScanResult(
            scan_id="dir_scan",
            scan_path=dir_path,
            scan_type="directory",
            scan_model=self.model_name,
            timestamp=2.0,
            issues=[],
            stats={"total_files": 3, "languages": {"python": 3}},
            project_info={"project_type": "fixture"},
        )

    def create_merge_scan_result(
        self,
        base_path: str,
        scan_id: str,
        issues: list[VulnerabilityIssue],
        diff_files: list[str],
    ) -> ScanResult:
        self.calls.append(("create_merge_scan_result", (base_path, tuple(diff_files))))
        return ScanResult(
            scan_id=scan_id,
            scan_path=base_path,
            scan_type="git-merge",
            scan_model=self.model_name,
            timestamp=3.0,
            issues=issues,
            stats={"total_files": len(diff_files)},
            project_info={"merge_info": {"diff_files": diff_files}},
        )


def build_fake_scanner_factory(calls: list[tuple[str, object]]):
    def factory(model_name: str) -> FakeScanner:
        calls.append(("factory", model_name))
        return FakeScanner(model_name=model_name, calls=calls)

    return factory


def test_mcp_server_exposes_scan_tools_and_returns_structured_results(tmp_path: Path) -> None:
    from codescan.mcp_server import build_mcp_server

    file_path = tmp_path / "demo.py"
    file_path.write_text("print('demo')\n", encoding="utf-8")

    calls: list[tuple[str, object]] = []
    server = build_mcp_server(scanner_factory=build_fake_scanner_factory(calls))

    async def exercise_server() -> None:
        async with create_connected_server_and_client_session(server) as session:
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}

            assert {
                "scan_file",
                "scan_directory",
                "scan_git_diff",
                "scan_github_repo",
            }.issubset(tool_names)

            file_result = await session.call_tool(
                "scan_file",
                {"path": str(file_path), "model": "unit-test"},
            )
            directory_result = await session.call_tool(
                "scan_directory",
                {"path": str(tmp_path), "model": "unit-test", "max_workers": 2},
            )

            assert file_result.isError is False
            assert file_result.structuredContent["scan_type"] == "file"
            assert file_result.structuredContent["total_issues"] == 1
            assert file_result.structuredContent["issues"][0]["title"] == "Hardcoded secret"
            assert file_result.structuredContent["issues"][0]["location"].endswith(":2")

            assert directory_result.isError is False
            assert directory_result.structuredContent["scan_type"] == "directory"
            assert directory_result.structuredContent["stats"]["total_files"] == 3
            assert directory_result.structuredContent["project_info"]["project_type"] == "fixture"

    asyncio.run(exercise_server())

    assert ("factory", "unit-test") in calls
    assert ("scan_file", str(file_path.resolve())) in calls
    assert ("scan_directory", (str(tmp_path.resolve()), 2)) in calls


def test_mcp_git_diff_tool_scans_changed_files(tmp_path: Path) -> None:
    from codescan.mcp_server import build_mcp_server

    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    repo = git.Repo.init(repo_path)
    changed_file = repo_path / "app.py"
    changed_file.write_text("print('base')\n", encoding="utf-8")
    repo.index.add(["app.py"])
    repo.index.commit("initial commit")
    repo.git.branch("-M", "main")
    repo.git.checkout("-b", "feature/mcp")

    changed_file.write_text("print('changed')\n", encoding="utf-8")
    repo.index.add(["app.py"])
    repo.index.commit("update app")

    calls: list[tuple[str, object]] = []
    server = build_mcp_server(scanner_factory=build_fake_scanner_factory(calls))

    async def exercise_server() -> None:
        async with create_connected_server_and_client_session(server) as session:
            result = await session.call_tool(
                "scan_git_diff",
                {
                    "base_branch": "main",
                    "repo_path": str(repo_path),
                    "model": "git-model",
                },
            )

            assert result.isError is False
            assert result.structuredContent["scan_type"] == "git-merge"
            assert result.structuredContent["project_info"]["merge_info"]["diff_files"] == ["app.py"]
            assert result.structuredContent["issues"][0]["file_path"] == str(changed_file.resolve())

    asyncio.run(exercise_server())

    assert ("factory", "git-model") in calls
    assert ("scan_file", str(changed_file.resolve())) in calls

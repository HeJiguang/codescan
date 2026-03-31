"""MCP server entry points for CodeScan."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import git
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from .scanner import CodeScanner, ScanResult, VulnerabilityIssue


ScannerFactory = Callable[[str], CodeScanner]


class MCPIssue(BaseModel):
    title: str = ""
    severity: str
    file_path: str
    location: str
    line_number: int | None = None
    code_snippet: str | None = None
    description: str = ""
    recommendation: str = ""
    cwe_id: str | None = None
    owasp_category: str | None = None
    vulnerability_type: str | None = None
    confidence: str = "medium"

    @classmethod
    def from_issue(cls, issue: VulnerabilityIssue) -> "MCPIssue":
        return cls(
            title=issue.title,
            severity=issue.severity,
            file_path=issue.file_path,
            location=issue.location,
            line_number=issue.line_number,
            code_snippet=issue.code_snippet,
            description=issue.description,
            recommendation=issue.recommendation,
            cwe_id=issue.cwe_id,
            owasp_category=issue.owasp_category,
            vulnerability_type=issue.vulnerability_type,
            confidence=issue.confidence,
        )


class MCPScanResult(BaseModel):
    scan_id: str
    scan_path: str
    scan_type: str
    timestamp: float
    scan_model: str
    total_issues: int
    issues_by_severity: dict[str, int]
    issues: list[MCPIssue]
    stats: dict[str, Any] = Field(default_factory=dict)
    project_info: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_scan_result(cls, result: ScanResult) -> "MCPScanResult":
        return cls(
            scan_id=result.scan_id,
            scan_path=result.scan_path,
            scan_type=result.scan_type,
            timestamp=result.timestamp,
            scan_model=result.scan_model,
            total_issues=result.total_issues,
            issues_by_severity=result.issues_by_severity,
            issues=[MCPIssue.from_issue(issue) for issue in result.issues],
            stats=result.stats,
            project_info=result.project_info,
        )


def _default_scanner_factory(model_name: str) -> CodeScanner:
    return CodeScanner(model_name=model_name)


def _resolve_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _require_file(path: str) -> str:
    resolved = _resolve_path(path)
    if not Path(resolved).is_file():
        raise ValueError(f"File does not exist: {resolved}")
    return resolved


def _require_directory(path: str) -> str:
    resolved = _resolve_path(path)
    if not Path(resolved).is_dir():
        raise ValueError(f"Directory does not exist: {resolved}")
    return resolved


def _build_git_diff_result(
    repo_path: str,
    base_branch: str,
    model_name: str,
    scanner_factory: ScannerFactory,
) -> MCPScanResult:
    resolved_repo_path = _require_directory(repo_path)
    repo = git.Repo(resolved_repo_path, search_parent_directories=True)
    repo_root = Path(repo.working_tree_dir or resolved_repo_path).resolve()

    try:
        repo.commit(base_branch)
    except (git.BadName, ValueError) as exc:
        raise ValueError(f"Unknown Git ref: {base_branch}") from exc

    diff_files = [line for line in repo.git.diff(f"{base_branch}..HEAD", name_only=True).splitlines() if line]

    scanner = scanner_factory(model_name)
    issues: list[VulnerabilityIssue] = []
    for relative_path in diff_files:
        file_path = (repo_root / relative_path).resolve()
        if file_path.is_file():
            file_result = scanner.scan_file(str(file_path))
            issues.extend(file_result.issues)

    scan_result = scanner.create_merge_scan_result(
        str(repo_root),
        f"git_diff_{int(time.time())}",
        issues,
        diff_files,
    )
    return MCPScanResult.from_scan_result(scan_result)


def build_mcp_server(
    scanner_factory: ScannerFactory | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "INFO",
) -> FastMCP:
    factory = scanner_factory or _default_scanner_factory
    server = FastMCP(
        name="CodeScan",
        instructions=(
            "Use CodeScan to inspect source code for security issues. "
            "Prefer scan_file for targeted review, scan_directory for repository sweeps, "
            "and scan_git_diff for branch-to-branch review."
        ),
        website_url="https://github.com/HeJiguang/codescan",
        host=host,
        port=port,
        log_level=log_level,
    )

    @server.tool(
        name="scan_file",
        description="Scan a single source file and return a structured security report.",
        structured_output=True,
    )
    def scan_file(path: str, model: str = "default") -> MCPScanResult:
        scanner = factory(model)
        scan_result = scanner.scan_file(_require_file(path))
        return MCPScanResult.from_scan_result(scan_result)

    @server.tool(
        name="scan_directory",
        description="Scan a directory and return a structured repository security report.",
        structured_output=True,
    )
    def scan_directory(path: str, model: str = "default", max_workers: int = 4) -> MCPScanResult:
        scanner = factory(model)
        scan_result = scanner.scan_directory(_require_directory(path), max_workers=max_workers)
        return MCPScanResult.from_scan_result(scan_result)

    @server.tool(
        name="scan_git_diff",
        description="Scan files changed between the current HEAD and a base Git branch or ref.",
        structured_output=True,
    )
    def scan_git_diff(base_branch: str, repo_path: str = ".", model: str = "default") -> MCPScanResult:
        return _build_git_diff_result(repo_path, base_branch, model, factory)

    @server.tool(
        name="scan_github_repo",
        description="Clone a Git repository URL to a temporary directory and scan it.",
        structured_output=True,
    )
    def scan_github_repo(repo_url: str, model: str = "default", max_workers: int = 4) -> MCPScanResult:
        temp_dir = tempfile.mkdtemp(prefix="codescan_mcp_")
        try:
            git.Repo.clone_from(repo_url, temp_dir)
            scanner = factory(model)
            scan_result = scanner.scan_directory(temp_dir, max_workers=max_workers)
            return MCPScanResult.from_scan_result(scan_result)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return server


def run_server(
    transport: str = "stdio",
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "INFO",
) -> int:
    server = build_mcp_server(host=host, port=port, log_level=log_level)
    server.run(transport=transport)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the CodeScan MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to expose.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transports.")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transports.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Server log level.",
    )
    return parser


def run_server_from_namespace(args: argparse.Namespace) -> int:
    return run_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return run_server_from_namespace(args)


if __name__ == "__main__":
    raise SystemExit(main())

# CodeScan MCP Guide

## Overview

CodeScan can run as an MCP server so coding agents can call the scanner directly instead of shelling out to the CLI and parsing report files afterward.

The MCP layer is intentionally thin:

- It reuses `codescan.scanner.CodeScanner` as the execution engine.
- It returns structured Pydantic output for stable tool schemas.
- It focuses on agent-native workflows: file review, repository review, Git diff review, and remote-repo scanning.

## Start The Server

After installing the package:

```bash
pip install -e .
codescan-mcp --transport stdio
```

You can also use the package entry point:

```bash
python -m codescan mcp --transport stdio
```

For debugging over HTTP transports:

```bash
codescan-mcp --transport streamable-http --host 127.0.0.1 --port 8000
codescan-mcp --transport sse --host 127.0.0.1 --port 8000
```

## Available Tools

### `scan_file`

Use this for a focused security review of one file.

Arguments:

- `path`
- `model`

### `scan_directory`

Use this for repository-wide sweeps.

Arguments:

- `path`
- `model`
- `max_workers`

### `scan_git_diff`

Use this for branch review or pre-merge inspection.

Arguments:

- `base_branch`
- `repo_path`
- `model`

### `scan_github_repo`

Use this when the repository is not checked out locally and the client wants to scan directly from a Git URL.

Arguments:

- `repo_url`
- `model`
- `max_workers`

## Output Shape

Every tool returns a structured scan payload with these top-level fields:

- `scan_id`
- `scan_path`
- `scan_type`
- `timestamp`
- `scan_model`
- `total_issues`
- `issues_by_severity`
- `issues`
- `stats`
- `project_info`

Each issue includes:

- `title`
- `severity`
- `file_path`
- `location`
- `line_number`
- `description`
- `recommendation`
- `cwe_id`
- `owasp_category`
- `vulnerability_type`
- `confidence`

## Why MCP Matters Here

The CLI is still useful for people. The MCP layer exists for agents.

Without MCP, an agent usually has to:

1. Run a shell command.
2. Wait for a report file.
3. Parse JSON or HTML.
4. Reconstruct the result into its own workflow.

With MCP, the agent can call a tool and immediately receive structured output it can reason over.

## Can MCP Make Agent-Written Code Safer?

Yes, but only if it is used as part of a disciplined review loop.

The practical upside is straightforward:

- agents can call a structured tool instead of shelling out and parsing files
- the lowest-friction review path becomes `scan_file` or `scan_git_diff`
- findings come back with severity, location, remediation, and metadata the agent can act on

The highest-value usage pattern is usually:

1. write or modify code
2. run `scan_git_diff` before merge, or `scan_file` on a risky file
3. inspect `critical` and `high` issues manually before accepting them as real
4. patch the code and re-run the scan

What MCP does not magically fix:

- false positives from lightweight pattern matching
- missing deeper data-flow analysis
- the need for human judgment on exploitability and business context
- the absence of an enforced blocking workflow

So the honest claim is: MCP can make secure review easier and more consistent for coding agents. It cannot, by itself, guarantee secure output.

## Verification

Use these checks before publishing MCP changes:

```bash
python -m pytest tests -q
python -m compileall codescan
python -m codescan --help
python -m codescan mcp --help
```

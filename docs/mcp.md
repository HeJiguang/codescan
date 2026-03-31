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

## Verification

Use these checks before publishing MCP changes:

```bash
python -m pytest tests -q
python -m compileall codescan
python -m codescan --help
python -m codescan mcp --help
```

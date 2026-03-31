# Use CodeScan With Codex

## Overview

CodeScan is now best used from Codex in a two-layer setup:

1. `codescan-review` skill for workflow guidance
2. `codescan-mcp` for real callable scan tools

That combination gives Codex both judgment scaffolding and structured security data.

## Quick Setup

### 1. Install the package

```bash
pip install -e .
```

### 2. Start the MCP server

```bash
codescan-mcp --transport stdio
```

If you prefer the package entry point:

```bash
python -m codescan mcp --transport stdio
```

### 3. Install the skill

```bash
install-skill-from-github.py --repo HeJiguang/codescan --path skills/codescan-review
```

Restart Codex after installing the skill.

## Recommended Flow

### Pre-merge review

Use this when you already have a local checkout and want the highest-value default:

```text
Use $codescan-review to inspect the current branch against main and report only actionable security findings.
```

This should naturally bias Codex toward `scan_git_diff`.

### Suspicious file review

Use this when one file looks risky:

```text
Use $codescan-review to inspect this file for security issues. Focus on input validation, secrets, command execution, and trust boundaries.
```

This should bias Codex toward `scan_file`.

### Repository intake

Use this when you want a broad first pass:

```text
Use $codescan-review to scan this repository and summarize the top security risks, ordered by severity.
```

This should bias Codex toward `scan_directory`.

### Remote repository review

Use this when the repository is only available as a Git URL:

```text
Use $codescan-review to scan this GitHub repository and tell me the highest-confidence security findings first.
```

This should bias Codex toward `scan_github_repo`.

## What Good Output Looks Like

When CodeScan is used well from Codex, the response should usually have:

- findings first
- severity ordering
- file and line references
- concrete remediation
- scope limits when the scan was partial

It should not collapse into generic secure-coding advice unless the scan found little and the user explicitly wants broader recommendations.

## Visual Workflow

![CodeScan with Codex workflow](/D:/Project/CodeScan/docs/assets/codex-workflow.svg)

## Why This Matters

Without the skill, Codex may know that CodeScan exists but still underuse it or choose the wrong scan scope.

Without MCP, Codex can still use the CLI, but it loses the benefit of structured tool output.

Together, they make CodeScan feel much closer to a native agent capability instead of an external script.

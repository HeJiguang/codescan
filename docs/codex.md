# Use CodeScan With Codex

## Overview

Recommended Codex setup:

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

Use this for branch review or pre-merge inspection.

### Detailed Branch Walkthrough

For a concrete walkthrough of a pre-merge scan, try a prompt like this:

**Prompt:**
> Use `scan_git_diff` to compare the current feature branch against `main`. Summarize any new security vulnerabilities introduced in this diff, focusing on high-severity issues like SQL injection or hardcoded secrets.

**What to expect in the response:**
1. **Tool Invocation:** Codex calls `scan_git_diff(base="main", head="HEAD")`.
2. **Analysis:** CodeScan identifies changed files, runs targeted rules and AI analysis on the diff.
3. **Structured Findings:**
   - **Vulnerability:** Hardcoded API Key
   - **File:** `src/services/auth.py:42`
   - **Severity:** High
   - **Description:** A Cloudflare API token was found hardcoded in the connection string.
   - **Remediation:** Move the token to an environment variable or secret manager.
4. **Conclusion:** A summary of whether the branch is "Safe to Merge" from a security perspective.

### Suspicious file review

Use this when one file looks risky:

```text
Use $codescan-review to inspect this file for security issues. Focus on input validation, secrets, command execution, and trust boundaries.
```

Use this for focused review of one risky file.

### Repository intake

Use this when you want a broad first pass:

```text
Use $codescan-review to scan this repository and summarize the top security risks, ordered by severity.
```

Use this for repository intake or broad sweeps.

### Remote repository review

Use this when the repository is only available as a Git URL:

```text
Use $codescan-review to scan this GitHub repository and tell me the highest-confidence security findings first.
```

Use this when the repository is only available by URL.

## What Good Output Looks Like

When CodeScan is used well from Codex, the response should usually have:

- findings first
- severity ordering
- file and line references
- concrete remediation
- scope limits when the scan was partial

It should not collapse into generic secure-coding advice unless the scan found little and the user explicitly wants broader recommendations.

## Visual Workflow

![CodeScan with Codex workflow](assets/codex-workflow.svg)

## Why This Setup Works

Without the skill, Codex may know that CodeScan exists but still underuse it or choose the wrong scan scope.

Without MCP, Codex can still use the CLI, but it loses the benefit of structured tool output.

Together, they give Codex workflow guidance plus structured scan output.

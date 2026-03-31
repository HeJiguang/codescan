---
name: codescan-review
description: Use when reviewing source code for security issues and CodeScan MCP tools or CLI are available, especially for pre-merge diff review, repository intake, suspicious auth or input-handling code, or when a user explicitly asks for a CodeScan-based security scan.
---

# CodeScan Review

## Overview

Use CodeScan as a focused security reviewer. Prefer MCP tools when they are available. Fall back to the CLI only when MCP is unavailable.

Prioritize exploitable findings over style issues or generic code smell commentary.

## When To Use

- The user asks for a security review or vulnerability scan
- The user wants a pre-merge or branch-diff review
- The code under review handles auth, secrets, input validation, file access, command execution, SQL, HTML rendering, network callbacks, or crypto
- The user wants CodeScan specifically, not just a generic security opinion

Do not use this skill for general refactoring, style cleanup, or performance review unless the user explicitly widens scope.

## Tool Selection

- Use `scan_file` for a focused review of one file
- Use `scan_directory` for repository or module sweeps
- Use `scan_git_diff` for active-branch or pre-merge review
- Use `scan_github_repo` when the target repo is only available as a Git URL

Prefer the smallest scope that answers the user's request.

## Workflow

1. Pick the narrowest scan that matches the request.
2. Run CodeScan through MCP first.
3. Read the structured findings and separate strong signals from weaker suspicions.
4. Manually inspect any `critical` or `high` finding before presenting it as real.
5. Respond with findings first:
   - severity
   - file path and line
   - why it is risky
   - concrete remediation
6. If no credible finding remains, say that explicitly and mention any residual blind spots.

## Fallback

If MCP tools are unavailable but `codescan` is installed locally, use the CLI:

```bash
python -m codescan file <path>
python -m codescan dir <path>
python -m codescan git-merge <base-branch>
```

If downstream parsing matters, prefer JSON output instead of HTML.

## Output Standard

- List findings before summaries
- Order by severity
- Use file and line references whenever possible
- Distinguish confirmed issues from lower-confidence suspicions
- Keep remediation concrete and code-facing
- Mention scan scope limits if the scan was partial

## Notes

- CodeScan is strongest when used as a security triage tool, not as the sole source of truth
- For active code review, `scan_git_diff` is usually the highest-value default
- For one suspicious file, `scan_file` is usually better than a full repository sweep

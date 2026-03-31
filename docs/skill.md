# CodeScan Skill Guide

## Overview

CodeScan now ships an installable skill inside this repository:

- `skills/codescan-review`

The skill does not replace the MCP server. It complements it.

- The MCP server exposes structured scan tools.
- The skill tells Codex when to use those tools and how to present the findings.

## Install From GitHub

Use Codex's GitHub skill installer with this repo path:

```bash
install-skill-from-github.py --repo HeJiguang/codescan --path skills/codescan-review
```

You can also install from the direct GitHub URL:

```bash
install-skill-from-github.py --url https://github.com/HeJiguang/codescan/tree/main/skills/codescan-review
```

After installing the skill, restart Codex so it picks up the new skill.

## What The Skill Does

The skill teaches Codex to:

- prefer CodeScan MCP tools when available
- choose the right scan scope for the task
- treat `scan_git_diff` as the default for active branch review
- report findings first, ordered by severity
- separate strong findings from weaker suspicions

## Recommended Setup

For the best experience, use both:

1. Install the `codescan-review` skill
2. Run the CodeScan MCP server with `codescan-mcp --transport stdio`

That gives Codex both:

- a reusable workflow
- a real callable security-scanning tool surface

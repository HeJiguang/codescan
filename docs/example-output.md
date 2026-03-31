# Example Output

## Overview

This repository now includes a tiny intentionally vulnerable fixture plus a representative structured scan result so visitors can understand what CodeScan produces without configuring a live model first.

## Fixture

The example target lives here:

- [`examples/demo-vulnerable-app/app.py`](../examples/demo-vulnerable-app/app.py)
- [`examples/demo-vulnerable-app/templates/profile.html`](../examples/demo-vulnerable-app/templates/profile.html)

It contains a few common security mistakes:

- command injection risk
- SQL injection risk
- unsafe HTML rendering
- hardcoded secret handling

## Structured Result

The representative MCP-style output is here:

- [`examples/sample-mcp-result.json`](../examples/sample-mcp-result.json)

This is the kind of shape Codex receives when CodeScan is used through MCP:

- `total_issues`
- `issues_by_severity`
- `issues`
- `stats`
- `project_info`

## Visual Preview

![Sample findings preview](/D:/Project/CodeScan/docs/assets/sample-findings.svg)

## Why This Helps

Open-source scanning tools lose a lot of GitHub visitors before installation because people cannot quickly tell:

- what the output looks like
- whether the findings are actionable
- whether the result is human-readable or machine-friendly

These example assets close that gap.

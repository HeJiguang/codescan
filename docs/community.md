# Community Guide

This page collects the highest-value ways to use, evaluate, and contribute to CodeScan.

## Best Starting Points

- Read the [Project README](../README.md)
- Inspect the [Example Output](example-output.md)
- Try the [MCP Guide](mcp.md) if you use coding agents
- Read [Use With Codex](codex.md) if you want the recommended Codex workflow

## High-Value Feedback

CodeScan benefits most from concrete feedback, not generic approval.

The most useful reports usually include:

- false positives with the exact file or snippet
- missed findings on a real repository or branch diff
- MCP or Codex workflow friction with exact steps
- installation or packaging blockers for first-time users
- comparisons against other tools on the same target

## Ways To Participate

### 1. Use it on real code

The fastest way to improve signal quality is to run CodeScan on real repositories, not only the demo fixture.

Particularly useful cases:

- branch diffs before merge
- auth, SQL, shell execution, file handling, or templating code
- repositories where structured output matters more than HTML reports

### 2. Open focused issues

Good issues for this project are usually narrow and testable.

Examples:

- one false positive class
- one missing vulnerability pattern
- one MCP ergonomics problem
- one onboarding blocker

### 3. Share workflow examples

Use GitHub Discussions to share:

- how you use CodeScan from Codex or another MCP client
- which prompt patterns worked well
- where the result shape helped or got in the way
- real before/after review examples

### 4. Contribute small PRs

The best first PRs usually fall into one of these buckets:

- docs and onboarding improvements
- tests around current behavior
- small rule quality improvements
- example asset or demo fixture improvements
- focused refactors in large modules

## What This Project Prioritizes

When trade-offs appear, CodeScan currently favors:

- review workflows over general-purpose chat behavior
- structured output over free-form explanation
- local usability over large hosted-platform assumptions
- tighter false-positive control over broader but noisier matching
- agent-native flows through MCP and skills

## Where To Go Next

- [Support](../SUPPORT.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Good First Issues](good-first-issues.md)
- [MCP Guide](mcp.md)

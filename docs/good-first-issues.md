# Good First Issues

This page exists to make outside contributions easier to start.

The fastest way to lose potential contributors is to say “good first issues” without showing what that actually means in this repository.

## Good First Issue Lanes

### 1. Documentation polish

Good if you want a low-risk first contribution.

Examples:

- improve setup wording in `README.md`
- add one more Codex prompt example to `docs/codex.md`
- improve explanation in `docs/example-output.md`

### 2. Example and preview assets

Good if you like product polish and developer tooling.

Examples:

- add another sample result asset
- improve the vulnerable demo fixture
- add a second output preview for a file scan

### 3. Tests around current behavior

Good if you want to understand the repo by tightening contracts.

Examples:

- add focused tests around `codescan/mcp_server.py`
- add tests around report rendering edge cases
- add tests for more skill metadata rules

### 4. Rule quality improvements

Good if you care about security signal quality.

Examples:

- tighten broad patterns that may cause obvious false positives
- add a targeted rule for a common vulnerability class
- improve severity mapping for a current rule

### 5. Refactor small slices of large files

Good if you want to make the codebase healthier without taking on a giant rewrite.

Examples:

- extract one more pure helper from `codescan/gui.py`
- split repeated formatting logic into a focused module
- reduce coupling in report helpers

## What Makes A Good First Issue Here

A good first issue in CodeScan usually has:

- a narrow scope
- a clear before/after outcome
- tests or docs to prove the change
- no requirement to redesign the full architecture

## If You Want To Open A PR Without Waiting

If you find a small improvement that obviously fits the current direction, you do not need to wait for a giant roadmap discussion.

The safest first PRs are:

- docs fixes
- onboarding improvements
- test additions
- small rule or example improvements

## Related Docs

- [Contributing Guide](CONTRIBUTING.md)
- [MCP Guide](mcp.md)
- [Skill Guide](skill.md)
- [Use With Codex](codex.md)

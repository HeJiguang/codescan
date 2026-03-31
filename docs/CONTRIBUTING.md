# Contributing to CodeScan

Thanks for considering a contribution to CodeScan.

This project is most valuable when contributors make it easier to:

- catch real security issues
- reduce false positives
- improve agent workflows through MCP and skills
- make onboarding and examples clearer for new users

## Good First Contribution Paths

If you want a good first contribution, start with one of these lanes:

- improve documentation, examples, and onboarding
- add or refine vulnerability rules
- improve test coverage around scanner, MCP, or report behavior
- break large files like `gui.py` into smaller units
- improve example outputs or Codex workflows

## Local Setup

```bash
git clone https://github.com/HeJiguang/codescan.git
cd codescan
python -m venv .venv
```

Activate the environment:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install the package plus development extras:

```bash
pip install -e .[dev]
```

## Local Verification

Before opening a pull request, run:

```bash
python -m pytest tests -q
python -m compileall codescan
python -m codescan --help
python -m codescan mcp --help
```

If you change skills, also validate the skill folder:

```bash
python C:\Users\sinwt\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\codescan-review
```

## What To Include In A Pull Request

Please keep PRs tight and explicit.

Good PRs usually include:

- one clear change theme
- tests or documentation updates when behavior changes
- before/after rationale for user-facing changes
- concrete verification notes

## Areas Where Contributions Are Especially Useful

### 1. Scanner quality

- Semgrep-backed checks
- AST-aware rules
- severity calibration
- false-positive reduction

### 2. Agent workflows

- better MCP ergonomics
- richer tool schemas
- stronger Codex skill prompts
- more example prompts and scenarios

### 3. Product polish

- better example reports
- clearer screenshots or preview assets
- onboarding for first-time users
- clearer homepage storytelling

### 4. Engineering health

- splitting large modules
- more targeted tests
- packaging improvements
- better CI checks

## Reporting Bugs

Please use the GitHub bug template and include:

- what you tried
- what happened
- what you expected
- your Python version and operating system
- relevant logs or screenshots

If the problem is model-related, include the provider and model name.

## Suggesting Features

Please use the GitHub feature request template and explain:

- who benefits
- what workflow it improves
- whether it is CLI, MCP, Skill, GUI, or report related
- what a good first version would look like

## Rule Contributions

If you are contributing new rules:

- explain the vulnerability class
- include a minimal positive example
- avoid overly broad patterns that will obviously spam false positives
- update examples or tests when possible

## Community Expectations

Please keep discussions technical, respectful, and concrete. See [Code of Conduct](CODE_OF_CONDUCT.md).

# CodeScan Docs Index

This directory collects the main technical and contribution docs for CodeScan.

## Read First

1. [Project README](../README.md)
2. [Technical Doc](technical_doc.md)
3. [MCP Guide](mcp.md)
4. [Skill Guide](skill.md)
5. [Use With Codex](codex.md)
6. [Rules Guide](rules_guide.md)
7. [Contributing](CONTRIBUTING.md)

## User-Facing Docs

- [Project README](../README.md)
- [MCP Guide](mcp.md)
- [Skill Guide](skill.md)
- [Use With Codex](codex.md)
- [Rules Guide](rules_guide.md)

## Developer Docs

- [Technical Doc](technical_doc.md)
- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## Notes

The current mainline architecture is centered on:

- `LangChain + LangGraph` for the AI runtime
- structured scan results for reports and clients
- MCP exposure for agent-native code review workflows
- an installable skill layer for Codex-native review guidance
- explicit Codex-facing setup docs and example prompts

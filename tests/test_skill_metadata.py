from pathlib import Path

import yaml


def test_codescan_review_skill_metadata_is_valid() -> None:
    skill_dir = Path(__file__).resolve().parents[1] / "skills" / "codescan-review"
    skill_file = skill_dir / "SKILL.md"
    openai_yaml = skill_dir / "agents" / "openai.yaml"
    icon_file = skill_dir / "assets" / "codescan-review.svg"

    assert skill_file.exists(), "CodeScan review skill should exist"
    assert openai_yaml.exists(), "Skill UI metadata should exist"
    assert icon_file.exists(), "Skill icon should exist"

    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---\n"), "Skill should start with YAML frontmatter"

    frontmatter_text = content.split("---", 2)[1]
    frontmatter = yaml.safe_load(frontmatter_text)
    assert frontmatter["name"] == "codescan-review"
    assert frontmatter["description"].startswith("Use when")

    openai_metadata = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
    interface = openai_metadata["interface"]
    assert interface["display_name"] == "CodeScan Review"
    assert "$codescan-review" in interface["default_prompt"]

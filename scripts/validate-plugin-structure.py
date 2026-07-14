from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SKILLS = [
    "backend-router",
    "backend-flow",
    "delivery-lifecycle",
    "backend-retro",
    "browser-qa",
    "skill-curator-tbs",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    require(match is not None, "SKILL.md must start with YAML frontmatter")
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def assert_plugin_json() -> None:
    plugin_json = ROOT / ".codex-plugin" / "plugin.json"
    require(plugin_json.exists(), ".codex-plugin/plugin.json is missing")
    data = json.loads(read_text(plugin_json))
    require(data.get("name") == "backend-dev", "plugin name must be backend-dev")
    require(data.get("skills") == "./skills/", "plugin skills path must be ./skills/")


def assert_skills() -> None:
    for skill in REQUIRED_SKILLS:
        skill_file = ROOT / "skills" / skill / "SKILL.md"
        require(skill_file.exists(), f"missing skill: {skill}")
        frontmatter = parse_frontmatter(read_text(skill_file))
        require(frontmatter.get("name") == skill, f"{skill} frontmatter name mismatch")
        require(frontmatter.get("description"), f"{skill} description is required")


def assert_browser_qa_docs() -> None:
    text = read_text(ROOT / "skills" / "browser-qa" / "SKILL.md")
    for phrase in ["networkidle", "console", "network", "channel", "chrome"]:
        require(phrase in text, f"browser-qa must mention {phrase}")
    flow = read_text(ROOT / "skills" / "backend-flow" / "SKILL.md")
    lifecycle = read_text(ROOT / "skills" / "delivery-lifecycle" / "SKILL.md")
    require("backend-dev:browser-qa" in flow, "backend-flow must call backend-dev:browser-qa")
    require("backend-dev:browser-qa" in lifecycle, "delivery-lifecycle must call backend-dev:browser-qa")


def assert_sync_docs() -> None:
    readme = read_text(ROOT / "README.md")
    for phrase in ["git clone", "git pull", "marketplace.json", "CODEX_HOME", ".codex/plugins/cache"]:
        require(phrase in readme, f"README must mention {phrase}")


def assert_curator_help() -> None:
    script = ROOT / "skills" / "skill-curator-tbs" / "scripts" / "skill_inventory_manual.py"
    require(script.exists(), "skill-curator-tbs inventory script is missing")
    result = subprocess.run([sys.executable, str(script), "--help"], text=True, capture_output=True)
    require(result.returncode == 0, result.stderr or result.stdout)


def main() -> None:
    assert_plugin_json()
    assert_skills()
    assert_browser_qa_docs()
    assert_sync_docs()
    assert_curator_help()
    print("plugin structure validation passed")


if __name__ == "__main__":
    main()

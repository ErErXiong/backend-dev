from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


def user_home() -> Path:
    return Path.home()


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", user_home() / ".codex")).expanduser()


def default_manual_path() -> Path:
    env_path = os.environ.get("SKILL_CURATOR_MANUAL")
    if env_path:
        return Path(env_path).expanduser()
    return user_home() / "Desktop" / "codex-skill-usage-manual.md"


def default_local_plugins() -> Path:
    return Path(os.environ.get("SKILL_CURATOR_LOCAL_PLUGINS", user_home() / "plugins")).expanduser()


def default_marketplace() -> Path:
    return Path(
        os.environ.get(
            "SKILL_CURATOR_MARKETPLACE",
            user_home() / ".agents" / "plugins" / "marketplace.json",
        )
    ).expanduser()


@dataclass
class Skill:
    name: str
    source: str
    path: str
    description: str
    enabled: bool = False


@dataclass
class Paths:
    codex_home: Path
    global_skills: Path
    plugin_cache: Path
    config_toml: Path
    local_plugins: Path
    marketplace: Path


def paths_from_args(args: argparse.Namespace) -> Paths:
    codex_home = args.codex_home.expanduser()
    return Paths(
        codex_home=codex_home,
        global_skills=args.global_skills.expanduser() if args.global_skills else codex_home / "skills",
        plugin_cache=args.plugin_cache.expanduser() if args.plugin_cache else codex_home / "plugins" / "cache",
        config_toml=args.config.expanduser() if args.config else codex_home / "config.toml",
        local_plugins=args.local_plugins.expanduser(),
        marketplace=args.marketplace.expanduser(),
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def parse_description(skill_file: Path) -> tuple[str, str]:
    text = read_text(skill_file)
    name = skill_file.parent.name
    description = ""
    match = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if not match:
        return name, description
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"')
        if line.startswith("description:"):
            description = line.split(":", 1)[1].strip().strip('"')
    return name, description


def enabled_plugins(config_toml: Path) -> list[str]:
    if not config_toml.exists():
        return []
    text = read_text(config_toml)
    enabled: list[str] = []
    current: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r'\[plugins\."([^"]+)"\]', stripped)
        if match:
            current = match.group(1)
            continue
        if current and stripped == "enabled = true":
            enabled.append(current)
            current = None
        elif current and stripped.startswith("["):
            current = None
    return enabled


def scan_global_skills(global_skills: Path) -> list[Skill]:
    skills: list[Skill] = []
    if not global_skills.exists():
        return skills
    for skill_file in sorted(global_skills.glob("*/SKILL.md")):
        if ".system" in skill_file.parts:
            continue
        name, description = parse_description(skill_file)
        skills.append(
            Skill(
                name=name,
                source="global",
                path=str(skill_file.parent),
                description=description,
                enabled=True,
            )
        )
    return skills


def scan_plugin_skills(plugin_cache: Path, enabled: set[str]) -> list[Skill]:
    skills: list[Skill] = []
    if not plugin_cache.exists():
        return skills
    for skill_file in sorted(plugin_cache.glob("*/*/*/skills/*/SKILL.md")):
        parts = skill_file.parts
        try:
            cache_index = parts.index("cache")
            marketplace = parts[cache_index + 1]
            plugin = parts[cache_index + 2]
            version = parts[cache_index + 3]
        except (ValueError, IndexError):
            marketplace = "unknown"
            plugin = "unknown"
            version = "unknown"
        plugin_id = f"{plugin}@{marketplace}"
        name, description = parse_description(skill_file)
        skills.append(
            Skill(
                name=f"{plugin}:{name}",
                source=f"plugin:{plugin_id}/{version}",
                path=str(skill_file.parent),
                description=description,
                enabled=plugin_id in enabled,
            )
        )
    return skills


def local_plugin_names(local_plugins: Path) -> list[str]:
    if not local_plugins.exists():
        return []
    return sorted(path.name for path in local_plugins.iterdir() if path.is_dir())


def marketplace_plugins(marketplace: Path) -> list[str]:
    if not marketplace.exists():
        return []
    try:
        data = json.loads(read_text(marketplace))
    except json.JSONDecodeError:
        return []
    return [plugin.get("name", "") for plugin in data.get("plugins", []) if plugin.get("name")]


def summarize_inventory(paths: Paths) -> dict[str, object]:
    enabled = enabled_plugins(paths.config_toml)
    enabled_set = set(enabled)
    global_skills = scan_global_skills(paths.global_skills)
    plugin_skills = scan_plugin_skills(paths.plugin_cache, enabled_set)
    enabled_plugin_skills = [skill for skill in plugin_skills if skill.enabled]
    cache_only_skills = [skill for skill in plugin_skills if not skill.enabled]
    global_names = {skill.name for skill in global_skills}
    enabled_short_names = {skill.name.split(":", 1)[1] for skill in enabled_plugin_skills if ":" in skill.name}
    duplicate_names = sorted(global_names & enabled_short_names)
    return {
        "paths": {key: str(value) for key, value in asdict(paths).items()},
        "global_skills": [asdict(skill) for skill in global_skills],
        "enabled_plugin_skills": [asdict(skill) for skill in enabled_plugin_skills],
        "cache_only_plugin_skills": [asdict(skill) for skill in cache_only_skills],
        "enabled_plugins": enabled,
        "local_plugins": local_plugin_names(paths.local_plugins),
        "marketplace_plugins": marketplace_plugins(paths.marketplace),
        "duplicate_skill_names": duplicate_names,
    }


def bullet(items: list[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- `{item}`" for item in items)


def table(rows: list[tuple[str, str, str]]) -> str:
    lines = ["| 场景 | 首选入口 | 中文用法 |", "| --- | --- | --- |"]
    for scene, entry, note in rows:
        lines.append(f"| {scene} | `{entry}` | {note} |")
    return "\n".join(lines)


def main_skill_groups() -> list[tuple[str, list[tuple[str, str, str]]]]:
    return [
        (
            "需求与讨论",
            [
                ("创意探索/需求发散", "brainstorming", "用于功能、组件、行为改动前的早期探索。"),
                ("简单需求细化", "grill-me", "没有代码库上下文时，用连续追问把想法变成可执行方向。"),
                ("代码库内需求澄清", "grill-with-docs", "有代码库时使用，边追问边沉淀 CONTEXT、术语和 ADR。"),
                ("整理成规格", "to-spec", "已经讨论得差不多时，把上下文整理成 spec/PRD。"),
                ("拆成任务", "to-tickets", "把规格拆成可逐步实现、可验证的 ticket。"),
            ],
        ),
        (
            "开发交付",
            [
                ("后端日常入口", "backend-dev:backend-router", "默认从这里开始；自动判断短流程、完整流程或专项技能。"),
                ("小范围后端改动", "backend-dev:backend-flow", "需求清楚的接口、校验、配置、导入导出或小 Bug。"),
                ("新模块/高风险交付", "backend-dev:delivery-lifecycle", "适合跨服务、权限、数据库迁移、发布准备等完整生命周期。"),
                ("禅道或指定网站 BUG", "zentao-bug-fix", "给 BUG ID、链接或问题描述；推送前必须再确认。"),
                ("普通 BUG 修复", "bugfix-workflow", "先复现或收集证据，再做最小修复。"),
            ],
        ),
        (
            "测试与验证",
            [
                ("测试驱动开发", "test-driven-development", "需要 test-first、先复现再修、补集成测试时使用。"),
                ("浏览器页面验收", "backend-dev:browser-qa", "新增功能或修复 Bug 后，有页面路径时验证真实请求和刷新结果。"),
                ("Playwright 自动化", "playwright", "需要直接编写或运行浏览器自动化脚本时使用。"),
                ("完成前验证", "verification-before-completion", "结束前核对 fresh 验证输出，避免未验证即完成。"),
            ],
        ),
        (
            "评审与复盘",
            [
                ("代码评审", "code-review / receiving-code-review", "按固定基点检查风险、回归和需求实现度。"),
                ("经验复盘", "backend-dev:backend-retro", "实质性后端改动完成后，提炼可确认经验候选。"),
                ("发布分支收尾", "finishing-a-development-branch", "提交、推送、PR 或分支收尾前使用。"),
            ],
        ),
        (
            "技能与插件维护",
            [
                ("整理 Codex 技能", "backend-dev:skill-curator-tbs", "盘点、简化入口、发现重复或缓存残留、更新本手册。"),
                ("发现技能/插件", "find-skills", "想找更好的技能、插件或工作流时使用。"),
                ("编写新技能", "writing-skills", "把稳定流程沉淀成可复用技能时使用。"),
            ],
        ),
    ]


def quick_selection() -> str:
    sections: list[str] = []
    for title, rows in main_skill_groups():
        sections.append(f"### {title}\n\n{table(rows)}")
    return "\n\n".join(sections)


def generate_manual(inv: dict[str, object]) -> str:
    global_skills = [skill["name"] for skill in inv["global_skills"]]
    enabled = list(inv["enabled_plugins"])
    local_plugins = list(inv["local_plugins"])
    marketplace = list(inv["marketplace_plugins"])
    enabled_skill_names = [skill["name"] for skill in inv["enabled_plugin_skills"]]
    cache_only_sources = sorted({skill["source"] for skill in inv["cache_only_plugin_skills"]})
    duplicates = list(inv["duplicate_skill_names"])
    paths = inv["paths"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    duplicate_note = "当前未发现全局技能与已启用插件技能同名重复。" if not duplicates else (
        "发现这些全局/已启用插件同名技能，后续建议优先保留插件前缀入口：\n\n" + bullet(duplicates)
    )

    return f"""# Codex 技能使用手册

更新时间：{now}

## 使用原则

技能名和插件名保持英文，不强行翻译 `SKILL.md`。这样插件升级、同步和触发规则更稳定。

中文体验放在本手册里解决：你只需要按中文场景选择英文入口即可。

插件命名偏好：显示名可使用 `@tbs`，机器名可使用 `-tbs` 后缀。

## 快速选择

{quick_selection()}

## 推荐工作流

### 1. BUG 修复

普通输入问题：

1. 先用 `backend-dev:backend-router`。
2. 如果原因很清楚，走 `backend-dev:backend-flow`。
3. 如果定位困难，转 `matt-skills-zh-tbs:diagnosing-bugs`。
4. 修完后按风险选择本地编译、测试或 `matt-skills-zh-tbs:code-review`。

禅道或指定网站：

1. 用 `zentao-bug-fix`。
2. 让 Codex 读取票据、截图、复现路径和本地代码。
3. 本地验证后再提交。
4. 推送远程前必须再次确认。

### 2. 开发新功能

需求已经明确：

1. 后端小改动用 `backend-dev:backend-router`。
2. 小范围接口、校验、导入导出用 `backend-dev:backend-flow`。
3. 新模块、跨服务、权限、数据库迁移用 `backend-dev:delivery-lifecycle`。

需求还不明确：

1. 先用 `brainstorming` 做早期发散。
2. 有代码库上下文时，用 `matt-skills-zh-tbs:grill-with-docs`。
3. 没有代码库上下文时，用 `matt-skills-zh-tbs:grill-me`。
4. 明确后用 `matt-skills-zh-tbs:to-spec`。
5. 需要拆任务时用 `matt-skills-zh-tbs:to-tickets`。
6. 落地实现时用 `matt-skills-zh-tbs:implement` 或 `backend-dev:backend-router`。

### 3. 自动化测试

1. 新功能要先写测试：`matt-skills-zh-tbs:tdd`。
2. BUG 要先复现再修：`matt-skills-zh-tbs:tdd` 或 `matt-skills-zh-tbs:diagnosing-bugs`。
3. 后端常规验证仍由 `backend-dev:backend-router` 判断是否需要编译、单测或集成验证。

### 4. 优化技能库和流程

1. 用 `skill-curator-tbs` 盘点当前状态。
2. 先给优化选项，不直接删除、禁用或覆盖。
3. 优先简化“使用入口”，不翻译或改写第三方技能本体。
4. 每次安装新插件后，更新本手册里的场景路由和重复/互补关系。

### 5. 发现更好的技能或插件

1. 用 `matt-skills-zh-tbs:find-skills`。
2. 新插件安装后，回到 `skill-curator-tbs` 做一次盘点。
3. 判断它和既有插件是否重复、互补或冲突。

## 当前状态

### 扫描路径

- Codex 目录：`{paths["codex_home"]}`
- 全局技能：`{paths["global_skills"]}`
- 插件缓存：`{paths["plugin_cache"]}`
- 配置文件：`{paths["config_toml"]}`
- 本地插件源：`{paths["local_plugins"]}`
- Personal marketplace：`{paths["marketplace"]}`

### 全局技能

{bullet(global_skills)}

### 已启用插件

{bullet(enabled)}

### 已启用插件技能数量

- `{len(enabled_skill_names)}`

### 本地插件源

{bullet(local_plugins)}

### Personal Marketplace 插件

{bullet(marketplace)}

### 缓存中但未启用的插件技能来源

这些通常是旧版本、未启用插件或历史缓存。不要手动删除，除非后续明确确认。

{bullet(cache_only_sources)}

## 当前优化结论

{duplicate_note}

建议采用“英文技能本体 + 中文手册解释”的策略，不把第三方技能内容强行翻译。这样方便后续升级插件，也能避免中文乱码影响技能触发。

## 后续维护规则

1. 新装插件后，先运行 `skill-curator-tbs` 重新扫描。
2. 手册只解释“什么时候用哪个英文技能名”，不要复制大段英文描述。
3. 发现同类能力时，优先保留插件前缀入口，例如 `matt-skills-zh-tbs:code-review`。
4. 对缓存残留只记录，不自动删除。
5. 如果某个技能经常用，可以再考虑做一个 `work-router-tbs` 统一入口。
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan Codex skills/plugins and generate a Chinese usage manual.")
    parser.add_argument("--codex-home", type=Path, default=default_codex_home())
    parser.add_argument("--global-skills", type=Path, default=None)
    parser.add_argument("--plugin-cache", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--local-plugins", type=Path, default=default_local_plugins())
    parser.add_argument("--marketplace", type=Path, default=default_marketplace())
    parser.add_argument("--manual", type=Path, default=default_manual_path())
    parser.add_argument("--json", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    paths = paths_from_args(args)
    inv = summarize_inventory(paths)
    manual = generate_manual(inv)

    args.manual.parent.mkdir(parents=True, exist_ok=True)
    args.manual.write_text(manual, encoding="utf-8", newline="\n")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"manual={args.manual}")
    print(f"global_skills={len(inv['global_skills'])}")
    print(f"enabled_plugin_skills={len(inv['enabled_plugin_skills'])}")
    print(f"cache_only_plugin_skills={len(inv['cache_only_plugin_skills'])}")
    print(f"duplicates={len(inv['duplicate_skill_names'])}")


if __name__ == "__main__":
    main()

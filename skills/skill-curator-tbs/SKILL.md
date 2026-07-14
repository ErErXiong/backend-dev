---
name: skill-curator-tbs
description: 整理、优化和维护当前 Codex 技能与插件的工作流。作为 backend-dev 插件内入口时，用于多机器同步后的技能盘点、重复检查和中文手册更新。用于盘点已安装技能、清理重复技能、规划插件前缀和命名、选择适合工作的技能组合、安装插件后给出优化建议，或生成/更新中文技能使用手册。必须先扫描真实本机状态，再向用户提问确认优化选项，最后按用户选择更新手册。
---

# 技能整理 @tbs

整理当前 Codex 技能和插件，让技能列表更适合用户的实际工作方式，并维护一份中文技能使用手册。

## 核心原则

1. 先扫描真实状态，不凭记忆判断。
2. 先给用户选择，不擅自删除、禁用、移动或覆盖技能。
3. 技能名和插件名默认保持英文；中文体验放在使用手册里解释。
4. 优先保留插件前缀入口，减少全局散装技能带来的误触发。
5. 发现新插件时，必须结合已有插件给出重复、互补、冲突和使用入口建议。

## 默认路径

脚本会自动识别当前用户环境，不绑定某一台机器：

- Codex 目录：优先读 `CODEX_HOME`，否则使用 `~/.codex`。
- 手册路径：优先读 `SKILL_CURATOR_MANUAL`，否则固定生成到 `~/Desktop/codex-skill-usage-manual.md`；桌面目录不存在时由脚本创建。
- 本地插件源：优先读 `SKILL_CURATOR_LOCAL_PLUGINS`，否则使用 `~/plugins`。
- Personal marketplace：优先读 `SKILL_CURATOR_MARKETPLACE`，否则使用 `~/.agents/plugins/marketplace.json`。

需要覆盖默认值时，优先通过脚本参数传入，而不是修改脚本源码。

## 工作流

### 1. 扫描现状

运行脚本生成当前清单和中文手册：

```powershell
python "<this-skill>\scripts\skill_inventory_manual.py"
```

常用参数：

```powershell
python "<this-skill>\scripts\skill_inventory_manual.py" --manual "$env:USERPROFILE\Desktop\codex-skill-usage-manual.md" --json "$env:USERPROFILE\Desktop\skill-inventory-current.json"
python "<this-skill>\scripts\skill_inventory_manual.py" --codex-home "$env:CODEX_HOME"
```

如果当前环境无法写入目标手册路径，改为生成到当前 workspace 的 `outputs/`，并告诉用户目标路径需要由用户本机复制或重新执行。

### 2. 分类技能

把扫描结果分为：

- 全局技能：直接在 `CODEX_HOME/skills` 下的技能。
- 已启用插件技能：`config.toml` 中启用的插件提供的技能。
- 缓存残留：缓存中存在但未启用、旧版本或历史缓存的插件技能。
- 项目/专项技能：例如禅道、后端开发、文档、浏览器、GitHub、Supabase。

### 3. 发现问题

至少检查这些问题：

- 全局技能和已启用插件中是否存在同名技能。
- 插件缓存是否仍在，但 marketplace/config 已不再指向。
- 插件是否启用但没有明确使用入口。
- 新插件是否和已有插件能力重叠。
- 技能描述是否过宽，可能误触发。
- 是否缺少中文手册入口或 `agents/openai.yaml`。

### 4. 向用户提问

不要直接改结构。先给用户 2 到 5 个清晰选项，例如：

```markdown
我看到这些可优化点：

1. 保守整理：只更新中文手册，不删除任何技能。
2. 简化入口：把日常场景压缩成少数主入口，技能本体保持英文。
3. 插件分组：把同类散装技能收进一个 `*-tbs` 插件。
4. 缓存清理：列出未启用缓存路径，由你确认后再处理。

你想选哪一种？
```

用户选择前，不执行删除、禁用、移动或覆盖配置。

### 5. 执行优化

根据用户选择执行：

- 更新手册：覆盖用户确认的手册路径。
- 清理重复项：先列路径，再确认，再删除。
- 启用插件：优先使用 `codex plugin add <plugin>@<marketplace>`；如果 CLI 权限失败，给出用户本机可执行命令。
- 修改配置：只做最小变更，保留原配置。

### 6. 更新手册

手册必须覆盖以下内容：

- 快速选择表，放在手册前部，并按需求与讨论、开发交付、测试验证、评审复盘、技能维护等分组。
- 推荐组合流程。
- 当前状态。
- 后续插件安装后的维护规则。
- 当前保留清单。
- 待优化项和用户已选择的策略。

如果本次安装了新插件，手册里要新增：

- 新插件能力摘要。
- 与已有插件的关系。
- 推荐使用入口。
- 建议禁用或保留的旧入口。

## 输出格式

最终回复使用：

```markdown
已完成：
- ...

手册：
- <path>

建议：
- ...

未执行/需你确认：
- ...
```

如果只是盘点，不要声称已经优化；明确说“这是建议，尚未执行”。

## 插件内使用说明

本技能已迁入 `backend-dev` 插件。新机器优先使用 `backend-dev:skill-curator-tbs`，旧机器上的全局 `skill-curator-tbs` 可以保留；不要为了入口整洁自动删除全局版本。

跨机器同步时只依赖环境变量和脚本参数，不写死本机路径：

- `CODEX_HOME`：覆盖 Codex 主目录。
- `SKILL_CURATOR_MANUAL`：覆盖中文手册输出路径。
- `SKILL_CURATOR_LOCAL_PLUGINS`：覆盖本地插件源目录。
- `SKILL_CURATOR_MARKETPLACE`：覆盖 personal marketplace 路径。

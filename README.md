# backend-dev

`backend-dev` 是面向日常后端研发的 Codex 插件，提供任务路由、短流程交付、完整研发流程、浏览器 QA 和确认式经验复盘。插件还内置 `skill-curator-tbs`，用于多机器同步后的技能盘点和中文手册维护。

## 能力入口

| 场景 | 入口 |
| --- | --- |
| 后端任务自动路由 | `backend-dev:backend-router` |
| 小范围修复或维护 | `backend-dev:backend-flow` |
| 新模块、跨服务、发布准备 | `backend-dev:delivery-lifecycle` |
| 浏览器页面验收 | `backend-dev:browser-qa` |
| 经验复盘 | `backend-dev:backend-retro` |
| 技能与插件整理 | `backend-dev:skill-curator-tbs` |

## 本地安装

当前插件源目录应是唯一事实来源：

```powershell
$pluginRoot = "$env:USERPROFILE\.agents\plugins\backend-dev"
```

personal marketplace 位于：

```powershell
$marketplace = "$env:USERPROFILE\.agents\plugins\marketplace.json"
```

`marketplace.json` 中的插件源应指向：

```json
{
  "name": "backend-dev",
  "source": {
    "source": "local",
    "path": "./.agents/plugins/backend-dev"
  }
}
```

安装或刷新插件：

```powershell
codex plugin add backend-dev@personal
```

安装或刷新后，新开一个 Codex 任务验证，因为当前任务不会自动重新加载新技能。

## 多机器同步

推荐把本目录作为公开 GitHub 仓库同步。示例：

```powershell
git clone https://github.com/<account>/backend-dev.git "$env:USERPROFILE\.agents\plugins\backend-dev"
codex plugin add backend-dev@personal
```

更新：

```powershell
Set-Location "$env:USERPROFILE\.agents\plugins\backend-dev"
git pull
codex plugin add backend-dev@personal
```

不要直接维护 `.codex/plugins/cache` 下的副本；它只是 Codex 安装后的缓存。真正修改请提交到 `.agents/plugins/backend-dev`，再重新安装或刷新插件。

## 环境变量

默认不需要手动配置环境变量。`skill-curator-tbs` 会按当前电脑自动使用常见路径；只有当你的 Codex 目录、插件源目录、手册输出位置或 marketplace 不在默认位置时，才需要覆盖。

推荐让 AI 代你检查和配置。新机器安装后，可以直接对 Codex 说：

```text
请帮我配置 backend-dev 插件的跨机器环境：
1. 检查 CODEX_HOME、SKILL_CURATOR_MANUAL、SKILL_CURATOR_LOCAL_PLUGINS、SKILL_CURATOR_MARKETPLACE 当前是否需要设置。
2. 如果默认路径已经可用，不要设置多余环境变量。
3. 如果某个路径和默认值不一致，请用当前操作系统的用户级环境变量方式设置，并说明设置了什么。
4. 检查 personal marketplace 是否存在，确认 backend-dev 指向 .agents/plugins/backend-dev。
5. 运行 backend-dev:skill-curator-tbs 的盘点脚本验证配置。
6. 刷新插件安装，并提醒我新开一个 Codex 任务测试。
```

AI 配置时应优先“先检查，后设置”：不要为了整齐而写入不必要的环境变量。需要覆盖默认路径时，使用以下变量或脚本参数：

| 变量 | 作用 |
| --- | --- |
| `CODEX_HOME` | Codex 主目录，默认 `~/.codex`。 |
| `SKILL_CURATOR_MANUAL` | 中文技能手册输出路径。 |
| `SKILL_CURATOR_LOCAL_PLUGINS` | 本地插件源目录，默认 `~/plugins`。 |
| `SKILL_CURATOR_MARKETPLACE` | personal marketplace 路径，默认 `~/.agents/plugins/marketplace.json`。 |

## 浏览器 QA

有页面路径时使用 `backend-dev:browser-qa`。默认优先 Playwright，并使用 Chrome channel：

```ts
use: { channel: "chrome" }
```

验证时要检查页面入口、真实请求、状态码、请求体、响应字段、console 错误、network 结果、页面提示和刷新后的列表/详情状态。无法自动化时，要说明原因并给出浏览器或截图证据。

## 公开仓库安全检查

公开到 GitHub 前至少运行一次敏感信息搜索，确认没有提交：

- Token、secret、password、cookie、私钥。
- 内部域名、内网 IP、账号或真实业务数据。
- 本机绝对路径、截图、临时输出、`.codex/plugins/cache`。
- 未确认许可的第三方脚本或大段复制内容。

本仓库可以参考公开技能仓库的结构和流程，但不要复制许可不明的外部代码。若以后引入第三方 helper，必须先确认 LICENSE 并保留 notice。

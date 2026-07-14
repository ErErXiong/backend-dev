# backend-dev 使用手册

## 插件用途

`backend-dev` 为后端任务选择合适流程，并在改动后要求本地验证、浏览器 QA、Git 范围检查和确认式经验复盘。它不会自动提交、推送、发布、修改生产数据或写入项目规则。

## 日常使用

直接描述任务即可，例如：

```text
修复库存导入时缺少库位导致失败的问题，保持现有接口契约，完成后给出提交建议。
```

明确指定流程时，使用以下表达：

| 表达 | 作用 |
| --- | --- |
| `按短流程处理` | 明确的小范围改动：短计划、实现、验证、Git 建议。 |
| `按完整研发流程处理` | 大功能或准备发布：探索、方案、架构审查、实现、QA、安全与发布检查。 |
| `使用浏览器 QA 验证` | 对新增功能或修复后的页面路径执行真实浏览器验证。 |
| `先出方案，暂不实现` | 只进行需求与方案工作。 |
| `只分析，不改代码` | 强制只读诊断或评审。 |
| `检查并提交本次改动` | 先核对 diff 和暂存范围；提交前仍会征求确认。 |

## 路由规则

| 信号 | 路由 |
| --- | --- |
| 禅道、Bug 编号、工单链接 | `zentao-bug-fix`（可用时）。 |
| 报错、异常、不生效、回归 | `bugfix-workflow`（可用时）。 |
| 页面不显示、按钮无效、列表/详情未刷新、表单提交异常 | 后端修复流程 + `backend-dev:browser-qa`。 |
| 新增、方案、改业务规则、需求不清 | 澄清和计划；存在多种可行方案时使用 `brainstorming`。 |
| 线上、生产、紧急、数据修复、迁移、权限 | 安全优先：先确认范围、回滚和授权。 |
| Excel、导入、导出、模板、请求参数、前端未显示 | 同时检查字段契约、解析/写出、接口调用和页面刷新链路。 |

`grill-me` 仅适用于架构、迁移、权限边界等高风险方案审查，不用于普通小改动。

## 浏览器 QA

`backend-dev:browser-qa` 用于刚新增的功能或刚修复的 Bug 有页面入口时。默认优先使用 Playwright，Chrome channel 使用 `chrome`，并在页面稳定后检查 DOM、console、network、真实请求和页面刷新结果。

无法自动化浏览器验证时，可以使用 Codex 浏览器、Chrome 或截图证据，但必须说明未使用 Playwright 的原因。没有 fresh 验证输出时，不声称浏览器验证已完成。

## 技能整理

插件内置 `backend-dev:skill-curator-tbs`，用于盘点当前 Codex 技能和插件、检查重复入口、更新中文技能使用手册。新机器优先使用插件内入口；旧机器上的全局 `skill-curator-tbs` 可以保留，不自动删除。

跨机器配置优先使用环境变量：

| 变量 | 作用 |
| --- | --- |
| `CODEX_HOME` | Codex 主目录。 |
| `SKILL_CURATOR_MANUAL` | 中文手册输出路径。 |
| `SKILL_CURATOR_LOCAL_PLUGINS` | 本地插件源目录。 |
| `SKILL_CURATOR_MARKETPLACE` | personal marketplace 路径。 |

## 多机器同步

把 `%USERPROFILE%\.agents\plugins\backend-dev` 作为当前机器的插件源。其他机器建议 clone 到对应用户目录下的 `.agents/plugins/backend-dev`：

```powershell
git clone https://github.com/<account>/backend-dev.git "$env:USERPROFILE\.agents\plugins\backend-dev"
codex plugin add backend-dev@personal
```

更新时：

```powershell
Set-Location "$env:USERPROFILE\.agents\plugins\backend-dev"
git pull
codex plugin add backend-dev@personal
```

不要直接维护 `.codex/plugins/cache`；它只是安装缓存。插件安装或更新后，请新开一个任务测试，以便 Codex 重新加载技能。

## 公开仓库安全检查

公开到 GitHub 前，搜索并清理 Token、secret、password、cookie、内部域名、账号、真实业务数据、本机绝对路径、截图、临时输出和未确认许可的第三方脚本。外部项目只作为结构和流程参考，不直接复制许可不明代码。

## 经验复盘

实质性任务完成且有可靠结论时，插件会生成不超过 5 条经验候选。没有高价值候选时静默结束。

回复 `写入`、`只写第 1 条`、`不写` 或修改候选内容。默认目标为当前仓库的 `ai-memory/<项目名>/`；项目规则（`AGENTS.md`）和 ADR 必须单独确认。经验不得包含密码、Token、内部地址或原始对话。

## 限制

Codex 会根据任务语义选用技能，但这不是一个对每条提示都绝对强制的拦截器。对流程有明确要求时，请使用上面的显式表达。插件安装或更新后，请新开一个任务测试，以便 Codex 重新加载技能。


# 适配层（adapters）

> 每个工具一份**薄壳**。它们不写死 role，而是从项目根的 `team.yaml`**生成**（A 方案：生成式）。
> 核心契约在 `../core/`；这里只放"把通用契约翻译成某个工具原生吃的格式"的那层。

## 为什么要适配层

同一套协作契约（文件总线、STATUS 状态机、role 职责）要被不同工具消费，但每个工具读配置的方式不同：

| 工具 | 原生读什么 | 适配壳产物 |
| :--- | :--- | :--- |
| Claude Code | `.claude/skills/`、CLAUDE.md | 配置向导 skill + /plan /review /sync 触发器 |
| Codex | 仓库顶层 `AGENTS.md` | 一份 AGENTS.md，写明它担任的 role 怎么干 |
| Cursor | `.cursorrules` 等 | 占位，待接入 |

## 生成式（A 方案）怎么工作

1. 用户填好 `team.yaml`（哪些 role、几个 agent、谁担哪些 role、handoff 逻辑）。
2. 运行生成命令（配置向导）：读 `team.yaml`，为每个 `agents[].tool` 生成对应适配文件，把"这个 agent 担任哪些 role、各 role 该读写哪些文件、STATUS 怎么流转"**烤进**该工具的原生格式。
3. 生成的适配文件是静态的，任何该工具的实例都能直接读，不需要运行时解析 yaml。
4. 改了 `team.yaml` → 重新生成一遍。生成本身就是"配置一次、确认无误再开跑"的那道确认节点。

## 接入一个新工具

在本目录加一个 `<tool-name>/` 子目录，提供：
- 一个模板，描述如何把 role 职责 + STATUS 状态机翻译成该工具的原生配置格式；
- 生成逻辑（如何从 team.yaml 渲染出该模板）。

核心契约（core/）不动。这正是"角色与工具解耦"的好处：加工具 = 加一个适配壳。

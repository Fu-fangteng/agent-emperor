# Claude Code 适配壳

CC 通过 `.claude/skills/` 提供触发器，通过 CLAUDE.md 提供常驻指令。本适配壳含两部分：

## 1. 前台 `/setup-team`（登记 + 分拣入口）

用户 clone 项目后，用 CC 打开并运行 `/setup-team`。它会：
1. 没有 `team.yaml` 时登记编制：项目名、roles、agents、handoff、锚点风格。
2. 把答案写成项目根的 `team.yaml`。
3. 据此**生成各工具适配文件**：本工具的 skill/CLAUDE.md，以及 codex 的 AGENTS.md 等。
4. 提示用户"编制已生成，确认无误再开始第一个增量"。
5. 已有 `team.yaml` 时进入分拣模式：只澄清和路由，给用户一段转达 prompt，不写产物。

这就是"隐式引导生成显式文件"——同事不用手写 yaml，但最终落地一份可审查、随 repo 走的 team.yaml。

## 2. 运行期触发器（从生成的配置读 role）

| skill | 干什么 | 对应 STATUS 流转 |
| :--- | :--- | :--- |
| `/setup-team` | 前台：登记配置，或把用户请求分拣到正确 worker role | —（不写产物） |
| `/act` | 通用 worker：读取 team.yaml + handoff.md，执行当前 STATUS 轮到的 role | 按 team.yaml.handoff |
| `/whoami` | 当场自检：报我担任什么 role、是否轮到我、当前 STATUS、下一步 | —（不改状态） |
| `/sync` | 读总线对齐当前状态，告诉用户轮到谁、下一步 | —（不改状态） |

每个 skill 干完都按 START_HERE 的规矩：更新 STATUS + 给用户准备「转达 prompt」。

## 文件位置

skill 文件就在仓库的 `.claude/skills/` 下，CC 原生可读：

```
.claude/skills/
├─ setup-team/SKILL.md   前台（登记配置 / 分拣请求）
├─ act/SKILL.md          通用 worker 触发器
├─ whoami/SKILL.md       当场自检：我是谁、轮到我没、当前 STATUS
└─ sync/SKILL.md         只读对齐状态
```

clone 本仓即可用 `/setup-team`、`/act`、`/whoami`、`/sync`。
`init.sh` 铺进已有项目时也会把这些 skill 拷到目标项目的 `.claude/skills/`。
生成脚本是 `core/generate.py`，由 `/setup-team` 在第 3 步调用。

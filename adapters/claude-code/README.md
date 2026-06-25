# Claude Code 适配壳

CC 通过 `.claude/skills/` 提供触发器，通过 CLAUDE.md 提供常驻指令。本适配壳含两部分：

## 1. 配置向导 `/setup-team`（隐式配置入口）

用户 clone 项目后，用 CC 打开并运行 `/setup-team`。它会：
1. 问四个问题：用哪几个 role、几个 agent、谁担哪些 role、要不要 tester 这类可选环节。
2. 把答案写成项目根的 `team.yaml`。
3. 据此**生成各工具适配文件**：本工具的 skill/CLAUDE.md，以及 codex 的 AGENTS.md 等。
4. 提示用户"编制已生成，确认无误再开始第一个增量"。

这就是"隐式引导生成显式文件"——同事不用手写 yaml，但最终落地一份可审查、随 repo 走的 team.yaml。

## 2. 运行期触发器（从生成的配置读 role）

| skill | 干什么 | 对应 STATUS 流转 |
| :--- | :--- | :--- |
| `/plan <想法>` | planner：调研、写 requirements + plan | PLANNING → PLAN_REVIEW |
| `/review` | reviewer：按 STATUS 圈范围审 diff、跑测、写 review，按 P0-P3 | DEV_DONE → APPROVED / CHANGES_REQUESTED |
| `/sync` | 读总线对齐当前状态，告诉用户轮到谁、下一步 | —（不改状态） |

每个 skill 干完都按 START_HERE 的规矩：更新 STATUS + 给用户准备「转达 prompt」。

## 占位说明

当前为骨架说明。具体 skill 文件（SKILL.md 等）与生成脚本是下一步实现。

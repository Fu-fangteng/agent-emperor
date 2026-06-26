---
name: sync
description: Use when a user wants to know the current state of the multi-agent collaboration — reads the file bus and reports which STATUS the project is in, whose turn it is, and what the next step should be. Does not change any state.
---

# sync —— 对齐状态触发器

只读不写。读总线，告诉用户当前局势，不改任何状态。

## 干活
1. 读项目根 `team.yaml`：有哪几个 role、哪个 agent 担哪些 role、交接逻辑。
2. 读当前 phase 的 `handoff.md` 顶部 STATUS 块：当前状态、轮到谁、上次谁更新的。
3. 扫一眼 `requirements.md` / `plan.md` / `review.md` 的最新状态，判断进度卡在哪。

## 报告给用户
- **当前 STATUS**：是什么状态。
- **轮到谁**：按交接逻辑，现在该哪个 role / 哪个 agent 动手。
- **下一步**：用户该切到哪个 agent、新开对话给它什么「转达 prompt」。
- 若发现异常（STATUS 与文件实际进度对不上、有人写了不该写的文件），直说。

不改 STATUS、不写总线文件。这是个纯对齐工具。

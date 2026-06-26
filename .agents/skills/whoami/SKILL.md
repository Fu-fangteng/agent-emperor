---
name: whoami
description: Use when a user wants a conversation window to prove it knows its own identity in this multi-agent framework — reads team.yaml and the current handoff.md and reports which role this window holds, whether it's this window's turn, the current STATUS, and the next step. Read-only, changes nothing.
---

# whoami —— 当场自检触发器

只读不写。用来回答一个问题：**这个对话窗口清不清楚自己在干嘛。** 你随时敲一下，它当场自报家门，证明读到了自己的 role、没丢上下文。

## 干活
1. 读项目根 `team.yaml`：本项目名 `project.name`、本项目有哪几个 role、本 agent（看 AGENTS.md 里声明的 agent 名）担任哪些 role、交接逻辑。
2. 读当前 phase 的 `handoff.md` 顶部 STATUS 块：当前状态、轮到谁。
3. 对照判断：当前 STATUS 是否轮到"我"担任的某个 role。

## 报告给用户（固定格式）
一句话回执，让用户一眼确认你就位：

> 我是「<产品/增量> · <role>」（agent: <名字>）。已读 team.yaml + handoff.md，当前 STATUS=<X>，<轮到我，可以开干 / 没轮到我，现在该 <某 role>（<某 agent>）>。

- 产品/增量名以用户给你的转达 prompt 为准；不知道就用 `team.yaml.project.name`。
- 结尾按 AGENTS.md 里配置的锚点风格署名——**这本身就是自检的一部分**：署得出且 role 对，说明身份在线。

## 规矩
不改 STATUS、不写任何总线文件。这是纯自检/对齐工具，跟 `/sync` 的区别是：`/sync` 看全局局势，`/whoami` 只确认"我自己"是否就位。

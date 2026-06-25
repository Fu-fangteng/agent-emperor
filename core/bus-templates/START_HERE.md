# START HERE —— agent 进入这块总线先读我

你是这个项目多 agent 协作中的一员。开始任何动作前，按顺序做：

1. **读项目根的 `team.yaml`** —— 搞清楚：这个项目有哪几个 role、你（当前 agent）担任哪些 role、交接逻辑（哪个 STATUS 轮到哪个 role）。
2. **读当前 phase 的 `handoff.md` 顶部 STATUS 块** —— 确认现在处于哪个状态、是不是轮到你。
3. **如果轮到你**：读这个 phase 里与你 role 相关的文件（见下），干你那一份活。
4. **如果没轮到你**：不要动手。告诉用户当前轮到谁、该切到哪个 agent。

## 各 role 读写哪些文件

| 你的 role | 读 | 写（独占/追加） |
| :--- | :--- | :--- |
| planner | requirements 输入、相关代码 | requirements.md、plan.md（独占） |
| developer | plan.md、代码 | handoff.md（独占）、plan.md 的「开发方反馈」段（追加） |
| reviewer | handoff.md、diff、plan.md | review.md（独占） |

## 干完活后必做

1. 更新 `handoff.md` 顶部 STATUS 块（状态、轮到谁、更新时间）。
2. **给用户准备一段「转达 prompt」**：告诉下一个 agent 读哪几个文件、做什么、产出什么、最后把 STATUS 设成什么，并把关键约束（边界、不能动的文件）一句话带上。用户会把这段复制到下一个对话。
3. 在恰当的节点提示用户 commit。

> 核心规矩：**同一时刻只有一个 agent 在动**（STATUS 串行接力）；**配置文件不擅自改**（走交接说明）；**一个 role 一个独立对话**（保上下文干净）。

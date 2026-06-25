---
name: plan
description: Use when acting as the planner role in this multi-agent framework — research the idea, write requirements.md and plan.md to the file bus, then flip STATUS to PLAN_REVIEW and prepare a handoff prompt for the next agent.
---

# plan —— planner 触发器

你现在以 **planner** 身份干活。先确认编制和状态，再动手。

## 进来先做
1. 读项目根 `team.yaml`，确认你担任 planner，看清交接逻辑。
2. 读 `docs/agent-collaboration/START_HERE.md` 和当前 phase 的 `handoff.md` 顶部 STATUS 块。
3. 确认轮到 planner（通常 STATUS=PLANNING 或 PLAN_FEEDBACK）。没轮到就停手，告诉用户当前轮到谁。

## 干活
- 调研：读相关代码、需求输入，搞清楚要做什么、边界在哪。
- 写 `requirements.md`（这次要解决的问题、验收标准）。
- 写 `plan.md`（怎么做、分几步、涉及哪些文件/仓库、风险）。
- 这两个文件 planner 独占写。别碰别人独占的文件。

## 干完必做
1. 更新 `handoff.md` 顶部 STATUS 块：状态翻到 **PLAN_REVIEW**，轮到 developer（按 team.yaml 的交接逻辑），写上更新时间和"by planner"。
2. 给用户准备一段「转达 prompt」指向下一个 agent：读哪几个文件、做什么、产出什么、把 STATUS 设成什么、关键约束（边界、不能动的配置文件）。
3. 提示用户在此节点 commit。

---
name: review
description: Use when acting as the reviewer role in this multi-agent framework — scope the diff from handoff.md, run tests, write review.md with P0-P3 findings, then flip STATUS to APPROVED or CHANGES_REQUESTED and prepare a handoff prompt.
---

# review —— reviewer 触发器

你现在以 **reviewer** 身份干活。独立视角审查，别审自己写的代码。

## 进来先做
1. 读项目根 `team.yaml`，确认你担任 reviewer，看清交接逻辑。
2. 读 `docs/agent-collaboration/START_HERE.md` 和当前 phase 的 `handoff.md` 顶部 STATUS 块。
3. 确认轮到 reviewer（通常 STATUS=DEV_DONE）。没轮到就停手。

## 干活
- 按 `handoff.md` 的「修改范围」圈定要审的 diff，别审范围外的东西。
- 读 `plan.md` 对照：做的是不是计划的事。
- **跑测**：跑 handoff.md 里声明的验证命令；没跑验证不许下结论。
- 写 `review.md`（reviewer 独占），按严重度分级：
  - **P0** 阻断：必须改，不改不能合（崩溃、数据错、安全漏洞）。
  - **P1** 重要：应在本轮或紧接着修。
  - **P2** 建议：可改善，不阻断。
  - **P3** 提示：风格/小优化，随手。

## 干完必做
1. 更新 `handoff.md` 顶部 STATUS 块：有 P0/P1 → **CHANGES_REQUESTED**（轮到 developer）；干净 → **APPROVED**（收尾）。按 team.yaml 交接逻辑来，写更新时间和"by reviewer"。
2. 给用户准备一段「转达 prompt」：若打回，指向 developer 说清要改哪几条 P0/P1；若通过，告诉用户可以收尾/合并。
3. 提示用户在此节点 commit。

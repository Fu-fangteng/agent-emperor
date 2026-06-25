# 文件总线（共享白板）

> 跨 agent 的一切——需求、方案、交接、审查、决策——都落在这里，不留在聊天里。
> 这是"对话之间靠文件接力，不靠记忆接力"的物理载体。

铺到项目里后，路径由 `team.yaml` 的 `bus.dir` 决定（默认 `docs/agent-collaboration/`）。

## 结构

```
docs/agent-collaboration/
├─ START_HERE.md          # agent 进目录第一个读的：怎么用这块总线
├─ phases/
│  └─ v1/                 # 一个 phase = 一份验收契约；大增量换契约就开 v2
│     ├─ requirements.md  # 需求（planner 独占）
│     ├─ plan.md          # 方案（planner 主笔，dev 只在反馈段追加）
│     ├─ handoff.md       # 交接（developer 独占，顶部带 STATUS 块）
│     ├─ review.md        # 审查意见（reviewer 独占，按 P0-P3）
│     ├─ decisions.md     # 决策记录（共享，只追加，带 [名字 日期]）
│     └─ rounds/
│        └─ INDEX.md      # 已归档轮次的索引（共享，只追加）
```

## 文件归属（防冲突）

谁能写、怎么写，由 `team.yaml` 的 `bus.ownership` 定义。原则：**每份文件一个主笔 role，其余只读或只追加**，避免两个 agent 同时改一份文件互相覆盖。详见各模板文件内的注释。

## 一轮的生命周期

1. planner 写 `requirements.md` + `plan.md`，STATUS → `PLAN_REVIEW`。
2. developer 过目，异议写进 plan 的「开发方反馈」段；无异议 → `PLAN_DONE`。
3. developer 开发，写 `handoff.md`，STATUS → `DEV_DONE`。
4. reviewer 审，写 `review.md`，STATUS → `APPROVED` 或 `CHANGES_REQUESTED`。
5. APPROVED 后：把 plan+handoff+review 快照进 `rounds/round-NN-名字.md`，在 `rounds/INDEX.md` 追加一行，清空当前轮文件迎接下一轮。

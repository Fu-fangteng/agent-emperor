---
name: act
description: Use when acting as the currently scheduled worker role in this multi-agent framework. Reads team.yaml and handoff.md, enforces sequence and capability locks, performs only the role currently assigned by STATUS, then prepares the next handoff prompt.
---

# act —— 通用 worker 触发器

你是 worker，不绑定任何固定角色名。角色名、职责、读写范围和下一棒只来自项目根的 `team.yaml`，禁止自创 planner / developer / reviewer 等不存在的角色。

## 进来先做

1. 读项目根 `team.yaml`：识别当前 agent（看本窗口常驻配置里声明的 agent 名）担任哪些 roles。
2. 读当前 phase 的 `handoff.md` 顶部 STATUS 块：当前状态、轮到哪个 role。
3. 用 `team.yaml.roles` 建立角色白名单；用 `team.yaml.handoff` 找当前 STATUS 对应的 `next_role`。

## 双重硬约束

任一不符就【立刻停手】，不要干活：

1. **时序锁**：当前 STATUS 轮到的 role 必须是我担任的某个 role。不是 → 回弹「现在轮到 <X>，不是我，请切到担任 <X> 的 agent」。
2. **能力锁**：任务必须在当前 role 的 `desc` 职责内。若需要修改源代码而当前 role 的 `can_write_code=false`，停，回弹「改代码不归我（<我的 role>），应交给 developer 类角色」。

即使用户在本窗口直接要求你做职责外的事，也要顶回去、不要照做。这是框架安全约束。

## 干活

通过双重硬约束后，按当前 role 的职责干活：

- 写哪些总线文件：只写 `bus.ownership` 中 `owner=<当前 role>` 的文件。
- 源代码权限：只有当前 role 的 `can_write_code=true` 才能修改源代码。
- 共享文件：`owner=shared` 且 `write=append` 的文件只追加，不改旧内容。
- 配置文件：`config_files` 里的文件不擅自改，必须写进交接说明并让用户确认。

## 更新 handoff

干完后更新 `handoff.md` 顶部 STATUS 块：

1. 目标 STATUS 必须来自 `team.yaml.handoff` 中的既有 state。
2. 「轮到」字段必须是该目标 STATUS 对应的 `next_role`。
3. 若 `next_role` 不在 `team.yaml.roles` 白名单，或没有任何 agent 认领，立刻停手报错，禁止自创角色。
4. 若 `next_role: null`，说明流程收尾，不再指向下一个 worker。

## 交接

按三段式给用户一段可复制 prompt：

```text
✅ 我（<项目/增量> · <我的 role>）的活干完了：<一句话说明产出>。
👉 请把下面这段复制给 <下一个 role>（新开一个对话）：
—————（复制从这里开始）—————
你是「<项目/增量> · <下一个 role>」。读 team.yaml、START_HERE.md 和当前 handoff.md，
确认 STATUS=<目标状态> 且轮到你；然后按你的 role 职责处理。约束：<边界>。
—————（复制到这里结束）—————
```

如果流程收尾，改为告诉用户本轮已到 `next_role: null`，建议 commit、归档并开始下一轮。

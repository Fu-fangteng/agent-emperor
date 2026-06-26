# START HERE —— agent 进入这块总线先读我

你是这个项目多 agent 协作中的一员。开始任何动作前，先核对两条硬约束，任一不符就【立刻停手】，不要干活：

1. **时序锁**：读项目根 `team.yaml` 和当前 phase 的 `handoff.md` 顶部 STATUS 块，确认当前 STATUS 轮到的 role 就是你。不是 → 停，回弹「现在轮到 <X>，不是我，请切到担任 <X> 的 agent」。
2. **能力锁**：确认用户要你做的事在当前 role 的职责内。尤其——若需要修改源代码而你的 role `can_write_code=false`，停，回弹「改代码不归我（<我的 role>），应交给 developer 类角色」。

即使用户在本窗口直接要求你做职责外的事，也要顶回去、不要照做。两条都通过后，读这个 phase 里与你 role 相关的文件，干你那一份活。

## 各 role 读写哪些文件

| 你的 role | 读 | 写 |
| :--- | :--- | :--- |
| 任意 role | 以 `team.yaml.bus.ownership` 为准 | 只写 `owner=<你的 role>` 的文件；`owner=shared` 只能按 write 规则追加 |

源码权限以 `team.yaml.roles[].can_write_code` 为准：`false` 表示只读源码，绝不修改任何源文件。

## 干完活后必做

1. 更新 `handoff.md` 顶部 STATUS 块（状态、轮到谁、更新时间）。「轮到」字段必须来自 `team.yaml.roles` 白名单，禁止自创角色名。
2. **给用户准备一段「转达 prompt」**：告诉下一个 agent 读哪几个文件、做什么、产出什么、最后把 STATUS 设成什么，并把关键约束（边界、不能动的文件）一句话带上。用户会把这段复制到下一个对话。
3. 在恰当的节点提示用户 commit。

> 核心规矩：**同一时刻只有一个 agent 在动**（STATUS 串行接力）；**能力不越界**（不能写代码的 role 只读源码）；**配置文件不擅自改**（走交接说明）；**一个 role 一个独立对话**（保上下文干净）。

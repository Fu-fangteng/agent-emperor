# 样例：填好的 team.yaml

> 这是作者本地验证过、跑在真实跑测平台项目上的编制：
> CC 兼任 planner + reviewer，Codex 当 developer，跨两个仓开发。
> 拿它当填写参考。字段含义见 ../core/team.schema.yaml 的注释。

```yaml
version: 1

project:
  name: atoms-benchmark
  repos:
    - .                  # atoms_benchmark 本仓
    - ../MetaGPT         # 跑测链路跨的第二个仓（通过 METAGPT_ROOT 注入）

roles:
  - name: planner
    desc: 写需求和方案，明确范围、验收标准和实施计划
    can_write_code: false
  - name: developer
    desc: 修改源代码、运行验证、维护交接说明
    can_write_code: true
  - name: reviewer
    desc: 独立审查 diff 和测试结果，输出 P0-P3 findings
    can_write_code: false

agents:
  - name: cc
    tool: claude-code
    roles: [planner, reviewer]
  - name: codex
    tool: codex
    roles: [developer]

handoff:
  - { state: PLANNING,           next_role: planner,    human_gate: false }
  - { state: PLAN_REVIEW,        next_role: developer,  human_gate: true  }
  - { state: PLAN_FEEDBACK,      next_role: planner,    human_gate: true  }
  - { state: PLAN_DONE,          next_role: developer,  human_gate: true  }
  - { state: DEV_DONE,           next_role: reviewer,   human_gate: true  }
  - { state: CHANGES_REQUESTED,  next_role: developer,  human_gate: true  }
  - { state: APPROVED,           next_role: null,       human_gate: true  }

bus:
  dir: docs/agent-collaboration
  ownership:
    - { file: requirements.md, owner: planner,   write: exclusive }
    - { file: plan.md,         owner: planner,   write: exclusive, note: "developer 只在「开发方反馈」段追加" }
    - { file: handoff.md,      owner: developer, write: exclusive, note: "顶部带 STATUS 块" }
    - { file: review.md,       owner: reviewer,  write: exclusive }
    - { file: decisions.md,    owner: shared,    write: append,    note: "每条带 [名字 日期] 前缀" }
    - { file: rounds/INDEX.md, owner: shared,    write: append }

config_files:
  - config2.yaml
  - .benchmark_secrets.yaml

anchor:
  style: stamp            # 打卡盖章 + role 吉祥物；10 种风格见 ../core/team.schema.yaml
  role_emoji:
    planner: 🦝
    developer: 🦫
    reviewer: 🦉
```

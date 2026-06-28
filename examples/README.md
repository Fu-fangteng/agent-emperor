# 样例:填好的 team.yaml

> 这是一个**通用样例**:做一个公司内部 wiki 站点,CC 兼任 planner+reviewer,Codex 当 developer。
> 拿它当填写参考。字段含义见 ../core/team.schema.yaml 的注释。
>
> 如果你的项目角色不同(比如做安全审计、做内容运营),把 roles / agents / handoff / bus.ownership 都换成你的角色名,
> 框架不绑定任何固定角色。

```yaml
version: 1

project:
  name: internal-wiki
  repos:
    - .

roles:
  - name: planner
    desc: 写需求和方案,明确范围、验收标准和实施计划
    can_write_code: false
  - name: developer
    desc: 修改源代码、运行验证、维护交接说明
    can_write_code: true
  - name: reviewer
    desc: 独立审查 diff 和测试结果,输出 P0-P3 findings
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

# 项目里那些"改错会让全员排查半天"的关键配置;无此类文件可整段留空
config_files: []

anchor:
  style: stamp            # 打卡盖章 + role 吉祥物;10 种风格见 ../core/team.schema.yaml
  role_emoji:
    planner: 🦝
    developer: 🦫
    reviewer: 🦉
```

## 换一种角色编制怎么改?

假如你做的是**安全审计项目**,角色是 analyst / pentester / auditor,改动如下:

```yaml
roles:
  - { name: analyst,   desc: 梳理目标和威胁面,            can_write_code: false }
  - { name: pentester, desc: 执行渗透测试、跑工具、写脚本, can_write_code: true  }
  - { name: auditor,   desc: 独立审查发现项、出报告,       can_write_code: false }

handoff:
  - { state: SCOPING,       next_role: analyst,   human_gate: false }
  - { state: SCOPE_DONE,    next_role: pentester, human_gate: true  }
  - { state: TESTING_DONE,  next_role: auditor,   human_gate: true  }
  - { state: APPROVED,      next_role: null,      human_gate: true  }

bus:
  ownership:
    - { file: scope.md,    owner: analyst,   write: exclusive }
    - { file: findings.md, owner: pentester, write: exclusive }
    - { file: handoff.md,  owner: pentester, write: exclusive }
    - { file: report.md,   owner: auditor,   write: exclusive }
```

关键:`roles`、`handoff.next_role`、`bus.ownership.owner` 这三处的角色名要互相对得上,生成器会校验。

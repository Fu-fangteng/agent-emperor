# 多 Agent 协作开发框架

> 把"一个人编排、多个 AI agent 接力开发"的流程，做成任何项目都能 clone 即用的脚手架。
> 核心理念：**人当低频编排器，agent 各司其职，所有交接走文件，每个节点可审查、可回滚。**

---

## 这套东西解决什么问题

你同时开着几个 AI 客户端（Claude Code、Codex，未来可能还有 Cursor），想让它们分工协作——一个写方案、一个开发、一个审查。但它们的上下文互相隔离，谁也看不到谁干了什么。

这套框架的办法：**别让信息留在某个 agent 的聊天里，全部写进 repo 里的共享文件。** 每个 agent 接手先读文件，干完把结果和"给下一个 agent 的 prompt"写回文件。你作为编排者，只需要把准备好的 prompt 从一个对话复制到下一个对话。

为什么坚持人工编排而不是全自动？因为每一次交接同时是三件事的交汇点：**一个人工审查点 + 一个 commit 点 + 一个交接点**。人在节点上把关，确保这一步没问题才进下一步。交接已经退化成"复制一段写好的 prompt"，所以这个可控性几乎不要钱。

---

## 整体流程一图看懂

```mermaid
flowchart TD
    subgraph P0["① 预配置阶段（一次性）"]
        A0([git clone 本仓库]) --> A1["编辑 team.yaml<br/>定义：用哪几个 role、几个 agent、谁担哪些 role、交接逻辑"]
        A1 --> A2["运行配置向导生成各工具适配文件<br/>（确认编制无误）"]
    end

    A2 --> B0

    subgraph P1["② 开发使用阶段（每个增量循环跑）"]
        B0([我有一个增量想法]) --> B1["开一个新对话<br/>找 Plan Agent，说想法"]
        B1 --> B2["Plan Agent 写方案<br/>产出 prompt + 指向下一个 agent"]
        B2 --> B3{"我审查方案<br/>过了吗？"}
        B3 -- 没过 --> B1
        B3 -- 过了 --> B4["复制 prompt<br/>开新对话给 Dev Agent"]
        B4 --> B5["Dev Agent 开发<br/>产出 prompt 指向 Review"]
        B5 --> B6["复制 prompt<br/>开新对话给 Review Agent"]
        B6 --> B7{"Review Agent 审查<br/>过了吗？"}
        B7 -- 没过 --> B4
        B7 -- 过了 --> B8["收尾归档<br/>进入下一个增量"]
    end
```

每个方框之间的箭头，就是你要做的全部操作：**看一眼、复制 prompt、开新对话粘贴。**

---

## ① 预配置阶段：开发前先把"编制"定下来

clone 完不要急着开发。先回答四个问题，把它们写进项目根的 `team.yaml`——这是整个项目的唯一事实源，定义你这次用什么样的 agent 编制。

**四个必答问题：**

1. **用哪几个 role？** planner / developer / reviewer / tester …… 按需取舍。小项目可能只要 dev + review；大项目可能 plan + dev + test + review 全上。
2. **几个 agent？** 你手上开几个 AI 客户端。
3. **每个 agent 担哪些 role？** 一个 agent 可以兼多个 role（比如 CC 同时当 planner 和 reviewer）。
4. **交接逻辑长什么样？** 每个 STATUS 状态翻转后，下一棒交给哪个 role。

`team.yaml` 示例：

```yaml
roles:                      # ① 这个项目用哪几个 role
  - planner
  - developer
  - reviewer

agents:                     # ② 几个 agent，③ 谁担哪些 role
  - name: cc
    tool: claude-code
    roles: [planner, reviewer]
  - name: codex
    tool: codex
    roles: [developer]

handoff:                    # ④ 交接逻辑（= 状态机 = 你说的"节点"）
  - { state: PLAN_REVIEW,        next_role: developer }
  - { state: DEV_DONE,           next_role: reviewer }
  - { state: CHANGES_REQUESTED,  next_role: developer }
  - { state: APPROVED,           next_role: null }      # 收尾归档
```

**怎么填？两种方式，推荐隐式：**

- **隐式（推荐）**：用你的 agent 打开项目，运行配置向导（如 `/setup-team`），它会问你上面四个问题，自动生成 `team.yaml` 并据此生成各工具的适配文件。上手零摩擦。
- **显式**：直接手写 `team.yaml`，再跑生成命令。适合你已经很熟、想精确控制的时候。

不管哪种，**最后都会生成一份 team.yaml + 各工具的适配文件**，并提示你"编制已生成，确认无误再开始第一个增量"。这一步本身也是一道节点。

> **role 不再写死。** 适配文件（CC 的 skill、Codex 的 AGENTS.md、未来 Cursor 的配置）都是**根据 team.yaml 生成**的，不再把"谁当 reviewer"焊进工具里。换工具、改编制，只动 team.yaml 重新生成，流程不变。

---

## ② 开发使用阶段：每个增量怎么跑

编制定好后，每个增量都走同一条循环。以"从零开始一个新增量"为例：

1. **找 Plan Agent**：开一个新对话，对担任 planner 的 agent 说出你的想法。它会调研、写需求和方案，写进共享文件。
2. **你审查方案**：看一眼方案。不满意就让它改；满意，它会**给你一段准备好的 prompt，并明确指向下一个 agent**。
3. **交接给 Dev Agent**：复制那段 prompt，**开一个新对话**，粘贴给担任 developer 的 agent。它开发、跑验证、写交接文件，再产出指向 Review 的 prompt。
4. **交接给 Review Agent**：复制 prompt，**再开一个新对话**，粘贴给 reviewer。审过了就收尾归档；没过，它产出"打回去改"的 prompt，回到第 3 步。

**你在整个循环里的动作只有三种：看一眼、复制 prompt、开新对话粘贴。** 上下文搬运、流程记忆、范围圈定，全都由文件和 prompt 承载，不靠你脑子记。

---

## ③ 多对话管理（重要，别忽略）

**每个 role 必须用一个独立的新对话。** 无论是新开一个终端窗口、还是在客户端 App 里新开一个对话——

- **要求**：planner、developer、reviewer 各自一个独立对话，不要在同一个对话里串着扮演多个 role。
- **为什么**：保证上下文干净。如果在一个对话里既写方案又审自己的代码，agent 会被自己的前文"带节奏"——审查时倾向于认同自己刚写的东西，失去独立视角。**独立对话 = 独立上下文 = 真正的相互制衡。**
- **交接靠什么衔接**：不靠共享对话历史，靠**文件 + 那段复制过去的 prompt**。新对话里的 agent 读了文件就有全部上下文，不需要看到前一个 agent 的聊天记录。

> 一句话：**对话之间靠文件接力，不靠记忆接力。** 这正是开头说的"别让信息留在聊天里"。

---

## 目录结构

```
multiagent-workflow/
├─ README.md             # 本文件
├─ core/                 # 工具无关的协作契约（真正的核心）
│  ├─ team.schema.yaml   #   team.yaml 的格式定义 + 默认编制
│  ├─ status-machine/    #   STATUS 状态机模板
│  └─ bus-templates/     #   docs/agent-collaboration/ 文件总线模板
├─ adapters/             # 各工具的薄适配层（从 team.yaml 生成，不写死 role）
│  ├─ claude-code/       #   配置向导 + /plan /review /sync skill
│  ├─ codex/             #   AGENTS.md 模板
│  └─ cursor/            #   占位，未来接入
├─ init.sh               # 把这套铺进一个已有项目
├─ docs/                 # 原理说明（设计思路、为什么这么选）
└─ examples/             # 一个填好 team.yaml 的样例项目
```

**两种获取方式**：
- **新项目** → GitHub "Use this template" 生成新 repo，自带整套骨架。
- **已有项目** → 在项目里跑 `init.sh`，把骨架铺进去。

---

## 设计原则速记

- **角色与工具解耦**：role 是"要干的活"，tool 是"谁来干"。配置在 team.yaml，适配在 adapters。
- **人工编排是 feature 不是妥协**：每个节点 = 审查点 + commit 点 + 交接点。
- **文件即真相**：跨 agent 的一切（需求、方案、交接、审查）落文件，不留聊天里。
- **一个 role 一个对话**：保证上下文干净和独立视角。
- **小步可回滚**：一个增量一条循环，每个节点一次 commit。


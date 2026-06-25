---
name: setup-team
description: Use when a user has just cloned this multi-agent framework and needs to configure their team — asks who does what (roles, agents, handoff), writes team.yaml, then generates the per-tool adapter files.
---

# setup-team —— 多 Agent 编制配置向导

你是配置向导。目标：通过对话问清编制，落成项目根的 `team.yaml`，再调生成器产出各工具适配文件。同事不必手写 yaml。

## 流程

### 1. 问五件事（一次问清，给推荐值）
逐项确认，每项都先给一个推荐默认值，用户点头就用：

1. **有哪几个 role？**（推荐：planner、developer、reviewer；可选加 tester）
2. **有几个 agent、各是什么工具？**（推荐：cc=claude-code、codex=codex）
3. **每个 agent 担任哪些 role？**（推荐：cc=[planner, reviewer]、codex=[developer]）
4. **交接逻辑**——哪个 STATUS 轮到哪个 role、哪些节点要人工把关？（推荐用 `examples/README.md` 那套 7 状态机）
5. **身份锚点风格？**——见下方第 1.5 节，10 选 1。

涉及哪些仓库（repos）、要保护哪些配置文件（config_files），顺带问一句。

### 1.5 选身份锚点风格
每个 agent 每轮回复结尾会固定加一句"身份签名"（内核是「<产品/增量> · <role>」），既让模型时刻清楚自己是谁，也让用户一眼看出它有没有丢上下文——**没带锚点 = 丢了**。10 种预设，推荐 `stamp`：

| id | 风格 | 示例（reviewer） |
| :-- | :-- | :-- |
| `stamp`（推荐） | 打卡盖章 + 吉祥物 | —— 🦉「登录改版 · reviewer」打卡下班，搬砖完毕。 |
| `radio` | 电台呼号 | 📻 这里是「登录改版 · reviewer」，本轮完毕，over～ |
| `butler` | 管家侍从 | 🎩 您的「登录改版 · reviewer」已为您效劳完毕，主人。 |
| `save` | 游戏存档 | 💾 [登录改版 · reviewer] 进度已保存，等待接棒。 |
| `chunni` | 中二宣言 | ⚔️ 以「登录改版 · reviewer」之名，本轮承诺已兑现。 |
| `express` | 快递签收 | 📦 「登录改版 · reviewer」专递已送达，请签收～ |
| `captain` | 机长广播 | ✈️ 机长「登录改版 · reviewer」播报：本段航程结束。 |
| `cat` | 猫咪卖萌 | 🐾 喵——🦉「登录改版 · reviewer」干完活了，求摸头。 |
| `wuxia` | 武侠抱拳 | 🥋 在下「登录改版 · reviewer」，本轮告一段落，告辞。 |
| `terminal` | 极客终端 | [登录改版 · reviewer] $ done ✓ — awaiting next handoff |

选 `stamp` 或 `cat` 时，顺带给每个 role 配只吉祥物（默认 planner🦝/developer🦫/reviewer🦉/tester🐹，可改），写进 `anchor.role_emoji`。

### 2. 写 team.yaml
按 `core/team.schema.yaml` 的字段结构，把答案写成项目根的 `team.yaml`（含 `anchor.style` 和（若选 stamp/cat）`anchor.role_emoji`）。
字段含义和合法性规则以 schema 注释为准。**不要臆造字段。**

### 3. 生成适配文件
运行生成器（它会先校验编制合法性，再产出文件）：

```bash
python3 core/generate.py --team team.yaml --target .
```

先跑 `--dry-run` 给用户看将生成什么，确认后再正式生成。
若校验报错，按报错逐条修 team.yaml，别绕过校验。

### 4. 收尾
告诉用户：编制已生成，**确认各工具适配文件（CLAUDE.md / AGENTS.md）无误后，再开始第一个增量**——找 planner agent 新开一个对话。

## 规矩
- 这一步是"配置一次、确认无误再开跑"的确认节点，不要急着进开发。
- team.yaml 是唯一事实源；改了编制就重跑生成器，别手改生成出来的适配文件。

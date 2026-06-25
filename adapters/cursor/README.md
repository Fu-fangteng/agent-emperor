# Cursor 适配壳（占位）

未来接入。Cursor 原生读 `.cursorrules`（或其等价配置）。

接入时在本目录提供：
- 一个模板，把 role 职责 + STATUS 状态机翻译成 Cursor 的原生规则格式；
- 从 team.yaml 渲染该模板的生成逻辑。

核心契约（../../core/）不变——这正是"角色与工具解耦"的意义：加 Cursor = 加这一个适配壳，流程不动。

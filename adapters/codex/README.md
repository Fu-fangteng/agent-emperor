# Codex 适配壳

Codex 进入仓库会原生读取顶层 `AGENTS.md`。本适配壳根据 `team.yaml` 生成那份 AGENTS.md，告诉 Codex：它担任哪些 role、各 role 怎么干、STATUS 怎么流转。

## 生成产物：仓库顶层 AGENTS.md

模板见 `AGENTS.md.template`。生成时按 team.yaml 填入：
- 这个 agent（tool=codex）担任的 role 列表；
- 每个 role 读写哪些总线文件；
- 它负责翻转的 STATUS 状态、以及翻转后该给用户准备的「转达 prompt」。

## 占位说明

当前为模板骨架。真正的生成脚本随配置向导一起实现（见 ../claude-code/）。

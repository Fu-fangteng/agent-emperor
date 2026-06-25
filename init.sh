#!/usr/bin/env bash
#
# init.sh —— 把多 Agent 协作框架铺进一个【已有项目】
#
# 新项目用 GitHub "Use this template" 即可；本脚本解决"老项目就地加装"。
# 做的事：把 core 的总线模板和 team.yaml 默认值拷进目标项目，提示下一步。
# 不覆盖已存在的文件（防止冲掉你的工作），只补缺失的。
#
# 用法：
#   ./init.sh /path/to/your/existing/project
#   ./init.sh                      # 默认铺到当前目录
#
set -euo pipefail

FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$(pwd)}"

if [[ ! -d "$TARGET" ]]; then
  echo "[init] 目标目录不存在：$TARGET"; exit 1
fi

echo "[init] 框架源：$FRAMEWORK_DIR"
echo "[init] 铺设到：$TARGET"

# 1) team.yaml —— 不覆盖已有的
if [[ -f "$TARGET/team.yaml" ]]; then
  echo "[init] 已存在 team.yaml，跳过（不覆盖你的编制）。"
else
  cp "$FRAMEWORK_DIR/core/team.schema.yaml" "$TARGET/team.yaml"
  echo "[init] ✓ 生成 team.yaml（基于默认编制，请按你的项目修改）。"
fi

# 2) 文件总线 —— 拷模板，不覆盖已有文件
BUS_SRC="$FRAMEWORK_DIR/core/bus-templates"
BUS_DST="$TARGET/docs/agent-collaboration"
mkdir -p "$BUS_DST"
# -n = no-clobber，已存在的不覆盖
cp -Rn "$BUS_SRC/." "$BUS_DST/" 2>/dev/null || cp -R "$BUS_SRC/." "$BUS_DST/"
echo "[init] ✓ 文件总线就位：$BUS_DST（已有文件未覆盖）。"

# 3) 提示后续（适配文件由配置向导生成，不在本脚本里硬写）
cat <<'EOF'

[init] 骨架铺设完成。接下来：
  1. 编辑 team.yaml：定义 role / agent / 职责 / handoff 交接逻辑。
  2. 用你的 agent 打开项目，运行配置向导（如 CC 的 /setup-team）生成各工具适配文件。
  3. 确认编制无误后，开始第一个增量（找 planner agent，新开一个对话）。

提醒：把 .loop-logs/、.env、本机私密配置加进目标项目的 .gitignore。
EOF

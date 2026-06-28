#!/usr/bin/env bash
#
# sync-framework-readme.sh —— 把父类 README 同步到子类 demo 的内容源位置
#
# 本项目自身是 Agent Emperor 框架的官网 demo,网页内容以父类 README 为唯一来源。
# 父类 README 改动后,跑这个脚本同步一次,再开新一轮迭代。
#
# 用法:
#   ./sync-framework-readme.sh                    # 默认同步到 ../multiagent-workflow-demo
#   ./sync-framework-readme.sh /path/to/subclass  # 同步到指定路径
#
set -euo pipefail

PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$PARENT_DIR/README.md"
DEFAULT_TARGET="$PARENT_DIR/../multiagent-workflow-demo"
TARGET="${1:-$DEFAULT_TARGET}"
DST="$TARGET/docs/framework-readme.md"

if [[ ! -f "$SRC" ]]; then
  echo "[sync] 找不到父类 README:$SRC" >&2; exit 1
fi
if [[ ! -d "$TARGET" ]]; then
  echo "[sync] 子类目录不存在:$TARGET" >&2; exit 1
fi

mkdir -p "$(dirname "$DST")"

if [[ -f "$DST" ]] && cmp -s "$SRC" "$DST"; then
  echo "[sync] 内容已一致,无需同步:$DST"
  exit 0
fi

cp "$SRC" "$DST"
echo "[sync] ✓ 已同步 README.md → $DST"
echo "[sync]   行数:$(wc -l < "$DST")"
echo "[sync]   下一步:在子类 git commit 这次同步,再开新一轮 v2 迭代。"
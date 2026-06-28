#!/usr/bin/env bash
#
# init.sh —— 把 Agent Emperor（多 Agent 协作框架）铺进一个【已有项目】
#
# 新项目用 GitHub "Use this template" 即可；本脚本解决"老项目就地加装"。
# 做的事：按 core/framework-manifest.txt 清单把框架层铺进目标项目；team.yaml
# 用默认模板首装。不覆盖已存在的文件（防止冲掉你的工作）。
#
# 用法：
#   ./init.sh /path/to/your/existing/project
#   ./init.sh                      # 默认铺到当前目录
#   ./init.sh --upgrade /path/to/project   # 镜像同步框架层 + 删废弃文件
#
# 依赖：python3、PyYAML（pip install pyyaml）—— 跑 /setup-team 第三步生成器要用
#
set -euo pipefail

FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPGRADE=0
if [[ "${1:-}" == "--upgrade" ]]; then
  UPGRADE=1
  shift
fi
TARGET="${1:-$(pwd)}"

if [[ ! -d "$TARGET" ]]; then
  echo "[init] 目标目录不存在：$TARGET"; exit 1
fi

# 防呆:不允许在框架自身目录铺设(常见误用)。--upgrade 模式合法(就是要更新自己,虽然罕见)。
TARGET_ABS="$(cd "$TARGET" && pwd)"
if [[ "$UPGRADE" == "0" && "$TARGET_ABS" == "$FRAMEWORK_DIR" ]]; then
  cat >&2 <<EOF
[init] ⚠ 看起来你在框架自身目录跑 ./init.sh,这通常是错的。
[init]   Agent Emperor 是模板,不是项目本身——在父类目录跑 init,所有框架文件
[init]   都"已存在被跳过",你什么也装不到。
[init]
[init] 正确做法二选一:
[init]   1. 用 GitHub "Use this template" 新建一个项目 repo
[init]   2. 跑:  ./init.sh /path/to/your-project-dir
EOF
  exit 1
fi

MANIFEST="$FRAMEWORK_DIR/core/framework-manifest.txt"
if [[ ! -f "$MANIFEST" ]]; then
  echo "[init] 找不到框架清单：$MANIFEST"; exit 1
fi

echo "[init] 框架源：$FRAMEWORK_DIR"
echo "[init] 铺设到：$TARGET"

if [[ "$UPGRADE" == "1" ]]; then
  cat <<'EOF'
[init] upgrade 模式会镜像覆盖框架层文件，并删除目标中已废弃的旧框架文件。
[init] 建议你先 commit 当前工作，便于回滚。实例层文件不会被触碰：
[init] team.yaml、业务代码、素材、phases 产物、.gitignore、本机配置等。
EOF

  while IFS= read -r rel || [[ -n "$rel" ]]; do
    [[ -z "$rel" || "$rel" =~ ^# ]] && continue
    src="$FRAMEWORK_DIR/$rel"
    dst="$TARGET/$rel"
    if [[ -e "$src" ]]; then
      mkdir -p "$(dirname "$dst")"
      cp -R "$src" "$dst"
      echo "[init] ✓ 更新 $rel"
    elif [[ -e "$dst" ]]; then
      rm -rf "$dst"
      echo "[init] ✓ 删除废弃 $rel"
    fi
  done < "$MANIFEST"

  for old in \
    ".claude/skills/plan" ".claude/skills/review" \
    ".agents/skills/plan" ".agents/skills/review"; do
    if [[ -e "$TARGET/$old" ]]; then
      rm -rf "$TARGET/$old"
      echo "[init] ✓ 删除废弃 $old"
    fi
  done

  echo "[init] 升级完成。建议运行 /setup-team 检查旧 team.yaml，并重跑 python3 core/generate.py。"
  exit 0
fi

# ----------------------------------------------------------------------------
# 普通 init 模式：按 manifest 铺框架层，已存在不覆盖
# ----------------------------------------------------------------------------

# 1) 框架层 —— 按 manifest 一条一条铺，已存在的不覆盖
while IFS= read -r rel || [[ -n "$rel" ]]; do
  [[ -z "$rel" || "$rel" =~ ^# ]] && continue
  src="$FRAMEWORK_DIR/$rel"
  dst="$TARGET/$rel"
  [[ ! -e "$src" ]] && continue
  if [[ -e "$dst" ]]; then
    echo "[init] - 跳过 ${rel}（已存在）"
    continue
  fi
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  echo "[init] ✓ $rel"
done < "$MANIFEST"

# 2) team.yaml —— 不覆盖已有；首装拿 schema 当默认模板
if [[ -f "$TARGET/team.yaml" ]]; then
  echo "[init] - 跳过 team.yaml（已存在，不覆盖你的编制）"
else
  cp "$FRAMEWORK_DIR/core/team.schema.yaml" "$TARGET/team.yaml"
  echo "[init] ✓ team.yaml（基于默认编制，请按你的项目修改）"
fi

# 3) 把总线模板真正铺到 docs/agent-collaboration/（默认 bus.dir）
BUS_SRC="$FRAMEWORK_DIR/core/bus-templates"
BUS_DST="$TARGET/docs/agent-collaboration"
if [[ -d "$BUS_SRC" ]]; then
  mkdir -p "$BUS_DST"
  cp -Rn "$BUS_SRC/." "$BUS_DST/" 2>/dev/null || cp -R "$BUS_SRC/." "$BUS_DST/"
  echo "[init] ✓ 文件总线就位：${BUS_DST}（已有文件未覆盖）"
fi

# 4) .gitignore:目标是 git repo 时,追加框架建议忽略的项(已含则跳过)
if [[ -d "$TARGET/.git" ]]; then
  GI="$TARGET/.gitignore"
  touch "$GI"
  added=0
  for entry in ".loop-logs/" ".env" "*.env.local"; do
    if ! grep -qxF "$entry" "$GI" 2>/dev/null; then
      echo "$entry" >> "$GI"
      added=1
    fi
  done
  if [[ "$added" == "1" ]]; then
    echo "[init] ✓ .gitignore 已追加框架建议忽略项(.loop-logs/、.env、*.env.local)"
  else
    echo "[init] - .gitignore 已包含框架建议忽略项"
  fi
fi

cat <<'EOF'

[init] 骨架铺设完成。接下来：
  1. 确保依赖：python3 + PyYAML（pip install pyyaml）
  2. 用你的 agent 打开项目，运行 /setup-team。
     - init.sh 复制的 team.yaml 只是默认模板；project.name 仍是 my-project 时，
       /setup-team 会进入"登记模式"，引导你把编制配齐。
     - 不想定制时，一路采用默认 plan -> dev -> review 编制即可。
     - 字段注释见 core/team.schema.yaml；样例见 examples/README.md。
     - 改 roles 时,同步检查 handoff.next_role、handoff.on_done/transitions.state
       和 bus.ownership.owner,保持引用名一致。
  3. 生成 CLAUDE.md / AGENTS.md 后,关掉旧 worker 窗口再开新对话。
  4. 配置完成后开始第一个增量。

提醒：把 .loop-logs/、.env、本机私密配置加进目标项目的 .gitignore。
EOF

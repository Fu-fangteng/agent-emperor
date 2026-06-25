#!/usr/bin/env python3
"""
generate.py —— 多 Agent 协作框架的适配文件生成器（A 方案：生成式）

读项目根的 team.yaml，校验编制合法性，然后为每个 agent 的工具生成它原生吃的
适配文件（CC 的 CLAUDE.md 协作段、Codex 的 AGENTS.md），并铺好文件总线。

工具无关：本脚本只产出静态文件，不要求任何 agent 在运行时解析 yaml。
改了 team.yaml 重新跑一遍即可，这一步本身就是"配置一次、确认无误再开跑"的确认节点。

用法：
    python3 generate.py [--team team.yaml] [--target .] [--dry-run]

依赖：PyYAML（pip install pyyaml）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("[generate] 需要 PyYAML：pip install pyyaml")


# --------------------------------------------------------------------------
# 加载与校验
# --------------------------------------------------------------------------
KNOWN_TOOLS = {"claude-code", "codex", "cursor"}
GENERATED_TOOLS = {"claude-code", "codex"}  # cursor 仍是占位，先不生成

# 身份锚点的 10 种预设外壳。{id} 会被替换成「<产品/增量> · <role>」这个身份内核，
# {emoji} 仅 stamp/cat 用（来自 anchor.role_emoji，缺省 🐾）。
ANCHOR_STYLES = {
    "radio":    "📻 这里是「{id}」，本轮完毕，over～",
    "stamp":    "—— {emoji}「{id}」打卡下班，搬砖完毕。",
    "butler":   "🎩 您的「{id}」已为您效劳完毕，主人。",
    "save":     "💾 [{id}] 进度已保存，等待下一位玩家接棒。",
    "chunni":   "⚔️ 以「{id}」之名，本轮承诺已兑现。",
    "express":  "📦 「{id}」专递已送达，请签收～",
    "captain":  "✈️ 机长「{id}」播报：本段航程结束，感谢搭乘。",
    "cat":      "🐾 喵——{emoji}「{id}」干完活了，求摸头。",
    "wuxia":    "🥋 在下「{id}」，本轮告一段落，告辞。",
    "terminal": "[{id}] $ done ✓ — awaiting next handoff",
}
ANCHOR_USES_EMOJI = {"stamp", "cat"}
DEFAULT_ROLE_EMOJI = "🐾"


def load_team(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"[generate] 找不到 team 配置：{path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        sys.exit("[generate] team.yaml 顶层必须是映射（mapping）。")
    return data


def validate(team: dict) -> list[str]:
    """返回错误列表；空列表表示通过。"""
    errors: list[str] = []

    roles = team.get("roles") or []
    agents = team.get("agents") or []
    handoff = team.get("handoff") or []

    if not roles:
        errors.append("roles 段为空：至少声明一个 role。")
    if not agents:
        errors.append("agents 段为空：至少声明一个 agent。")

    role_set = set(roles)

    # agent 的 roles 必须在顶层 roles 里声明；tool 必须已知
    claimed: set[str] = set()
    for a in agents:
        name = a.get("name", "<未命名>")
        tool = a.get("tool")
        if tool not in KNOWN_TOOLS:
            errors.append(f"agent {name} 的 tool='{tool}' 未知（支持：{sorted(KNOWN_TOOLS)}）。")
        for r in a.get("roles", []):
            claimed.add(r)
            if r not in role_set:
                errors.append(f"agent {name} 担任的 role='{r}' 未在顶层 roles 声明。")

    # 顶层每个 role 至少被一个 agent 认领
    for r in roles:
        if r not in claimed:
            errors.append(f"role='{r}' 没有任何 agent 认领（没人干这活）。")

    # handoff 的 next_role 必须是已声明且被认领的 role（或 null 表示收尾）
    for h in handoff:
        state = h.get("state", "<无 state>")
        nxt = h.get("next_role", "__MISSING__")
        if nxt in (None, "null"):
            continue
        if nxt == "__MISSING__":
            errors.append(f"handoff 规则 state={state} 缺 next_role 字段。")
        elif nxt not in role_set:
            errors.append(f"handoff 规则 state={state} 的 next_role='{nxt}' 未在 roles 声明。")

    # anchor.style 必须是已知预设（缺 anchor 段时回退默认，不报错）
    anchor = team.get("anchor") or {}
    style = anchor.get("style", "stamp")
    if style not in ANCHOR_STYLES:
        errors.append(f"anchor.style='{style}' 未知（支持：{sorted(ANCHOR_STYLES)}）。")

    return errors


# --------------------------------------------------------------------------
# 渲染辅助：把 team.yaml 的信息整理成各 role 的读写范围
# --------------------------------------------------------------------------
def role_io(team: dict) -> dict[str, dict[str, list[str]]]:
    """从 bus.ownership 推导每个 role 读什么、写什么。"""
    bus = team.get("bus") or {}
    ownership = bus.get("ownership") or []
    io: dict[str, dict[str, list[str]]] = {}
    for r in team.get("roles", []):
        io[r] = {"writes": [], "reads": []}
    for o in ownership:
        owner = o.get("owner")
        f = o.get("file")
        if owner in io:
            io[owner]["writes"].append(f)
        # 非 owner 的 role 默认可读所有总线文件（读不冲突）
    for r, d in io.items():
        d["reads"] = [o.get("file") for o in ownership]
    return io


def handoff_for_agent(team: dict, agent: dict) -> list[dict]:
    """这个 agent 承担的 role 会触发哪些状态翻转。"""
    my_roles = set(agent.get("roles", []))
    # 当某状态轮到我担任的 role 时，我负责把它推进
    out = []
    for h in team.get("handoff", []):
        if h.get("next_role") in my_roles:
            out.append(h)
    return out


def anchor_example(team: dict, role: str, product: str = "<本增量>") -> str:
    """渲染某个 role 的锚点示例句（身份内核=product · role）。"""
    anchor = team.get("anchor") or {}
    style = anchor.get("style", "stamp")
    tmpl = ANCHOR_STYLES.get(style, ANCHOR_STYLES["stamp"])
    emoji = ""
    if style in ANCHOR_USES_EMOJI:
        role_emoji = anchor.get("role_emoji") or {}
        emoji = role_emoji.get(role, DEFAULT_ROLE_EMOJI)
    return tmpl.format(id=f"{product} · {role}", emoji=emoji)


def render_anchor_lines(team: dict, agent: dict) -> list[str]:
    """生成写进适配文件的「身份锚点」指令段。"""
    lines = [
        "## 身份锚点（每轮回复结尾必加）",
        "",
        "每轮回复的**最后一行**，固定加一句身份签名。格式：身份内核「<产品/增量> · <role>」套上固定外壳。",
        "你担任的 role 各举一例（把 <本增量> 换成用户告诉你的产品/增量名）：",
    ]
    for r in agent.get("roles", []):
        lines.append(f"- {r}：`{anchor_example(team, r)}`")
    lines += [
        "",
        "规矩：身份内核（产品 · role）不能省，外壳别乱改。一旦你某轮忘了加这行，",
        "就说明你可能丢了上下文——用户会回你「你是谁？」，届时重新声明身份并找回状态。",
    ]
    return lines


# --------------------------------------------------------------------------
# 渲染：Codex 的 AGENTS.md
# --------------------------------------------------------------------------
def render_agents_md(team: dict, agent: dict) -> str:
    bus_dir = (team.get("bus") or {}).get("dir", "docs/agent-collaboration")
    io = role_io(team)
    cfgs = ", ".join(team.get("config_files", []) or ["（无）"])
    lines = [
        "# AGENTS.md —— Codex 协作协议（由 team.yaml 生成，勿手改）",
        "",
        f"你在本仓库参与多 agent 协作开发。你是 agent **{agent.get('name')}**（tool: codex）。",
        f"你担任的 role：**{', '.join(agent.get('roles', []))}**。",
        "",
        "## 进仓库先做",
        f"1. 读 `{bus_dir}/START_HERE.md`。",
        f"2. 读 `{bus_dir}/phases/<当前phase>/handoff.md` 顶部 STATUS 块，确认是否轮到你。",
        "3. 轮到你才动手；没轮到，告诉用户当前轮到谁、该切到哪个 agent。",
        "",
        "## 你各 role 的读写范围",
    ]
    for r in agent.get("roles", []):
        writes = ", ".join(io.get(r, {}).get("writes", [])) or "（只读）"
        lines.append(f"- **{r}**：写 {writes}；其余总线文件只读。")
    lines += ["", "## 你负责的 STATUS 流转"]
    hf = handoff_for_agent(team, agent)
    if hf:
        for h in hf:
            gate = "（人工把关后）" if h.get("human_gate") else ""
            lines.append(f"- 当 STATUS={h.get('state')} 轮到你{gate} → 干活 → 完成后翻转到下一状态。")
    else:
        lines.append("- （无：你的 role 不在 handoff 的 next_role 中）")
    lines += [""] + render_anchor_lines(team, agent)
    lines += [
        "",
        "## 干完必做",
        "1. 更新 handoff.md 顶部 STATUS 块（状态、轮到谁、更新时间）。",
        "2. 给用户准备一段「转达 prompt」，指向下一个 agent：读哪些文件、做什么、",
        "   产出什么、设成什么 STATUS、关键约束（边界、不能动的文件）。",
        f"3. 不擅自改配置文件（{cfgs}），要动走交接说明。",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 渲染：Claude Code 的 CLAUDE.md 协作段
# --------------------------------------------------------------------------
def render_claude_md(team: dict, agent: dict) -> str:
    bus_dir = (team.get("bus") or {}).get("dir", "docs/agent-collaboration")
    io = role_io(team)
    cfgs = ", ".join(team.get("config_files", []) or ["（无）"])
    lines = [
        "<!-- 多 Agent 协作段（由 team.yaml 生成，勿手改此段） -->",
        "# 多 Agent 协作",
        "",
        f"你是 agent **{agent.get('name')}**（tool: claude-code），担任 role：**{', '.join(agent.get('roles', []))}**。",
        "",
        f"开始任何任务前，读 `{bus_dir}/START_HERE.md` 和当前 phase 的 handoff.md STATUS 块，确认是否轮到你。",
        "",
        "## 你各 role 的读写范围",
    ]
    for r in agent.get("roles", []):
        writes = ", ".join(io.get(r, {}).get("writes", [])) or "（只读）"
        lines.append(f"- **{r}**：写 {writes}；其余总线文件只读。")
    lines += [
        "",
        "## 可用触发器（skill）",
        "- `/plan <想法>` —— planner：调研、写 requirements + plan，STATUS → PLAN_REVIEW",
        "- `/review` —— reviewer：按 STATUS 圈范围审 diff、跑测、按 P0-P3 写 review",
        "- `/sync` —— 读总线对齐状态，告诉用户轮到谁、下一步",
        "",
    ]
    lines += render_anchor_lines(team, agent)
    lines += [
        "",
        "## 干完必做",
        "1. 更新 handoff.md 顶部 STATUS 块。",
        "2. 给用户准备一段「转达 prompt」指向下一个 agent。",
        f"3. 不擅自改配置文件（{cfgs}）。一个 role 一个独立对话，保上下文干净。",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="多 Agent 框架适配文件生成器")
    ap.add_argument("--team", default="team.yaml", help="team.yaml 路径")
    ap.add_argument("--target", default=".", help="生成到哪个项目根")
    ap.add_argument("--dry-run", action="store_true", help="只打印将生成什么，不落盘")
    args = ap.parse_args()

    team_path = Path(args.team)
    target = Path(args.target)
    team = load_team(team_path)

    errors = validate(team)
    if errors:
        print("[generate] team.yaml 校验未通过：", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("[generate] ✓ team.yaml 校验通过。")

    # 为每个 agent 生成其工具的适配文件
    planned: list[tuple[Path, str]] = []
    for agent in team.get("agents", []):
        tool = agent.get("tool")
        if tool not in GENERATED_TOOLS:
            print(f"[generate] - 跳过 {agent.get('name')}（tool={tool} 暂不生成）")
            continue
        if tool == "codex":
            planned.append((target / "AGENTS.md", render_agents_md(team, agent)))
        elif tool == "claude-code":
            planned.append((target / "CLAUDE.md", render_claude_md(team, agent)))

    for path, content in planned:
        if args.dry_run:
            print(f"[generate] [dry-run] 将写 {path}（{len(content)} 字节）")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"[generate] ✓ 写入 {path}")

    print("[generate] 完成。确认生成的适配文件无误后，再开始第一个增量。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

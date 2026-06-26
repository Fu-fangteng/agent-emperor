#!/usr/bin/env python3
"""
generate.py —— Agent Emperor 多 Agent 协作框架的适配文件生成器（A 方案：生成式）

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


def normalize_roles(team: dict) -> dict[str, dict]:
    """兼容 roles: [name] 与 roles: [{name, desc, can_write_code}] 两种写法。"""
    out: dict[str, dict] = {}
    for item in team.get("roles") or []:
        if isinstance(item, str):
            out[item] = {"name": item, "desc": "", "can_write_code": False}
        elif isinstance(item, dict):
            name = item.get("name")
            if name:
                out[name] = {
                    "name": name,
                    "desc": item.get("desc", ""),
                    "can_write_code": bool(item.get("can_write_code", False)),
                }
        else:
            continue
    return out


def role_names(team: dict) -> list[str]:
    return list(normalize_roles(team))


def role_source_permission(team: dict, role: str) -> str:
    role = normalize_roles(team).get(role, {})
    if role.get("can_write_code", False):
        return "✅ 可修改源代码。"
    return "🚫 **只读源代码，绝不修改任何源文件**。任何代码改动诉求，一律产出「打回给 developer 类角色」的转达 prompt，自己不动手。"


def project_name(team: dict) -> str:
    return (team.get("project") or {}).get("name") or "<项目名称>"


def validate(team: dict) -> list[str]:
    """返回错误列表；空列表表示通过。"""
    errors: list[str] = []
    warnings: list[str] = []

    role_defs = normalize_roles(team)
    roles = list(role_defs)
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

    if role_defs and not any(r.get("can_write_code", False) for r in role_defs.values()):
        warnings.append("没有任何 role 设置 can_write_code: true；这意味着没人被授权修改源代码。")

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

    validate.warnings = warnings
    return errors


# --------------------------------------------------------------------------
# 渲染辅助：把 team.yaml 的信息整理成各 role 的读写范围
# --------------------------------------------------------------------------
def role_io(team: dict) -> dict[str, dict[str, list[str]]]:
    """从 bus.ownership 推导每个 role 读什么、写什么。"""
    bus = team.get("bus") or {}
    ownership = bus.get("ownership") or []
    io: dict[str, dict[str, list[str]]] = {}
    for r in role_names(team):
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
        f"你担任的 role 各举一例（默认产品名来自 project.name：{project_name(team)}；转达 prompt 可临时覆盖）：",
    ]
    for r in agent.get("roles", []):
        lines.append(f"- {r}：`{anchor_example(team, r, project_name(team))}`")
    lines += [
        "",
        "规矩：身份内核（产品 · role）不能省，外壳别乱改。一旦你某轮忘了加这行，",
        "就说明你可能丢了上下文——用户会回你「你是谁？」，届时重新声明身份并找回状态。",
    ]
    return lines


def render_checkin_lines(team: dict, agent: dict) -> list[str]:
    """开场自检：接到转达 prompt 后，第一句先回执身份，证明已就位。"""
    return [
        "## 开场双重硬约束（接到转达 prompt 的第一件事）",
        "",
        "你被新开一个对话、收到一段「转达 prompt」时，先核对两条，任一不符就【立刻停手】，不要干活：",
        "",
        "1. **时序锁**：读 handoff.md 顶部 STATUS，确认当前轮到的 role 就是「我」。不是 → 停，回弹一句「现在轮到 <X>，不是我，请切到担任 <X> 的 agent」。",
        "2. **能力锁**：我要做的事是否在我角色职责内？尤其——若需要修改源代码而我的角色 `can_write_code=false`，停，回弹「改代码不归我（<我的 role>），应交给 developer 类角色」。",
        "",
        "即使用户在本窗口直接要求你做职责外的事，也要顶回去、不要照做——这是框架的安全约束，不是不配合。",
        "",
        "两条都通过后，第一句先回执，让用户确认你已就位：",
        "",
        "> 收到。我是「<产品/增量> · <role>」，已读 START_HERE 和 handoff.md，当前 STATUS=<X>，"
        "确认轮到我，开始干活。",
        "",
        "- 产品和 role 以转达 prompt 里指定的为准；STATUS 以 handoff.md 顶部为准。",
        f"- 默认产品名是 `{project_name(team)}`；若转达 prompt 指定了增量名，以 prompt 为准。",
    ]


def render_handoff_format_lines(team: dict) -> list[str]:
    """交接三段式：我（已完成）→ 指向谁 → 待复制 prompt。"""
    return [
        "## 转达 prompt 的标准格式（三段式）",
        "",
        "干完活给用户的交接，必须是「我 + 指向 + 待复制 prompt」三段，方便用户一眼看懂、直接复制：",
        "",
        "```",
        "✅ 我（<产品/增量> · <我的 role>）的活干完了：<一句话说清这轮产出>。",
        "👉 请把下面这段复制给 <下一个 role>（新开一个对话）：",
        "—————（复制从这里开始）—————",
        "你是「<产品/增量> · <下一个 role>」。读 <要读的文件>，做 <要做的事>，",
        "产出 <要产出什么>，完成后把 STATUS 设成 <目标状态>。约束：<边界、不能动的文件>。",
        "—————（复制到这里结束）—————",
        "```",
        "",
        "下一个 role 是谁，按 team.yaml 的 handoff 交接逻辑确定。流程收尾（next_role 为空）时，",
        "把第二、三段换成「本增量到此收尾，建议 commit 并归档」。",
    ]


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
    ]
    lines += render_checkin_lines(team, agent)
    lines += [
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
        desc = normalize_roles(team).get(r, {}).get("desc")
        desc_part = f"职责：{desc}；" if desc else ""
        lines.append(f"- **{r}**：{desc_part}写 {writes}；其余总线文件只读；{role_source_permission(team, r)}")
    lines += ["", "## 你负责的 STATUS 流转"]
    hf = handoff_for_agent(team, agent)
    if hf:
        for h in hf:
            gate = "（人工把关后）" if h.get("human_gate") else ""
            lines.append(f"- 当 STATUS={h.get('state')} 轮到你{gate} → 干活 → 完成后翻转到下一状态。")
    else:
        lines.append("- （无：你的 role 不在 handoff 的 next_role 中）")
    lines += [""] + render_anchor_lines(team, agent)
    lines += [""] + render_handoff_format_lines(team)
    lines += [
        "",
        "## 干完必做",
        "1. 更新 handoff.md 顶部 STATUS 块（状态、轮到谁、更新时间）。",
        "2. 按上面的三段式给用户准备「转达 prompt」，指向下一个 agent。",
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
    ]
    lines += render_checkin_lines(team, agent)
    lines += [
        "",
        "## 你各 role 的读写范围",
    ]
    for r in agent.get("roles", []):
        writes = ", ".join(io.get(r, {}).get("writes", [])) or "（只读）"
        desc = normalize_roles(team).get(r, {}).get("desc")
        desc_part = f"职责：{desc}；" if desc else ""
        lines.append(f"- **{r}**：{desc_part}写 {writes}；其余总线文件只读；{role_source_permission(team, r)}")
    lines += [
        "",
        "## 可用触发器（skill）",
        "- `/setup-team` —— 前台：未配置时登记编制；已配置时分拣请求并生成转达 prompt",
        "- `/act` —— 通用 worker：按 team.yaml + STATUS 执行当前轮到的 role",
        "- `/whoami` —— 当场自检：报我担任什么 role、是否轮到我、当前 STATUS、下一步",
        "- `/sync` —— 读总线对齐状态，告诉用户轮到谁、下一步",
        "",
    ]
    lines += render_anchor_lines(team, agent)
    lines += [""] + render_handoff_format_lines(team)
    lines += [
        "",
        "## 干完必做",
        "1. 更新 handoff.md 顶部 STATUS 块。",
        "2. 按上面的三段式给用户准备「转达 prompt」指向下一个 agent。",
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
    for w in getattr(validate, "warnings", []):
        print(f"[generate] ⚠ {w}")

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

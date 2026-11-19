#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 Saved/ue_audit 下的只读导出转成 Markdown 表格，供直接粘进文档。

用法（在工程根目录 D:\\UE5\\Chemistry\\aa 5.7 下执行）：

    python tools/audit_to_md.py                    # 全部，输出到 stdout
    python tools/audit_to_md.py --out out.md       # 写文件
    python tools/audit_to_md.py --section assets   # 只出资产分类
    python tools/audit_to_md.py --section actors   # 只出关卡 actor 统计

数据来源（由 RemoteControl / AssetRegistry 导出，只读）：
    00_class_counts.json   资产类型计数
    01_blueprints.json     全部 Blueprint 派生资产 [{path,name,class}]
    02_level_actors.json   关卡 actor 清单（含组件树）
    03_widgets.json        控件蓝图根控件

设计原则：只做「事实汇总」，不做解释。解释是你写文档的工作。
结构不确定的字段全部防御式读取，读不到就跳过，不抛异常。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

AUDIT_DIRS = [
    os.path.join("Saved", "ue_audit"),
    os.path.join("..", "aaa", "Saved", "ue_audit"),
]


def find_audit_dir() -> str:
    for d in AUDIT_DIRS:
        if os.path.isdir(d):
            return os.path.abspath(d)
    here = os.path.abspath(os.getcwd())
    for root, dirs, _ in os.walk(here):
        if os.path.basename(root) == "ue_audit":
            return root
    raise SystemExit("找不到 ue_audit 目录，请在工程根目录执行，或用 --audit-dir 指定")


def load_json(path: str):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def md_table(headers, rows) -> str:
    if not rows:
        return "_（无数据）_\n"
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out) + "\n"


def top_dir(path: str) -> str:
    """/Game/UI/BP/interact/x → /Game/UI"""
    parts = [p for p in str(path).split("/") if p]
    if len(parts) >= 3 and parts[0].lower() == "game":
        return "/".join(parts[:3])
    return "/".join(parts[:2]) if parts else "(unknown)"


def section_assets(audit: str) -> str:
    items = load_json(os.path.join(audit, "01_blueprints.json")) or []
    counts = load_json(os.path.join(audit, "00_class_counts.json"))
    out = ["## 资产分类（Blueprint 派生）\n"]

    if isinstance(counts, dict):
        rows = sorted(((k, v) for k, v in counts.items()), key=lambda x: -int(x[1] or 0))
        out.append("### 全资产类型计数\n")
        out.append(md_table(["类型", "数量"], [(k, v) for k, v in rows[:40]]))

    if isinstance(items, list) and items:
        by_class = Counter(str(i.get("class", "?")) for i in items)
        by_dir = Counter(top_dir(i.get("path", "")) for i in items)
        out.append("### 按目录\n")
        out.append(md_table(["目录", "数量"], sorted(by_dir.items(), key=lambda x: -x[1])))
        out.append("### 按类型\n")
        out.append(md_table(["类型", "数量"], sorted(by_class.items(), key=lambda x: -x[1])))
        out.append("### 交互点清单（/Game/UI/BP/interact）\n")
        rows = [(i.get("name"), i.get("path"))
                for i in items if "interact" in str(i.get("path", "")).lower()]
        out.append(md_table(["资产名", "路径"], rows))
    return "\n".join(out) + "\n"


def section_actors(audit: str) -> str:
    data = load_json(os.path.join(audit, "02_level_actors.json"))
    if not data:
        return "## 关卡 Actor\n\n_（无 02_level_actors.json）_\n"
    actors = data.get("actors", []) if isinstance(data, dict) else data
    world = data.get("world", "") if isinstance(data, dict) else ""
    out = [f"## 关卡 Actor（{len(actors)} 个）\n", f"world: `{world}`\n"]

    by_cls = Counter(str(a.get("cls") or a.get("class") or "?") for a in actors)
    out.append("### 按类型\n")
    out.append(md_table(["类型", "数量"], sorted(by_cls.items(), key=lambda x: -x[1])))

    by_folder = Counter(str(a.get("folder") or "(未分组)") for a in actors)
    out.append("### 按 Outliner 文件夹\n")
    out.append(md_table(["文件夹", "数量"], sorted(by_folder.items(), key=lambda x: -x[1])))

    bp = [(a.get("label"), a.get("cls_path") or a.get("cls")) for a in actors
          if str(a.get("cls", "")).startswith("BP_")
          or "BlueprintGeneratedClass" in str(a.get("cls_path", ""))]
    if bp:
        out.append("### 蓝图实例\n")
        out.append(md_table(["实例名", "类路径"], bp))

    rows = [(a.get("label"), len(a.get("comps") or []),
             ", ".join(str(c) for c in (a.get("comps") or []))[:120]) for a in actors]
    rows.sort(key=lambda r: -r[1])
    out.append("### 组件数 Top 20\n")
    out.append(md_table(["实例", "组件数", "组件"], rows[:20]))
    return "\n".join(out) + "\n"


def section_materials(audit: str) -> str:
    stats_dir = os.path.join(os.path.dirname(audit), "MaterialStats")
    if not os.path.isdir(stats_dir):
        return "## 材质统计\n\n_（无 Saved/MaterialStats）_\n"
    files = sorted(os.listdir(stats_dir))
    if not files:
        return "## 材质统计\n\n_（目录为空）_\n"
    latest = os.path.join(stats_dir, files[-1])
    out = [f"## 材质统计（最新：{files[-1]}）\n"]
    try:
        with open(latest, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        out.append("```text\n" + "\n".join(lines[:20]) + "\n```\n")
    except OSError as e:
        out.append(f"_读取失败：{e}_\n")
    return "\n".join(out) + "\n"


SECTIONS = {
    "assets": section_assets,
    "actors": section_actors,
    "materials": section_materials,
}


def main() -> None:
    ap = argparse.ArgumentParser(description="ue_audit JSON → Markdown")
    ap.add_argument("--audit-dir", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--section", choices=sorted(SECTIONS) + ["all"], default="all")
    args = ap.parse_args()

    audit = args.audit_dir or find_audit_dir()
    keys = list(SECTIONS) if args.section == "all" else [args.section]

    chunks = [f"<!-- 由 tools/audit_to_md.py 生成，数据源：{audit} -->\n"]
    for k in keys:
        try:
            chunks.append(SECTIONS[k](audit))
        except Exception as e:  # 单节失败不影响其它节
            chunks.append(f"## {k}\n\n_生成失败：{e!r}_\n")
    text = "\n".join(chunks)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"written: {args.out}  ({len(text)} chars)")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

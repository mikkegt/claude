#!/usr/bin/env python3
"""
Claude Codeのセッションtranscriptを集計してツール/スキル使用パターンを可視化する。

参考: https://qiita.com/masato_makino/items/5807d80a026d8dbd82ad
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"


def find_sessions(project=None, days=None):
    """対象セッション(JSONL)のリストを返す。"""
    if not PROJECTS_DIR.exists():
        print(f"Error: {PROJECTS_DIR} not found", file=sys.stderr)
        sys.exit(1)

    cutoff = None
    if days is not None:
        cutoff = datetime.now() - timedelta(days=days)

    sessions = []
    project_dirs = (
        [PROJECTS_DIR / d for d in os.listdir(PROJECTS_DIR) if project in d]
        if project
        else [PROJECTS_DIR / d for d in os.listdir(PROJECTS_DIR)]
    )

    for pdir in project_dirs:
        if not pdir.is_dir():
            continue
        for f in pdir.glob("*.jsonl"):
            if cutoff:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    continue
            sessions.append({"path": f, "project": pdir.name})

    return sessions


def parse_session(session_info):
    """1セッションのJSONLからtool_use/tool_resultペアを抽出する。"""
    filepath = session_info["path"]
    tool_uses = {}
    tool_results = {}

    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message", {})
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content", [])
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "tool_use":
                        tool_uses[c.get("id")] = {
                            "name": c.get("name", "unknown"),
                            "input": c.get("input", {}),
                        }
                    elif c.get("type") == "tool_result":
                        tool_results[c.get("tool_use_id")] = {
                            "is_error": c.get("is_error", False),
                        }
    except (OSError, IOError) as e:
        print(f"Warning: cannot read {filepath}: {e}", file=sys.stderr)
        return []

    entries = []
    for tid, tu in tool_uses.items():
        tr = tool_results.get(tid, {})
        entries.append({
            "tool": tu["name"],
            "input": tu.get("input", {}),
            "is_error": tr.get("is_error"),
            "has_result": tid in tool_results,
        })
    return entries


def aggregate(entries):
    """ツール名ごとに集計する。"""
    stats = defaultdict(lambda: {"total": 0, "ok": 0, "fail": 0, "unknown": 0})
    for e in entries:
        s = stats[e["tool"]]
        s["total"] += 1
        if not e["has_result"]:
            s["unknown"] += 1
        elif e["is_error"]:
            s["fail"] += 1
        else:
            s["ok"] += 1
    return stats


def extract_skill_invocations(entries):
    """Skillツールの呼び出しからskill名を抽出する。"""
    skill_stats = defaultdict(lambda: {"total": 0, "ok": 0, "fail": 0, "unknown": 0})
    for e in entries:
        if e["tool"] != "Skill":
            continue
        skill_name = e["input"].get("skill", "unknown") if isinstance(e["input"], dict) else "unknown"
        s = skill_stats[skill_name]
        s["total"] += 1
        if not e["has_result"]:
            s["unknown"] += 1
        elif e["is_error"]:
            s["fail"] += 1
        else:
            s["ok"] += 1
    return skill_stats


def print_report(title, stats, top=None):
    if not stats:
        print(f"\n=== {title}: no data ===")
        return

    total_calls = sum(s["total"] for s in stats.values())
    print(f"\n=== {title} ({total_calls} calls, {len(stats)} unique) ===")
    print(f"{'Name':<30} {'Total':>6} {'OK':>6} {'Fail':>6} {'?':>4} {'Fail%':>6}")
    print("-" * 64)

    sorted_items = sorted(stats.items(), key=lambda kv: -kv[1]["total"])
    if top:
        sorted_items = sorted_items[:top]

    for name, s in sorted_items:
        denom = s["ok"] + s["fail"]
        fail_pct = (s["fail"] / denom * 100) if denom > 0 else 0
        print(
            f"{name[:30]:<30} {s['total']:>6} {s['ok']:>6} {s['fail']:>6} "
            f"{s['unknown']:>4} {fail_pct:>5.0f}%"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="特定プロジェクトのみ集計（部分マッチ）")
    parser.add_argument("--days", type=int, help="過去N日のみ集計")
    parser.add_argument("--top", type=int, help="上位N件のみ表示")
    args = parser.parse_args()

    sessions = find_sessions(project=args.project, days=args.days)
    if not sessions:
        print("対象セッションが見つかりませんでした", file=sys.stderr)
        sys.exit(1)

    print(f"集計対象: {len(sessions)} sessions", file=sys.stderr)

    all_entries = []
    for s in sessions:
        all_entries.extend(parse_session(s))

    print(f"ツール呼び出し: {len(all_entries)} 件", file=sys.stderr)

    tool_stats = aggregate(all_entries)
    print_report("Tool Calls", tool_stats, top=args.top)

    skill_stats = extract_skill_invocations(all_entries)
    print_report("Skill Invocations", skill_stats, top=args.top)


if __name__ == "__main__":
    main()

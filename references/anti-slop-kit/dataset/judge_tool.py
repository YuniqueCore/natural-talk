#!/usr/bin/env python3
"""judge_tool.py — 偏好对裁决工具：候选 → 裁决记录 → 并入 pairs 数据集。

RLAIF/RFHL 共用同一条通路：裁决者（LLM 裁判或人类）对候选对逐条给出裁决记录，
本工具把裁决并入 pairs 文件。字段语义与 dataset/README.md 的 schema 一致。

用法：
  # 1) 生成待评批次（可选：人类标注者用它导出审阅清单）
  python3 judge_tool.py emit --candidates candidates.jsonl --ids id1,id2 --out batch.jsonl

  # 2) 并入裁决（替换同 id 记录或追加）
  python3 judge_tool.py merge --candidates candidates.jsonl --judgments judgments.jsonl \
      --into pairs-en.jsonl

裁决记录（judgments.jsonl 每行一条）：
  {"id": "en-hc3-...", "slop_good": 1, "slop_bad": 6, "reason": "...",
   "confidence": 0.85, "split": "train",
   "tells_bad": ["hedges"],          // 可省：默认用候选的机械 top_cats
   "tells_good": []}                  // 可省：默认空

纯函数核心 + IO 边界分离；不联网。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

JUDGE_MODEL_DEFAULT = "GLM-5.3-Flash (RLAIF, agent session)"
JUDGE_DATE_DEFAULT = "2026-09-25"


def load_jsonl(path: Path) -> list:
    records = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{lineno}: JSON 解析失败 {e}")
    return records


def build_pair(candidate: dict, judgment: dict, judge_model: str, judge_date: str) -> dict:
    """候选 + 裁决 -> 完整 pairs 记录。纯函数。"""
    return {
        "id": candidate["id"],
        "lang": candidate["lang"],
        "domain": candidate["domain"],
        "source": candidate["source"],
        "license": candidate["license"],
        "question": candidate["question"],
        "good": {"text": candidate["good"]["text"], "who": candidate["good"]["who"]},
        "bad": {
            "text": candidate["bad"]["text"],
            "who": candidate["bad"]["who"],
            "patterns": judgment.get("tells_bad",
                                     candidate["mech"]["bad"]["top_cats"]),
        },
        "judge": {
            "model": judgment.get("judge_model", judge_model),
            "date": judgment.get("judge_date", judge_date),
            "slop": {"good": judgment["slop_good"], "bad": judgment["slop_bad"]},
            "top_tells": {"good": judgment.get("tells_good", []),
                          "bad": judgment.get("tells_bad",
                                              candidate["mech"]["bad"]["top_cats"])},
            "reason": judgment["reason"],
            "confidence": judgment["confidence"],
        },
        "split": judgment.get("split", "train"),
    }


def merge_records(pairs_path: Path, new_pairs: list) -> dict:
    """按 id 替换或追加，返回统计。"""
    existing = {}
    if pairs_path.exists():
        existing = {json.loads(l)["id"]: json.loads(l)
                    for l in open(pairs_path, encoding="utf-8") if l.strip()}
    replaced = 0
    for pair in new_pairs:
        if pair["id"] in existing:
            replaced += 1
        existing[pair["id"]] = pair
    with open(pairs_path, "w", encoding="utf-8") as fh:
        for pair in existing.values():
            fh.write(json.dumps(pair, ensure_ascii=False) + "\n")
    return {"written": len(existing), "replaced": replaced,
            "appended": len(new_pairs) - replaced}


def emit_batch(candidates: list, ids: set, out_path: Path) -> int:
    """导出待审阅批次。"""
    n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for c in candidates:
            if ids and c["id"] not in ids:
                continue
            fh.write(json.dumps({
                "id": c["id"], "question": c["question"],
                "good_text": c["good"]["text"], "bad_text": c["bad"]["text"],
                "mech": c["mech"],
                "instruction": "按 dataset/judge_prompt.md 打分：slop 0-10、"
                               "top_tells、一句话证据、confidence。",
            }, ensure_ascii=False) + "\n")
            n += 1
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="偏好对裁决工具（RLAIF/RFHL 共用）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_emit = sub.add_parser("emit", help="从候选导出待评批次")
    p_emit.add_argument("--candidates", required=True)
    p_emit.add_argument("--ids", default="", help="逗号分隔；空 = 全部")
    p_emit.add_argument("--out", default="batch.jsonl")

    p_merge = sub.add_parser("merge", help="把裁决并入 pairs 文件")
    p_merge.add_argument("--candidates", required=True)
    p_merge.add_argument("--judgments", required=True)
    p_merge.add_argument("--into", required=True, help="pairs-*.jsonl 目标文件")

    args = ap.parse_args(argv)

    if args.cmd == "emit":
        candidates = load_jsonl(Path(args.candidates))
        ids = {i for i in args.ids.split(",") if i}
        n = emit_batch(candidates, ids, Path(args.out))
        print(f"emit: {n} 条 -> {args.out}")
        return 0

    candidates = {c["id"]: c for c in load_jsonl(Path(args.candidates))}
    judgments = load_jsonl(Path(args.judgments))
    new_pairs, problems = [], []
    for j in judgments:
        c = candidates.get(j.get("id"))
        if c is None:
            problems.append(f"未知候选 id: {j.get('id')}")
            continue
        for field in ("slop_good", "slop_bad", "reason", "confidence"):
            if field not in j:
                problems.append(f"{j.get('id')}: 缺字段 {field}")
        new_pairs.append(build_pair(c, j, JUDGE_MODEL_DEFAULT, JUDGE_DATE_DEFAULT))
    if problems:
        for p in problems:
            print("judge_tool:", p, file=sys.stderr)
        return 2
    stats = merge_records(Path(args.into), new_pairs)
    print(f"merge -> {args.into}: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

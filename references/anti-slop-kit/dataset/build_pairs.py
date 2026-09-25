#!/usr/bin/env python3
"""build_pairs.py — 从 HF datasets-server 的 HC3 行数据构建 slop 偏好对候选。

流程（RLAIF 数据管线第一步）：
1. 手工下载数据（脚本不联网，保持纯函数核心）：
   curl -sL "https://datasets-server.huggingface.co/rows?dataset=Hello-SimpleAI/HC3-Chinese&config=open_qa&split=train&offset=0&length=100" -o hc3zh-open_qa.json
   （其余 config 同理，文件名前缀 hc3zh- / hc3en-）
2. 本脚本扫描行数据，逐条产出 (human_answer, chatgpt_answer) 候选对，
   用 slop_check.scan 做机械 slop 对比度排序，输出 candidates.jsonl。
3. 人工/裁判复核 candidates.jsonl，把选中的条目整理进 pairs-zh.jsonl / pairs-en.jsonl
   并补 judge 打分（schema 见同目录 README.md）。

候选排序是辅助不是裁决：机械分数高只说明「值得看」，选对与打分都走 judge_prompt.md。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from slop_check import load_packs, scan  # noqa: E402

PACKS = load_packs(Path(__file__).resolve().parent.parent / "scripts" / "data")

# 两侧文本裁剪边界：太短没有风格信号，太长会让裁判上下文爆炸
MIN_CHARS = 60
MAX_CHARS = 1500


def trim(text: str, limit: int = MAX_CHARS) -> str:
    """超长文本按自然边界截断（段落 > 句号 > 英文句点）。

    只负责截断：过短文本的过滤由 extract_candidates 的 MIN_CHARS 下限负责。
    限制长度内找不到任何自然边界时返回 None——中段硬截会制造伪结尾，
    宁缺毋滥。
    """
    if not text:
        return None
    text = text.strip()
    if len(text) <= limit:
        return text or None
    cut = text[:limit]
    keeper = max(cut.rfind("\n\n"), cut.rfind("。"), cut.rfind(". "))
    if keeper < 0:
        return None
    return cut[: keeper + 1]


def side_score(text: str) -> dict:
    r = scan(text, PACKS)
    return {"score": r.score, "band": r.band, "units": r.units,
            "top_cats": _top_categories(r)}


def _top_categories(report, limit: int = 4) -> list:
    weight = {}
    for f in report.findings:
        if f.evidence:
            weight[f.category] = weight.get(f.category, 0) + f.weight
    return sorted(weight, key=weight.get, reverse=True)[:limit]


def extract_candidates(payload: dict, lang: str, config: str, license_name: str) -> list:
    """行数据 -> 候选对（纯函数）。"""
    dataset_id = ("Hello-SimpleAI/HC3-Chinese" if lang == "zh"
                  else "Hello-SimpleAI/HC3")
    out = []
    for item in payload.get("rows", []):
        row = item.get("row", {})
        answers = [
            ("human", row.get("human_answers") or []),
            ("chatgpt", row.get("chatgpt_answers") or []),
        ]
        picked = {}
        for who, texts in answers:
            for t in texts:
                trimmed = trim(t)
                if trimmed and len(trimmed) >= MIN_CHARS:
                    picked[who] = trimmed
                    break
        if "human" not in picked or "chatgpt" not in picked:
            continue
        question = (row.get("question") or "").strip()
        if len(question) > 300:
            question = question[:300] + "…"
        good, bad = picked["human"], picked["chatgpt"]
        out.append({
            "id": f"{lang}-hc3-{config}-{row.get('id', len(out))}",
            "lang": lang,
            "domain": config,
            "source": f"{dataset_id}#{config}/row:{row.get('id')}",
            "license": license_name,
            "question": question,
            "good": {"text": good, "who": "human"},
            "bad": {"text": bad, "who": "chatgpt"},
            "mech": {"good": side_score(good), "bad": side_score(bad)},
        })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="HC3 行数据 -> slop 偏好对候选")
    ap.add_argument("rows_dir", help="含 hc3*.json 的目录")
    ap.add_argument("--out", default="candidates.jsonl")
    ap.add_argument("--per-file", type=int, default=10,
                    help="每个文件按机械对比度取前 N 条")
    args = ap.parse_args(argv)

    rows_dir = Path(args.rows_dir)
    files = sorted(rows_dir.glob("hc3*.json"))
    if not files:
        print(f"build_pairs: {rows_dir} 下没有 hc3*.json", file=sys.stderr)
        return 2

    all_pairs = []
    for path in files:
        stem = path.stem  # hc3zh-open_qa 或带下载偏移的 hc3zh-open_qa-o100
        lang, config = stem[3:5], re.sub(r"-o\d+$", "", stem[5:]).lstrip("-")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"build_pairs: 跳过 {path.name}: {e}", file=sys.stderr)
            continue
        cands = extract_candidates(payload, lang, config, "CC BY-SA 4.0")
        cands.sort(key=lambda c: c["mech"]["bad"]["score"] - c["mech"]["good"]["score"],
                   reverse=True)
        all_pairs.extend(cands[: args.per_file])

    with open(args.out, "w", encoding="utf-8") as fh:
        for pair in all_pairs:
            fh.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"build_pairs: {len(all_pairs)} candidates -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

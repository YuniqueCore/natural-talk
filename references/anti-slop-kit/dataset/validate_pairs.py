#!/usr/bin/env python3
"""validate_pairs.py — 校验偏好对数据集（纯函数核心 + IO 边界）。

检查四类不变量：
1. schema：必填字段齐全、slop/confidence 取值范围。
2. 词库一致性：bad.patterns 的类别 id 必须存在于同语言词库（单一数据源交叉验证）。
3. 偏好方向：slop(good) <= slop(bad)；不满足的必须显式标记 split=hard。
4. 唯一性：id 不重复。

用法：python3 validate_pairs.py pairs-zh.jsonl pairs-en.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from slop_check import load_pack, DATA_DIR  # noqa: E402

REQUIRED_TEXT_LEN = {"zh": 12, "en": 30}  # 中文单字信息密度高，句级对按 12 字起
HARD_SPLIT = "hard"


def load_category_ids(data_dir: Path = DATA_DIR) -> dict:
    """语言 -> 该语言词库全部类别 id 集合。"""
    ids = {}
    for f in ("zh.json", "en.json"):
        pack = load_pack(data_dir / f)
        ids[pack.lang] = set(pack.categories)
    return ids


def validate_pair(pair: dict, lang: str, category_ids: set, seen: set) -> list:
    """单条校验，返回问题列表（空列表 = 通过）。纯函数。

    category_ids 必须是「该语言」的类别集合（调用方负责按语言取）。
    """
    problems = []
    min_len = REQUIRED_TEXT_LEN[lang]

    def need(path: str, cond: bool, detail: str = ""):
        if not cond:
            problems.append(f"{path}: {detail or '缺失或不合法'}")

    pid = pair.get("id", "<missing id>")
    need("id", bool(pid) and pid not in seen, "重复 id" if pid in seen else "缺失")
    seen.add(pid)
    need("lang", pair.get("lang") == lang, f"应为 {lang}")
    need("license", bool(pair.get("license")))
    need("source", bool(pair.get("source")))

    for side in ("good", "bad"):
        text = pair.get(side, {}).get("text", "")
        need(f"{side}.text", len(text) >= min_len,
             f"长度 {len(text)} < {min_len}")
        who = pair.get(side, {}).get("who")
        need(f"{side}.who", bool(who))

    judge = pair.get("judge", {})
    slop = judge.get("slop", {})
    for side in ("good", "bad"):
        v = slop.get(side)
        need(f"judge.slop.{side}", isinstance(v, int) and 0 <= v <= 10, f"值 {v}")
    conf = judge.get("confidence")
    need("judge.confidence", isinstance(conf, (int, float)) and 0 <= conf <= 1, f"值 {conf}")
    need("judge.model", bool(judge.get("model")), "裁判必须留名（RLAIF 溯源）")

    for p in pair.get("bad", {}).get("patterns", []):
        need("bad.patterns", p in category_ids, f"{p} 不在 {lang} 词库类别中")

    gs, bs = slop.get("good", 0), slop.get("bad", 0)
    if isinstance(gs, int) and isinstance(bs, int) and gs > bs:
        need("split", pair.get("split") == HARD_SPLIT,
             f"slop(good)={gs} > slop(bad)={bs}，必须标记 split={HARD_SPLIT}")
    need("split", pair.get("split") in ("train", "val", HARD_SPLIT),
         str(pair.get("split")))
    return problems


def validate_file(path: Path, category_ids: set) -> tuple:
    """返回 (问题列表, 统计)。"""
    lang = "zh" if path.stem.startswith("pairs-zh") else "en"
    problems, seen = [], set()
    stats = {"lang": lang, "pairs": 0, "slop_bad_sum": 0, "conf_sum": 0, "splits": {}}
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                pair = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"{path.name}:{lineno}: JSON 解析失败 {e}")
                continue
            for p in validate_pair(pair, lang, category_ids[lang], seen):
                problems.append(f"{path.name}:{lineno}: {p}")
            stats["pairs"] += 1
            stats["slop_bad_sum"] += pair.get("judge", {}).get("slop", {}).get("bad", 0)
            stats["conf_sum"] += pair.get("judge", {}).get("confidence", 0)
            sp = pair.get("split", "?")
            stats["splits"][sp] = stats["splits"].get(sp, 0) + 1
    return problems, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="偏好对数据集校验")
    ap.add_argument("files", nargs="+", help="pairs-*.jsonl")
    args = ap.parse_args(argv)

    category_ids = load_category_ids()
    all_problems = []
    for name in args.files:
        problems, stats = validate_file(Path(name), category_ids)
        avg_slop = stats["slop_bad_sum"] / stats["pairs"] if stats["pairs"] else 0
        avg_conf = stats["conf_sum"] / stats["pairs"] if stats["pairs"] else 0
        print(f"{name}: {stats['pairs']} pairs | splits {stats['splits']} | "
              f"avg slop(bad) {avg_slop:.1f} | avg conf {avg_conf:.2f}")
        all_problems.extend(problems)

    if all_problems:
        print(f"\n{len(all_problems)} 个问题:", file=sys.stderr)
        for p in all_problems:
            print(" ", p, file=sys.stderr)
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

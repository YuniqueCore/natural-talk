#!/usr/bin/env python3
"""slop_check.py — AI slop 候选信号检测器（词库 + 正则，确定性、无网络、无模型）。

定位：找出**值得人工/LLM 复核的候选信号**，不是作者鉴定器。
命中 ≠ 成立：引用原话、行业术语、有意修辞受保护，判断规则见 SKILL.md 与 references/。

用法：
    python3 slop_check.py FILE...            # 文本报告
    python3 slop_check.py - < text           # 从 stdin 读
    python3 slop_check.py FILE --json        # JSON 输出
    python3 slop_check.py FILE --fail-on heavy   # CI：达到阈值时退出码 1

数据：data/zh.json 与 data/en.json 是唯一词库来源；两侧同时扫描，
     按语言分别归组，互不干扰。
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Pattern

DATA_DIR = Path(__file__).resolve().parent / "data"
PACK_FILES = ("zh.json", "en.json")

SCORE_BANDS = ("clean", "light", "noticeable", "heavy")
BAND_UPPER = ((2.0, "light"), (5.0, "noticeable"))  # score < upper -> band; else heavy
CONTEXT_WIDTH = 24
FAIL_LEVELS = SCORE_BANDS


# ---------------------------------------------------------------- 数据模型

@dataclass(frozen=True)
class Entry:
    """词库最小单元：一个正则 + 权重 + 触发模式。"""
    regex: Pattern[str]
    category: str
    label: str
    weight: int
    mode: str            # plain | cluster | density
    cluster_min: int
    cluster_w: int       # cluster 升级后计的权重
    density_min: int
    density_w: int       # density 达阈值后计的权重
    note: str
    fix: str
    evidence: bool       # False = 仅清晰度建议，不计入评分


@dataclass(frozen=True)
class SlopPack:
    lang: str
    version: str
    categories: dict     # id -> {"label": str, "note": str}
    entries: tuple


@dataclass
class Finding:
    lang: str
    category: str
    label: str
    match: str
    line: int
    col: int
    context: str
    weight: int
    evidence: bool
    note: str
    fix: str

    @property
    def where(self) -> str:
        return f"L{self.line}C{self.col}"


@dataclass
class Report:
    findings: list = field(default_factory=list)
    units: int = 0
    score: float = 0.0
    band: str = "clean"


# ---------------------------------------------------------------- 词库装载

def load_pack(path: Path) -> SlopPack:
    """把 JSON 词库编译为可用规则包。词库 JSON 是唯一数据源。"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    meta, categories = raw["meta"], raw["categories"]
    entries = []
    for cat in categories:
        for e in cat["entries"]:
            flags = re.UNICODE
            for fl in e.get("flags", []):
                flags |= getattr(re, fl)
            entries.append(Entry(
                regex=re.compile(e["p"], flags),
                category=cat["id"],
                label=cat["label"],
                weight=e.get("w", 0),
                mode=e.get("mode", "plain"),
                cluster_min=e.get("cluster_min", 1),
                cluster_w=e.get("cluster_w", e.get("w", 0)),
                density_min=e.get("density_min", 1),
                density_w=e.get("density_w", e.get("w", 0)),
                note=e.get("note", ""),
                fix=e.get("fix", ""),
                evidence=e.get("evidence", True),
            ))
    return SlopPack(
        lang=meta["lang"],
        version=meta["version"],
        categories={c["id"]: {"label": c["label"], "note": c["note"]} for c in categories},
        entries=tuple(entries),
    )


def load_packs(data_dir: Path = DATA_DIR) -> list:
    return [load_pack(data_dir / name) for name in PACK_FILES]


# ---------------------------------------------------------------- 纯函数核心

# 代码围栏 / 行内代码 / URL：结构化内容，不做扫描。
CODE_FENCE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://\S+|\b[\w.-]+@[\w.-]+\.\w+\b")


def protect(text: str) -> str:
    """把非正文区替换为等长占位，保证偏移与行号不变。"""
    def blank(m: re.Match) -> str:
        return "\n" * m.group().count("\n") + "·" * (len(m.group()) - m.group().count("\n"))
    return URL.sub(blank, INLINE_CODE.sub(blank, CODE_FENCE.sub(blank, text)))


def split_paragraphs(scannable: str) -> list:
    """按空行分段，返回 [(start_offset, paragraph_text)]。"""
    paras, start = [], 0
    for m in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]*)*", scannable):
        paras.append((m.start(), m.group()))
    return paras


def line_col(scannable: str, offset: int) -> tuple:
    line = scannable.count("\n", 0, offset) + 1
    col = offset - (scannable.rfind("\n", 0, offset) + 1) + 1
    return line, col


def excerpt(scannable: str, start: int, end: int) -> str:
    lo, hi = max(0, start - CONTEXT_WIDTH), min(len(scannable), end + CONTEXT_WIDTH)
    ctx = scannable[lo:hi].replace("\n", " ")
    return f"…{ctx}…"


def collect_matches(entries, scannable: str) -> list:
    """第一遍扫描：每个词条在正文里的全部命中（含权重，未升级）。"""
    hits = []  # (entry, start, end, match_text)
    for e in entries:
        for m in e.regex.finditer(scannable):
            hits.append((e, m.start(), m.end(), m.group()))
    hits.sort(key=lambda h: (h[1], -(h[2] - h[1])))
    return hits


def dedupe(hits: list) -> list:
    """重叠去重：同一位置保留更长的匹配（如「综上所述」压过「总之」）。"""
    kept, last_end, last_start = [], -1, -1
    for e, s, t, txt in hits:
        if s < last_end and s >= last_start:
            continue
        kept.append((e, s, t, txt))
        last_start, last_end = s, t
    return kept


def escalate(entries, hits: list, paragraphs: list) -> list:
    """cluster / density 模式升级：达标才产生 finding，未达标静默。

    cluster 语义（对齐 avoid-ai-writing Tier 2 与 qu-ai-wei「密集才处理」）：
    同一段落内出现 >= cluster_min 个【同类目不同词条】时，该段内所有
    cluster 词条命中一并报告；孤立的单词不构成信号。
    """
    para_of = [s for s, _ in paragraphs]

    by_rule = {}
    for h in hits:
        by_rule.setdefault(id(h[0]), []).append(h)

    def pidx_of(offset: int) -> int:
        return bisect.bisect_right(para_of, offset) - 1

    # 先按类目统计每段出现的不同词条集合
    cat_para_entries: dict = {}
    for e in entries:
        if e.mode != "cluster":
            continue
        for h in by_rule.get(id(e), []):
            cat_para_entries.setdefault(e.category, {}) \
                            .setdefault(pidx_of(h[1]), set()).add(id(e))

    findings = []
    for e in entries:
        group = by_rule.get(id(e), [])
        if not group:
            continue
        if e.mode == "plain":
            findings.extend((e, s, t, txt, e.weight) for _, s, t, txt in group)
        elif e.mode == "cluster":
            para_entries = cat_para_entries.get(e.category, {})
            for h in group:
                if len(para_entries.get(pidx_of(h[1]), set())) >= e.cluster_min:
                    findings.append((e, *h[1:], e.cluster_w))
        elif e.mode == "density":
            if len(group) >= e.density_min:
                findings.extend((e, s, t, txt, e.density_w)
                                for _, s, t, txt in group)
    return findings


def count_units(text: str) -> int:
    """评分单位：CJK 字符 + 拉丁词。"""
    cjk = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
    latin = len(re.findall(r"[A-Za-z]+", text))
    return max(cjk + latin, 1)


def score_band(score: float) -> str:
    if score <= 0:
        return "clean"
    for upper, band in BAND_UPPER:
        if score < upper:
            return band
    return "heavy"


def scan(text: str, packs: list) -> Report:
    """主入口：文本 -> 报告。纯函数，不触 IO。"""
    scannable = protect(text)
    paragraphs = split_paragraphs(scannable)
    findings: list = []
    for pack in packs:
        hits = dedupe(collect_matches(pack.entries, scannable))
        upgraded = escalate(pack.entries, hits, paragraphs)
        for e, s, t, txt, w in upgraded:
            line, col = line_col(scannable, s)
            findings.append(Finding(
                lang=pack.lang, category=e.category, label=e.label,
                match=txt[:40], line=line, col=col,
                context=excerpt(scannable, s, t),
                weight=w, evidence=e.evidence, note=e.note, fix=e.fix,
            ))
    findings.sort(key=lambda f: (f.line, f.col))
    units = count_units(text)
    weight_sum = sum(f.weight for f in findings if f.evidence)
    score = round(weight_sum * 1000 / units, 1)
    return Report(findings=findings, units=units, score=score,
                  band=score_band(score))


# ---------------------------------------------------------------- 渲染（文本输出）

def render_text(report: Report, sources_note: str = "") -> str:
    out = ["== AI slop 检测报告 =="]
    n = len(report.findings)
    out.append(f"命中: {n} 处候选信号 | 单位: {report.units} 字/词 | "
               f"评分: {report.score}/千单位 ({report.band})")
    if n == 0:
        out.append("未发现候选信号。正常文本可以直接返回，不需要为了改而改。")
        return "\n".join(out)

    by_cat = {}
    for f in report.findings:
        by_cat.setdefault((f.lang, f.category, f.label), []).append(f)
    for (lang, cat, label), items in by_cat.items():
        weights = {i.weight for i in items}
        evidence = all(i.evidence for i in items)
        tag = f"w{max(weights)}" if evidence else "建议(不计分)"
        out.append(f"\n[{lang}] {label} ×{len(items)} ({tag})")
        for f in items:
            out.append(f"  {f.where}  「{f.match}」")
            if f.note:
                out.append(f"      note: {f.note}")
            if f.fix:
                out.append(f"      fix : {f.fix}")
    out.append("\n提示: 以上是候选信号，不是作者鉴定。引用原话、行业术语、有意修辞"
               "受保护；是否成立需结合语义判断（见 SKILL.md 的触发/保护规则）。")
    if sources_note:
        out.append(f"词库来源: {sources_note}")
    return "\n".join(out)


def report_to_json(report: Report) -> dict:
    return {
        "score": report.score,
        "band": report.band,
        "units": report.units,
        "findings": [
            {"lang": f.lang, "category": f.category, "label": f.label,
             "match": f.match, "line": f.line, "col": f.col,
             "context": f.context, "weight": f.weight,
             "evidence": f.evidence, "note": f.note, "fix": f.fix}
            for f in report.findings
        ],
    }


# ---------------------------------------------------------------- CLI 边界

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AI slop 候选信号检测（词库+正则，确定性）")
    ap.add_argument("files", nargs="+", help="文本文件路径，- 表示 stdin")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--fail-on", choices=sorted(FAIL_LEVELS), default=None,
                    help="评分达到该档位时退出码 1（供 CI 使用）")
    ap.add_argument("--data-dir", default=None, help="词库目录（默认随包 data/）")
    args = ap.parse_args(argv)

    packs = load_packs(Path(args.data_dir) if args.data_dir else DATA_DIR)
    level_order = {b: i for i, b in enumerate(SCORE_BANDS)}

    exit_code = 0
    for idx, path in enumerate(args.files):
        if path == "-":
            text = sys.stdin.read()
            name = "stdin"
        else:
            p = Path(path)
            if not p.is_file():
                print(f"slop_check: 找不到文件: {p}", file=sys.stderr)
                return 2
            text = p.read_text(encoding="utf-8", errors="replace")
            name = str(p)
        report = scan(text, packs)
        if args.json:
            payload = {"file": name, **report_to_json(report)}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            header = f"\n──── {name} " + "─" * max(4, 60 - len(name))
            print(header)
            print(render_text(report))
        if args.fail_on and level_order[report.band] >= level_order[args.fail_on]:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""test_pairs.py — 偏好对数据集管线的金标准测试。

覆盖三块：
1. 交付物自检：pairs-zh.jsonl / pairs-en.jsonl 必须全部通过 validate（测试即文档）。
2. validate_pairs 规则：坏记录必须被抓到（schema/范围/词库交叉/偏好方向）。
3. build_pairs 纯函数：trim 截断与 extract_candidates 的最小 fixture。
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

from validate_pairs import (  # noqa: E402
    load_category_ids, validate_file, validate_pair,
)
from build_pairs import trim, extract_candidates  # noqa: E402

CATEGORY_IDS = load_category_ids()


def load_pairs(name):
    return [json.loads(l) for l in open(HERE / name, encoding="utf-8") if l.strip()]


class TestShippedDatasets(unittest.TestCase):
    """交付物自检：随包的两份 pairs 文件必须通过全部校验。"""

    def test_shipped_files_pass_validation(self):
        for name in ("pairs-zh.jsonl", "pairs-en.jsonl"):
            problems, stats = validate_file(HERE / name, CATEGORY_IDS)
            self.assertEqual(problems, [], f"{name}: {problems[:5]}")
            self.assertGreaterEqual(stats["pairs"], 10, f"{name} 样本量不足")
            self.assertGreater(stats["splits"].get("hard", 0), 0,
                               "缺少 hard 分歧样本——裁判校准需要它们")


class TestValidateRules(unittest.TestCase):
    """坏记录必须被抓到。"""

    def make_pair(self, **over):
        base = {
            "id": "zh-test-1", "lang": "zh", "domain": "qa", "license": "CC BY-SA 4.0",
            "source": "unit-test", "question": "Q",
            "good": {"text": "这是一段足够长的人类味文本，包含具体的人名、数字和结果。", "who": "human"},
            "bad": {"text": "这是一段足够长的 AI 味文本，随着时代的发展充满套话与空转表达。", "who": "chatgpt",
                    "patterns": ["canned_openers"]},
            "judge": {"model": "unit-test", "date": "2026-09-25",
                      "slop": {"good": 1, "bad": 6}, "confidence": 0.9},
            "split": "train",
        }
        base.update(over)
        return base

    def test_valid_pair_passes(self):
        self.assertEqual(validate_pair(self.make_pair(), "zh", CATEGORY_IDS["zh"], set()), [])

    def test_slop_out_of_range_caught(self):
        pair = self.make_pair(judge={"model": "t", "slop": {"good": 1, "bad": 11},
                                     "confidence": 0.9})
        problems = validate_pair(pair, "zh", CATEGORY_IDS["zh"], set())
        self.assertTrue(any("judge.slop.bad" in p for p in problems))

    def test_unknown_pattern_id_caught(self):
        pair = self.make_pair(bad={"text": "x" * 40, "who": "chatgpt",
                                   "patterns": ["nonexistent_category"]})
        problems = validate_pair(pair, "zh", CATEGORY_IDS["zh"], set())
        self.assertTrue(any("nonexistent_category" in p for p in problems))

    def test_inverted_preference_requires_hard_split(self):
        pair = self.make_pair(judge={"model": "t", "slop": {"good": 7, "bad": 2},
                                     "confidence": 0.5})
        problems = validate_pair(pair, "zh", CATEGORY_IDS["zh"], set())
        self.assertTrue(any("split" in p for p in problems))
        pair["split"] = "hard"
        self.assertEqual(validate_pair(pair, "zh", CATEGORY_IDS["zh"], set()), [])

    def test_duplicate_id_caught_across_pairs(self):
        seen = set()
        validate_pair(self.make_pair(), "zh", CATEGORY_IDS["zh"], seen)
        problems = validate_pair(self.make_pair(), "zh", CATEGORY_IDS["zh"], seen)
        self.assertTrue(any("重复 id" in p for p in problems))


class TestBuildPairs(unittest.TestCase):
    """build_pairs 纯函数：裁剪与抽取。"""

    def test_trim_cuts_at_paragraph_boundary(self):
        text = "第一段。\n\n" + "长" * 2000
        cut = trim(text, limit=100)
        self.assertIsNotNone(cut)
        self.assertLessEqual(len(cut), 101)
        self.assertIn("第一段", cut)

    def test_trim_pass_through_and_rejects(self):
        # 短文本原样通过——最短长度下限是 extract_candidates 的职责
        self.assertEqual(trim("短", 100), "短")
        self.assertIsNone(trim("", 100))
        self.assertIsNone(trim(None, 100))
        # 限制长度内没有任何自然边界：宁缺毋滥
        self.assertIsNone(trim("长" * 2000, 100))

    def test_extract_candidates_needs_both_sides(self):
        long_human = "这是人类回答，长度足够触发保留逻辑，包含具体的步骤与结果说明，超过最小字符限制，还补足了一些额外的说明文字来达到下限要求。"
        long_ai = "这是 AI 回答，同样长度足够，随着技术的不断发展套话很多，但长度必须达标才能保留，这里也补足额外的文字来满足最小长度限制。"
        payload = {"rows": [
            {"row": {"id": "0", "question": "什么是测试",
                     "human_answers": [long_human],
                     "chatgpt_answers": [None, long_ai]}},
            {"row": {"id": "1", "question": "缺人类回答",
                     "human_answers": [],
                     "chatgpt_answers": [long_ai]}},
            {"row": {"id": "2", "question": "人类侧过短",
                     "human_answers": ["太短了。"],
                     "chatgpt_answers": [long_ai]}},
        ]}
        got = extract_candidates(payload, "zh", "test", "CC BY-SA 4.0")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["id"], "zh-hc3-test-0")
        self.assertEqual(got[0]["domain"], "test")
        for side in ("good", "bad"):
            self.assertIn("score", got[0]["mech"][side])
            self.assertIn("band", got[0]["mech"][side])


class TestJudgeTool(unittest.TestCase):
    """judge_tool：裁决 -> pairs 记录的构造与合并。"""

    def test_build_pair_defaults_tells_to_mech(self):
        from judge_tool import build_pair
        cand = {"id": "en-x-1", "lang": "en", "domain": "x", "source": "s",
                "license": "MIT", "question": "q",
                "good": {"text": "g", "who": "human"},
                "bad": {"text": "b", "who": "chatgpt"},
                "mech": {"good": {"top_cats": []}, "bad": {"top_cats": ["tier1a"]}}}
        judgment = {"slop_good": 1, "slop_bad": 5, "reason": "r", "confidence": 0.8}
        pair = build_pair(cand, judgment, "model-x", "2026-09-25")
        self.assertEqual(pair["bad"]["patterns"], ["tier1a"], "未指定 tells 时默认机械 top_cats")
        self.assertEqual(pair["judge"]["model"], "model-x")
        self.assertEqual(pair["split"], "train")

    def test_merge_replaces_by_id(self, tmp=None):
        from judge_tool import merge_records
        import tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
            fh.write(json.dumps({"id": "a", "v": 1}) + "\n")
            tmp_path = fh.name
        try:
            stats = merge_records(Path(tmp_path), [{"id": "a", "v": 2}, {"id": "b", "v": 1}])
            self.assertEqual(stats, {"written": 2, "replaced": 1, "appended": 1})
            ids = [json.loads(l)["id"] for l in open(tmp_path)]
            self.assertEqual(sorted(ids), ["a", "b"])
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

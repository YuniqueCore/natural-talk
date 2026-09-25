#!/usr/bin/env python3
"""test_slop_check.py — 用正反例语料做金标准测试。

反例（AI slop 样本）必须被命中到指定类别；正例（人类味样本）必须保持干净。
这些语料同时是 references/examples.md 的来源：测试即文档，文档即测试。

v1.1 扩充：ZH_NEW_SLOP / EN_NEW_SLOP 覆盖新来源词条（zh-TW humanizer、
ai-writing-markers、anti-ai-tell、vale-ai-tells、会话案例库）；
ZH_NEW_CLEAN / EN_NEW_CLEAN 守住新词条的误伤边界（copulative、density、cluster）。
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slop_check import load_packs, scan, protect, score_band  # noqa: E402

PACKS = load_packs(Path(__file__).resolve().parent / "data")


# ---------------------------------------------------------------- 反例（AI slop）

ZH_SLOP = """\
随着人工智能的不断发展，各行各业都在积极探索转型升级的新路径。众所周知，技术赋能已成为企业
打造核心竞争力的关键抓手，其重要性不言而喻。

值得注意的是，这项技术不仅是一次工具升级，更是一场深刻的范式革命。它看似改变了工作方式，实则
重塑了整个行业的底层逻辑。综上所述，只有主动拥抱变化，才能在激烈的赛道竞争中立于不败之地。

让我们一起来回顾一下这一里程碑式的突破：它标志着行业迈上了新台阶，为未来发展注入了新的活力，
也为从业者开辟了星辰大海般的广阔前景。未来可期！
"""

EN_SLOP = """\
In today's fast-paced world, artificial intelligence stands as a testament to human ingenuity.
Nestled at the intersection of data and creativity, AI is not just a tool, but a transformative
force that is reshaping the very fabric of our society.

It's important to note that leveraging cutting-edge algorithms allows organizations to unlock
unprecedented insights. Moreover, this pivotal technology serves as a game-changer, fostering
innovation across a myriad of industries. Experts agree that we are witnessing a paradigm shift.

In conclusion, the journey into the world of AI has only just begun. The future looks bright,
and only time will tell what remarkable breakthroughs await us in this ever-evolving landscape.
"""

ZH_NEW_SLOP = """\
说白了，这次改版就是为了抢流量。所谓降本增效，不过是把成本转嫁给用户。原因很简单：
对手先做了，我们跟不上就只能被动挨打。

官方通稿自然要说意义：这次合作为后续的生态布局奠定了坚实的基础，实现了三套系统的无缝衔接，
在关键节点发挥了重要作用。理解了这个前提，我们就能明白各家为什么都在深入探讨落地路径。

**划重点：**历史将会记住这一天！愿我们都能在浪潮里站稳。家人们谁懂啊，看到这里直接泪目了。
干货满满，建议收藏慢慢看。每一个细节都是诚意，每一处打磨都是匠心，每一次迭代都是突破，
这片蓝海值得我们奔赴。
"""

EN_NEW_SLOP = """\
Based on the information provided, the results are encouraging. The catch?
Nobody outside the vendor can reproduce them. This matters because procurement
decisions hang on those numbers. It is important to note that the team garnered
widespread praise for its commendable work. Notably, the vendor unveiled a
versatile dashboard that marks a new era of self-service analytics.

Think of it as a Swiss Army knife for data. The key here is that it offers a
glimpse into the future while setting the stage for broader adoption.
**Key takeaway:** seamless integration paves the way to realizing the
transformative power of data.
"""


# ---------------------------------------------------------------- 正例（人类味）

ZH_CLEAN = """\
周二上午改了三版方案，第四版过了。老周在会上只说了一句：数据口径先统一，别的下周一再说。
散会后我把口径文档补了两处：渠道来源去重、退款单不计入 GMV。下午两点接到客服那边电话，
说有用户反映账单金额和实际扣款对不上，我查了十分钟，是四月份那次促销规则没写进结算逻辑，
记了 bug，标了 P1。
"""

EN_CLEAN = """\
I spent five days in Lisbon last October and still have mixed feelings about it. Beautiful,
yes. Also harder on the knees than anyone warned me.

The hills are the whole story and somehow never make the brochures. My hotel was up in Alfama,
which photographs beautifully and translates, in practice, to climbing what felt like a
six-story staircase every time I wanted coffee. By the second day my calves had opinions.

Everyone says to ride Tram 28, so I did, wedged against a stranger's backpack for forty
minutes while three tour groups filmed the same corner. I would walk the route next time.
"""

ZH_NEW_CLEAN = """\
问题定位花了半天。先看网关日志，请求打到 v2 接口就 502；再查数据库，慢查询列表里那条
全表扫描的语句很显眼。排查到这一步，原因其实已经清楚了：四月的迁移把索引建在了旧字段上。

麻烦在于重建索引要锁表，白天不能动。我们分成三个夜晚窗口做，每晚迁一张表，迁完跑回归。
周三全部迁完，监控曲线平稳，第二天只有两单超时工单。这套分批切换的流程后来写进了团队文档。
"""

EN_NEW_CLEAN = """\
The timeout parameter represents a floor, not a ceiling: requests can outlive it
when the connection stays busy. Section 4 features a table of the failure modes
we saw in staging, and the mitigation for each one. Deployments still roll out
in three phases, since the migration tool marks a checkpoint after every batch.

The findings section of the postmortem lists two action items. Both are small:
one config default, one alert threshold. The rest of the document explains how
the incident was contained within forty minutes.
"""


class TestSlopSamples(unittest.TestCase):
    """反例：必须命中，且落在预期类别。"""

    def test_zh_slop_hits_expected_categories(self):
        report = scan(ZH_SLOP, PACKS)
        cats = {f.category for f in report.findings}
        for expected in ("canned_openers", "corporate_jargon", "negative_parallel",
                         "transition_pileup", "inflated_significance", "chicken_soup"):
            self.assertIn(expected, cats, f"缺少类别 {expected}；实际命中: {sorted(cats)}")
        self.assertGreaterEqual(report.score, 5.0, f"评分应达到 heavy 档: {report.score}")
        self.assertEqual(report.band, "heavy")

    def test_en_slop_hits_expected_categories(self):
        report = scan(EN_SLOP, PACKS)
        cats = {f.category for f in report.findings}
        for expected in ("tier1a", "transitions", "chatbot_residue", "structural"):
            self.assertIn(expected, cats, f"缺少类别 {expected}；实际命中: {sorted(cats)}")
        self.assertGreaterEqual(report.score, 5.0, f"评分应达到 heavy 档: {report.score}")

    def test_specific_terms_found(self):
        report = scan(ZH_SLOP, PACKS)
        matches = {f.match for f in report.findings}
        self.assertTrue(any("众所周知" in m for m in matches), matches)
        self.assertTrue(any("抓手" in m for m in matches), matches)
        self.assertTrue(any("赋能" in m for m in matches), matches)
        self.assertTrue(any("综上所述" in m for m in matches), matches)

        report_en = scan(EN_SLOP, PACKS)
        matches_en = {f.match for f in report_en.findings}
        self.assertTrue(any("delve" in m or "testament" in m or "pivotal" in m
                            for m in matches_en), matches_en)


class TestCleanSamples(unittest.TestCase):
    """正例：人类味文本必须保持干净。"""

    def test_zh_clean_stays_clean(self):
        report = scan(ZH_CLEAN, PACKS)
        self.assertLessEqual(len(report.findings), 2,
                             "干净样本不应有超过 2 个候选: " +
                             "; ".join(f"{f.match}@{f.where}" for f in report.findings))
        self.assertIn(report.band, ("clean", "light"), f"评分: {report.score}")

    def test_en_clean_stays_clean(self):
        report = scan(EN_CLEAN, PACKS)
        self.assertLessEqual(len(report.findings), 3,
                             "干净样本不应有超过 3 个候选: " +
                             "; ".join(f"{f.match}@{f.where}" for f in report.findings))
        self.assertIn(report.band, ("clean", "light"), f"评分: {report.score}")


class TestRules(unittest.TestCase):
    """规则行为：保护、升级、评分。"""

    def test_code_fence_protected(self):
        text = "正常句子。\n\n```python\n# 赋能抓手闭环，综上所述 delving into tapestry\n```\n\n结束。"
        report = scan(text, PACKS)
        self.assertEqual(len(report.findings), 0, "代码块内不应产生命中")

    def test_inline_code_and_url_protected(self):
        text = "配置里写 `赋能闭环`，参考 https://example.com/delve-into-tapestry 即可。"
        report = scan(text, PACKS)
        self.assertEqual(len(report.findings), 0)

    def test_cluster_requires_multiple_in_paragraph(self):
        single = "这个项目主要靠数据驱动做赋能。"
        multi = "我们要抓手明确，打法清晰，还要持续赋能业务、沉淀方法论。"
        r1 = scan(single, PACKS)
        r2 = scan(multi, PACKS)
        single_hits = [f for f in r1.findings if f.category == "corporate_jargon"]
        multi_hits = [f for f in r2.findings if f.category == "corporate_jargon"]
        self.assertEqual(len(single_hits), 0, "单次黑话不应升级")
        self.assertGreaterEqual(len(multi_hits), 2, "密集黑话应升级")

    def test_density_suppressed_below_threshold(self):
        few = "可能有效。或许如此。"
        many = "可能一。可能二。可能三。可能四。可能五。也许六。"
        r_few = scan(few, PACKS)
        r_many = scan(many, PACKS)
        self.assertEqual([f for f in r_few.findings if f.category == "hedges"], [])
        self.assertTrue(any(f.category == "hedges" for f in r_many.findings))

    def test_not_x_but_y_regex(self):
        zh = "这不是一次普通的延期，而是团队协作机制的系统性失灵。"
        en = "The win is not about the speed but about the trust it builds."
        for text in (zh, en):
            report = scan(text, PACKS)
            self.assertTrue(any(
                f.category in ("negative_parallel", "structural") or "对举" in f.label
                for f in report.findings), text)

    def test_score_band_ordering(self):
        self.assertEqual(score_band(0.0), "clean")
        self.assertEqual(score_band(1.9), "light")
        self.assertEqual(score_band(4.9), "noticeable")
        self.assertEqual(score_band(5.1), "heavy")


class TestCli(unittest.TestCase):
    """CLI 边界与 JSON 输出。"""

    def test_json_output_shape(self):
        import io
        from slop_check import report_to_json
        report = scan(ZH_SLOP, PACKS)
        payload = report_to_json(report)
        json.dumps(payload, ensure_ascii=False)  # 可序列化
        self.assertIn("score", payload)
        self.assertIn("findings", payload)
        first = payload["findings"][0]
        for key in ("lang", "category", "match", "line", "col", "context", "weight"):
            self.assertIn(key, first)

    def test_stdin_smoke(self):
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "slop_check.py"), "-", "--json"],
            input=ZH_CLEAN, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("band", payload)


class TestNewSlopSamples(unittest.TestCase):
    """v1.1 新词条反例：必须命中到预期类别。"""

    def test_zh_new_slop_hits_expected_categories(self):
        report = scan(ZH_NEW_SLOP, PACKS)
        cats = {f.category for f in report.findings}
        for expected in ("canned_openers", "false_insight", "inflated_significance",
                         "chicken_soup", "fake_engagement", "rhythm"):
            self.assertIn(expected, cats, f"缺少类别 {expected}；实际命中: {sorted(cats)}")
        self.assertGreaterEqual(report.score, 5.0, f"评分应达到 heavy 档: {report.score}")

    def test_zh_new_specific_terms_found(self):
        report = scan(ZH_NEW_SLOP, PACKS)
        matches = {f.match for f in report.findings}
        for term in ("说白了", "不过是", "奠定", "无缝衔接", "家人们", "建议收藏"):
            self.assertTrue(any(term in m for m in matches),
                            f"应命中「{term}」；实际: {sorted(matches)}")

    def test_en_new_slop_hits_expected_categories(self):
        report = scan(EN_NEW_SLOP, PACKS)
        cats = {f.category for f in report.findings}
        for expected in ("chatbot_residue", "structural", "transitions",
                         "tier1a", "tier1b"):
            self.assertIn(expected, cats, f"缺少类别 {expected}；实际命中: {sorted(cats)}")
        self.assertGreaterEqual(report.score, 5.0, f"评分应达到 heavy 档: {report.score}")

    def test_en_new_specific_terms_found(self):
        report = scan(EN_NEW_SLOP, PACKS)
        matches = {f.match for f in report.findings}
        self.assertTrue(any("commendable" in m for m in matches), sorted(matches))
        self.assertTrue(any("The catch" in m for m in matches), sorted(matches))
        self.assertTrue(any("Based on the information provided" in m for m in matches),
                        sorted(matches))


class TestNewCleanSamples(unittest.TestCase):
    """v1.1 正例护栏：新词条不得误伤合法用法。"""

    def test_zh_new_clean_stays_clean(self):
        report = scan(ZH_NEW_CLEAN, PACKS)
        self.assertLessEqual(len(report.findings), 2,
                             "干净样本不应有超过 2 个候选: " +
                             "; ".join(f"{f.match}@{f.where}" for f in report.findings))
        self.assertIn(report.band, ("clean", "light"), f"评分: {report.score}")

    def test_en_new_clean_score_untouched_by_clarity_edits(self):
        """represents a / features a / marks a 是 clarity edit：可提示但不计分。"""
        report = scan(EN_NEW_CLEAN, PACKS)
        self.assertEqual(report.score, 0.0,
                         "tier1b clarity edits 不应计入评分: " +
                         "; ".join(f"{f.match}@{f.where}" for f in report.findings))
        self.assertEqual(report.band, "clean")
        for f in report.findings:
            self.assertFalse(f.evidence, f"非 evidence 命中不应计分: {f.match}")


class TestNewRules(unittest.TestCase):
    """v1.1 新词条的阈值语义：低频静默，密集才报。"""

    def test_new_density_entries_stay_silent_below_threshold(self):
        few = "The findings show one thing. The findings also show another."
        report = scan(few, PACKS)
        self.assertEqual([f for f in report.findings if f.category == "tier3"], [],
                         "2 次 findings 低于 density_min=3，应静默")
        many = ("We must enhance the API. Enhance the docs. Enhance the UI. "
                "Enhance the onboarding, and enhance the changelog.")
        report = scan(many, PACKS)
        self.assertTrue(any(f.category == "tier3" for f in report.findings),
                        "5 次 enhance 达到 density_min=4，应报告")

    def test_gejuju_cluster_single_occurrence_silent(self):
        single = "这次调整把团队的格局打开了。"
        report = scan(single, PACKS)
        self.assertEqual([f for f in report.findings if f.category == "corporate_jargon"], [])

    def test_label_and_explain_colon_flagged(self):
        text = "The tradeoff: you give up latency for consistency."
        report = scan(text, PACKS)
        self.assertTrue(any(f.category == "structural" for f in report.findings), text)


ZH_R2_SLOP = """\
今天我们盘一盘大模型赛道的舆论场。划重点：这套合作面子上是技术共享，里子是各自卡位。

问得好！简单来说，选哪个框架取决于个人需求。严苛的标准之下，这份报告引发全网热议。
以下是修改后的版本，请查收。
"""

EN_R2_SLOP = """\
Ever wondered why your stack feels slow? Make no mistake, this frictionless
platform serves as a stark reminder that developer experience matters.
You're absolutely right to ask. It wasn't the code. It wasn't the config.
Then everything changed. Last modified: 2024-01-0x.
"""

ZH_R2_CLEAN = """\
四月迁移后我们把数据口径统一了一份，报表才对得上。复盘时梳理了三件事：索引、缓存、
超时参数，各归各的负责人。周三改完，周四观察了一天，超时率回到改造前的水平。
"""

EN_R2_CLEAN = """\
The proxy pools Postgres connections and fails over in under a second. The
dashboard streams real-time data over websockets, and the migration tool marks
a checkpoint after every batch.
"""


class TestRound2Entries(unittest.TestCase):
    """v1.2 新词条：stop-slop / de-slop / De-AI / speak-human-tw 来源。"""

    def test_zh_r2_slop_hits(self):
        report = scan(ZH_R2_SLOP, PACKS)
        cats = {f.category for f in report.findings}
        for expected in ("corporate_jargon", "false_insight", "canned_openers",
                         "translation_tone", "inflated_significance", "fake_engagement"):
            self.assertIn(expected, cats, f"缺少 {expected}；实际: {sorted(cats)}")

    def test_en_r2_slop_hits(self):
        report = scan(EN_R2_SLOP, PACKS)
        cats = {f.category for f in report.findings}
        for expected in ("chatbot_residue", "tier1a", "structural"):
            self.assertIn(expected, cats, f"缺少 {expected}；实际: {sorted(cats)}")
        matches = {f.match for f in report.findings}
        self.assertTrue(any("2024-01-0x" in m for m in matches), sorted(matches))
        self.assertTrue(any("Ever wondered" in m for m in matches), sorted(matches))

    def test_zh_r2_clean_datacaliber_protected(self):
        """「数据口径」是数据术语（N4 放行）；单次「梳理」cluster 不报。"""
        report = scan(ZH_R2_CLEAN, PACKS)
        self.assertEqual(len(report.findings), 0,
                         "干净样本应 0 命中: " +
                         "; ".join(f"{f.match}@{f.where}" for f in report.findings))

    def test_en_r2_clean_score_untouched(self):
        report = scan(EN_R2_CLEAN, PACKS)
        self.assertEqual(report.score, 0.0,
                         "真实数据语境的 rider 词与 marks a 不应计分: " +
                         "; ".join(f"{f.match}@{f.where}" for f in report.findings))


class TestRound3Entries(unittest.TestCase):
    """v1.3 新词条：slopbuster / unslop。"""

    def test_en_r3_hits(self):
        slop = ("It functions as a hub that goes beyond simple storage — more than just "
                "a database. From startups to enterprises, from tech giants to small "
                "teams, everyone benefits. What a fascinating development! Generally "
                "speaking, this novel approach is novel in every way. It is novel.")
        report = scan(slop, PACKS)
        matches = {f.match for f in report.findings}
        self.assertTrue(any("functions as" in m for m in matches), sorted(matches))
        self.assertTrue(any("What a fascinating" in m for m in matches), sorted(matches))
        self.assertTrue(any("Generally speaking" in m for m in matches), sorted(matches))
        # chained from-to sweep 需要 ≥2 段 from…to 连发才报
        sweeps = [m for m in matches if m.startswith("From ")]
        self.assertTrue(sweeps, sorted(matches))

    def test_en_r3_single_from_to_stays_silent(self):
        report = scan("We migrated from Postgres 9 to Postgres 14 last quarter.", PACKS)
        self.assertEqual(len(report.findings), 0,
                         "单个 from…to 是正常范围表达: " +
                         "; ".join(f"{f.match}@{f.where}" for f in report.findings))

    def test_en_pack_silent_on_pure_chinese(self):
        """双包同扫的证据边界：纯中文正文不应触发 en 包计分词条。"""
        text = ("四月迁移后我们把数据口径统一了一份，报表才对得上。周三改完，"
                "周四观察了一天，超时率回到改造前的水平。")
        report = scan(text, PACKS)
        self.assertEqual([f for f in report.findings if f.lang == "en"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

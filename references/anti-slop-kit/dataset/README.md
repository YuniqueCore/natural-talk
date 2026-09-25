# slop 偏好对数据集（RFAIL/RLAIF → RLHF 管线）

为「去掉 AI slop」这个目标构建的偏好对数据集：每条记录包含同一任务下的一段
**人类味文本（good）** 和一段 **AI slop 文本（bad）**，附裁判打分与类别标注。
它是两条训练管线的地基：

- **RLAIF（现在）**：用 `judge_prompt.md` 让 LLM 裁判给 pairs 打分。本目录的
  slop 分数即由 GLM-5.3-Flash 在 2026-09-25 的会话中逐对人工审阅后给出（记录在
  `judge.model`，可复现、可替换、可追溯）。
- **RLHF（下一步）**：人类标注者在 judge 预筛之上做两件事——给 `split: hard` 的
  分歧样本标偏好方向；复核 judge 低置信度（`confidence < 0.6`）样本。一致样本
  直接采用 judge 标签，人工预算只花在刀刃上。标注产物可直接导出为 DPO/RM 训练
  格式（chosen = good，rejected = bad）。

## 文件

| 文件 | 职责 |
|---|---|
| `pairs-zh.jsonl` | 中文偏好对（24 条：HC3-Chinese 18 + 会话案例库 6） |
| `pairs-en.jsonl` | 英文偏好对（21 条：HC3 18 + MIT 来源对照 3） |
| `judge_prompt.md` | RLAIF 裁判提示词：0-10 锚点、保护条款、五维人味、校准样例 |
| `build_pairs.py` | HF datasets-server 行数据 → 候选对（机械对比度排序），纯函数核心 |
| `validate_pairs.py` | schema / 词库交叉 / 偏好方向 / 唯一性校验 |
| `test_pairs.py` | 管线金标准测试（含交付物自检） |
| `judge_tool.py` | RLAIF/RFHL 共用裁决工具：`emit` 导出待评批次，`merge` 把裁决记录并入 pairs |

## 记录 schema

```jsonc
{
  "id": "zh-hc3-open_qa-72",          // {lang}-{来源}-{domain}-{序号}；案例库为 zh-case-NN
  "lang": "zh",                        // zh | en
  "domain": "open_qa",                 // 来源数据集的领域划分
  "source": "Hello-SimpleAI/HC3-Chinese#open_qa/row:72",
  "license": "CC BY-SA 4.0",           // 逐条标注，案例库为 internal（见下）
  "question": "……",                    // 可为 null（段落对）
  "good": {"text": "……", "who": "human"},
  "bad":  {"text": "……", "who": "chatgpt", "patterns": ["hedges"]},  // patterns = 词库类别 id
  "judge": {
    "model": "GLM-5.3-Flash (RLAIF, agent session)",  // 裁判必须留名
    "date": "2026-09-25",
    "slop": {"good": 2, "bad": 6},     // 0-10，锚点见 judge_prompt.md
    "top_tells": {"good": [], "bad": ["hedges"]},
    "reason": "一句话证据",
    "confidence": 0.85                  // < 0.6 → RFHL 阶段转人工
  },
  "split": "train"                     // train | val | hard（分歧样本）
}
```

约束（`validate_pairs.py` 强制）：`bad.patterns` 必须是同语言词库里的真实类别 id
（与 `scripts/data/*.json` 单一数据源交叉验证）；`slop(good) > slop(bad)` 的反转对
必须标 `split: hard`；id 全局唯一。

## 扩数据

```bash
# 1. 下载更多行（脚本不联网，保持纯函数核心）
curl -sL "https://datasets-server.huggingface.co/rows?dataset=Hello-SimpleAI/HC3-Chinese&config=open_qa&split=train&offset=100&length=100" -o hc3zh-open_qa.json

# 2. 生成候选（机械对比度排序，每文件取前 N）
python3 build_pairs.py <rows_dir> --out candidates.jsonl --per-file 10

# 3a. （可选）导出待评批次给人类标注者或 LLM 裁判
python3 judge_tool.py emit --candidates candidates.jsonl --out batch.jsonl

# 3b. 裁决记录（逐条 slop_good/slop_bad/reason/confidence）并入 pairs
python3 judge_tool.py merge --candidates candidates.jsonl --judgments judgments.jsonl --into pairs-zh.jsonl

# 4. 校验 + 测试
python3 validate_pairs.py pairs-zh.jsonl pairs-en.jsonl
python3 test_pairs.py
```

## 来源与许可

**许可声明**：由于引入 HC3 系内容，本目录数据（`pairs-*.jsonl` 及后续扩量产物）整体按
**CC BY-SA 4.0** 共享；仓库其余代码与文档按根目录 [LICENSE](../../../LICENSE)（MIT）发布。

| 来源 | 许可 | 用量 | 说明 |
|---|---|---|---|
| Hello-SimpleAI/HC3-Chinese | CC BY-SA 4.0 | zh 18 条 | 同一问题的人类专家 vs ChatGPT 回答；衍生数据集如对外发布需遵循同源共享 |
| Hello-SimpleAI/HC3 | CC BY-SA 4.0 | en 18 条 | 同上（英文 reddit_eli5 / wiki_csai / medicine / finance / open_qa） |
| natural-talk 会话案例库 | internal | zh 6 条 | 本仓库 anti-examples.md 记录的真实退稿句（AI 草稿）与用户定稿改法 |
| blader/humanizer 里斯本对照 | MIT | en 1 条 | patterns-en.md 末尾完整 before/after |
| isatimur/de-slop examples | MIT | en 1 条 | hedge 掩埋论点的教科书案例 |
| anti-slop-kit 会话内写作 | internal | en 1 条 | vendor 博客样例与改写 |

已探明并**主动弃用**：aadityaubhat/GPT-wiki-intro（15 万条 wiki 简介 vs GPT 生成，两侧都是正式百科文体，slop 对比度低，不适合本目标）。
其他已探明、暂未接入的数据源（扩量时按 `build_pairs.py` 的 adapter 模式接入）：
Kaggle「LLM - Detect AI Generated Text」（学生作文 vs LLM，essay_id/text/generated 三列，
需 Kaggle 账号）、DAIGT V2 社区合集（4.4 万条增广）、M4 多生成器检测集、
OpenAssistant oasst2（带人类质量分，可做单侧质量信号而非成对）。
浏览器交互式探查（Kaggle/HF 页面）需要本机 Chrome 在运行；本次会话 Chrome 不可用，
全部改走 HF API 与 web search 完成。

## 已知边界

- 样本量（45 对）是**种子规模**：足够校准 judge、跑通管线、做 RFHL 预演，
  不够训 RM。扩量路径已经打通（build_pairs → judge → validate）。
- HC3 的 ChatGPT 答案是 GPT-3.5 时代产物：hedges 堆叠、空转收尾多，
  新模型的 slop 形态（如 mic-drop 短句、系词回避）在 en-case 三条里补充。
- `split: hard` 里的反转对（zh-hc3-baike-34：人类侧反而是宣传腔）是裁判校准的
  高价值样本，不要混进 train。

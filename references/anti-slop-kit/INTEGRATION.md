# INTEGRATION — 并入 natural-talk 的说明

本包按"可直接集成"的边界设计：词库、检测器、LLM 裁决规则、正反例各自独立成层，合并时只做文件放置与入口拼接，不改内部结构。

## 文件清单与职责

| 文件 | 职责 | 依赖 |
|---|---|---|
| `SKILL.md` | 入口与工作流（Agent Skills 格式，带 frontmatter） | references/* |
| `references/patterns-zh.md` | 中文模式裁决规则（触发/保护/动作 + 正反例） | 无 |
| `references/patterns-en.md` | 英文 tier 体系与模式目录 | 无 |
| `references/examples.md` | 正反例库（与测试语料同源） | scripts/test_slop_check.py |
| `references/humanizer-prompt.md` | 三个可复制提示词模板 | 无 |
| `scripts/slop_check.py` | 检测 CLI（纯函数核心 + IO 边界） | scripts/data/*.json |
| `scripts/data/zh.json` | 中文词库（唯一数据源，169 词条） | — |
| `scripts/data/en.json` | 英文词库（唯一数据源，212 词条） | — |
| `scripts/test_slop_check.py` | 金标准测试（29 例：反例必中、正例必净、阈值语义、证据边界） | scripts/data/*.json |
| `dataset/` | slop 偏好对数据集（RFAIL/RLAIF→RLHF 管线，45 条种子 + 裁判提示词 + judge_tool + 构建校验工具） | scripts/slop_check.py |

## 合并到既有 skill 的推荐方式

1. **整体并入**：把 `anti-slop/` 目录放进 natural-talk 的 skills 目录，作为独立子技能。natural-talk 的入口 SKILL.md 增加一行指引："需要检测/清理 AI 味时加载 anti-slop/SKILL.md"。**不要**把两份 SKILL.md 的正文互相拼接——两套工作流边界不同，拼在一起会互相稀释。
2. **词库扩展**：如果 natural-talk 已有自己的词表，把它的词条按本包 schema（`p`/`w`/`mode`/`note`/`fix`）迁移进 `data/zh.json` 或 `en.json` 后删除旧表——**词库只允许一个数据源**，两份并行词表是技术债。
3. **Prompt 层复用**：`references/humanizer-prompt.md` 的三个模板可直接拷进 natural-talk 的 prompt 资产；它们与词库同源，迁移后无需改动。
4. **CI 门禁（可选）**：`python3 scripts/slop_check.py docs/ --fail-on heavy`，评分达到 heavy 时失败，适合放在内容仓库的预提交检查里。

## 设计约束（改代码前先读）

- `slop_check.py` 的 `scan()` 是纯函数：不触网络、不读时钟、不用随机数；`main()` 是唯一 IO 边界。新增检测逻辑写在纯函数层，不往 CLI 塞。
- 三种词条模式（plain / cluster / density）覆盖全部阈值语义；不要为单个新词增加第四种模式。cluster 语义是"同段不同词条数达标"，与 avoid-ai-writing Tier 2 一致。
- 词库 JSON 是唯一权威；references 文档只写模式规则与示例，不复述完整词条表。文档与词库各说各的领域，避免双源漂移。
- 每次改词库或引擎后跑 `python3 scripts/test_slop_check.py`；正例语料（人类味文本必须 0–3 命中）是防止词库膨胀误伤的护栏。

## 来源与致谢

| 来源 | 许可 | 吸收内容 |
|---|---|---|
| sam-paech/antislop-sampler | Apache-2.0 | slop 短语词表思路、"not X but Y" 正则 |
| conorbronsdon/avoid-ai-writing | MIT | Tier 1A/1B/2/3 词库体系、editing contract、保护条件（carve-out）写法 |
| blader/humanizer | MIT | 25 模式分组、"默认选择"理论、里斯本改写对照 |
| petergyang/no-ai-slop | MIT | 模式清单与 editing principles、portability test |
| stephenturner/skill-deslop | MIT | 学术写作语体边界、quick checks |
| LifelongLazyLearner/qu-ai-wei | MIT | 中文八模式族骨架（触发/保护/动作）、正反例、证据分级 |
| MrGeDiao/shuorenhua | MIT | 保真规则（信息账本、引用保护、scope 分档） |
| en.wikipedia "Wikipedia:Signs of AI writing" / 中文维基《AI生成文的特征》 | CC BY-SA | 特征词表、负向排比、三连、格式残留 |
| Kobak et al. 2024 (arXiv:2406.07016) | — | excess vocabulary 实证（delve/intricate/pivotal 等） |
| gabelul/slopbuster | MIT | copula 家族补全、false-range 连发、more than just/goes beyond、novel 密度词（v1.3） |
| MohamedAbdallah-14/unslop | MIT | What a fascinating 谄媚、Generally speaking 垫话（v1.3） |
| hardikpandya/stop-slop | MIT | call-to-action、performed candor、weasel quantifier、五维自评（v1.2） |
| isatimur/de-slop | MIT | marketing-register 词、corrective reveal、negative listing、dramatic fragment、judging rubric（v1.2，dataset/judge_prompt 吸收其两测试） |
| shessenauer/deslop-ai-lint-skill | MIT | chatbot 残留句、模板占位日期（v1.2） |
| OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL | MIT | 中文伪口语动作词、分析动词签名词、伪严谨/伪坦率、舆论场/叙事/口径/话术、面子里子（v1.2） |
| Raymondhou0917/speak-human-tw | MIT | 立场真空、以下是修改后的版本、五维自评（v1.2，与 stop-slop 收敛） |
| Hello-SimpleAI/HC3 / HC3-Chinese | CC BY-SA 4.0 | dataset/ 偏好对种子（27 条，人类 vs ChatGPT 同题回答） |
| humzakt/ai-writing-markers | CC0-1.0 (data) | 词汇/短语/结构标记数据集（v1.1：treasure trove、setting the stage、left an indelible mark、chatbot 残留、结构标记分类） |
| MikkoParkkola/anti-ai-tell | MIT | 时代标注词表与实证（v1.1：commendable/garner/unveil 等 strong_flag，copulative avoidance 系词回避，density_watch） |
| tbhb/vale-ai-tells | MIT | Vale 规则库保守子集（v1.1：RhetoricalSelfAnswer 自问自答、LabelAndExplain 标签冒号、Metacommentary 元评论/残留加粗、JourneyMetaphors 旅程隐喻） |
| shyuan/writing-humanizer | MIT | 繁中 AI 词替换表（v1.1：深入探讨、奠定基础、无缝衔接、不容忽视的是、愿我们、每一…都是…，转简体并入） |
| natural-talk rules-full.md | 仓库内 | B10 起手式（说白了/说穿了/先说结论/归根结底）、B16 所谓X不过是Y，词库迁移（v1.1） |

本包在上述内容基础上重新组织与实现，未复制任何仓库的完整文件；具体吸收范围见各文件头注与 `references/*.md` 的来源段。

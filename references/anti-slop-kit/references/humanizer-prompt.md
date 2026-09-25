# Humanizer 提示词模板

三个可复制的模板：**改写**（默认）、**检测**（只报不改）、**预防**（写作前贴）。规则蒸馏自本包 references 与调研到的开源 skill（blader/humanizer、conorbronsdon/avoid-ai-writing、petergyang/no-ai-slop、stephenturner/skill-deslop、qu-ai-wei、shuorenhua；v1.1 增补 ai-writing-markers、anti-ai-tell、vale-ai-tells、writing-humanizer），与本包检测脚本的词库/模式一一对应，可以和脚本输出串联使用。

---

## 1. 改写模板（去 AI 味，保声口）

```
你是一名挑剔的人类编辑。改写我给的文字，去掉 AI 写作套路，但保住我的声口。

保住（硬约束）：
- 全部事实、数字、条件、否定、情态（"可能""我觉得"）、归因和责任主体；一个都不能漂移
- 我的立场、犹豫、锋利、幽默、口头禅——它们是"我"的证据
- 原文确实抽象的地方保持抽象，不许补造细节、数据、经历或观点

去掉（命中才动，逐条对照，不机械替换）：
- 不承载信息的开场（"随着……的发展""In today's world"）和收尾升华（"综上所述""The future looks bright"）
- 否定对举壳子："不是 X 而是 Y""It's not just X, it's Y"——改成事实主干或独立句，两端含义冻结；不许换成"问题不只在 X"这类换壳
- 假揭示（"看似 X 实则 Y""所谓 X 不过是 Y""原因很简单："）、拔高词（"赋能/至关重要/pivotal/delve/tapestry""奠定坚实基础/无缝衔接"）、三连排比凑数、起手垫话（"说白了/先说结论"）
- 聊天残留（"希望对你有帮助""Certainly!""Based on the information provided"）、标签句（"值得注意的是""It's worth noting"）、鼓点标点（"The catch?""The tradeoff:""**Key takeaway:**"）、系词回避（serves as / marks a / represents a → is / has）、旅程隐喻（paves the way / offers a glimpse into）
- 名词化外壳还原为"谁做了什么"（"进行了分析"→"分析了"）

方法：
- 先通读，列出要保住的声口特征和事实清单，再动笔
- 让事实和动作承担主干；每句要能通过"可移植性测试"——如果一句换个人换家公司也成立，它就是废话
- 引用原话一字不动；术语不降格；学术公文语体保持正式
- 改完自查：有没有新增断言？有没有把判断的方向改掉（"不够努力不是原因"≠"团队一直在努力"）？

输出：改写稿 + 「What changed」清单（每条一句话）。
```

附：想要更像你，在模板前面加一段你的旧文（2–3 段）并注明"这是我的声口样本，按它的词汇、节奏、标点习惯改"。

## 2. 检测模板（只报不改）

```
逐句检查下面文字里的 AI 写作模式。只报告，不改写：
- 指出模式名（否定对举／假揭示／拔高／三连排比／聊天残留 / not-X-but-Y / -ing rider / ...）
- 引用原句片段作为证据
- 每条一句话给修改方向
- 引用原话、术语、真实修辞放行，不要为了凑数报告
- 不猜测是不是 AI 写的——报告模式，不做作者鉴定

待检文本：
```

配合脚本：先跑 `python3 scripts/slop_check.py <file> --json` 拿到候选位置和分类，再把 JSON 结果贴进这个模板，让模型逐条复核并补充结构层问题（脚本看不到的：段落过齐、句长均匀、信息账本漂移风险）。

## 3. 预防模板（生成前贴进 system prompt）

```
写作规则（每次生成遵守）：
1. 直接从事实、问题或动作开始；不用"随着……""In today's……"开场，不用总结腔收尾
2. 陈述句直说；禁止"不是 X 而是 Y""It's not X, it's Y"结构
3. 每个判断后面跟一个可核对的具体物：数字、例子、机制、反例；否则删掉判断
4. 三连排比只在恰好有三项真实内容时使用；不用"化/性"词组三连
5. 禁用词：赋能、抓手、闭环、沉淀、底层逻辑、颗粒度 / delve、tapestry、testament、pivotal、robust、leverage、seamless、landscape（比喻义）、ecosystem（比喻义）
6. 句长要参差；段落长短不一；每段结尾不要都是总结句
7. 不要 emoji 标题、不要粗体标签列表、不要破折号当万能连接符
8. 保留我的口气：短句碎片、口语连接词、偶尔的不完整句——不要"润色"掉
```

## 4. 与脚本串联的完整流程

```
python3 scripts/slop_check.py draft.md          # 1. 候选地图
# 2. 把报告 + 模板 1 一起交给模型改写
python3 scripts/slop_check.py draft_v2.md       # 3. 复检：命中应下降，且无新增
# 4. diff 人工抽查：对照模板 1 的"保住"清单核对数字与判断方向
```

评分只看趋势：从 heavy 降到 light/near-clean 即达标。**不要为刷 0 分而改写真人声口**——那等于用另一种模板覆盖了作者。

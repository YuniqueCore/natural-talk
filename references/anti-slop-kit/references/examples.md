# 正反例库

所有反例/正例都在 `scripts/test_slop_check.py` 中作为金标准语料运行：反例必须命中、正例必须保持干净。改语料之前先跑测试。

使用方式：改写前浏览一遍校准"改到什么程度"；改写后如拿不准某处该不该动，来这里找同型案例。

---

## 一、中文反例（AI slop → 修改稿）

### 反例 1：工作同步（综合型，测试语料 ZH_SLOP 的来源风格）

> 随着人工智能的不断发展，各行各业都在积极探索转型升级的新路径。众所周知，技术赋能已成为企业打造核心竞争力的关键抓手，其重要性不言而喻。
> 值得注意的是，这项技术不仅是一次工具升级，更是一场深刻的范式革命。它看似改变了工作方式，实则重塑了整个行业的底层逻辑。综上所述，只有主动拥抱变化，才能在激烈的赛道竞争中立于不败之地。

命中模式：万能开场（随着…不断发展／众所周知）→ 黑话 cluster（赋能+抓手 同段）→ 否定对举（不仅…更是）→ 假揭示（看似…实则）→ 总结腔（综上所述／值得注意的是）。

> 改：本周我们试点了两个自动化流程：合同初审从 2 天压到 3 小时，报销审核只剩人工抽检。试点期间没有新增投诉。

判定要点：改写需要原文没有的事实。如果原文真的没有这些数字，就问作者——不许把套话删完了事、也不许编数字凑内容。

### 反例 2：产品发布

> 本次发布的智能摘要功能，不仅仅是一次功能迭代，更是我们对用户价值深度思考的结晶。它将全方位重塑用户的阅读体验，为产品注入新的活力。未来，我们将继续深耕这一赛道，打造行业标杆。

命中模式：否定对举 → 无依据拔高（全方位重塑／注入新活力／深耕／打造标杆／赛道）。

> 改：本次发布上线智能摘要：长文自动生成 3 句以内摘要，首屏可读。后台数据显示测试组阅读完成率提高了 9 个百分点（18% → 27%）。

### 反例 3：自媒体收尾

> 星辰大海，未来可期。愿你我都能在这条路上眼里有光、心中有火，遇见更好的自己。码字不易，点个关注，我们下期再见！

命中模式：鸡汤收尾（星辰大海／未来可期／眼里有光）→ 假互动（码字不易／点个关注）。

> 改：下一次我会把这套流程里踩过的三个坑单独写一篇。第一个坑是关于权限的，比想象中麻烦。

### 反例 4：学术技术（降格失真演示——这类文本不该这样改）

> 在长上下文推理中，latency 会随 context window 扩展而变化，因此不能只用单一指标判断系统性能。

这句话没有 AI slop 问题：技术词、因果关系、正式程度都正常。**不要**为了"去 AI 味"把它改成聊天语气，也不要拆掉"因此"承载的真实因果。学术、公文、法律文本的排比与名词化是体裁要求。

## 二、中文正例（人类味，保持原样）

### 正例 1：日常记录（测试语料 ZH_CLEAN）

> 周二上午改了三版方案，第四版过了。老周在会上只说了一句：数据口径先统一，别的下周一再说。散会后我把口径文档补了两处：渠道来源去重、退款单不计入 GMV。下午两点接到客服那边电话，说有用户反映账单金额和实际扣款对不上，我查了十分钟，是四月份那次促销规则没写进结算逻辑，记了 bug，标了 P1。

人类信号：具体时间与人名、句长参差、没有总结句、信息密度稳定。脚本 0 命中。

### 正例 2：个人叙述（来自 qu-ai-wei，"真人文本"边界案例）

> 我到楼下才想起来钥匙还在桌上。站了两秒，又觉得有点好笑——这周已经第二次了。

具体经历、自嘲和自然节奏。**只贴出文字、没有编辑要求时，停手**——不把破折号、口语节奏或自嘲当成 AI 痕迹去改。明确要求改写后，可以调整结构，但保留这些个人声口。

## 三、英文反例（AI slop → fix）

### 反例 5：产品博客

> In today's fast-paced world, AI-powered analytics is a game-changer. It's not just about dashboards — it's about unlocking unprecedented insights. Experts agree that this transformative technology will revolutionize how teams operate.

命中模式：transition frame（In today's）→ Tier1A（game-changer, transformative, revolutionize, unprecedented, unlocking）→ not-X-but-Y → vague attribution（Experts agree）。

> Fix: AI-powered analytics cut our incident triage time from 40 minutes to 6. The dashboards did not change; the alert grouping did.

### 反例 6：旅行帖（blader/humanizer 全篇对照的节选）

> Nestled along the banks of the Tagus River, Lisbon stands as a vibrant testament to Portugal's enduring spirit, where rich history and modern energy intertwine at every turn.

> Fix: My hotel was up in Alfama, which photographs beautifully and translates, in practice, to climbing what felt like a six-story staircase every time I wanted coffee.

完整 before/after 全文见 `references/patterns-en.md` 末尾与测试语料：before heavy / after clean（0 命中）。

## 四、英文正例（人类味，测试语料 EN_CLEAN 节选）

> I spent five days in Lisbon last October and still have mixed feelings about it. Beautiful, yes. Also harder on the knees than anyone warned me.
> The hills are the whole story and somehow never make the brochures. … By the second day my calves had opinions.

人类信号：立场不装（mixed feelings）、短句碎片是节奏不是表演、每个判断都能落回具体经历。**注意**：它含有 "the whole story" 这类表达和行首碎片句——这些不是 slop。把所有短句当成 AI 味去"修理"，恰恰是 AI 润色会做的事。

## 五、边界案例速查

| 情形 | 处理 |
|---|---|
| 引用原话里的"不是……而是……" | 原话一字不动；改周边叙述 |
| "闭环控制""对齐（ML）""生态（生物学）" | 术语保护，放行 |
| 作者的三连排比确有三个真实项 | 放行（授权遗漏、日志丢失、通知延迟三件都要保留） |
| 原文只谈潜力与目标 | 保持抽象，不补实现细节 |
| "研究表明"没有出处 | 默认保留归属与论断，正文外提示缺来源；不把无源论断洗成裸事实 |
| 疑似凭证（密码、API key） | 停手，要求先脱敏 |
| 真人文本 + 无编辑指令 | 停手 |

## 六、v1.1 扩充语料与真人校准

### 反例 7：中文混合腔（测试语料 ZH_NEW_SLOP）

> 说白了，这次改版就是为了抢流量。所谓降本增效，不过是把成本转嫁给用户。原因很简单：对手先做了，我们跟不上就只能被动挨打。
> 官方通稿自然要说意义：这次合作为后续的生态布局奠定了坚实的基础，实现了三套系统的无缝衔接，在关键节点发挥了重要作用。……
> 历史将会记住这一天！愿我们都能在浪潮里站稳。家人们谁懂啊……干货满满，建议收藏慢慢看。每一个细节都是诚意，每一处打磨都是匠心，每一次迭代都是突破……

命中模式：起手式（说白了）→ 假揭示（所谓…不过是／原因很简单：／理解了…就能明白）→ 拔高（奠定基础／无缝衔接／发挥重要作用／历史将会记住）→ 呼告（愿我们都能）→ 短视频腔（家人们谁懂／建议收藏／干货满满）→ 排比金句（每一…都是…）。

> 改：这次改版把首页信息流换成了推荐流。降本的部分是砍掉了人工运营位，用户看到的是算法挑的内容——想薅羊毛的老用户会不高兴，这是取舍，不是副作用。

### 反例 8：英文 vendor 博客（测试语料 EN_NEW_SLOP）

> Based on the information provided, the results are encouraging. The catch? Nobody outside the vendor can reproduce them. This matters because procurement decisions hang on those numbers. … Notably, the vendor unveiled a versatile dashboard that marks a new era of self-service analytics. … **Key takeaway:** seamless integration paves the way to realizing the transformative power of data.

命中模式：chatbot 残留（Based on the information provided）→ 自问自答（The catch?）→ 元评论（This matters because／The key here is）→ 系词回避（marks a）→ 超额词（garnered／commendable／unveiled／versatile／seamless）→ 旅程隐喻（paves the way）→ 万能短语（setting the stage／transformative power／offers a glimpse）→ 残留加粗（**Key takeaway:**）。

> Fix: The vendor reports good results, but independent teams have not reproduced them yet. Procurement should ask for a reference deployment before signing.

### 正例 3：真人好文的 light 档（校准"改到什么程度"）

博客园系真人技术文实测（v1.1 词库）：

- 《手撸一套纯粹的CQRS实现》：1 处命中（"本文旨在"，论文摘要式开头，体裁常规），评分 1.0/千单位，band=light。
- 《多线程&线程池》：1 处命中（"随着c#的不断发展"，确实是壳但孤立），评分 0.8，band=light。

真人好文不是 0 命中：**低密度 + 每处命中有放行理由**就是合格线。把真人文本刷到 0 分是过度清理。《多线程》里"诶，相信现在你明白了""佬们还是觉得很麻烦"这类口语气，《CQRS》代码中间的"*我不知道这里直接使用DTO对象来初始化是否合理，我先这样来实现*"，都是要保护的人味信号。

### 正例 4：clarity edit 不计分（测试语料 EN_NEW_CLEAN）

> The timeout parameter represents a floor, not a ceiling: … Section 4 features a table of the failure modes … the migration tool marks a checkpoint after every batch.

represents a / features a / marks a 全部命中 tier1b，但 evidence=false：报告出来供改写参考（还原成 is/has），**不推进 AI 证据评分**。同段 "findings" 只出现 1 次，低于 density_min=3，静默。这是"候选信号"定位的样板：可提示、不计分、低频不报。

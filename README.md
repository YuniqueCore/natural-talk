# natural-talk

让 AI 说人话：一套面向 coding agent 的写作规范与检测工具链，消除 AI 腔——客服腔、谄媚评判、金句癖、排比堆叠、上位者旁白——覆盖技术文档、踩坑过程文与小说叙事。

规范骨架基于 [chengzhi-c/natural-talk](https://github.com/chengzhi-c/natural-talk)（MIT）扩展，感谢上游的工作。

## 结构

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 规范入口：蒸馏核心 + 按场景路由到对应参考页 |
| `references/rules-full.md` | 全量编号规范（D/B/C/N 四层），清理模式逐条引用的依据 |
| `references/anti-examples.md` | 反面教材案例库：同一题材连写四版被退三次的真实退稿实录 + 用户定稿改法 |
| `references/fiction.md` | 小说叙事去 AI 腔与工法指南 |
| `scripts/` | `scan-mechanical.py` 长尾扫描器与测试套件 |
| `references/anti-slop-kit/` | 确定性 slop 检测：zh/en 词库（zh 169 / en 212 条，v1.2+）+ `slop_check.py` |
| `references/anti-slop-kit/dataset/` | slop 偏好对数据集（45 对种子）与 RLAIF→RLHF 管线工具 |

## 作为 skill 安装

把本目录放到 agent 的 skills 目录即可（Claude Code / Codex 等）：

```bash
git clone https://github.com/YuniqueCore/natural-talk.git .agents/skills/natural-talk
```

或作为其他项目的子模块引入：

```bash
git submodule add https://github.com/YuniqueCore/natural-talk.git skill
```

日常生成只需读 `SKILL.md` 蒸馏核心；清理模式逐条改动需指认 `rules-full.md` 编号；
需要词库+脚本的确定性 slop 扫描时加载 `references/anti-slop-kit/SKILL.md`。

## 词库与数据来源

词库收敛自 20+ 个带实证来源的公开项目（MIT / Apache-2.0 / CC0 / CC BY-SA），
逐条来源与许可标注见 `references/anti-slop-kit/scripts/data/*.json` 的 `meta.sources`；
数据集逐条带 `license` 字段，来源与许可表见 `references/anti-slop-kit/dataset/README.md`。

## 测试

```bash
python3 scripts/test-skill-contract.py
python3 scripts/verify_repo.py
python3 references/anti-slop-kit/scripts/test_slop_check.py
python3 references/anti-slop-kit/dataset/test_pairs.py
```

## 许可

- 代码与规范文档：[MIT](LICENSE)（含对上游 chengzhi-c/natural-talk 的署名）
- `references/anti-slop-kit/dataset/` 数据集：CC BY-SA 4.0（继承 HC3 来源的同源共享要求）

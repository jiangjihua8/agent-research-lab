---
name: research-ideation
description: Turn an empirical AI research topic or rough idea into competing explanations, verified prior-work comparisons, evidence-based critique, and a minimal discriminating experiment. Use for topic selection, idea debates, novelty checks, and deciding what to test next. Produces research plans and decisions, not manuscript prose.
---

# AI 科研选题与创新讨论

把“看上去新颖的点子”推进到“值得花资源检验的判断”。本技能属于实验研究，不加载写作技能；表达是否漂亮不参与实验选择。

## 根据项目状态开始

读取研究问题、资源、literature.json、hypothesis.json、STATE.md 与已有运行。不要求先指定创新模块。新项目可以先从兴趣或近邻论文形成候选问题；基线还未验收时，输出的是**待验证草案**，下一步是校准环境或复现失效。通过基线验收后，才用 research.py propose 登记用于实验筛选的正式提案。

## 一轮讨论

1. **缩问题**：选一个当前资源能观察的现象。将“改进大模型”压到条件、对象与可测变化。可借 AI 给出的问句启发思路，但不以它说“好点子”为依据。
2. **拆解释**：研究员给出一个原因，质疑者给出至少一个具体竞争解释。追问“依据在哪里”“什么读数能区分”“什么情况下预测相反”。可以由同一 Agent 顺序完成，不能冒充独立复核。
3. **核近邻**：核查任务词、机制词和最接近工作的引用网络。读直接支撑新颖性判断的原文。结果可以是已做、部分覆盖、未在已查范围发现或尚不明确；附链接与具体位置。已做的工作可转成基线、反例或新的边界问题。
4. **评估证据**：用 [idea-review.md](references/idea-review.md) 分别检查意义、新颖性、可检验性和可行性。分数只显示当前证据状态，不代表 ICML 评分或录用概率；有硬缺口先补缺口。
5. **安排下一步**：优先选能让某个解释失败的便宜实验。把干预、对照、预测、反证、成本写进 idea 草案或已验收项目的提案；需要实际执行时交回 [research-experiments](../research-experiments/SKILL.md)。

## 讨论应改变什么

每轮只保留能影响下一项实验的质疑和回答，写入工作目录 `inputs/idea-review.md` 的副本并链接真实来源。修订假设要说明新增证据，不能只换说法提高自评分。不同解释预测完全相同时，先改实验设计，不再让模型反复投票。

已有结果与预测不符时，先排查实现和评测，再比较竞争解释。探索也可以没有单一方向预测：明确未知、列出不同结果各会改变的决定；不为完成模板编造确信。

连续讨论没有新增证据或可判别实验时结束本轮，记录下一步是阅读、实现、实验还是停止。正式结论须来自后续验证。来源与采纳边界见 [作者系列核查](../research-paper/references/vuk-series.md)。

多个候选之间的价值、范围和资源取舍仍不清楚时，使用 [research-supervisor](../research-supervisor/SKILL.md) 复盘。导师判断不能代替近邻原文、实验验收或正式证据。

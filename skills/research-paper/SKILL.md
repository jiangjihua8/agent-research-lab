---
name: research-paper
description: Route a research workspace between experiment work and evidence-based paper preparation, preserve handoffs, and use the local research CLI. Load the experiment or writing skill according to the actual task; do not mix their decision rules.
---

# 科研项目调度入口

读取 AGENTS.md、project.json、STATE.md、DECISIONS.md。运行 `python3 tools/research.py status --project . --json` 和 `next --project .`，检查当前事实、预算、缺项及最近候选决策。工具不在本地时可维护等价记录，但不声称运行过检查。

## 两条分开的工作流

- 选题、文献、环境、创新、跑实验、分析结果：加载 [research-experiments](../research-experiments/SKILL.md) 作为实验入口。项目的 scope 到 experiments 都由它处理，不加载写作技能。
- 需要深入讨论研究问题、竞争解释或近邻差异时，实验流程按需调用 [research-ideation](../research-ideation/SKILL.md)；它输出研究决策，不产出论文措辞。
- 用户要求导师指导，或方向取舍、扩大实验、结果冲突和停滞需要复盘时，调用 [research-supervisor](../research-supervisor/SKILL.md)。导师输出判断与下一项行动，交回实验流程执行，沿用 review／decide，不另建审批状态。
- 用户要求撰写或修改论文、准备回复或投稿材料：加载 [research-writing](../research-writing/SKILL.md)，以已经冻结和审阅的实验材料为输入。
- 写作中发现证据缺口：将缺口、受影响主张和需要回答的问题写入 `paper/experiment-requests.md`，切回实验技能判断是否值得补实验，不能用写作规则调整实验口径。

填写记录或运行 CLI 查 [records.md](references/records.md)。来源、已核实的技能版本及采纳边界见 [sources.md](references/sources.md)，不必每轮加载。

## 持续推进

在已有授权与资源内完成当前工作，不逐阶段重复请求许可。缺少必要信息时先完成不依赖它的工作，再集中询问。默认一个 Agent 顺序切换职责，自查不等于独立复核。

每轮更新 STATE.md：已执行内容、证据位置、当前判断、下一项具体实验或任务、预计成本。DECISIONS.md 保存取舍。机器状态在 JSON，正文不反向覆盖实验记录。

框架允许负结果、缩小问题或停止研究。阶段检查通过表示记录一致，研究价值、方法正确性和最终提交仍需真实判断。

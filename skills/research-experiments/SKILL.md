---
name: research-experiments
description: Develop and test empirical machine learning ideas through failure diagnosis, strong baselines, fair evaluations, bounded experiment execution, and evidence-backed candidate decisions. Use for research planning, innovation, implementation, experiments, or analysis; excludes manuscript polishing and publication storytelling.
---

# 科研实验与创新

目标是用有限实验增加可信认识。先建立能揭示错误的评测环境，再让 Agent 在其中提出和筛选方法。研究可产出有效方法、适用边界或负结果。

**本技能不读取或应用任何写作技能。** 选题、指标、对照、数据、实验预算和结果取舍由研究问题与证据决定。“让论文更有说服力”不能成为改变这些条件的理由。

## 开始

读取 project.json、STATE.md、DECISIONS.md，运行 `status --json` 与 `next`。沿用已有数据、领域、资源与动作授权。优先完成下一个能改变判断的具体实验，少写重复计划。

本流程面向实验型 AI 研究，不局限于某种模型。首次接入或更换方向时读 [ai-domains.md](references/ai-domains.md)，选择与课题匹配的数据、指标、对照和训练适配器。

方向取舍、扩大实验投入、结果与解释冲突或探索停滞时，按需调用 [research-supervisor](../research-supervisor/SKILL.md) 做导师复盘；得到具体实验任务后继续本流程。普通短测和修复不增加一轮导师审查。

## 实验主循环

1. **问题与材料**：从可核查失效建立问题—方法—证据表；阅读 [workflow.md](references/workflow.md)。需要选题、与 AI 争论假设或核查点子时使用 [research-ideation](../research-ideation/SKILL.md)。此时可以有初始草案，暂不据此大规模造模块。
2. **环境和基线**：阅读 [experiments.md](references/experiments.md)。先把数据切分、指标、训练和强基线跑通、合理调优；按 [evaluator-validation.md](references/evaluator-validation.md) 验证评测能区分预设对照。允许只含基线的初始协议。
3. **创新提案**：阅读 [innovation.md](references/innovation.md)。按失效、原因、干预、预测、反证和近邻对照登记少量提案。每个提案先做最小判别实验。
4. **执行与判读**：阅读 [execution.md](references/execution.md)。运行前保存预测，smoke 检查实现，pilot 用验证集检验方向；用实际运行做 continue / revise / drop / promote 决策。进行自动探索、预算晋级或解释意外结果时读 [search-and-scale.md](references/search-and-scale.md)。失败不能改写成负科学结论，负科学结论也不能隐藏。
5. **正式确认**：固定方法、代码、配置、训练与调参规则，保留独立测试；完整比较、多种子、机制消融、替代解释、成本与适用边界。正式结果才能支撑正式主张。

## 判断规则

- 简单基线、强近邻方法、容量或算力控制都应与问题匹配。公平调参是透明且合理的预算，不是无限调到“最大”，也不是故意削弱基线。
- 短训练只暴露部分错误，不能证明无 bug，不能自动排名。延长训练或扩规模前说明要解决什么不确定性。
- 比较训练信号、可见输入、数据量、参数、计算、调参资源。复用模块写清来源、成立前提与新增加的认识。
- 测试结果不用于挑方法、种子或故事。改协议建立新版本；见过测试结果后仍需新的独立确认依据。
- 所有尝试、失败和消耗保留。停止条件按预算和信息收益事先约定，不以“直到赢”为条件。
- 审查围绕可定位的问题和复测证据，通常每轮最多三次修复迭代；关键问题不解决就停止扩算力。审查者的身份和独立性如实记录。

## 实验交付

完成当前协议下 summary、analysis、运行档案和实验审查，明确支持什么、推翻什么、还有什么未知。只有转入论文任务时才把证据交给 research-writing；补实验请求返回本技能处理。记录格式见 [records.md](../research-paper/references/records.md)。

---
name: research-supervisor
description: Advise an empirical AI research project at direction, experiment-design, scaling, or pivot decisions. Audit the value of the question, nearest prior work, evidence gaps, and resource fit; prioritize the next discriminating experiment and explain the judgment. Use for advisor feedback, progress reviews, or stalled research. Does not polish manuscripts or replace execution and evidence checks.
license: CC-BY-NC-SA-4.0
---

# 科研导师：判断下一步是否值得做

以研究导师的职责审视当前工作：问题是否重要、证据是否可信、还缺什么认识、下一笔资源该花在哪里。依据真实材料形成建议，给研究者解释判断，不凭角色身份替代证据。

本技能参考 HKUSTDial/Supervisor-Skills 并针对本项目改编；不是其完整安装，也不代表原作者提供指导。来源、固定版本、改动和许可见 [attribution.md](references/attribution.md)。

## 何时介入

- 初步文献和问题已形成，需要比较候选方向、检查范围与资源匹配。
- 要从调试／探索转入显著更贵的实验，或准备固定正式确认方案。
- 结果与预测冲突、连续探索没有新增认识，或新近邻工作改变了创新判断。
- 用户明确要求导师意见、组会复盘或下一步研究安排。

不要求每次 smoke 或普通修复都做导师复盘。一个 Agent 可以顺序承担导师与实验者职责，记录为角色自查；单独的模型或人员参与时才如实记录。不会因为加载本技能自动启动其他 Agent。

## 阅读事实后再判断

先运行 `status --json`、`next`，读取 project.json、STATE.md、DECISIONS.md。按当前问题读取相关文献原文、hypothesis、协议、pilot 检查、运行、预测与候选决策。预算、原始日志和负结果都是输入；不要只读候选作者的总结或精选表格。

材料不足时明确缺口，先推进可做的检索或检查。导师不能用自己的解释补出缺失结果，也不替用户虚构资源或研究经验。

## 一次有效指导

1. **定位研究贡献**：用一句可核对的话描述要增加的认识。方法改进、机制解释、评测、边界与负结果采用不同证据标准；不强迫所有课题达到 SOTA。检查价值时按需读 [checkpoints.md](references/checkpoints.md)。
2. **找最影响判断的缺口**：真实近邻是否覆盖、评测是否能检验主张、基线是否公平、竞争解释是否被区分、完整确认是否在资源内。按结论影响排序，突出最优先的问题，同时保留全部未解决的重要问题。
3. **审视当前解释**：区分文献事实、已观测结果、机制推测和未知。结果落后时先看实现、预算、噪声与原预测；可靠反证要求修订或停止相应主张，不能靠换指标或换说法保住它。
4. **安排下一项行动**：选择最能改变判断的阅读、校准或判别实验，说明为何优先于其他选项。交付问题、必要对照、预期读数、相反结果如何决策、成本上限及停止条件。
5. **解释并交接**：用简短说明连接证据、判断和下一步，让研究者知道为何这样做。保存工作目录 `inputs/supervision.md` 的已填写副本，交回 [research-experiments](../research-experiments/SKILL.md) 执行；需要细化竞争假设时调用 [research-ideation](../research-ideation/SKILL.md)。

## 接入现有闭环

- 尚无真实候选运行：建议准备基线、补证据、缩小范围或停止草案，保存指导记录和 STATE；不为登记 `decide` 编造运行。
- 已有候选及真实运行：建议对应 continue / revise / drop / promote，由实验流程按既有字段和条件登记 `decide`。promote 只表示值得正式验证。
- 已有冻结协议，发现环境／正式实验中的关键问题：使用现有 `review` 的 pilot 或 experiments 范围登记，沿用 issue id。未冻结时先记录阻断项，修正设计；不能伪造协议来登记。
- 扩大实验前，原有验收、预算、冻结和测试集隔离要求继续适用。导师建议不能覆盖未通过的检查，也不直接改写代码、数据、协议或历史成绩；改动由实验流程实施、记录与复测。

指导报告不是新的机器状态或额外审批。已有授权范围内，在完成必要记录后继续执行下一项工作。用户是否接受最终研究判断，不得伪写为已确认。

## 实验与写作边界

本角色在实验侧不加载写作技能，不用叙事完整度、语言强弱或论文版式决定指标与结果。写作任务交给 research-writing；写作发现的实验缺口仍按价值、证据成本和资源评估。论文潜力、模型自评分和“导师认可”都不是实验结论或录用保证。

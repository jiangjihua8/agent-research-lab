# 来源、改写与适用边界

## 输入材料

最初版本根据用户提供的五条抖音提取文本和⑤的完整逐字稿整理，没有在工作目录找到材料所列的原视频与转写文件；因此以下五条按用户材料使用。后续按用户新增短链，另行获取并核对了 Vuk 的 7 条完整视频，详见 [系列核查与摘要](vuk-series.md) 和 [分级来源目录](vuk-catalog.json)。⑤仍按用户逐字稿引用，不混同为本轮下载。点赞和热度未作为方法依据。写作仓库通过 GitHub 核查，结果见下文。

| 用户提供的内容 | 原链接 | 在本项目中的采用方式 |
| --- | --- | --- |
| ① 反防御性写作 | https://www.douyin.com/note/7703971691089675110 | 删除空泛退让，保留真实局限，依据证据作正向表达 |
| ② AI 辅助找 Idea | https://www.douyin.com/note/7703481201215321050 | 文献表、前提拆解、可证伪假设、创新与证据成本检查 |
| ③ Claude 修订 GPT | https://www.douyin.com/note/7700986432148668026 | 用明确规则与证据复核写作；跨模型可选，不假定换模型必然更好 |
| ④ 创新点与模块替换 | https://www.douyin.com/note/7699880421630340554 | 采用基线复现和功能拆解；要求披露复用，不采用隐藏替换、跑平即写成创新的做法 |
| ⑤ 先环境与评测 | https://www.douyin.com/video/7704356876992974089 | 先评测与强基线、短测排错、有限审查，再做受预算约束的搜索 |

实验技能依据②④⑤以及后续核对的 Vuk 方法系列，另拆出 research-ideation 负责选题讨论；写作技能只在论文任务中使用①③的表达建议。两类工作流分目录、分入口，写作阶段对实验材料只读。

## 导师角色：Supervisor-Skills（2026-11-06）

用户补充 [HKUSTDial/Supervisor-Skills](https://github.com/HKUSTDial/Supervisor-Skills) 后，核查固定提交 `4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8` 的选题评价、文献调研、能力匹配及相关参考资料，并加入项目内 [research-supervisor](../../research-supervisor/SKILL.md)。它负责研究价值、证据缺口、资源优先级和阶段复盘，将具体任务交回实验流程。

没有整体安装上游，也没有把其写作、稿件评分或固定生命周期门槛带入实验决策。导师判断不替代已有验收与真实运行；关键取舍仍用 review／decide 记录。适配范围、未采纳规则及 CC BY-NC-SA 4.0 署名许可见 [导师来源说明](../../research-supervisor/references/attribution.md)。

## ⑤视频如何转为实验流程

以下时间和含义来自用户提供的逐字稿，不将视频作者的个人经验当作 ICML 官方要求。

| 视频段落 | 关键启发 | 本项目执行方式 |
| --- | --- | --- |
| 00:00–01:10 | AI 容易自选简单任务、评测不全、少调基线 | 基线校准卡、公共评测、近邻覆盖、合理调参、pilot 验收先于候选执行 |
| 01:11–02:00 | 先用极短运行找实现问题，避免长实验返工 | smoke 与 pilot 分层，真实日志与正确性检查；短测不进入正式汇总 |
| 02:00–02:37 | 找问题和修复；模型常组合现有模块 | 有限审查、稳定 issue id、修复证据；组合需说明机制、来源与近邻差异 |
| 02:37–03:00 | 组合也可能产生有用方案 | 提案有互补假设、单模块/简单组合/资源对照，以新增认识评价价值 |
| 03:00–04:00 | 环境可信后再自动搜索；比较参数和计算 | execute 基线准入、预算预检、验证集探索、propose/decide 循环、正式冻结 |
| 04:00–04:46 | 存在效果与资源权衡；规模和新颖性未解决 | 成本与机制诊断、保真度晋级、适用范围检验、真实查新；不设通用模型参数门槛 |

②补充了视频中较少展开的部分：如何找材料、判断迁移前提、形成可证伪假设，以及查新/实现/证据三类成本。④提供了拆模块与适配思路，但其隐藏替换过程、跑平即可包装创新的建议未采用。

## 写作技能核实与取舍（2026-11-05）

- [Adkid-Zephyr/anti-defensive-writing-Skill](https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill)：核查提交 `82d31402caa0db1790026824399044538483171b` 的中文 SKILL.md 和 MIT LICENSE。该版本包含按已有结果改换评价维度、不陈述落后等规则，与输入中较保守的“公开版规则”并不完全相同。**没有安装或原样加载此技能**；只保留用户材料中“删除空泛退让、准确表达证据”的写作目的，排除其对实验组织的干预。
- 用户材料中的 `Acyee/gpt-writing-guide` 返回 404；搜索并核实的仓库是 [Acyeee/gpt-writing-guide](https://github.com/Acyeee/gpt-writing-guide)。固定提交 `65d5d095ba74e9936252aefa21d8d6c4ec31dee3` 的 formal-doc-revision、配套经验全文及 LICENSE 均已读取。其第六部分明确区分论文适用规则。本项目据此制作独立 research-writing 适配技能，保留证据限定、复现过程和文献核查，不采用对每次改稿重复确认的通用流程。署名与 CC BY 4.0 许可见 [attribution.md](../../research-writing/references/attribution.md)。

未把任何上游写作技能的宽泛触发词带入实验技能，也不安装到用户全局配置。

## 已核对的官方参考

核查日期：2026-11-05。用于方法论参考，未来投稿要重新查目标年份和 track。

- [ICML 2026 Reviewer Instructions](https://icml.cc/Conferences/2026/ReviewerInstructions)：评估技术可靠性、表达、意义和原创性，并检查主张的证据支持。其原创性说明也涵盖有价值的已有想法组合；组合仍需解释贡献。
- [ICML 2026 Call for Papers](https://icml.cc/Conferences/2026/CallForPapers) 与 [Author Instructions](https://icml.cc/Conferences/2026/AuthorInstructions)：核对主张的可复现证据、作者责任和投稿材料。2026 文件只作已核实参考，不默认选择投稿年份；正式投稿重新核查当年 track。
- [NeurIPS Paper Checklist Guidelines](https://neurips.cc/public/guides/PaperChecklist)：检查主张范围、局限、复现说明、实验设置、不确定性和计算资源。本项目据此要求证据账本与运行成本记录。

## 未提升为规则的说法

- 视频中“ICML 可能需要 100M 或几百 M 参数”的口述不足以建立通用录用门槛；本项目不采用该规则。
- 没有采信视频中某架构超过 Engram 的性能说法；需要原始论文、实现与评测记录才能判断。
- 五秒训练只能作为短测启发，不能证明没有 bug，也不能给出论文级比较结论。
- “AI 自审直到没有问题”改为有限轮次、可核对的问题处理与停止条件。
- “一周形成 proposal”可以是时间安排，不能作为创新已成立或论文会录用的保证。

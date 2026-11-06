# 导师技能的来源与适配

本模块参考并改编自 **Yuyu Luo（骆昱宇）及贡献者**的 [HKUSTDial/Supervisor-Skills](https://github.com/HKUSTDial/Supervisor-Skills)。固定核查提交：`4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8`；核查与接入日期：2026-11-06（Asia/Shanghai）。不代表上游作者或机构认可、参与本项目。

## 已读来源及使用方式

| 上游内容 | 本项目采用的部分 | 调整 |
| --- | --- | --- |
| [idea-evaluator](https://github.com/HKUSTDial/Supervisor-Skills/blob/4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8/skills/idea-evaluator/SKILL.md) 及 five-dimensions 参考 | 研究价值、近邻差异、重要缺口与可行性检查 | 不输出 Strong Accept／Reject 作为会议预测，不用 1–10 分阈值替代实验 |
| [fatal-flaws](https://github.com/HKUSTDial/Supervisor-Skills/blob/4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8/skills/idea-evaluator/references/fatal-flaws.md) | 问题优先级、主张可验证性、范围控制、避免给技术硬找问题 | 不按基线年份或缺陷数量自动否决；不把一次落后等同机制已证伪 |
| [lifecycle-capability-matching](https://github.com/HKUSTDial/Supervisor-Skills/blob/4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8/skills/idea-evaluator/references/lifecycle-capability-matching.md) 与 handbook 2.1、2.2 | 以实际能力、数据和资源选择可完成的问题；从基线缺口寻找方向 | 不使用固定到期月份、周工时、GPU 张数作为通用门槛 |
| [deep-research](https://github.com/HKUSTDial/Supervisor-Skills/blob/4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8/skills/deep-research/SKILL.md) 及 search-strategy、citation-protocol | 研究问题先行，多角度查文献，分开核对存在性与内容支持 | 只输出研究证据与缺口，不套综述论文叙事；按需要和预算补查，不无限循环或强制多 Agent |
| [vibe-research-workflow](https://github.com/HKUSTDial/Supervisor-Skills/blob/4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8/skills/vibe-research-workflow/SKILL.md) | 已阅读，用于核对职责边界 | 不整体启用；用户已授权 Agent 提案、设计与跑实验，不采用每步让用户重新确认的泛化流程 |

还检查了 benchmark-paper-template 入口；它把研究设计和正文结构放在一起，本次没有安装或调用。paper-writer、paper-polish、intro-drafter 等写作技能未引入实验侧。

上游存在需谨慎解释的规则：例如 fatal-flaws 将两个 MAJOR 升级为 CRITICAL，同时又给两个 MAJOR 指定 Accept with Revisions；本项目不采用该数量映射，而用已有 blocker/major/minor 和证据处理。机制落后需要结合实现有效性、比较设计、训练保真度与不确定性判断；被可靠反证的主张应修订，但负结果不等于研究没有价值。

新增的本地适配包括：与现有 review／decide／STATE 的衔接、导师与执行职责分工、实验与写作隔离、真实运行前后不同的建议记录方式。没有改动执行器或另建一套审批状态机。

## 许可与分发

上游根 [LICENSE](https://github.com/HKUSTDial/Supervisor-Skills/blob/4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8/LICENSE) 声明 **CC BY-NC-SA 4.0**；部分技能 frontmatter 写 CC-BY-4.0，而 deep-research 写 CC-BY-NC-SA-4.0。本适配模块统一按根声明的 **CC BY-NC-SA 4.0** 提供，保留署名、非商业与相同方式共享条款，不将它标为 MIT 或无条件商用。

上游许可声明保存在 [UPSTREAM-LICENSE.txt](../UPSTREAM-LICENSE.txt)；[许可说明](https://creativecommons.org/licenses/by-nc-sa/4.0/)与[完整法律文本](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)。该声明覆盖本目录的改编文本及项目中的导师提示词、导师记录模板，不改变框架其他文件的权利状态。没有安装到用户全局技能目录，也没有复制整套上游技能。

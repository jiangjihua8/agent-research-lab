# Agent Research Lab 开发约定

本目录是科研 Agent 工作流框架。用户要求开展具体研究时，先用 `scripts/research.py init` 创建独立工作目录；框架开发不等于已获授权启动其中的研究示例。

- 入口文档是 README.md，科研规则在 `skills/research-paper/SKILL.md`，协议字段在其 references/records.md。
- Python 工具只使用标准库，负责本地实验执行、记录与一致性检查，不接管模型 API、集群调度或投稿账号。
- 用户明确要求实验与写作分开：research-experiments 管选题、创新、跑实验和分析，research-ideation 按需协助点子辩论和查新；research-writing 只改论文材料。实验阶段不得加载写作技能或用叙事需要选择结果。
- research-supervisor 在方向取舍、扩算力和结果复盘时提供导师判断，仍受实验验收与预算约束。导师是职责，不默认意味着另启 Agent 或新增人工审批；其适配资料的来源和许可随技能保留。
- 修改校验逻辑时验证真实失效场景：数据协议变更、重复种子、证据被改、历史问题丢失、预算超限、失败实验被遗漏。不要只测试字段名字。
- `python3 -m unittest discover -s tests -v` 是框架检查命令。
- 实验记录与正文不允许使用虚构成绩。测试样例只可存在于临时目录，不得作为真实研究输出。
- 新建技能遵循渐进加载；把阶段细则保留在 references，不把全部手册塞进入口。

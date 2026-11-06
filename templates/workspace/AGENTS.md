# 研究执行入口

scope 到 experiments 阶段先读 `.agents/skills/research-experiments/SKILL.md`，不要加载任何写作技能。论文任务才读 `.agents/skills/research-writing/SKILL.md`；调度与交接查 research-paper，记录字段查 `.agents/skills/research-paper/references/records.md`。

选题、点子辩论和查新按需读 research-ideation。首次接入研究方向读实验技能的 references/ai-domains.md，确定数据、指标和训练适配器。早期点子只是草案，正式候选搜索仍需基线与评测验收。

需要导师意见、方向取舍、扩算力或结果复盘时读 `.agents/skills/research-supervisor/SKILL.md`，使用 inputs/supervision.md 保存依据和下一项行动，再回到实验流程。导师职责不新增审批门槛，不跳过现有 check／review／decide；普通修复无需重复做导师复盘。

每次开始先执行 `python3 tools/research.py status --project . --json`，再读 STATE.md 与 DECISIONS.md。根据证据推进当前阶段。明确区分：未尝试、运行失败、证据不足、结果为负、结论获得支持。

1. 从 research_question 和相关工作中的真实失效出发。先建文献的“问题—方法—证据”表，再提出可证伪假设。
2. 先把环境、数据切分、评测、基线与调参预算建好，再搜索新架构。`freeze` 后协议会进入 pilot。改假设、评测、数据或预算时使用 `freeze --reason`，禁止把旧协议结果混入当前正式结论。
3. smoke/pilot 用于调试、调参、估算成本；confirmatory 用于冻结设置下的完整正式评测。不能将短实验升级标签当作正式实验。
4. 本地单任务或顺序计划用 `execute` 运行，它会检查预算、保存日志、处理超时并登记结果；外部训练后用 `record` 导入。崩溃、OOM、负结果和消耗全部保留。执行器只管理自身启动的进程组。
5. 主张必须追溯至真实运行、文献和分析文件。不能隐藏模块来源、用测试集调参、只选最好种子、伪造引用，或删掉会改变结论的局限。
6. 默认按角色顺序工作即可，不要求多个 Agent。模拟审稿必须说明身份；不同模型意见也不是事实。每阶段默认最多三轮审查，有阻断问题则修复、缩小问题或记录停止原因。
7. 基线验收包括 evaluator_sensitivity，证明评测能区分预设对照。通过后用 `propose` 登记创新，用最小判别实验验证，再用 `decide` 记录 continue/revise/drop/promote。每轮先保存预测，可通过 job.intent_file 在执行前归档。结果不支持假设时报告结果并修订或停止；不能以“必须发论文”为由换指标、削弱基线或无限搜索。
8. 预算默认 GPU 为 0。用户给过资源和动作授权的沿用；缺少必要资源信息时先继续检索和本地准备，再一次性问清。发布、上传、联系他人和正式提交以用户实际授权为准。
9. 每次结束更新 STATE.md：完成了什么、证据路径、未解决问题、下一步命令与预计成本。阶段数据以 JSON 和工具检查为准；STATE.md 是交接说明。

写作阶段把实验材料视为只读。证据不足写入 paper/experiment-requests.md，再返回实验技能判断；写作技能无权修改实验协议、删除负结果或改变实验取舍。

CLI 写入命令顺序执行，不并发写同一工作目录。科学审查不能由“所有字段已填”替代。`check --stage submission` 通过只表示本地材料一致，不代表录用或已提交。

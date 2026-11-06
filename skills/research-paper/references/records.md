# 记录格式与工具行为

命令在研究工作目录内使用 `python3 tools/research.py`；在框架仓库内也可用 `python3 scripts/research.py`。只有框架仓库版本包含用于 `init` 的模板。路径参数可为绝对路径；JSON 内的证据路径必须相对于研究目录，不允许越界或通过符号链接访问目录外文件。

## project.json 与阶段

保留 `schema_version=1`。填写 topic、research_question、contribution、constraints、target_venue。stage 由 advance/freeze 维护，active_protocol 由 freeze 维护。预算：

```json
{
  "max_runs": 50,
  "max_gpu_hours": 0,
  "max_gpu_hours_per_run": 0,
  "max_wall_hours": 2,
  "max_wall_hours_per_run": 0.5
}
```

零 GPU 预算可进行 CPU 工作。总运行数、GPU 小时和墙钟运行小时包含 smoke、pilot、失败运行以及所有旧协议。墙钟预算字段对旧目录可选，新模板默认提供。`execute` 管理自己启动的进程组并在运行前做预算预检；`record` 导入外部记录，超预算仍保存真实运行，返回非零，使阶段检查失败。GPU 小时按运行占用卡数乘墙钟时间计算，不按利用率打折。预算修改也是协议变更。

`status` 显示当前缺项但正常返回 0，方便恢复任务。`check` 累计检查至当前或 `--stage` 指定阶段，每阶段报告首先发现的错误；补齐后继续检查。`advance` 通过当前阶段的累计检查后推进一步。freeze 会验证 scope/literature/hypothesis 与协议，首次或新版本冻结后直接进入 pilot。

## literature.json

- `searches`：非空数组，每项有 query、source、searched_at。记录真实检索，不用“AI 说没有”代替检索。
- `papers`：非空数组，id 唯一；每项有 title、url、problem、mechanism、evidence、limitations、accessed_at。
- `relevance`：direct / transfer / context；`read_status`：abstract / full；`source_checked` 为核查原始来源后手工填写的布尔值。
- `synthesis`：跨论文的判断。至少一篇 direct + full 是结构下限，检索充分性不由计数证明。

id 同时作为 BibTeX key，推荐 P001。evidence 给出表/图/章节位置，limitations 写真实限制，不使用“无”掩盖未读。工具不会联网核查论文。

## hypothesis.json

必填 baseline_failure、explanation、intervention、falsification、novelty、evidence_cost。predictions、alternatives、related_work_ids 均为非空字符串数组；related_work_ids 必须已登记。数个不兼容问题应拆成不同研究目录，不把每次失败都改写为最初目标。

## protocol.json

模板给出完整字段。数组条目使用：

```json
{
  "datasets": [
    {"id": "D1", "version": "真实数据版本或校验和", "split_manifest": "artifacts/splits.json"}
  ],
  "baselines": [
    {"id": "B1", "rationale": "来源、代码版本、为何是合理强基线", "tuning_budget": "实际搜索范围与预算"}
  ],
  "candidates": [
    {"id": "C1", "rationale": "干预及要验证的机制", "tuning_budget": "与基线的资源关系"}
  ],
  "ablations": [
    {"id": "A1", "rationale": "去掉什么，以检验哪条解释", "tuning_budget": "控制条件"}
  ]
}
```

以上是字段示意，必须换成实际设置；其他必填字段不要删除。

- 主指标 name 非空，direction 为 min/max。种子是非重复非负整数；默认三种子，可根据任务调整。
- uncertainty 说明不确定性来源、独立单位与计划分析；n=1 的汇总 std 为 null。
- baselines 非空；candidates/ablations 可以为空，允许只搭基线环境再提出方法。ablation_rationale 必须解释本轮设计，机制主张另要求消融证据。
- 模型可提供 code_artifact 和 config_file，路径纳入冻结指纹。用 execute 跑 confirmatory 时这两个字段必填，任务代码快照需与冻结模型相符。代码包应包含所有执行代码和依赖配置，不能只存一个无关文件。
- fairness 的 axis/rationale/tuning_policy/capacity_control 填具体控制方式；selection_split 固定为 validation。
- environment_file 和 evaluation_file 必须是实际非空文件。每个 split_manifest 同样必须存在，内容与实际切分一致。
- stopping_rule 说明训练/早停及研究搜索的停止规则，不能写“直到比基线好”。

freeze 保存到 `protocols/<sha256>.json`；指纹覆盖假设、研究问题、贡献、预算、协议及上述文件内容。仅改变 JSON 空格不会改变协议，改变任何被覆盖的内容会使 current 检查失败。修改已有协议需 `freeze --reason`，新旧正式结果不混合；旧消耗仍累计。历史协议文件不得覆盖，不能通过返回旧配置反复挑选结果。新版本需基线短回归和审查，旧长实验保留，不改标签充当新结果。

## 执行任务、创新提案与决策

`execute --file inputs/具体任务.json [--dry-run]` 接受一项 job，或 `{"jobs": [job, ...]}` 的顺序计划。全部字段和适配器接口见 [execution.md](../../research-experiments/references/execution.md)。预检使用 timeout_seconds 加 5 秒终止余量，执行结果用实际耗时；失败即停。退出 1 表示已归档的失败或预算超限，2 表示参数/阶段/协议错误。出现未登记执行时保留原始证据并先恢复，不能悄悄重试。

`propose --file inputs/具体提案.json` 要求当前基线 pilot 检查通过。输入模板见工作目录 inputs/idea.json。提案保存为 `ideas/<id>/proposal.json` 和校验摘要，绑定当时的基线协议、失效证据及已核实近邻。模型 id 可以是尚未加入协议的新候选；先设计最小实验，再实现候选并修订协议。

`decide --file inputs/具体决策.json` 读取已登记提案，要求实际候选运行和分析证据。action 为 continue/revise/drop/promote；保存为 `ideas/<id>/decisions/<decision-id>/decision.json`，同时追加 DECISIONS.md。promote 还要求当前协议下候选与全部基线的 completed validation pilot，共享至少一个 dataset/seed 单元，并填写 confirmation_plan。工具不会根据分数替你判断创新是否成立。

`next --project .` 输出阶段缺项、每个提案的最近决策、下一项实验及累计预算。提案和决策的证据使用每轮独立文件，不能复用路径覆盖历史解释。修改提案用新 id，保留 predecessor 信息在说明中；决策迭代用新 decision id。

## 登记运行

本地 execute 会自动登记。使用已有调度系统时，运行前固定 kind，运行后填输入文件，再用 `record --file` 登记。输入示例：

```json
{
  "id": "R001",
  "protocol_sha256": "替换为 freeze 输出的完整 SHA-256",
  "kind": "pilot",
  "status": "completed",
  "model_id": "B1",
  "dataset_id": "D1",
  "seed": 17,
  "evaluation_split": "validation",
  "command": "实际执行的完整命令与工作目录",
  "code_revision": "实际 Git commit；存在未提交改动时注明并纳入代码快照",
  "code_artifact": "artifacts/R001/source.tar.gz",
  "environment_file": "artifacts/environment.txt",
  "log_file": "artifacts/R001/stdout.log",
  "metrics_file": "artifacts/R001/metrics.json",
  "elapsed_seconds": 12.5,
  "gpu_count": 0,
  "notes": "实际设置、超参配置路径和其他运行说明"
}
```

kind 为 smoke / pilot / confirmatory。evaluation_split 为 train/validation/test/unknown，旧外部记录省略时为 unknown，不能用于候选晋级。smoke/pilot 不允许用 test 选方法。completed 的 metrics_file 是非空平坦 JSON 对象，例如 `{"mse": 0.123}`；该示例数字只是格式示意。pilot/confirmatory 必须包含协议主指标；smoke 可以只记录实际正确性检查读数。所有值均为有限数字，允许负指标，不接受 bool/NaN/Infinity。命令需要含全部配置参数或明确引用已归档的配置，保证可复现。可选 config_file、intent_file 随代码、环境、日志一起复制归档；intent 保存原预测和反证条件。execute 对 intent_file 在启动前快照，外部 record 仅能证明导入内容，不能证明它是事前预测。

失败记录用 `status=failed`，补 failure_reason，不要求 metrics_file，但代码、环境、日志和真实耗时仍需保存。所有运行 id 唯一，只允许安全文件名字符。model/dataset/seed 必须在协议中。

record 不执行命令。它复制证据到 `runs/<id>/`，保存结构化 record.json 与校验摘要；原始输入文件之后改动不会影响归档证据。归档被改会使后续校验失败。同一协议、模型、数据和种子的正式完成记录只能有一个；同单元失败后可重试。

## pilot.json

填写 protocol_sha256。六个必要检查名为 data_leakage、metric_correctness、evaluator_sensitivity、gradient_or_equivalent、tiny_overfit、baseline_reproduction，可添加额外检查。

每项用 status=pass/na、reason、artifacts（项目内实际文件路径数组）。evaluator_sensitivity 必须 pass，不能用 na 跳过；其证据包括预设对照、预期、实际读数和适用边界，见实验技能的 evaluator-validation.md。其他检查的 na 也要有理由和等价检查证据。每个 baseline/dataset 还需要至少一次有记录的 completed pilot 运行。通过短检查不意味着已复现完整论文，复现范围和差异写进证据。旧目录升级需补此项并复审，不删除旧结果或覆盖已有材料。

## 登记审查

审查者先阅读对应材料，再写输入文件并执行 review。默认每阶段最多三轮；工具保存记录，不自动终止模型的循环。

```json
{
  "id": "REV-pilot-01",
  "scope": "pilot",
  "protocol_sha256": "替换为当前 SHA-256",
  "reviewer": "实际模型或人员，以及是否同一 Agent 角色自查",
  "assessment": "已检查什么、发现什么、哪些仍未知",
  "issues": [
    {
      "id": "I001",
      "severity": "major",
      "description": "具体问题",
      "evidence": "代码位置、日志或结果文件中的依据",
      "status": "open"
    }
  ]
}
```

scope 为 pilot/experiments/paper。工具绑定当前协议以及被审材料的哈希：pilot 的检查与基线 smoke/pilot；experiments 的汇总、分析和正式运行；paper 的主张、正文、文献、汇总和正式运行。后续被审材料改变需要新审查。候选探索和正式运行新增不会让基线 pilot 审查过期；协议变化仍需重新验收。

问题 severity 为 blocker/major/minor；status 为 open/resolved/accepted。resolved 或 accepted 还需 resolution 和非空 resolution_artifacts 路径数组。blocker 不能直接 accepted；major 可以有证据地接受，但必须在论文中反映范围限制。各轮按稳定 issue id 累计，旧的重要 open 问题不能靠省略或降低级别来消失。若初始判断有误，保留原严重级别，在 resolved 的 resolution 中给出修正判断与证据。没有发现问题时 issues=[]，assessment 仍说明检查范围，不写“保证无 bug”。

修复证据在登记时绑定哈希；后续复测使用新文件，不覆盖过去的修复证明。

## 汇总与主张

summarize 生成 `reports/summary.json` 和 `.md`。正式实验网格缺单元、预算超限、汇总过期或存在重要未关闭问题会使 experiments 检查失败。需自行完成 reports/analysis.md。

claims.json 的条目示意：

```json
{
  "claims": [
    {
      "id": "C001",
      "text": "由实际证据支持的具体表述",
      "kind": "empirical",
      "status": "qualified",
      "included_in_paper": true,
      "scope": "实际评测的条件",
      "limitation": "结论边界",
      "location": "摘要、4.1 节、表 1",
      "run_ids": ["实际正式运行 ID"],
      "paper_ids": ["P001"],
      "artifacts": ["reports/analysis.md", "reports/summary.json"]
    }
  ]
}
```

kind 为 empirical/mechanistic/literature。前两类必须引用当前正式完成运行；mechanistic 还要引用协议中的 ablation。literature 必须引用已登记文献，可无运行。每项都有分析证据路径。正文用 `[@P001]`，与文献 id 和 BibTeX key 对应。工具只核对结构，不能证明一句机制或因果表述成立。

## 投稿材料与退出码

submission.json 的每项检查用 status=pass/na、reason、artifacts。package_files 包含实际包内全部提交文件；pdf 指向最终 PDF。工具只检查 PDF 文件头，最终渲染质量、匿名性和与初稿一致性必须实际检查并留下证据。它不会发起投稿。

- 0：命令成功；status 即使显示缺项也返回 0。
- 1：check 未通过，或 record 已保存但预算超限。
- 2：参数对应的数据/文件错误、协议不一致或其他操作被拒绝。

没有任何命令会把“本地检查通过”改成“科学结论被认证”。归档应纳入自己的版本控制或备份；当前校验不抵御有意同时篡改文件与摘要。CLI 写入命令只支持单写入者，顺序执行。

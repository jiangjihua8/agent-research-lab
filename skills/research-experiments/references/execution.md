# 跑实验：从短测到正式确认

## 按疑问分配训练预算

| 层级 | 要解决的问题 | 执行内容 | 可以推出的结论 |
| --- | --- | --- | --- |
| smoke | 程序能正确走通关键路径吗 | 前反向、有限值、梯度、保存恢复、设备、批次形状 | 本次覆盖的路径未暴露这些错误 |
| pilot：正确性 | 数据与评测可信，基线训练正常吗 | 小样本过拟合、指标手算、标签扰动、泄漏检查、官方结果对照 | 环境与基线在已检查范围内可用 |
| pilot：判别 | 哪个解释更符合证据，是否值得继续 | 验证集、最小干预、机制诊断、等预算对照、成本探针 | 某候选值得继续、修改或淘汰 |
| confirmatory | 冻结方法后的结论在目标范围是否成立 | 独立测试、完整训练、重复、消融、尺度或分布检查 | 与已测条件、统计不确定性相称的正式证据 |

视频的“五秒”属于第一层；它不是排名预算，也不能替代小数据过拟合、指标核对或基线复现。层级按证据用途划分，不按固定秒数划分。

## 基线先行的执行顺序

1. 读论文和官方实现，记录真实版本、数据、指标及复现目标。用 `inputs/baseline-card.md` 整理每个基线，不只记录论文表格中的最好数字。
2. 实现数据、训练、验证、测试的公共接口，验证切分和指标。简单方法和强近邻方法共享同一评测。
3. 初始 protocol 可以只有 baselines。冻结后先 smoke，再 pilot；在公平且可负担的调参预算内把基线调好，解释复现偏差。
4. pilot.json 每项附证据，包含评测有效性验收；登记 pilot 审查。基线/数据集的 pilot 覆盖完整后才开始候选探索。
5. 提出候选，固定新增实现及其测试计划，`freeze --reason`；新版本做基线短回归与审查。候选参数和指标在 validation 选择。
6. 达到 promote 条件后，固定完整方法与配置，再冻结正式协议；先短回归确认，再运行正式计划。旧结果继续保留，不改标签充当新实验。

协议冻结的是该轮要运行的设置。调参范围可以先写入协议，再在 validation 内执行不同配置的 pilot；选定配置后把模型 `code_artifact` 和 `config_file` 纳入正式协议。对同一模型的正式种子运行使用相同代码和训练配方。

## 训练程序的输出接口

已有训练代码不必重写成某个框架。增加一个适配器：从下列环境变量取输出路径和本次设置，训练后写一个非空、平坦的 `metrics.json`。所有指标必须为有限数值；pilot/confirmatory 含 protocol 的主指标。smoke 可以只报告实际通过的正确性检查数，无须为了通过检查编造基准成绩。

| 环境变量 | 内容 |
| --- | --- |
| RESEARCH_OUTPUT_DIR | 本次唯一绝对输出目录 |
| RESEARCH_SEED | 当前种子；训练器还应设置 Python、NumPy、框架与数据加载随机性 |
| RESEARCH_MODEL_ID / RESEARCH_DATASET_ID | 当前模型与数据集标识 |
| RESEARCH_EVALUATION_SPLIT | train / validation / test；适配器必须真的选择该切分 |
| RESEARCH_PROTOCOL_SHA256 | 当前协议指纹 |

例如，训练代码**已有真实计算结果**后可用如下写出方式：

```python
output = Path(os.environ["RESEARCH_OUTPUT_DIR"])
# measured_metrics 来自本次实际评测，不填常量占位成绩。
(output / "metrics.json").write_text(
    json.dumps(measured_metrics, allow_nan=False), encoding="utf-8"
)
```

保存逐样本预测、诊断、checkpoint 和完整配置到该目录或 artifacts，并在分析中引用。运行记录自动复制代码快照、环境、stdout、标量指标以及协议中声明的模型配置；其他文件如参与主张，需要登记为分析证据并纳入自己的备份。

执行器声明的 seed/split/gpu_count 不是对训练代码内部行为的认证。Agent 必须核对适配器实际使用这些设置、资源设备及冻结配置；不能在 JSON 写 validation、代码实际读 test。

## 任务文件与执行

从 `inputs/job.json` 复制为具体任务。示意：

```json
{
  "id": "B1-D1-pilot-s17",
  "protocol_sha256": "填写当前完整指纹",
  "kind": "pilot",
  "model_id": "B1",
  "dataset_id": "D1",
  "seed": 17,
  "evaluation_split": "validation",
  "argv": ["python3", "src/train.py", "--config", "configs/baseline.json"],
  "code_revision": "实际 commit 和未提交改动说明",
  "code_artifact": "artifacts/source.tar.gz",
  "environment_file": "artifacts/environment.txt",
  "gpu_count": 1,
  "timeout_seconds": 300,
  "notes": "本次要检查的假设与读取的配置"
}
```

这只是格式示意；要换成自己的实际路径和已分配预算。argv 是参数数组，不使用 shell 字符串、管道或重定向。额外环境需求可由受版本控制的适配脚本设置。

运行前从 `inputs/experiment-intent.md` 写出预测、竞争解释和判断规则。任务可添加 `"intent_file": "artifacts/intent-round-001.md"`；执行器在启动前复制归档，随后作为运行的 intent 证据保存并校验哈希。该字段兼容旧任务，可省略；省略时不能声称工具已保存事前预测。外部 `record` 也能附此字段，但回顾性导入不能证明文件形成于运行之前。

```bash
python3 tools/research.py execute --project . --file inputs/run-001.json --dry-run
python3 tools/research.py execute --project . --file inputs/run-001.json
```

批量计划用 `{"jobs": [任务对象1, 任务对象2]}`；逐项顺序运行，失败即停。计划应属于同一轮可比实验，不跨越需要审查或科研决策的关口。先按整个计划的最大消耗检查预算，避免跑了一半才发现无法完成。

执行器会：

- 检查当前协议、任务单元、环境、预算；候选运行需基线验收，正式运行还需相应模型/数据集的 pilot，以及被冻结的源代码快照和配置。
- 建立唯一 `executions/<id>/`，保存任务与启动记录，捕获 stdout/stderr，测量实际耗时。
- 超时或中断时终止本次 POSIX 进程组；错误退出、缺失指标、非有限指标均记为 failed，保留消耗并停止计划。
- 把本次记录导入 `runs/<id>/`。失败重试使用新 id，不能覆盖先前失败。

smoke 允许 train/validation，pilot 使用 validation，confirmatory 使用 test。外部执行的实际记录可用 `record` 导入，执行前的科研准入和预算责任仍属于执行者。

## 预算与中断恢复

project.budget 的 max_runs、max_gpu_hours、max_gpu_hours_per_run，以及可选 max_wall_hours/max_wall_hours_per_run 控制本地计划。墙钟小时是各次运行耗时之和，CPU 同样计入。GPU 小时按占用卡数乘耗时计算。

预检用 timeout_seconds 加 5 秒终止余量估算最大成本，实际账本用测量耗时。默认 GPU 为 0，CPU 总运行时间上限 2 小时、单次半小时；这是模板的保守起点，按用户已给出的资源填写。执行器不会采购算力，不会侦测或限制其他进程、GPU 显存、网络 API 费用，也不是容器沙箱。

写入者必须串行；执行期间不要运行 freeze/record 或修改冻结文件。硬中断时：

1. 查看 `.execution.lock`、executions 中的 started/job/stdout，核对实际进程是否仍在运行；有进程先恢复监控或终止，不直接删锁重跑。
2. 对照实际日志和调度账本恢复耗时。若已存在 record-input.json，核对后用 record 导入；没有则按 records.md 建失败运行输入，不能把未知消耗记为零。
3. 如协议在运行中被外部改动，先恢复本次实际使用的冻结材料完成归档，再按新事实建立版本，不把结果重新挂到不相符的协议。
4. 确认本次进程结束且证据已登记后清理残留锁；用新 id 再执行。

存在未登记 executions 目录时，执行器拒绝再次开跑。该约束用于防止崩溃后遗漏成本；原始日志不会因此被删除。

## 每轮实验后的最小交付

用 `inputs/round-report.md` 记录：原预测、实际执行、全体结果、是否有实现或公平性问题、解释、决策、下一项实验和预算余额。先检查机制诊断再看是否值得扩大；某个主指标好看并不自动晋级。

`decide` 保存取舍，`next` 显示各候选最近决策和已用预算。正式网格完成后运行 summarize，写 analysis 并做 experiments 审查。基线未验收、证据不一致、关键问题未关闭或预算不足时，先解决这些具体问题。

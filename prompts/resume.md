恢复当前研究。先运行 `python3 tools/research.py status --project . --json` 和 `next --project .`，再读 AGENTS.md、STATE.md 和 DECISIONS.md。实验阶段只读 research-experiments，论文任务才读 research-writing。

确认冻结协议、已有运行和当前阻断问题，检查记录的原始证据仍存在。不要重跑已完成的昂贵实验，也不要重置旧失败记录。沿用已有授权，在预算内完成当前阶段最有信息量的一步。需要改变假设、数据、评测或预算时保留理由与历史版本。

如果有执行锁或未登记 executions，先核对进程、真实消耗和日志，按 execution.md 恢复；不要删记录来获得一次不计成本的重试。

交付实际变更、检查结果、科学判断仍不确定的部分，以及下一步预计成本。更新交接文件后结束本轮。

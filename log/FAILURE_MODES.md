# 失败与阻塞记录

- **Agent synergy 未复现**：matched pilot 和 GCP transfer 均未超过 deterministic baseline；保留数据和负结论。
- **Closed-loop P2 未确认**：MAESTRO_LOOP 23 vs CONV_LOOP 18，p=.18；不得宣称闭环优势。
- **Knowledge gain 是机制类别混淆**：gene relabelling 重现增益，target/context/provenance 路线无增益。
- **Prediction-as-evidence**：把预测写入证据导致 15 个 false NO-GO；所有决策必须经过 measured-evidence admission。
- **Endpoint 单位错误**：历史 test viability 被错误按百分比除 100；修复为 metadata/固定单位读取，并保留 excluded run 与偏差说明。
- **机制真值缺失**：本地 61,413 对注释无 measured positive/negative reference；benchmark 不能替代科学验证，状态为 `ASSET_BLOCKED`。
- **冷启动与泛化弱**：transfer 增益依赖已声明 source/assay/context；不得外推为通用药物发现能力。

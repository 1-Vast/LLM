# Lead 裁定：ON3 执行溯源偏差 → 走严格修复（Option B），不采用元数据豁免

2026-10-27 23:0x。事实：ON3 v1.1 执行技术完成（B6 5,000 real perms refit_cu_only、bootstrap 5,000、两跑逐字节一致；provisional on3_exec.json SHA `5698151968…`；wall 1173.78/1298.86 s > 冻结预算估计 <15 min，须登记 runtime deviation）；但 `run_on3_exec.py`（批准 SHA `41D2BC2C…`）在输出的 `protocol` 与 `inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 写入了**旧 invalid spec**（`8B4B8FCC…`/`41BC637C…`），而 Lead 批准的是 v1.1（`8C4B2D9B…`/`14A6E1E3…`），且明文规定旧 SHA 不得引用/用于批准。执行语义（数据/切分/mask/B4/B6/指标/阈值/两跑）未受影响，但**正式证据链不得携带 invalid spec SHA**。

## 裁定：Option B（严格修复 + 重跑一次）

1. **不采用 Option A**：provisional 结果（Δρ_mean=0.0730667、CI [0.04746,0.10031]、5/5 folds 正、verdict `no_increment`）**保持 quarantine、不得引用、不得登记为结果**；不得以"结果不变"为理由发布。
2. **批准 AMEND-001.3 / v1.2（仅溯源修复）**：只改 `run_on3_exec.py` 的 input 路径/SHA 字段为批准的 v1.1 protocol `8C4B2D9B…`/freeze `14A6E1E3…`（及必要 schema 字段名），**不得改执行语义/数据/切分/mask/超参/rank/λ/指标/差值规则/B6 置换数/bootstrap**；给出精确代码 diff、15/15 单测、两跑 selfcheck 预检、新 v1.2 protocol/freeze SHA（仅溯源变化，其余逐项不变）。
3. **授权重跑 ON3 一次**（v1.2；non-blind/peeked，仍受 PEEK_DISCLOSURE_ON3 限制）：full B6 1,000×5 refit_cu_only、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap；正式产物 `on3_exec.json`/`report_on3_exec.md`/`record_on3_exec.md`/`usage_on3_exec.json` 必须写入正确 v1.2 SHA 链；报告含 `peek_disclosure` 与 **runtime deviation（wall≈19.6/21.6 min > 冻结估计 <15 min，仅计时偏差、未改设计）**。
4. **结果解释边界（不变）**：仅 O'Neil 内部开发性描述（non-blind/peeked）；不称盲验/独立确认/迁移/决策收益/机制/新颖性；`no_increment` 只表示"未达到预注册 δ_min=0.10 描述性增量"；Δρ 点估计 0.0731、CI [0.0475,0.1003]、5/5 folds 正仅描述性，不得写成结构成立/不存在、迁移或决策证据；冻结≠资源足够/关系成立/Stage1/效果。
5. **审计链**：旧 provisional artifacts 保持 `tmp/*_provisional.*` quarantine；oneil_dev 中不得存在携带旧 invalid spec SHA 的正式 on3_exec；最终 Lead 复核以 v1.2 freeze SHA + 正式产物 SHA 为准。

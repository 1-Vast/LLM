# Lead 批准并冻结 ON3 execution protocol（approve_freeze_exec）

2026-10-27。依据：ON3-READY.3-C1 最终确认（task-77）判 approve_freeze_exec；全链 SHA/预算/15 单测/两跑/raw 5,000/reconstruction 一致；无剩余必改。**Lead 批准并冻结，授权执行 ON3 开发性描述分析（仅执行一次，执行时报告实测 wall/bootstrap；结果只能写开发性描述）。**

## 冻结文本
- 冻结文本：`FREEZE_ON3_exec.md` SHA256 `41BC637C6BE391E2609B478A717CBF367A10A0EC7A262CA7E12551178B34C2E1`
- execution protocol：`PROTOCOL_ON3_exec_DRAFT.md` v0.3 SHA256 `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336`
- record `92EC25CD…`；usage `252E59D7…`；budget `4D08670F…`；refimpl `B5485B23…`；test_refimpl `B36D1FCF…`；test_results `8E17572B…`（15/15 OK）；selfcheck.py/json `032F2149…`/`2B0537A1…`（两跑一致）；reconstruction `DC93D4FE…`（target30 0/157,768；per fold 0）；data_prep `7C11B0C5…`；raw `F81DCC09…`/`0ABE96F0…`/`38A3B9F3…`（5,000 perms / 306.722 s）
- 冻结值：B6 `refit_cu_only` **1,000 置换**；预算 **306.722 s**（308.086 仅 early history；693.34 撤回；full_refit 不采用）；执行总预算 measured <15 min。

## 执行授权与边界
- 允许：按冻结协议执行 ON3 一次（O'Neil 内部 complete-case 开发性描述）；执行时记录实测 wall/bootstrap、两跑确定性（若代码未变可复用）。
- 必须遵守：仅 O'Neil 内部开发性描述；**不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性**；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**；不运行效果/更新器（ON3 本身即开发性描述）。
- 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；发现实现偏差须停并重新预注册；结果写 `report_on3.md`/`record_on3.md`/`usage_on3.json` + 输出 SHA。
- 阴性只能写"本资源/本设计下无描述性增量"；不得写结构不存在/迁移/决策收益。

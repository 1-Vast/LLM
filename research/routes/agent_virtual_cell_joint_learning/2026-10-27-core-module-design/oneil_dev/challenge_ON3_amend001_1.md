# R199-ON3-AMEND-001.1-C1 独立复核（challenge_ON3_amend001_1.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 AMEND-001.1 起草）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{AMENDMENT_ON3_EXEC-001.md v0.2, AMENDMENT_ON3_EXEC-001_delta.md, PROTOCOL_ON3_exec_v1_1_DRAFT.md, FREEZE_ON3_exec_v1_1_DRAFT.md, on3_refimpl/, report_on3.md, record_on3.md, usage_on3.json, record_on3_amend001.md, usage_on3_amend001.json}` + `tmp/on3_amend001_1_code.diff` + `tmp/on3_exec_quick_debug.invalid.json`。
方式：**只读复核**（草案/diff/代码 diff/15 单测/两跑/既有 QUICK invalid artifact；**不运行 ON3、不解析原始响应值做统计、不改产物**）；只写本文件与 `tmp/`。
完整性：`AMENDMENT_ON3_EXEC-001.md` v0.2 **`EC0A3E9313F33D181B978F7886F01D0631B5353B18FF5C5EC026AC8FB750C5A1`**；`AMENDMENT_ON3_EXEC-001_delta.md` `9B397B56…`；`PROTOCOL_ON3_exec_v1_1_DRAFT.md` **`DC4C40829F744DF67D160BD5F20DF2547583ACF9C980A8FBD89BD5EBC643F6FF`**；`FREEZE_ON3_exec_v1_1_DRAFT.md` **`DA4D787E91EE64E3F80F5D113813C815940AFFB97384BA14A3D9BDC42AF2E686`**；code diff `1F1AA05E…`；refimpl `AD1C54D5…`、run `41D2BC2C…`、test `25B6E410…`/test_results `6282E395…`、selfcheck `7F3EDA17…`/`3EB44C25…`；QUICK invalid `39868CE4…`/usage `60DB423C…`——均与记录一致。

## 0. 总判决

**revise（≤5 必改；当前不可 approve_to_lead；不是 stop）。**
AMEND-001.1 已把上一轮 5 条中的大部分闭合：QUICK 完整披露并改名 `.invalid.json`；代码 diff 仅 null gate 条件+输出字段；15/15、两跑 SHA 一致；v1.1 protocol/freeze 新 SHA 与旧 invalid spec 标记齐；QUICK 未用于选择。但 **task-82 ④ 的 peek 限制没有写入**：有效 v1.1 执行是**非盲**（实现方已见 QUICK 的 result-shaped primary），v1.1/freeze/AMEND/report/usage 未明确披露“peek/非盲”、未限制解释（不得称盲验/独立确认；结论仅开发性描述并带 peek 披露）。另外 QUICK 改名后 **旧路径仍在多处文档/usage 残留**，且 **v1.1 freeze 全链表缺更新后的 report/record/usage 等 SHA**。这些是文档/披露层 must-fix；修完可 approve_to_lead。

**最致命 3 条**

1. **peek 限制缺失（task-82 ④）**：`tmp/on3_exec_quick_debug.invalid.json` 已被实现方看过，并含 primary/results（Δρ 0.0277068、CI、4-of-5、B0–B5 metrics）；因此 v1.1 的有效 full-run 是 **non-blind/peeked**，不能写成盲验、预注册确认或独立确认。当前 AMEND v0.2/FREEZE v1.1/PROTOCOL v1.1/report/record/usage 只写“QUICK invalid、不得引用、no independent confirmation”之类，**没有 explicit peek 披露与解释限制**。必须写入：peek 事实、非盲性质、结论仅开发性描述、不得称盲验/独立确认/迁移/决策收益/机制；执行报告必须带 peek 披露。
2. **QUICK 旧路径残留**：改名后旧 `tmp/on3_exec_quick_debug.json`/`tmp/usage_on3_quick_debug.json` 已不存在，但 `report_on3.md`（§3 line37/§6 line60）、`record_on3.md`（line54）、`usage_on3.json`（`quick_debug_settings.note`）仍写旧路径；正确路径应 `.invalid.json`。这直接违反 task ① “旧路径不存在/QUICK 已隔离”的一致性。
3. **v1.1 freeze 全链缺更新后的 stop/审计文件 SHA**：`FREEZE_ON3_exec_v1_1_DRAFT.md` 表 1–24 包含 protocol/AMEND/delta/refimpl/run/test/test_results/selfcheck/reconstruction/data_prep/code diff/text diff/budget/old invalid/challenge/QUICK，但**未列**更新后的 `report_on3.md`、`record_on3.md`、`usage_on3.json`、`record_on3_amend001.md`、`usage_on3_amend001.json` 的 SHA；task ③ 要求 v1.1 全链 SHA 一致/完整，需补；否则 freeze 引用的 QUICK 更正记录不在链内。

## 1. 逐条确认（①–④）

### ① QUICK 披露/隔离 —— **PASS 主体；旧路径残留 FAIL**

- AMEND v0.2 §1.3/§6 完整披露：原路径→`tmp/on3_exec_quick_debug.invalid.json`（SHA `39868CE4…`）；QUICK=1/N_PERM=20/BOOT=100；无效执行（非 full run、无两跑）；含完整 schema primary/results：`delta_rho_mean=0.0277068`、CI95 [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、context-ablation/pure-cold、verdict=design_invalid；`null.n_perm=20` vs gate.n_perm=100 不一致；**不得作为结果引用**；正式 `on3_exec.json` 不存在≠无 result-like artifact；性质 **post-freeze, pre-valid-result**。**PASS（披露主体）**。
- 改名实际存在：`tmp/on3_exec_quick_debug.invalid.json` 与 `tmp/usage_on3_quick_debug.invalid.json` 存在；旧路径不存在。**PASS（隔离）**。
- **FAIL（残留旧路径）**：`report_on3.md` line37/60、`record_on3.md` line54、`usage_on3.json` `quick_debug_settings.note` 仍引用旧 `on3_exec_quick_debug.json`/`usage_on3_quick_debug.json`；应改为 `.invalid.json` 并明确 quarantine。
- **QUICK 未用于选择**：AMEND §2/§4 声明修订仅由 Δρ_null 定义/代数必然性决定；QUICK Δρ 0.0277<0.10 不构成正结果；**PASS**（声明上；仍需 peek 限制，见致命 1）。

### ② 代码 diff / 15 单测 / 两跑 —— **PASS**

- `tmp/on3_amend001_1_code.diff` 仅：
  - `run_on3_exec.py` null gate：`null_rho` → `null_drho`，输出字段 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`；
  - `refimpl.py` `null_calibration_gate(values, field_prefix='delta_rho')` + `validate_null_gate_schema`；
  - `test_refimpl.py` test_11 delta 字段；
  - `selfcheck.py` field_prefix；
  - **无 mask/指标/差值/阈值改动**；diff 内容与说明一致；**PASS**。
- `test_results.txt`：**Ran 15 tests OK（2.867 s）**；`test_11` 字段断言/正负例；**PASS**。
- 两跑：`tmp/on3_v1_1_selfcheck_run1.json`/run2 SHA 均 **`3EB44C25…`**，`selfcheck.json` 同 SHA；**PASS**。

### ③ v1.1 冻结链 / 旧 invalid —— **WEAK（SHA 实际一致；freeze 表缺 stop/审计记录）**

- 实际 SHA：protocol v1.1 `DC4C4082…`、freeze v1.1 `DA4D787E…`、AMEND v0.2 `EC0A3E93…`、delta `9B397B56…`、refimpl `AD1C54D5…`、run `41D2BC2C…`、test `25B6E410…`/test_results `6282E395…`、selfcheck `7F3EDA17…`/`3EB44C25…`、code diff `1F1AA05E…`、text diff `2AFF481E…`、QUICK invalid `39868CE4…`/usage `60DB423C…`——与 AMEND/FREEZE/record/usage 声明一致；**PASS**。
- 旧 protocol `8B4B8FCC…`、freeze `41BC637C…`、approval `F514347B…` 均标 **invalid spec, no valid execution**；**PASS**。
- **WEAK/FAIL**：FREEZE v1.1 表未含更新后的 `report_on3.md`/`record_on3.md`/`usage_on3.json`/`record_on3_amend001.md`/`usage_on3_amend001.json` SHA；task ③ 要求全链完整，需补；`FREEZE_ON3_exec_v1_1_DRAFT.md` 自身 SHA 由 Lead 批准文本引用（不可自引用），但 freeze 表应明确列出更新后的 stop/审计文档。
- **v1.1 只改 null gate/字段**：AMEND/FREEZE/protocol 声明；diff 支持；PASS。

### ④ peek 限制 —— **FAIL（核心缺失）**

- **事实**：QUICK invalid artifact 含 primary/results，已被实现方看到；v1.1 有效执行**不是盲验**。
- 当前 AMEND v0.2/FREEZE v1.1/PROTOCOL v1.1/report/record/usage **没有“peek/非盲”披露或解释限制**；仅写 QUICK invalid/不得引用/不称独立确认（一般边界），不足以满足 task ④。必须写：
  - 执行是 **non-blind / peeked**（实现方已见 QUICK primary、CI、positive folds、B0–B5 等）；
  - 不得称 **盲验/盲预注册/独立确认**；结论只能写“本资源/本设计下的开发性描述结果，带 peek 披露”；
  - 不得用 QUICK primary 选择指标/门槛/方向；修复理由仅代数必然；
  - 执行报告/结论必须包含 **peek disclosure**，并明确这是**探索性、非盲、非独立确认**。
- **PASS 其他**：AMEND 已披露 QUICK primary 且标注无效；没有把它当结果；成功标准未降（Δρ≥max(0.10,Q95_null)、4/5、bootstrap、null p≤0.05 不变）。

## 2. 必改（≤5；均为文档/披露/链补，不需跑 ON3）

1. **写入 peek 限制（最高优先）**：在 `PROTOCOL_ON3_exec_v1_1_DRAFT.md`、`FREEZE_ON3_exec_v1_1_DRAFT.md`、`AMENDMENT_ON3_EXEC-001.md`（§3/§5/§7）、`report_on3.md`/`record_on3.md`/`usage_on3.json`、`record_on3_amend001.md`/`usage_on3_amend001.json` 明确：
   - 实现方已见 QUICK invalid artifact 的 primary/results；v1.1 有效执行是 **non-blind/peeked**；
   - 不得称盲验、盲预注册确认、独立确认；结论仅开发性描述并带 peek 披露；
   - QUICK primary 未用于选择指标/门槛/方向；修复依据仅代数必然；
   - 执行报告必须记录 peek 披露。
2. **修旧路径残留**：`report_on3.md` line37/60、`record_on3.md` line54、`usage_on3.json` quick note 的 `on3_exec_quick_debug.json`/`usage_on3_quick_debug.json` 改为 `.invalid.json`，并注明 quarantine/不引用；保持 §0 更正一致。
3. **补 v1.1 freeze 全链 SHA**：把更新后的 `report_on3.md`、`record_on3.md`、`usage_on3.json`、`record_on3_amend001.md`、`usage_on3_amend001.json` 的 SHA 写入 `FREEZE_ON3_exec_v1_1_DRAFT.md` 表（以及 protocol/freeze 的引用链）；freeze 自身 SHA 由 Lead 批准文本引用；旧 SHA 不进批准文本。
4. **（建议）将 `FREEZE_ON3_exec_v1_1_DRAFT.md` 表补 AMEND delta/代码 diff 的语义注释**（已有 SHA，补充用途），便于 Lead 批准逐项核对；不阻断。
5. **（建议）在 `usage_on3_amend001.json`/`record_on3_amend001.md` 记 `peek` 字段/披露状态**；不阻断。

## 3. 若修完，Lead 批准文本（建议模板；当前不批准）

> **批准 AMENDMENT_ON3_EXEC-001 v0.2，冻结 ON3 execution protocol v1.1，授权执行一次（非盲/peeked，带限制）。**
> 修订依据：`AMENDMENT_ON3_EXEC-001.md` v0.2 SHA `EC0A3E9313F33D181B978F7886F01D0631B5353B18FF5C5EC026AC8FB750C5A1`；v1.1 protocol `PROTOCOL_ON3_exec_v1_1_DRAFT.md` SHA `DC4C40829F744DF67D160BD5F20DF2547583ACF9C980A8FBD89BD5EBC643F6FF`；v1.1 freeze `FREEZE_ON3_exec_v1_1_DRAFT.md` SHA `DA4D787E91EE64E3F80F5D113813C815940AFFB97384BA14A3D9BDC42AF2E686`；旧 v0.3 protocol `8B4B8FCC…`/freeze `41BC637C…`/approval `F514347B…` 标 invalid spec。
> 唯一改动：null gate 对象 `ρ_null` → `Δρ_null=ρ(B4_null)−ρ(B2)`，输出字段 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`；其余数据/切分/mask/端点/B2/B4/B5/纯冷/B6 1,000 refit_cu_only/bootstrap 5,000/指标/差值规则/MDE/schema/两跑/wall/失败类别/禁改项全部不变；成功标准未降。
> **peek 披露**：实现方已见 QUICK invalid artifact 的 primary/results（Δρ 0.0277068 等）；v1.1 执行是 **non-blind/peeked**，**不得称盲验/独立确认/预注册确认**；结论仅 O'Neil 内部开发性描述并带 peek 披露；QUICK artifact 不得引用，不用于选择指标/门槛/方向。
> 执行一次：full B6 1,000×5、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap；结果不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结≠资源足够/关系成立/Stage1/效果；发现实现偏差→停并重新预注册。

## 4. 复核证据与本轮边界

- 实际 SHA 见页首；代码 diff `1F1AA05E…` 仅 null gate/字段；15/15 OK（2.867 s）；两跑 `3EB44C25…`；QUICK invalid `.invalid.json` 存在、旧路径不存在（但文档残留旧路径）；v1.1 protocol/freeze/AMEND SHA 实际匹配。
- **本轮未运行 ON3、未运行效果/训练/更新器、未解析原始响应值做统计**；只读草案/diff/测试/SHA/既有 QUICK invalid artifact；只写本文件与 `tmp/`；未改冻结/草案产物。
- **当前不可 approve_to_lead**；修完 1–3 后可 approve_to_lead，再走 Lead 批准→冻结 v1.1→执行一次。冻结≠资源足够/关系成立/Stage1/效果；QUICK invalid artifact 不得引用。

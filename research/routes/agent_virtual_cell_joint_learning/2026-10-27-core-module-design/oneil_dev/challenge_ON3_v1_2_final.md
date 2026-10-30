# R199-ON3-v1.2-FINAL 验收复核（challenge_ON3_v1_2_final.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 v1.2 执行/修复）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{DECISION_ON3_PROVENANCE.md, AMENDMENT_ON3_EXEC-001_3.md, PROTOCOL_ON3_exec_v1_2_DRAFT.md, FREEZE_ON3_exec_v1_2_DRAFT.md, on3_exec.json, report_on3_exec.md, record_on3_exec.md, usage_on3_exec.json, on3_refimpl/}` + `tmp/on3_amend001_3_code.diff`。
方式：**只读复核**（文档/SHA/diff/测试/两跑日志/正式 JSON 元数据；**不运行 ON3、不读原始响应做统计、不改产物**）；只写本文件与 `tmp/`。
完整性：`DECISION` `6C2DFD55…`；`AMEND_001_3` `7AFCE1C9…`；protocol v1.2 **`B22A7FC7…`**；freeze v1.2 **`C69BA93E…`**；`run_on3_exec.py` `B3A5569E…`；diff **`EF43ACDE…`**；refimpl `AD1C54D5…`；test `25B6E410…`/`D93AAA06…`；selfcheck `7F3EDA17…`/`3EB44C25…`；**on3_exec.json `3A9F99D4…`**；report **`1F4CD991…`**；record **`EB38A73C…`**；usage **`17EA15FE…`**；PEEK `B4CAD955…`——全部与磁盘实算一致。

## 0. 总判决

**accept_final。可登记为 ON3 v1.2 最终结果（带 runtime deviation 与 peek/CI 解释边界）。**
v1.2 的溯源修复确为 **2 hunk / 6 行**（`run_on3_exec.py` 的 protocol/inputs.* 改 v1.2），执行语义/数据/切分/mask/超参/rank/λ/指标/差值/B6 5,000 real perms refit_cu_only/bootstrap 5,000 零改动；15/15 单测与两跑 selfcheck 一致；正式 `on3_exec.json` 的 protocol/freeze/inputs 全部为 v1.2，**无旧 invalid spec SHA**；两跑 `3A9F99D4…` 逐字节一致；门/结果自洽（`no_increment`）。
**无 fatal must-fix；以下 3 条是登记时必须写明的边界（不阻断 accept）：**

1. **runtime deviation**：wall **1272.06 / 1130.61 s（18.8–21.2 min）> 冻结估计 <15 min**；report/record/usage 已登记；仅计时偏差，未改设计/协议/置换数/成功标准/重跑非结果驱动。**登记时不得写“预算 <15 min 已满足”**；应写“observed 1272.06/1130.61 s, deviation registered, design unchanged”。
2. **`no_increment` 的证据边界**：Δρ_mean=.0730667<δ_min=.10，但 **95% CI 上界 .100310485 略高于 .10**；`no_increment` 只表示**点估计未达预注册 δ_min**，**不能据此声称不存在 δ 大小的增量/无效应**。report/usage 已列 CI；最终登记文本必须写此边界。
3. **peek/non-blind**：v1.2 执行 non-blind/peeked；report §0/usage 已披露；**不得称盲验/预注册确认/独立确认**；`on3_exec.json` 本身不含 peek/runtime 字段（由 report/usage 承载），登记文本须同时引用 report §0/usage 的 peek 与 runtime 段落。旧 v0.3 invalid spec 与 provisional v1.1 仅作为 quarantine/invalid 记录，不进入正式结果。

## 1. 逐条确认

### ① 溯源修复 / 正式链 —— **PASS**

- `tmp/on3_amend001_3_code.diff`（`EF43ACDE…`）仅 **2 hunk**：`inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 的 path/sha 从旧 invalid spec 改为 v1.2；`out.protocol` 的 file/sha 同步；**无其他 hunk**。代码 diff 只改溯源字段，执行逻辑/数据/切分/mask/超参/rank/λ/指标/差值/B6/bootstrap/两跑要求零改动。**PASS**。
- **正式 `on3_exec.json`**：`protocol.file=PROTOCOL_ON3_exec_v1_2_DRAFT.md`、`protocol.sha256=B22A7FC7…`、`freeze_sha256=C69BA93E…`；`inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 均为 v1.2；**无** `8B4B8FCC`/`41BC637C`/`F514347B`，无 provisional 引用。**PASS**。
- 旧 invalid spec 在 report/record/freeze 中仅以 **invalid spec/quarantine** 出现，未用于批准/正式输入；可接受为 provenance。**PASS**。

### ② 预检（15/15 / 两跑 selfcheck） —— **PASS**

- `test_results.txt` `D93AAA06…`：**Ran 15 tests OK（2.626 s）**；`test_refimpl.py` `25B6E410…`、`refimpl.py` `AD1C54D5…`、`selfcheck.py` `7F3EDA17…` 与 v1.1 相同，未变。
- 两跑 selfcheck：`selfcheck.json` `3EB44C25…` 逐字节一致；**PASS**。

### ③ 正式执行 / 两跑 / 门 —— **PASS**

- full B6 **每 fold 1,000 ×5=5,000 real permutations**、`refit_cu_only`；bootstrap **B=5,000**、seed=20261130；每 fold mask 31,767/30,824/30,876/32,400/31,901；target30 340,088；非 mask 182,320。**PASS**。
- **两跑**：run1 wall 1272.06 s / run2 1130.61 s；`on3_exec.json` 两跑均 **`3A9F99D4…`**，逐字节一致；run logs SHA `69514BE6…`/`A2B13A90…`；**PASS**。
- **门**：data PASS、design PASS、9 项二元泄漏审计全 PASS、reconstruction target30 **0/157,768**（per fold 0）、B6 null gate **PASS**（2.5–97.5=[−0.0109437,.0289608508]，mean|Δρ_null|=.0136118422≤.05）；**PASS**。
- **runtime deviation**：>冻结估计 <15 min，report/record/usage 登记；仅计时偏差、无设计/协议/置换数/成功标准变化；**PASS（带登记）**。

### ④ 结果/判定 —— **PASS（带 CI 边界）**

- Primary B4 vs B2：Δρ_mean **.0730667336**；CI95 **[.0474619712,.100310485]**；单侧下界 **.0512309652**；null_p **0.0**；positive folds **5/5**；Δρ_min_rank **.10**；ΔMAE **−.0100447885**（描述性，不用 MDE80）。
- **verdict=`no_increment`**：点估计 <δ_min=.10，符合冻结 G4 的 no_increment 语义；**但 CI 上界 .100310485 略 > .10**，所以**不能把 no_increment 写成“不存在 δ 大小增量/无效应”**；report/usage 已列 CI，最终登记文本须写此边界。**PASS（带解释边界）**。
- 每 fold B4 超参 rank 5、λ 0.01/1.0/0.01/0.01/0.1，未改网格；B5 负 ρ 仅 secondary；context-ablation/纯冷仅诊断/敏感性；**PASS**。

### ⑤ 披露/边界/provisional —— **PASS**

- report §0/record §0/usage `peek_disclosure`：non-blind/peeked；QUICK invalid artifact `39868CE4…` 的 primary/results（Δρ .0277068、CI [.01828,.03572]、4-of-5）已披露；**不得称盲验/独立确认/预注册确认**；**PASS**。
- provisional v1.1 artifacts quarantine：`on3_exec_v1_1_provisional.json` 等；正式 v1.2 不引用其数字；**PASS**。
- 边界：仅 O'Neil 内部开发性描述；不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；技术重复≠独立培养；batch2 仅披露、batch3 全失、702 pair-cell、无 exposure/assay、单药参照未用；冻结≠资源足够/关系成立/Stage1/效果；**PASS**。

## 2. 登记用最终验收文本（建议直接采用）

> **ON3 v1.2 最终验收：accept_final。**
> **v1.2 冻结/正式链**：`FREEZE_ON3_exec_v1_2_DRAFT.md` SHA `C69BA93E7651E4B580F9DD92C6642D414C97E224B6F13837D1961628B580B09C`；`PROTOCOL_ON3_exec_v1_2_DRAFT.md` SHA `B22A7FC791B07C415DE8C8A48DF916DDAC7309A9ECD02CFBE567050F9099A2A8`；`on3_exec.json` SHA `3A9F99D448C76F0D9D83C86AA5FA2A0291C1D08A75533E9064E3E7508AA0C1F3`；`report_on3_exec.md` SHA `1F4CD991583545585D12CD23468F0B170C62A5D6E417FF856886CD6E758B4B8F`；`record_on3_exec.md` SHA `EB38A73C7136B6F53CE9DD11DE738AFDA6A4E4ED82932A60E1C13251886C2761`；`usage_on3_exec.json` SHA `17EA15FEE1DE4B99F3E6E9BA22F3A6E4D6A1A7672E72EBD1BF6A2A99F4A4CE67`；`test_results.txt` `D93AAA06…`（15/15 OK）；`selfcheck.json` `3EB44C25…`（两跑一致）；`AMEND-001.3` `7AFCE1C9…`；溯源 diff `EF43ACDE…`；旧 v0.3 `8B4B8FCC…`/`41BC637C…`/`F514347B…` = invalid spec；provisional v1.1 全部 quarantine、不引用。
> **执行**：v1.2 仅溯源修复后重跑一次（两跑为确定性）；full B6 1,000×5 **5,000 real permutations**、`refit_cu_only`；bootstrap **5,000**；两跑 `on3_exec.json` 逐字节一致；wall **1272.06 s / 1130.61 s**（**runtime deviation >冻结估计 <15 min，已登记，仅计时偏差，未改设计/协议/置换数/成功标准**；不得写预算 <15 min 已满足）。
> **结果**：data/design PASS、9 泄漏 PASS、reconstruction 0/157,768、Δρ_null gate PASS；primary Δρ_mean **.0730667336**、95% CI **[.0474619712,.100310485]**、单侧下界 **.0512309652**、null_p **0.0**、5/5 folds 正、Δρ_min_rank **.10**、ΔMAE **−.0100447885**（描述性）；**verdict=`no_increment`**：点估计未达 δ_min=.10；**但 CI 上界 .100310485 略高于 .10，不能声称不存在 δ 大小的增量/无效应**。
> **解释边界**：non-blind/peeked；不得称盲验/预注册确认/独立确认；仅 O'Neil 内部、本设计下的开发性描述；不称迁移/外推/决策收益/机制/更新器优势/资源足够/新颖性；`no_increment` 不等于结构不存在/不可迁移/无决策价值；冻结≠资源足够/关系成立/Stage1/效果；B5 负 ρ/context-ablation/纯冷/MAE 仅描述性/诊断；不用于选优。

## 3. 非阻断登记事项（不改变 accept）

1. `on3_exec.json` 本体没有 `peek_disclosure`/runtime 字段；这两项在 `report_on3_exec.md` §0/§6 与 `usage_on3_exec.json` 中；最终登记文本已同时引用，**可接受**。若未来要机器可读，可在 schema 增字段，但不阻断本次最终登记。
2. report/record/freeze/protocol 中旧 invalid spec 与 provisional SHA 作为 invalid/quarantine provenance 出现；正式 `on3_exec.json` 无它们；登记时不得把旧 SHA 当有效链。
3. runtime deviation 已登记；后续任何成本/资源足够声明不得引用 <15 min 作为已满足；资源足够仍未被本结果证明。

## 4. 边界

- 本轮**未运行 ON3、未读原始响应做统计、未改产物**；只读文档/SHA/diff/测试/正式 JSON 元数据；只写本文件与 `tmp/`。
- **accept_final**；可登记为 ON3 v1.2 最终开发性描述结果；**不是独立确认/迁移/决策收益/机制/新颖性**；provisional v1.1 不得引用；旧 invalid spec 不得用于批准。

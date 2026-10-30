# R199-ON3 execution record v1.2（record_on3_exec.md；AMEND-001.3 溯源修复；non-blind/peeked）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。本记录记录 Lead 裁定 **Option B（严格溯源修复）** 后按 **v1.2** 的授权重跑一次（含两跑确定性）。**执行报告含 peek_disclosure；non-blind/peeked；不称盲验/独立确认；仅 O'Neil 内部开发性描述。v1.1 provisional 结果 quarantine、不引用。**

## 0. peek_disclosure（随执行记录引用）

- 实现方已见 `tmp/on3_exec_quick_debug.invalid.json`（`39868CE4…`）的 primary/results（Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、per-fold B0–B5、verdict=design_invalid）→ **本次 v1.2 有效执行 non-blind/peeked**。
- 不得称盲验/盲预注册确认/独立确认；结论仅"O'Neil 内部、本设计下的开发性描述结果（non-blind/peeked）"；QUICK invalid artifact 不得引用；QUICK primary 未用于选择方向/指标/门槛/切分/mask/超参/比较器。
- 规范文本：`PEEK_DISCLOSURE_ON3.md` SHA `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`。

## 1. 依据/v1.2 链（唯一有效 SHA）

| 文件 | SHA256 |
|---|---|
| `DECISION_ON3_PROVENANCE.md`（Lead Option B） | `6C2DFD55C89D2BE4989480307A7A538829E850627E784CB0F815EEE359EB00C3` |
| `AMENDMENT_ON3_EXEC-001_3.md` | `7AFCE1C9BA1FC73385EA6EFEEBC51009B7F258D20511B853A2137C118F1A1184` |
| `PROTOCOL_ON3_exec_v1_2_DRAFT.md` | `B22A7FC791B07C415DE8C8A48DF916DDAC7309A9ECD02CFBE567050F9099A2A8` |
| `FREEZE_ON3_exec_v1_2_DRAFT.md` | `C69BA93E7651E4B580F9DD92C6642D414C97E224B6F13837D1961628B580B09C` |
| `on3_refimpl/run_on3_exec.py`（v1.2） | `B3A5569EC852AE6FD1B5D879336E44EC3F1F5F55D2BB420DF9D7EED41CEC8E39` |
| `tmp/on3_amend001_3_code.diff` | `EF43ACDE57EB3DB574F2142CE9904E7F8D19651E3DAF9154486A795A13F0CCBA` |
| `on3_refimpl/refimpl.py`（未变） | `AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515` |
| `on3_refimpl/test_refimpl.py`（未变） | `25B6E410089E945EC1245A91BBE005F522CC4B058BE0211F7546222223D8A0CA` |
| `on3_refimpl/test_results.txt`（15/15 OK 2.626 s） | `D93AAA067C46B0836E7FD7F604F08CBE3B304F7F790121B669F5313C302E232F` |
| `on3_refimpl/selfcheck.py` / `selfcheck.json`（两跑一致） | `7F3EDA17…` / `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A` |
| `PEEK_DISCLOSURE_ON3.md` | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| v1.1 protocol/freeze（已批准基线；仅 input 溯源被 v1.2 superseded） | `8C4B2D9B…` / `14A6E1E3…` |
| 旧 v0.3/freeze/approval（invalid spec） | `8B4B8FCC…` / `41BC637C…` / `F514347B…`（不引用/不用于批准） |
| v1.1 provisional（**quarantine，不引用**） | `tmp/on3_exec_v1_1_provisional.json` `5698151968…`；report `7AC71D57…`；record `4BCC8BAC…`；usage `11DFF763…` |

## 2. 溯源修复（v1.1 → v1.2；仅 6 行）

- 唯一改动：`run_on3_exec.py` 的 `protocol` 与 `inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 由旧 invalid spec 改为 v1.2 protocol/freeze；`tmp/on3_amend001_3_code.diff` 仅含该 hunk；执行逻辑/数据/切分/mask/超参/rank/λ/指标/差值/B6/bootstrap/两跑要求零改动。
- 预检：`run_on3_exec.py` 编译通过；**15/15 单测 OK（2.626 s）**；**两跑 selfcheck 逐字节一致**（`3EB44C25…`）；refimpl/test/selfcheck 未变。
- v1.2 正式 `on3_exec.json` 的 `protocol.file`=`PROTOCOL_ON3_exec_v1_2_DRAFT.md`、`sha256`=`B22A7FC7…`；`freeze_sha256`=`C69BA93E…`；`inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 均为 v1.2；全文无旧 `8B4B8FCC…`/`41BC637C…`/`F514347B…`。

## 3. 执行配置/两跑

- 命令：`python -X utf8 -u on3_refimpl/run_on3_exec.py`；环境 `PYTHONHASHSEED=0`、`OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`；`QUICK` 未设置。
- 授权：Lead DECISION Option B 重跑一次；为满足协议"两跑逐字节一致"执行两次（非结果驱动重跑）；未改代码/协议/设计/数据（v1.2 溯源修复已在执行前完成并预检）。

| 运行 | 日志 | wall | on3_exec.json SHA256 |
|---|---|---|---|
| run1 | `tmp/on3_exec_v12_run1.log` SHA `69514BE61FEAEAA2E2E1EA236C8DC1F8A99573BB8F25C4BD434DE6D8E2DFDFCE` | **1272.06 s** | `3A9F99D448C76F0D9D83C86AA5FA2A0291C1D08A75533E9064E3E7508AA0C1F3` |
| run2 | `tmp/on3_exec_v12_run2.log` SHA `A2B13A906068154ACB72E6B1F5E61192DA83893A92378F9C1F092F264254A6E8` | **1130.61 s** | `3A9F99D448C76F0D9D83C86AA5FA2A0291C1D08A75533E9064E3E7508AA0C1F3` |

- **两跑 `on3_exec.json` 逐字节一致**；正式 `on3_exec.json` = run2（同字节）；两跑 exit 0；wall 仅记录在 usage/log，不进入 JSON。
- v1.1 provisional 产物保持 `tmp/*_provisional.*` quarantine，未参与本记录/正式结果。

## 4. 门/覆盖/结果（摘要；详见 report_on3_exec.md 与正式 on3_exec.json）

- 覆盖：target30 **340,088**；mask **157,768**；非 mask **182,320**；每 fold mask **31,767/30,824/30,876/32,400/31,901**。
- 门：data PASS、design PASS、9 项二元泄漏审计全 PASS、reconstruction **0/157,768**（per fold 0）、B6 null gate（Δρ_null）**PASS**（2.5–97.5=[-0.0109437,0.0289608508]；mean|Δρ_null|=0.0136118422≤0.05）。
- B6：每 fold 1,000 ×5 = **5,000 real permutations**（refit_cu_only）；bootstrap B=**5,000**，seed 20261130。
- 每 fold B4 超参（训练细胞 LOO CV，未改网格）：fold0 rank5/λ0.01、fold1 5/1.0、fold2 5/0.01、fold3 5/0.01、fold4 5/0.1。
- Primary：Δρ_mean=**0.0730667336**；95% CI [0.0474619712,0.100310485]；单侧 95% 下界 0.0512309652；null_p=0.0；positive folds=5/5；Δρ_min_rank=0.10；**verdict=`no_increment`**（未达 δ_min=0.10）。
- ΔMAE=−0.0100447885（95% CI [−0.0147008382,−0.005619376]；描述性，不用 MDE80 判 MAE）。
- context-ablation/纯冷仅诊断/敏感性；B5 secondary（负 ρ 仅记录）。
- 结论措辞（冻结）："在本资源（O'Neil complete-case、batch1、30 目标细胞）与本设计（整成员块掩码、5 折细胞留出）下，未观察到 B4 相对 B2 的预注册描述性增量（non-blind/peeked）；Δρ=0.0731 未达预注册阈值 δ_min=0.10。这不等于结构不存在、不可迁移或没有决策价值。"

## 5. 偏差/限制

- **runtime deviation（登记）**：实测 wall 1272.06 s（run1）/1130.61 s（run2），高于冻结预算估计 <15 min（约 18.8–21.2 min）；仅计时偏差、未改设计/协议/置换数/成功标准；非结果驱动重跑。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；仅 viability；技术重复≠独立培养；batch2 仅披露、batch3 全失；702 个 15 行 pair-cell 排除；无暴露时间/assay；单药参照未用；缺失机制未知。
- 未运行效果/训练/更新器/迁移/决策分析；不称迁移/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。
- v1.1 provisional quarantine、不引用；v1.2 结果为唯一正式结果。

## 6. 产出 SHA

| 文件 | SHA256 |
|---|---|
| `on3_exec.json`（v1.2） | `3A9F99D448C76F0D9D83C86AA5FA2A0291C1D08A75533E9064E3E7508AA0C1F3` |
| `report_on3_exec.md` | `1F4CD991583545585D12CD23468F0B170C62A5D6E417FF856886CD6E758B4B8F` |
| `record_on3_exec.md` | 本文件（SHA 见 usage/复核方） |
| `usage_on3_exec.json` | 见该文件 |
| run1/run2 log | `69514BE6…` / `A2B13A90…` |

## 7. attestation

- 按 v1.2 重跑一次（两跑仅为逐字节确定性）；未改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；未做结果驱动重跑；未运行效果/更新器/迁移/决策。
- 执行报告含 `peek_disclosure`；non-blind/peeked 已披露；QUICK invalid artifact 未引用；v1.2 正式输入链无旧 invalid spec；provisional v1.1 未引用。

# R199-ON3 execution report v1.2（**non-blind/peeked**；O'Neil 内部开发性描述；授权重跑一次 + 两跑确定性）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。执行对象：Lead 批准/裁定的 **ON3 execution protocol v1.2**（`DECISION_ON3_PROVENANCE.md` Option B；AMEND-001.3 溯源修复）。**本报告遵守 peek 限制：本执行是 non-blind/peeked，不得称盲验/盲预注册确认/独立确认；结论仅 O'Neil 内部、本设计下的开发性描述结果，并附本 peek 披露。**

## 0. peek_disclosure（必须随本报告引用）

- **peek 事实**：实现方在本执行前已看到真实数据上的 QUICK invalid artifact `tmp/on3_exec_quick_debug.invalid.json`（原 `on3_exec_quick_debug.json`；SHA `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5`）的 **primary/results**：Δρ mean **0.0277068**、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10；per-fold B0–B5、context-ablation/pure-cold、verdict=design_invalid。
- **性质**：该 artifact 是 `QUICK=1, N_PERM=20, BOOT_B=100` 的**无效执行**（非冻结 full run；无两跑），已 quarantine、**不得作为结果引用**。因此本次 v1.2 有效执行 **non-blind / peeked**。
- **解释限制**：不得称盲验/盲预注册确认/独立确认；不得写"预注册确认/独立验证/blind validation"；结论只能写"O'Neil 内部、本设计下的开发性描述结果（non-blind/peeked）"并附本披露；不得升级为迁移/外推/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。
- **QUICK primary 未用于选择**：v1.2 唯一改动是 input 溯源字段（旧 invalid spec SHA → v1.2 protocol/freeze），**不涉及任何结果选择**；QUICK 的 Δρ/CI/positive folds/B0–B5 未用于选择方向/指标/门槛/切分/mask/超参/比较器。
- 规范文本：`PEEK_DISCLOSURE_ON3.md` SHA `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`。

## 1. 批准/冻结/v1.2 链（唯一有效 SHA）

| 文件 | SHA256 |
|---|---|
| `DECISION_ON3_PROVENANCE.md`（Lead Option B 裁定） | `6C2DFD55C89D2BE4989480307A7A538829E850627E784CB0F815EEE359EB00C3` |
| `AMENDMENT_ON3_EXEC-001_3.md`（AMEND-001.3） | `7AFCE1C9BA1FC73385EA6EFEEBC51009B7F258D20511B853A2137C118F1A1184` |
| `PROTOCOL_ON3_exec_v1_2_DRAFT.md`（v1.2 protocol） | `B22A7FC791B07C415DE8C8A48DF916DDAC7309A9ECD02CFBE567050F9099A2A8` |
| `FREEZE_ON3_exec_v1_2_DRAFT.md`（v1.2 freeze） | `C69BA93E7651E4B580F9DD92C6642D414C97E224B6F13837D1961628B580B09C` |
| `on3_refimpl/run_on3_exec.py`（v1.2；仅溯源字段） | `B3A5569EC852AE6FD1B5D879336E44EC3F1F5F55D2BB420DF9D7EED41CEC8E39` |
| `tmp/on3_amend001_3_code.diff`（v1.1→v1.2 精确 diff） | `EF43ACDE57EB3DB574F2142CE9904E7F8D19651E3DAF9154486A795A13F0CCBA` |
| `on3_refimpl/refimpl.py` | `AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515` |
| `on3_refimpl/test_refimpl.py` / `test_results.txt` | `25B6E410…` / `D93AAA06…`（15/15 OK 2.626 s） |
| `on3_refimpl/selfcheck.py` / `selfcheck.json` | `7F3EDA17…` / `3EB44C25…`（两跑逐字节一致） |
| `PEEK_DISCLOSURE_ON3.md` | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| v1.1 protocol/freeze（已批准基线；仅 input 溯源被 v1.2 superseded） | `8C4B2D9B…` / `14A6E1E3…` |
| 旧 v0.3 `PROTOCOL_ON3_exec_DRAFT.md`/`FREEZE_ON3_exec.md`/`APPROVAL_ON3_EXEC.md` | `8B4B8FCC…`/`41BC637C…`/`F514347B…` = **invalid spec, no valid execution；不引用/不用于批准** |
| v1.1 provisional 结果（**quarantine，不得引用**） | `tmp/on3_exec_v1_1_provisional.json` `5698151968…` 等（见 §6） |

## 2. 执行事实（v1.2 授权重跑一次 + 两跑确定性）

- 命令：`python -X utf8 -u on3_refimpl/run_on3_exec.py`（环境 `PYTHONHASHSEED=0`、`OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`；`QUICK` 未设置）。
- **v1.2 唯一改动 = input 溯源字段**（旧 invalid spec SHA → v1.2 protocol/freeze），执行语义/数据/切分/mask/B4/B6/指标/阈值与 v1.1 相同；本为重跑修复（非结果驱动），Lead 已授权一次。
- 实测 wall：run1 **1272.06 s**；run2 **1130.61 s**（约 18.8–21.2 min；**超过冻结预算估计 <15 min**——**runtime deviation**，仅计时偏差、未改设计；见 §6）。
- **两跑 `on3_exec.json` 逐字节一致**：SHA256 **`3A9F99D448C76F0D9D83C86AA5FA2A0291C1D08A75533E9064E3E7508AA0C1F3`**（run1=run2）。
- `on3_exec.json` 中 `protocol.sha256` = v1.2 `B22A7FC7…`、`freeze_sha256` = v1.2 `C69BA93E…`；`inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 均为 v1.2；**不含**旧 invalid spec SHA。
- full B6：每 fold **1,000** 次、5 folds = **5,000 次真实置换**；语义 `refit_cu_only`（训练结构每 fold 只拟合一次；每次置换只重估 c/U）；bootstrap **B=5,000**、seed=20261130、按 held-out 细胞配对。
- 覆盖/mask：target30 单元 **340,088**；mask **157,768**；非 mask **182,320**；每 fold mask **31,767/30,824/30,876/32,400/31,901**；4×4 complete-case、无插值、k=1 排除。
- 门：data PASS；design PASS；9 项二元泄漏审计全 PASS；reconstruction target30 **0/157,768**、per fold **0**；B6 null gate（Δρ_null）**PASS**（2.5–97.5=[-0.0109437,0.0289608508] 覆盖 0；mean|Δρ_null|=0.0136118422≤0.05）。
- 本执行**未**运行效果/训练/更新器/迁移/决策分析；仅按冻结协议做 O'Neil 开发性描述。

## 3. 结果

### 3.1 Primary（唯一 primary：B4 vs B2）

| 指标 | 值 |
|---|---|
| Δρ_mean（B4−B2，5 fold 均值） | **0.0730667336** |
| Δρ 95% CI（配对细胞 bootstrap 5,000） | **[0.0474619712, 0.100310485]** |
| 单侧 95% 下界 | 0.0512309652 |
| Δρ_min_rank = max(0.10, Q95_null(Δρ_null)) | **0.10**（Q95_null=0.0280246988） |
| null_p（单侧） | **0.0**（0/5,000 null Δρ ≥ observed） |
| positive folds | **5/5** |
| ΔMAE_mean（描述性，不用 MDE80 判 MAE） | −0.0100447885；95% CI [−0.0147008382, −0.005619376] |
| **增量判定** | **`no_increment`**：Δρ_mean 0.0731 < δ_min=0.10（其余条件成立：CI 下界>0、null_p≤0.05、5/5 folds 正）；**仅表示未达到预注册 δ_min=0.10 描述性增量** |

### 3.2 每 fold ρ / MAE（B0–B5；B5 为 secondary）

| fold | rank/λ | ρ B0 | ρ B1 | ρ B2 | ρ B3 | ρ B4 | ρ B5 | MAE B4 | MAE B2 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 5 / 0.01 | 0.0000 | 0.6393 | 0.6770 | 0.6772 | 0.7632 | −0.3770 | 0.1050 | 0.1152 |
| 1 | 5 / 1.0 | 0.0000 | 0.7062 | 0.7427 | 0.7444 | 0.8173 | −0.3657 | 0.0865 | 0.1012 |
| 2 | 5 / 0.01 | 0.0000 | 0.6533 | 0.6894 | 0.6923 | 0.7309 | −0.1003 | 0.1080 | 0.1120 |
| 3 | 5 / 0.01 | 0.0000 | 0.6965 | 0.7350 | 0.7501 | 0.7982 | −0.0912 | 0.0937 | 0.1012 |
| 4 | 5 / 0.1 | 0.0000 | 0.6043 | 0.6428 | 0.6471 | 0.7426 | −0.1601 | 0.1020 | 0.1159 |

- Δρ（B4−B2）每 fold：0.0862/0.0747/0.0415/0.0631/0.0998（5/5 正；仅描述性）。
- B5（HistGBM）为 secondary、capacity control；其 ρ 为负（−0.09…−0.38），仅记录，不参与 primary 选择/不改变判定。
- top-k 附录（B4，k=1/3/5 precision，按 fold）：0.32–0.40 / 0.41–0.56 / 0.46–0.59（仅附录，无决策含义）。

### 3.3 诊断/敏感性（不改 primary 判定）

- **context-ablation（描述性诊断）**：Δρ_context = ρ(B4)−ρ(B4-ablated) = 0.0862/0.0747/0.0415/0.0631/0.0998（全>0；仅诊断，不触发 design_invalid）。
- **纯冷细胞（sensitivity）**：ρ/MAE 等于 B2 静态基线（无 context）：fold ρ 0.6770/0.7427/0.6894/0.7350/0.6428；仅 sensitivity，不进 primary/increment。
- B0（常数）ρ=0；B1 层级参照；B3=B2+cell offset；B4 vs B2 为唯一 primary，完整表不做选优。

## 4. 结论（冻结措辞；non-blind/peeked）

**在本资源（O'Neil complete-case、batch1、30 目标细胞）与本设计（整成员块掩码、5 折细胞留出）下，未观察到 B4 相对 B2 的预注册描述性增量（non-blind/peeked）；Δρ=0.0731 未达预注册阈值 δ_min=0.10。这不等于结构不存在、不可迁移或没有决策价值。**

- 该结论仅 O'Neil 内部、本设计下的**开发性描述结果（non-blind/peeked）**，并附 §0 peek 披露；**不是盲验、不是预注册确认、不是独立确认**。
- 不称迁移/外推/决策收益/机制/更新器优势/资源足够/新颖性；不写"效应/有效/优于"；B5 负 ρ 仅记录，不改变 primary。
- MAE 仅描述性（不用 MDE80 判 MAE）；context-ablation/纯冷仅诊断/敏感性；`no_increment` 只表示未达 δ_min=0.10。

## 5. 产出 SHA

| 文件 | SHA256 |
|---|---|
| `on3_exec.json`（v1.2；两跑一致） | `3A9F99D448C76F0D9D83C86AA5FA2A0291C1D08A75533E9064E3E7508AA0C1F3` |
| `report_on3_exec.md` | 本文件（SHA 见 record/usage/复核方） |
| `record_on3_exec.md` | 见该文件 |
| `usage_on3_exec.json` | 见该文件 |
| run1 `tmp/on3_exec_v12_run1.log` | `69514BE61FEAEAA2E2E1EA236C8DC1F8A99573BB8F25C4BD434DE6D8E2DFDFCE` |
| run2 `tmp/on3_exec_v12_run2.log` | `A2B13A906068154ACB72E6B1F5E61192DA83893A92378F9C1F092F264254A6E8` |

## 6. 资源说明/限制

- **runtime deviation（登记）**：实测 wall 1272.06 s（run1）/1130.61 s（run2），**高于冻结预算估计 <15 min**（约 18.8–21.2 min；环境/OMP 计时因素）；**仅计时偏差，未改设计/协议/置换数/成功标准**；不是结果驱动重跑。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；仅 viability；技术重复≠独立培养；batch2 仅披露、batch3 全失；702 个 15 行 pair-cell 排除；无暴露时间/assay；单药参照未用；缺失机制未知（不假设 MCAR/MAR）。
- 未运行更新器/迁移/决策分析；不称迁移/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。
- v1.1 provisional 结果 quarantine、本报告不引用其数字作为证据；v1.2 结果为唯一正式结果。

## 7. attestation

- 按 v1.2 重跑一次（两跑仅为逐字节确定性）；未改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；未做结果驱动重跑；未运行效果/更新器/迁移/决策。
- 执行报告含 `peek_disclosure`；non-blind/peeked 已披露；QUICK invalid artifact 未引用；旧 invalid spec SHA 未出现在 v1.2 正式产物输入链。

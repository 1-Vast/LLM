# AMENDMENT_ON3_EXEC-001（草案 v0.3）—— B6 null 门规格缺陷修复 + **peek（非盲）披露**（post-freeze, pre-valid-result）

**状态：DRAFT v0.3，未生效。** 本文件是冻结后、**有效结果之前**的规格缺陷修复草案（**post-freeze, pre-valid-result**）；**不在本任务执行 ON3、不新读原始响应值**。**v0.3 新增（AMEND-001.2-C1 必改）**：显式 **peek（非盲）披露与解释限制**（见 §2A；规范文本 `PEEK_DISCLOSURE_ON3.md` SHA `B4CAD955…`）。须经独立挑战者（endpoint-auditor）只读复核本 v0.3（含 peek）+ 代码 diff/单测/两跑 + Lead 批准后，形成 ON3 execution protocol **v1.1** 并冻结，才可执行一次。

**v0.2 关键更正（相对 v0.1/`5362C5A7…`）**：
1. **QUICK artifact 完整披露**：`tmp/on3_exec_quick_debug.invalid.json`（原 `tmp/on3_exec_quick_debug.json`，SHA `39868CE4…`）**不是"仅 null 诊断"**——它是 `QUICK=1, N_PERM=20, BOOT_B=100` 的**无效执行**，但含**真实数据上的 result-shaped primary/results**：`delta_rho_mean=0.0277068`、CI95 `[0.01828,0.03572]`、`positive_folds=4`、`delta_rho_min_rank=0.10`、每折 B0–B5 ρ/MAE/top-k、context-ablation/pure-cold、`verdict=design_invalid`。**不得作为结果引用**；正式 `on3_exec.json` 不存在 **≠** 无 result-like artifact。v0.2 删除"QUICK 仅说明/无结果/未读响应值/pre-result"等不准确表述。
2. **QUICK 隔离**：artifact 已改名为 `.invalid.json` 并留在 `tmp/` quarantine（见 §1.3/§6）；不进入正式结果路径。
3. **修订正当性不含 QUICK**：仅由**同节已冻结的 `Δρ_null` 定义 + null 预测含不变 `B2_static` 的代数必然性**决定；**QUICK 的 Δρ/任何 primary 数字未用于选择指标/门槛/方向**（且 QUICK Δρ 0.0277 <0.10，即使修复 gate 按冻结增量规则也 likely `no_increment`，不构成正结果）。
4. **实现/schema 代码级 diff**：null gate 条件 + 输出字段名（`p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`）一并更正；test_11/schema 更新；**重跑 15/15 单测与两跑 selfcheck**；精确 diff 见 §3/`tmp/on3_amend001_1_code.diff`。
5. **v1.1 冻结链**：生成 `PROTOCOL_ON3_exec_v1_1_DRAFT.md`（SHA `DC4C4082…`）与 `FREEZE_ON3_exec_v1_1_DRAFT.md`（全链 SHA）；旧 `8B4B8FCC…`/`41BC637C…`/`F514347B…` 标 **invalid spec, no valid execution**。
6. **v0.3 新增 —— peek（非盲）披露与限制（AMEND-001.2-C1）**：实现方已看到 `tmp/on3_exec_quick_debug.invalid.json`（`39868CE4…`）的 primary/results（Δρ 0.0277068/CI/positive_folds/B0–B5 等），因此 **v1.1 有效执行是 non-blind/peeked**；规范披露见新文件 **`PEEK_DISCLOSURE_ON3.md`（SHA `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`）**。**不得称盲验/盲预注册确认/独立确认**；结论仅 O'Neil 内部开发性描述并附 peek 披露；QUICK primary 未用于选择指标/门槛/方向；执行报告必须含 `peek_disclosure`。

## 0. 依据（只读）

- Lead 批准/冻结：`APPROVAL_ON3_EXEC.md` SHA `F514347B…`（旧；invalid spec）。
- 旧冻结执行协议：`PROTOCOL_ON3_exec_DRAFT.md` v0.3 SHA `8B4B8FCC…`（**invalid spec, no valid execution**）。
- 旧冻结文本：`FREEZE_ON3_exec.md` SHA `41BC637C…`（**invalid spec, no valid execution**）。
- 停止记录：`report_on3.md` / `record_on3.md` / `usage_on3.json`（执行在冻结门处停止；**无正式 on3_exec.json**；QUICK invalid artifact 见 §1.3）。
- v1.1 协议草案：`PROTOCOL_ON3_exec_v1_1_DRAFT.md`（v0.3 修订后新 SHA 见 FREEZE v1.1/Lead 文本；旧 `DC4C4082…` superseded）；v1.1 冻结草案：`FREEZE_ON3_exec_v1_1_DRAFT.md`（全链 SHA 见该文件）。
- peek 规范文本：`PEEK_DISCLOSURE_ON3.md` SHA `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`；AMEND-001.2-C1：`challenge_ON3_amend001_1.md` SHA `926C23F5C4C5F45608346EB29BA09DB54C8091E1D7A6C13AB35DCCCA8F45E10C`。
- 代码 diff/自检：`tmp/on3_amend001_1_code.diff`（SHA `1F1AA05E…`）；`tmp/on3_amend001_diff.json`（文本 diff，SHA `2AFF481E…`）。

## 1. 缺陷陈述

### 1.1 冻结原文与内部矛盾

旧 v0.3 §2 的 null 门：
> "**null 校准门（二元，冻结）**：B4 null **ρ** 的 2.5–97.5 覆盖 0 且 mean|ρ_null| ≤ 0.05；否则 `design_invalid`。"

同一 §2 上一行已冻结正确 null 对象：
> "**null Δρ 定义 = ρ(B4_null)−ρ(B2)**（同一掩码单元/同一 B2 静态预测）；p = mean(null Δρ ≥ observed)。"

即：文本自己定义了 `Δρ_null`，门却误写为绝对 `ρ_null`——**自相矛盾**。

### 1.2 数学理由（不依赖数据/结果）

B6 `refit_cu_only` 的 null 预测 = `B2_static + c_perm + U_perm·V`；`B2_static` 不随置换改变。因此 `ρ(B4_null,y)` 与 `ρ(B2,y)` 同量级>0，`ρ_null` 的 2.5–97.5 **不可能覆盖 0**、`mean|ρ_null|` **不可能 ≤0.05**；旧门对**任何真实数据都必然 design_invalid**，与模型/数据有效性无关。正确对象 `Δρ_null=ρ(B4_null)−ρ(B2)` 差掉静态分量，中心≈0；这正是同节已冻结的定义。**修订必要性由上述代数矛盾独立证明，不由 QUICK 结果决定。**

### 1.3 QUICK artifact 完整披露（invalid, quarantined）

- 原路径 `tmp/on3_exec_quick_debug.json`；**现 `tmp/on3_exec_quick_debug.invalid.json`**；SHA256 `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5`；配套 usage 原名 `tmp/usage_on3_quick_debug.json`（SHA `60DB423C22DA660FD43D5DEA4D5FBD857B9DD076D74B124C089D273150F9CC11`）**现 `.invalid.json`**。
- 设置：`QUICK=1, N_PERM=20, BOOT_B=100`；**无效执行（非冻结 full run：B6 1,000×5 / bootstrap 5,000 未跑）**；无两跑。
- 内容（如实披露，**不得作为结果引用**）：完整 schema 的 primary/results——`delta_rho_mean=0.0277068`、`delta_rho_ci95=[0.01828,0.03572]`、`positive_folds=4`、`delta_rho_min_rank=0.10`；每折 B0–B5 的 ρ/MAE/top-k；context-ablation/pure-cold；`verdict=design_invalid`；`null.n_perm=20` 与 gate.n_perm=100 也不一致（无效执行痕迹）。
- 隔离：已改名 `.invalid.json` 并留 `tmp/` quarantine；**不进入正式结果路径、不得引用、不得用于选择指标/门槛/方向**。正式 `on3_exec.json` 不存在仅指正式执行产物未生成，**不等于没有 result-like artifact**。

## 2. 修订（**仅** null 校准门；其余一切不变）

### 2.1 唯一协议改动（before → after）

**Before（旧 v0.3 §2）：**
> - **null 校准门（二元，冻结）**：B4 null ρ 的 2.5–97.5 覆盖 0 且 mean|ρ_null| ≤ 0.05；否则 `design_invalid`。

**After（v1.1 §2）：**
> - **null 校准门（二元，冻结；v1.1 AMEND-001）**：B6 null 的 **Δρ_null = ρ(B4_null) − ρ(B2)**（同一掩码单元/同一 B2 静态预测）的 **2.5–97.5 覆盖 0 且 mean|Δρ_null| ≤ 0.05**；否则 `design_invalid`（实现字段：`p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`，不得使用 rho 命名）。

### 2.2 不变清单（v1.1 逐项保留；不得改）

- 数据 cohort/切分/5 折/mask M（8/38 药物）+seed 20261130+fraction/rule/scope；端点/Δ/符号/k=1；B2/B4/B5/纯冷；超参 rank{1,2,3,5}×λ{0.01,0.1,1,10}/ALS/LOO；B6 `refit_cu_only` 1,000/seed/分层/refit 语义；bootstrap B=5,000/seed/percentile；指标 Spearman+MAE+top-k 附录；差值规则 Δρ≥max(0.10,Q95_null)+≥4/5 folds+配对 CI+null p≤0.05；MDE80/δ_min；schema（除 null gate 字段名）；两跑；实测 wall/<15 min；batch2 仅披露；失败类别；禁改项。
- 成功标准**未降**：即使修复 gate，primary 增量仍按上述冻结规则判定；修复本身不改变任何 primary metric/阈值/方向。

## 2A. peek（非盲）披露与解释限制（v0.3 新增；规范文本 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`）

- **peek 事实**：实现方已看到 `tmp/on3_exec_quick_debug.invalid.json`（原 `on3_exec_quick_debug.json`；SHA `39868CE4…`）的 **primary/results**（Δρ mean 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、context-ablation/pure-cold、verdict=design_invalid）。该 artifact 是 QUICK=1/N_PERM=20/BOOT=100 **无效执行**，已 quarantine、不得引用为结果。
- **性质**：**ON3 v1.1 有效执行是 non-blind / peeked**；不是盲验、不是盲预注册确认、不是独立确认。
- **解释限制（冻结）**：
  1. 不得称盲验/盲预注册确认/独立确认；不得写"预注册确认/独立验证/blind validation"。
  2. 结论只能写"O'Neil 内部、本设计下的开发性描述结果（non-blind/peeked），附 peek 披露"；不得升级为迁移/外推/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。
  3. **QUICK primary 未用于选择方向/指标/门槛/切分/mask/超参/比较器**；null gate 修订依据仅同节 Δρ_null 定义 + null 预测含不变 B2_static 的代数必然性（§1.2）。
  4. 修复后仍可能 `no_increment`/`evaluation_cannot_distinguish`；QUICK Δρ 0.0277<0.10，即使按冻结增量规则也 likely `no_increment`，不构成正结果。
  5. 执行报告（`report_on3.md`/`record_on3.md`/`usage_on3.json`）必须含 **`peek_disclosure`** 字段/段落并写明 non-blind/peeked、QUICK invalid artifact 不得引用。
  6. QUICK invalid artifact 已 `.invalid.json` quarantine；正式 `on3_exec.json` 不存在 ≠ 无 result-like artifact。

## 3. 代码级实现 diff（v1.0 → v1.1；精确 diff 见 `tmp/on3_amend001_1_code.diff`）

### 3.1 `run_on3_exec.py`（唯一实质逻辑 + 字段名）

**Before：**
```python
null_gate = {'pass': bool((np.percentile(null_rho, 2.5) <= 0 <= np.percentile(null_rho, 97.5))
                          and float(np.mean(np.abs(null_rho))) <= 0.05),
             'p2_5_rho': float(np.percentile(null_rho, 2.5)),
             'p97_5_rho': float(np.percentile(null_rho, 97.5)),
             'mean_abs_rho': float(np.mean(np.abs(null_rho))),
             'q95_delta_rho': q95_drho, 'p_one_sided': p_perm, 'n_perm': int(N_PERM * 5)}
```
**After：**
```python
# v1.1 (AMEND-001): gate object = delta_rho_null = rho(B4_null)-rho(B2); delta-named fields ONLY
null_gate = R.null_calibration_gate(null_drho, mean_abs_max=0.05, field_prefix='delta_rho')
null_gate.update({'q95_delta_rho': q95_drho, 'p_one_sided': p_perm, 'n_perm': int(N_PERM * 5)})
```
**字段映射（old → new）**：`p2_5_rho → p2_5_delta_rho`；`p97_5_rho → p97_5_delta_rho`；`mean_abs_rho → mean_abs_delta_rho`（`pass`/`q95_delta_rho`/`p_one_sided`/`n_perm` 保留）。

### 3.2 `refimpl.py`（gate 函数 + schema 校验）

- `null_calibration_gate(values, mean_abs_max=0.05, field_prefix='delta_rho')`：输出 `p2_5_<prefix>`/`p97_5_<prefix>`/`mean_abs_<prefix>`/`covers_zero`/`mean_abs_threshold`/`gate_object`；v1.1 执行固定 `field_prefix='delta_rho'`。
- 新增 `validate_null_gate_schema(gate)`：必须含 `pass`、`p2_5_delta_rho`、`p97_5_delta_rho`、`mean_abs_delta_rho`；缺键报错。
- 新 SHA：`AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515`（旧 `B5485B23…` 标 v1.0）。

### 3.3 `test_refimpl.py`（test_11 更新）

- test_11 改为 delta 字段：断言 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho` 存在，`p2_5_rho`/`mean_abs_rho` 不在 gate；`validate_null_gate_schema` PASS；centered 过/ shifted 失败。
- 新 SHA：`25B6E410089E945EC1245A91BBE005F522CC4B058BE0211F7546222223D8A0CA`。
- **重跑结果：Ran 15 tests — OK（2.867 s）**；`test_results.txt` 新 SHA `6282E395AF3CF4675F322F2D1CF6CE925A25F8217AC6F09B1172B80229E2DDD1`。

### 3.4 `selfcheck.py` / 两跑

- selfcheck 的 gate 调用改 `field_prefix='delta_rho'`；两跑输出 **逐字节一致**，`selfcheck.json` 新 SHA `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A`（`selfcheck.py` 新 SHA `7F3EDA177854D1877C7A5BBC805C7A30A9BE0FA822A7EDAEC5B19CCDA33B180A`）。
- 代码 diff：`tmp/on3_amend001_1_code.diff` SHA `1F1AA05EC90F46B1C47EBBAC664F94E98D68AF9408F5640B173A0E43624A0871`。

## 4. 自检：为什么不是换指标/门槛制造收益

1. **唯一改动** = null gate 对象（ρ_null→Δρ_null）+ 实现输出字段名；primary metric/增量阈值/成功标准全部不变（见 §2.2）。
2. 旧门对**任何真实数据必然 FAIL**（代数必然），修复是使门对象与同节已冻结 `Δρ_null` 一致；不是降低模型/数据要求。
3. **QUICK primary 未用于选择方向/指标/阈值**：修订理由独立于 QUICK（§1.2）；QUICK Δρ=0.0277<0.10，即使修复 gate，按冻结增量规则也 likely `no_increment`，**不构成正结果**；不得引用 QUICK primary 作为支持/反对证据。
4. 修复后仍可能 `no_increment`/`evaluation_cannot_distinguish`；不能保证正结果。
5. 修订发生在**任何有效 full-run 结果之前**（无正式 on3_exec.json）；但存在 QUICK invalid result-shaped artifact（已披露/隔离），故性质为 **post-freeze, pre-valid-result**，不是"无 result-like artifact"。

## 5. v1.1 与执行条件

- v1.1 协议草案：`PROTOCOL_ON3_exec_v1_1_DRAFT.md`（v0.3 修订后新 SHA 见 FREEZE v1.1/Lead 文本；旧 `DC4C4082…` superseded）。peek 规范文本：`PEEK_DISCLOSURE_ON3.md` `B4CAD955…`。
- v1.1 冻结草案：`FREEZE_ON3_exec_v1_1_DRAFT.md`（全链 SHA；含本 AMENDMENT v0.3 SHA、v1.1 protocol、PEEK_DISCLOSURE、refimpl/test/selfcheck/code diff、stop/审计记录、旧 invalid spec、QUICK invalid artifact）。
- 旧 invalid spec（保留不改）：protocol `8B4B8FCC…`、freeze `41BC637C…`、approval `F514347B…`。
- 执行一次条件：独立挑战者复核 + Lead 批准冻结 v1.1 → 按 v1.1 执行 **full B6 1,000×5 refit_cu_only、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap**；结果仅 O'Neil 内部开发性描述并**必须附 peek 披露（non-blind/peeked）**；不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结≠资源足够/关系成立/Stage1/效果；QUICK invalid artifact 不得引用；若实现偏差→停并重新预注册。
- 本草案 SHA（v0.2）由 `record_on3_amend001.md`/`usage_on3_amend001.json`/`FREEZE_ON3_exec_v1_1_DRAFT.md` 记录（文件不能自引用）。

## 6. 隔离/产物

- QUICK artifact：`tmp/on3_exec_quick_debug.invalid.json`（`39868CE4…`）、`tmp/usage_on3_quick_debug.invalid.json`（`60DB423C…`）；**invalid/quarantine，不得引用**。
- 旧冻结/批准文件：未改，标 invalid spec。
- 代码/测试/自检/两跑：见 §3。
- 文本 diff：`tmp/on3_amend001_diff.json`（`2AFF481E…`）；代码 diff：`tmp/on3_amend001_1_code.diff`（`1F1AA05E…`）。

## 7. 边界

- 本任务**不执行 ON3、不新读原始响应值做统计、不改旧冻结文件**；只写 `oneil_dev/` 草案与 `tmp/`。
- 不称新颖性/迁移/决策收益/机制/独立确认/更新器/资源足够；技术重复≠独立培养；缺失机制未知；batch3 全失、702 个 15 行 pair-cell、无暴露时间/assay、单药未用等限制不变。
- 若不批准：ON3 记为"规格缺陷、无可解释结果"（QUICK invalid artifact 不作为结果），不重跑。

# FREEZE_ON3_exec_v1_1_DRAFT —— ON3 execution protocol v1.1 冻结文本（DRAFT；待独立复核 + Lead 批准）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。**本文件是 v1.1 冻结候选文本**；在独立挑战者（endpoint-auditor）只读复核 AMEND-001 v0.2 + 代码 diff/15 单测/两跑后，由 Lead 批准冻结并授权执行 ON3 一次。**文件不能自引用：本文件 SHA 由 Lead 批准文本引用。**

## 0. 冻结声明（v1.1）

> **ON3 execution protocol v1.1：`design_frozen_qualified_with_conditions` 的 execution protocol（v1.1；仅 null gate 规格修复）。**
> **性质：post-freeze, pre-valid-result 规格缺陷修复。** 无有效 full-run ON3 结果；存在 **QUICK=1 无效执行** artifact `tmp/on3_exec_quick_debug.invalid.json`（原 `on3_exec_quick_debug.json`，SHA `39868CE4…`；含 primary/results，**不得引用**）。
> **唯一改动**：null 门对象 `ρ_null` → **`Δρ_null = ρ(B4_null) − ρ(B2)`**，门条件为其 **2.5–97.5 覆盖 0 且 mean|Δρ_null| ≤ 0.05**；实现字段同步改为 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`。**其余全部逐项不变**（数据/切分/mask M+seed 20261130+fraction/端点/Δ/B2/B4/B5/纯冷/超参 grid/rank/λ/ALS/LOO/B6 1,000 refit_cu_only/bootstrap 5,000/指标/差值规则/MDE80/δ_min/schema（除 gate 字段名）/两跑/实测 wall/<15 min/batch2 仅披露/top-k 附录/失败类别/禁改项）。
> 旧 v0.3 协议 `8B4B8FCC…`、旧 freeze `41BC637C…`、旧 approval `F514347B…` 标 **invalid spec, no valid execution**（保留不改）。
> **peek（非盲）披露（AMEND-001.2-C1；规范文本 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`）**：实现方已见 QUICK invalid artifact 的 primary/results（Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、per-fold B0–B5、verdict=design_invalid）→ **v1.1 有效执行是 non-blind/peeked**；**不得称盲验/盲预注册确认/独立确认**；结论仅 O'Neil 内部开发性描述并必须附 peek 披露；QUICK primary 未用于选择方向/指标/门槛/切分/mask/超参/比较器；QUICK invalid artifact 不得引用；执行报告必须含 `peek_disclosure`。
> 不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**；阴/阳性措辞按冻结协议；执行仍仅 O'Neil 内部开发性描述。
> **执行一次条件**：独立挑战者复核 + Lead 批准 → 按 v1.1 执行 full B6 **1,000×5 refit_cu_only**、bootstrap **5,000**、**两跑逐字节一致**、实测 wall/bootstrap；发现实现偏差→停并重新预注册，不得执行时改协议。

## 1. 全链最终 SHA（v1.1 冻结引用）

| # | 文件 | SHA256 |
|---|---|---|
| 1 | `PROTOCOL_ON3_exec_v1_1_DRAFT.md`（v1.1 协议；含 peek 披露） | `8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4` |
| 2 | `AMENDMENT_ON3_EXEC-001.md`（v0.3；含 peek 披露） | `37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062` |
| 3 | `AMENDMENT_ON3_EXEC-001_delta.md`（v0.1→v0.3 delta） | `37A2B7FF0EA64313705B49A01441C2ECE7FD71318CFA3B960354C2F88C6C38F1` |
| 4 | `on3_refimpl/refimpl.py`（v1.1；null gate delta 字段+schema） | `AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515` |
| 5 | `on3_refimpl/run_on3_exec.py`（v1.1；gate 条件+字段名） | `41D2BC2C9BF2000FB1D46011A529B77061A7A24F6460A0429C6B7A73B0C789B4` |
| 6 | `on3_refimpl/test_refimpl.py`（test_11 delta gate） | `25B6E410089E945EC1245A91BBE005F522CC4B058BE0211F7546222223D8A0CA` |
| 7 | `on3_refimpl/test_results.txt`（Ran 15 tests OK 2.867 s） | `6282E395AF3CF4675F322F2D1CF6CE925A25F8217AC6F09B1172B80229E2DDD1` |
| 8 | `on3_refimpl/selfcheck.py`（v1.1） | `7F3EDA177854D1877C7A5BBC805C7A30A9BE0FA822A7EDAEC5B19CCDA33B180A` |
| 9 | `on3_refimpl/selfcheck.json`（v1.1；两跑逐字节一致） | `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A` |
| 10 | `on3_refimpl/reconstruction_audit.json`（target30 0/157,768；per fold 0） | `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315` |
| 11 | `on3_refimpl/data_prep.py`（metadata/nullness only） | `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510` |
| 12 | `tmp/on3_amend001_1_code.diff`（v1.0→v1.1 精确代码 diff） | `1F1AA05EC90F46B1C47EBBAC664F94E98D68AF9408F5640B173A0E43624A0871` |
| 13 | `tmp/on3_amend001_diff.json`（文本 diff 自检） | `2AFF481E9EF8F75C8AB4EA222CBD53D6ADA8EBF3730E4938455700EA9B9C0FF0` |
| 14 | `budget_test/run_b6_full_raw.py`（raw 5,000 perms） | `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A` |
| 15 | `budget_test/b6_full_raw.json`（5,000 perms / 306.722 s） | `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A` |
| 16 | `budget_test/b6_full_raw.log` | `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D` |
| 17 | `budget_test/budget_test.json`（frozen 306.722） | `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8` |
| 18 | `budget_test/run_budget.py`（early history） | `5BCA9F93F0CB59512BAF0BED7276A486709C09035875FC8D648661DF844AB963` |
| 19 | `challenge_ON3_amend001.md`（AMEND-001-C1 revise） | `A800627E25AF489A5C68526E1B8314E57142165CAB660415D54F9E1FF990EA29` |
| 20 | `tmp/on3_exec_quick_debug.invalid.json`（QUICK invalid；不引用） | `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5` |
| 21 | `tmp/usage_on3_quick_debug.invalid.json`（QUICK invalid） | `60DB423C22DA660FD43D5DEA4D5FBD857B9DD076D74B124C089D273150F9CC11` |
| 22 | 旧 protocol（invalid spec, no valid execution） | `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336` |
| 23 | 旧 freeze（invalid spec） | `41BC637C6BE391E2609B478A717CBF367A10A0EC7A262CA7E12551178B34C2E1` |
| 24 | 旧 approval（invalid spec） | `F514347BA162A571D9FE9A9B7BC1B0012AAADCE46EA233778D6C6BC7A7866280` |
| 25 | `PEEK_DISCLOSURE_ON3.md`（peek 规范文本） | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| 26 | `report_on3.md`（stop 报告；peek+路径更正后） | `9F2DC14E91E825E6A43FC5AB528FA7711163BBB8E81614A4B77962FC2723AE89` |
| 27 | `record_on3.md`（stop 审计记录；peek+路径更正后） | `2292C04853CB9FDCA451C790DC8863879E934CC1BBB05B9D4DD89249A0F43C16` |
| 28 | `usage_on3.json`（stop usage；peek+路径更正后） | `38647AFFCB7A0C91435C97E65EA02A79F8CBF14A6968F0FD5B0CBE4FA59AB548` |
| 29 | `record_on3_amend001.md`（AMEND 记录 v0.3/peek） | `883E27E4DD02AA82A37BF53033116E9AF1AC6840CFA2AAC6FC230BD493A90883` |
| 30 | `usage_on3_amend001.json`（AMEND usage v0.3/peek） | `B2A6236BC89B642E4CA8C5B595A8006344766058C13F0AC6DC01095417DC75B5` |
| 31 | `challenge_ON3_amend001_1.md`（AMEND-001.1-C1 revise 3） | `926C23F5C4C5F45608346EB29BA09DB54C8091E1D7A6C13AB35DCCCA8F45E10C` |

> 本文件 `FREEZE_ON3_exec_v1_1_DRAFT.md` 自身 SHA 由 Lead 批准文本引用（文件不能自引用）；获批后冻结为正式 v1.1 freeze 文本。

## 2. 执行条件/边界

- 仅 O'Neil 内部开发性描述；不称迁移/外推/决策收益/机制/独立确认/更新器优势/资源足够/新颖性；阴性只能写"本资源/本设计下无描述性增量"。
- 仅 viability；技术重复≠独立培养；batch2 仅披露；batch3 全失披露；702 个 15 行 pair-cell 排除；无暴露时间/assay 列；单药参照未用；缺失机制未知。
- **QUICK invalid artifact 不得引用为结果**；正式 `on3_exec.json` 不存在（仅指 formal artifact 未生成）。
- 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数/B6 语义（refit_cu_only）/bootstrap B/seed/percentile/schema（除已修 null gate 字段名）/报告模板。
- 发现实现偏差须停并重新预注册，不得执行时调整。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果。

## 3. 版本

v1.1-DRAFT，2026-10-27；待 endpoint-auditor 只读复核 + Lead 批准。旧 v0.3 标 invalid spec。**Lead 批准文本须引用 AMEND v0.3 `37D4BA11…` + 本 v1.1 freeze 新 SHA（旧 SHA 不得用于批准）并含 peek 限制/执行一次条件。**

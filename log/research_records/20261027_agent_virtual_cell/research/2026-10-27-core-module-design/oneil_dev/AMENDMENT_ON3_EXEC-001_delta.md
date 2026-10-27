# AMENDMENT_ON3_EXEC-001_delta —— v0.1 → v0.2 修订说明（按 challenge_ON3_amend001.md 5 必改）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。本文件说明 `AMENDMENT_ON3_EXEC-001.md` v0.1 → v0.2 的修订 delta；**不执行 ON3、不新读原始响应值做统计、不改旧冻结文件**。

## 0. 状态

- v0.1：`AMENDMENT_ON3_EXEC-001.md` 旧 SHA `5362C5A7D4A42AF2B87A1453A84A17405BFD7CAA874E47E4A4D02B4EE5532B8E`（**superseded/invalid**，按 challenge 修订）。
- v0.2（superseded）：`AMENDMENT_ON3_EXEC-001.md` SHA `EC0A3E93…`。
- **v0.3（当前）**：`AMENDMENT_ON3_EXEC-001.md` 新 SHA **`37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062`**（AMEND-001.2：peek 披露写死 + 旧路径修复 + freeze 全链）。
- 挑战：`challenge_ON3_amend001.md` SHA `A800627E25AF489A5C68526E1B8314E57142165CAB660415D54F9E1FF990EA29`（revise，5 必改）。

## 1. 5 必改的落实

| # | challenge 必改 | v0.2 落实 |
|---|---|---|
| 1 | 披露 QUICK 完整性质 | amendment §1.3/§4/§5 明确 `tmp/on3_exec_quick_debug.invalid.json`（原 `on3_exec_quick_debug.json`，SHA `39868CE4…`）是 **QUICK=1/N_PERM=20/BOOT=100 无效执行**，但含**primary/results**（Δρ mean 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5 ρ/MAE/top-k、context-ablation/pure-cold、verdict=design_invalid）；**不得引用为结果**；正式 on3_exec.json 不存在 ≠ 无 result-like artifact；性质改为 **post-freeze, pre-valid-result**；删除"QUICK 仅说明/无结果/未读响应值/pre-result"不准确表述。report_on3/record_on3/usage_on3/record_on3_amend001/usage_on3_amend001 同步更正（见各自文件）。 |
| 2 | 隔离 QUICK + 明确修订依据 | QUICK artifact 改名 `tmp/on3_exec_quick_debug.invalid.json`（SHA `39868CE4…`）、usage `tmp/usage_on3_quick_debug.invalid.json`（`60DB423C…`）；tmp quarantine、不进正式路径。修订依据仅来自同节已冻结 `Δρ_null` 定义 + null 预测含不变 `B2_static` 的代数必然性；**QUICK 的 primary/任何数字未用于选择指标/门槛/方向**；并明确 QUICK Δρ=0.0277<0.10，即使修复 gate 按冻结增量规则也 likely `no_increment`，不构成正结果。 |
| 3 | 实现/schema 精确 diff + test/schema/15/15/两跑 | `run_on3_exec.py`：null gate 条件改用 `null_drho`，输出字段改为 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`（old→new mapping 见 amendment §3.1）；`refimpl.py` 增加 `field_prefix` 与 `validate_null_gate_schema`；test_11 更新为 delta 字段+schema 断言；**Ran 15 tests OK（2.867 s）**（`test_results.txt` 新 SHA `6282E395…`）；两跑 selfcheck 逐字节一致（`selfcheck.json` `3EB44C25…`）；精确代码 diff `tmp/on3_amend001_1_code.diff` SHA `1F1AA05E…`。 |
| 4 | v1.1 freeze 链 | v1.1 protocol（新 SHA `8C4B2D9B…`，含 peek）；`FREEZE_ON3_exec_v1_1_DRAFT.md` 新全链 SHA（含 AMENDMENT v0.3 `37D4BA11…`、PEEK_DISCLOSURE、v1.1 protocol、代码/测试/selfcheck、stop/审计记录、旧 invalid spec、QUICK invalid artifact）；旧 `8B4B8FCC…`/`41BC637C…`/`F514347B…` 标 **invalid spec, no valid execution**；Lead 批准文本须引用 **AMENDMENT v0.3 `37D4BA11…` + v1.1 freeze 新 SHA**，不得引用旧 SHA。 |
| 5 | （建议）QUICK 改名 | 已改为 `.invalid.json` 并记录 SHA（见 §1/§2）。 |

## 2. 产物 SHA（本 delta 写入时）

| 文件 | SHA256 |
|---|---|
| `AMENDMENT_ON3_EXEC-001.md`（v0.2） | `EC0A3E9313F33D181B978F7886F01D0631B5353B18FF5C5EC026AC8FB750C5A1` |
| `PROTOCOL_ON3_exec_v1_1_DRAFT.md` | `DC4C40829F744DF67D160BD5F20DF2547583ACF9C980A8FBD89BD5EBC643F6FF` |
| `FREEZE_ON3_exec_v1_1_DRAFT.md` | 见该文件（全链） |
| `tmp/on3_amend001_1_code.diff` | `1F1AA05EC90F46B1C47EBBAC664F94E98D68AF9408F5640B173A0E43624A0871` |
| `on3_refimpl/refimpl.py` | `AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515` |
| `on3_refimpl/test_refimpl.py` | `25B6E410089E945EC1245A91BBE005F522CC4B058BE0211F7546222223D8A0CA` |
| `on3_refimpl/test_results.txt` | `6282E395AF3CF4675F322F2D1CF6CE925A25F8217AC6F09B1172B80229E2DDD1` |
| `on3_refimpl/selfcheck.py` | `7F3EDA177854D1877C7A5BBC805C7A30A9BE0FA822A7EDAEC5B19CCDA33B180A` |
| `on3_refimpl/selfcheck.json` | `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A` |
| `on3_refimpl/run_on3_exec.py`（v1.1） | `41D2BC2C9BF2000FB1D46011A529B77061A7A24F6460A0429C6B7A73B0C789B4` |
| `tmp/on3_exec_quick_debug.invalid.json`（QUICK invalid） | `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5` |
| `tmp/usage_on3_quick_debug.invalid.json`（QUICK invalid） | `60DB423C22DA660FD43D5DEA4D5FBD857B9DD076D74B124C089D273150F9CC11` |
| 旧 protocol/freeze/approval（invalid spec） | `8B4B8FCC…` / `41BC637C…` / `F514347B…` |

## 3. 性质与边界

- **post-freeze, pre-valid-result**：旧 v0.3 已冻结但无有效 full-run 结果；存在 QUICK invalid result-shaped artifact（已披露/隔离，不引用）。
- 修订仅 null gate + 实现字段名；成功标准/增量规则/所有设计不变；不是换指标/换门槛制造收益。
- 本任务未执行 ON3 full run、未新读原始响应值；QUICK 不当作结果；不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结≠资源足够/关系成立/Stage1/效果。
- 下一步：endpoint-auditor 只读复核 v0.2 + 代码 diff + 15/15 + 两跑 + v1.1 草案；通过后 Lead 批准冻结 v1.1 并授权执行一次。


## 4. v0.3 增量（AMEND-001.2-C1；3 必改）

| # | 必改 | 落实 |
|---|---|---|
| 1 | **peek 限制写死** | 新 `PEEK_DISCLOSURE_ON3.md`（SHA `B4CAD955…`）为规范披露；AMEND v0.3（`37D4BA11…`）§2A、PROTOCOL v1.1（`8C4B2D9B…`）、FREEZE v1.1、report_on3/record_on3/usage_on3/record_on3_amend001/usage_on3_amend001 全部明确：实现方已见 QUICK invalid primary/results → **non-blind/peeked**；不得称盲验/预注册确认/独立确认；结论仅 O'Neil 内部开发性描述并附 peek；QUICK 未用于选择指标/门槛/方向；执行报告必须含 `peek_disclosure`。 |
| 2 | **旧 QUICK 路径修复** | report_on3（§3/§6）、record_on3（§5）、usage_on3（`quick_debug_settings.note`）等全部改 `tmp/on3_exec_quick_debug.invalid.json`/`tmp/usage_on3_quick_debug.invalid.json`（quarantine）；旧路径不存在（已核）。 |
| 3 | **freeze v1.1 全链 SHA** | `FREEZE_ON3_exec_v1_1_DRAFT.md` 新表补入更新后 report_on3/record_on3/usage_on3/record_on3_amend001/usage_on3_amend001 + PEEK + AMEND v0.3 + protocol 新 SHA；全链重算；旧 SHA 不得用于批准。 |

**v0.3 关键 SHA（写入时）**：
- AMEND v0.3：`37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062`
- PEEK_DISCLOSURE：`B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`
- PROTOCOL v1.1（含 peek）：`8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4`
- report_on3 / record_on3 / usage_on3：`9F2DC14E…` / `2292C048…` / `38647AFF…`（最终 SHA 见 FREEZE v1.1）
- FREEZE v1.1：本文件写入后重算（见该文件/Lead 文本）。

**性质/边界不变**：post-freeze, pre-valid-result；不执行 ON3；QUICK invalid artifact 不引用；不称盲验/迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结≠资源足够/关系成立/Stage1/效果。

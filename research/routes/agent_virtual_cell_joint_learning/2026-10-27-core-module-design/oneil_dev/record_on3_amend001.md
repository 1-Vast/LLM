# R199-ON3-AMEND-001.2 起草审计记录（record_on3_amend001.md；AMEND v0.3 + peek 披露）

角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R199-ON3-AMEND-001.2（按 `challenge_ON3_amend001_1.md` 3 必改：peek 披露写死 + 旧 QUICK 路径修复 + freeze v1.1 全链 SHA）。**本任务未执行 ON3 full run；未新读原始响应值做统计；未改旧冻结/批准文件；QUICK invalid artifact 已披露/隔离且不引用为结果。**

## 0. peek（非盲）披露（AMEND-001.2-C1；规范文本 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`）

- **peek 事实**：实现方已见 `tmp/on3_exec_quick_debug.invalid.json`（SHA `39868CE4…`）的 primary/results（Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、context-ablation/pure-cold、verdict=design_invalid）→ **ON3 v1.1 有效执行 non-blind/peeked**。
- **限制**：不得称盲验/盲预注册确认/独立确认；结论仅 O'Neil 内部开发性描述并附 peek 披露；不得升级为迁移/外推/决策收益/机制/独立确认/更新器优势/资源足够/新颖性；**QUICK primary 未用于选择方向/指标/门槛/切分/mask/超参/比较器**；QUICK invalid artifact 不得引用；执行报告必须含 `peek_disclosure`。
- 旧 QUICK 路径已全部改 `.invalid.json`（quarantine）；旧 `on3_exec_quick_debug.json`/`usage_on3_quick_debug.json` 不存在。

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 22:04–22:05 | 读 task-81、`challenge_ON3_amend001.md`（revise 5 必改）、旧冻结协议/AMEND v0.1/停止记录/QUICK artifact |
| 22:05 | QUICK artifact 改名为 `*.invalid.json`（quarantine）；保存 v1.0 代码副本 |
| 22:06–22:08 | 修 `refimpl.py`（null gate `field_prefix='delta_rho'`+`validate_null_gate_schema`）、test_11、selfcheck、`run_on3_exec.py`（条件+字段名）；重跑 **15/15 单测 OK（2.867 s）**；两跑 selfcheck 逐字节一致 |
| 22:08 | 生成精确代码 diff `tmp/on3_amend001_1_code.diff`（SHA `1F1AA05E…`）；生成 `PROTOCOL_ON3_exec_v1_1_DRAFT.md`（`DC4C4082…`） |
| 22:09 | 重写 `AMENDMENT_ON3_EXEC-001.md` v0.2（`EC0A3E93…`；QUICK 完整披露+代码 diff+v1.1 链）；写 `AMENDMENT_ON3_EXEC-001_delta.md`（`9B397B56…`） |
| 22:10 | 写 `FREEZE_ON3_exec_v1_1_DRAFT.md`（`DA4D787E…`；全链 SHA）；写 report/record/usage 更正段；写本记录/usage |


> **版本注**：本记录中的 v0.2 `EC0A3E93…`、旧 protocol `DC4C4082…`、旧 freeze `DA4D787E…`、旧 delta `9B397B56…` 均为前一任务历史，已被 AMEND v0.3 / 本任务新 SHA **superseded**；**不得用于批准**。当前批准链以本文 §2 表与 `FREEZE_ON3_exec_v1_1_DRAFT.md` 为准。

## 2. 输入/关键 SHA

| 文件 | SHA256 |
|---|---|
| `challenge_ON3_amend001.md`（revise 5 必改） | `A800627E25AF489A5C68526E1B8314E57142165CAB660415D54F9E1FF990EA29` |
| `PEEK_DISCLOSURE_ON3.md`（peek 规范文本） | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| 旧 protocol v0.3（invalid spec） | `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336` |
| 旧 freeze（invalid spec） | `41BC637C6BE391E2609B478A717CBF367A10A0EC7A262CA7E12551178B34C2E1` |
| 旧 approval（invalid spec） | `F514347BA162A571D9FE9A9B7BC1B0012AAADCE46EA233778D6C6BC7A7866280` |
| AMEND v0.1（superseded） | `5362C5A7D4A42AF2B87A1453A84A17405BFD7CAA874E47E4A4D02B4EE5532B8E` |
| **AMEND v0.3（含 peek）** | **`37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062`** |
| AMEND delta | `9B397B56B94A851DA82469F69A139582C81C3FFFF68032B8249BCADBADEE0066` |
| **v1.1 protocol（含 peek）** | **`8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4`** |
| **v1.1 freeze draft** | 见 `FREEZE_ON3_exec_v1_1_DRAFT.md`（本任务后重算；Lead 批准文本引用新 SHA） |
| 代码 diff | `1F1AA05EC90F46B1C47EBBAC664F94E98D68AF9408F5640B173A0E43624A0871` |
| `on3_refimpl/refimpl.py`（v1.1） | `AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515` |
| `on3_refimpl/run_on3_exec.py`（v1.1） | `41D2BC2C9BF2000FB1D46011A529B77061A7A24F6460A0429C6B7A73B0C789B4` |
| `on3_refimpl/test_refimpl.py` | `25B6E410089E945EC1245A91BBE005F522CC4B058BE0211F7546222223D8A0CA` |
| `on3_refimpl/test_results.txt`（15/15 OK） | `6282E395AF3CF4675F322F2D1CF6CE925A25F8217AC6F09B1172B80229E2DDD1` |
| `on3_refimpl/selfcheck.py` / `selfcheck.json`（两跑一致） | `7F3EDA177854D1877C7A5BBC805C7A30A9BE0FA822A7EDAEC5B19CCDA33B180A` / `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A` |
| QUICK invalid artifact（不引用） | `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5`；usage `60DB423C22DA660FD43D5DEA4D5FBD857B9DD076D74B124C089D273150F9CC11` |
| `report_on3.md` / `record_on3.md` / `usage_on3.json`（peek+路径更正后） | `9F2DC14E91E825E6A43FC5AB528FA7711163BBB8E81614A4B77962FC2723AE89` / `2292C04853CB9FDCA451C790DC8863879E934CC1BBB05B9D4DD89249A0F43C16` / `38647AFFCB7A0C91435C97E65EA02A79F8CBF14A6968F0FD5B0CBE4FA59AB548` |

## 3. 3 必改落实（对照 AMEND-001.2-C1）

1. **QUICK 完整披露**：AMEND v0.3 §1.3/§4/§5 与 report/record/usage 更正段明确：QUICK artifact 是 `QUICK=1/N_PERM=20/BOOT=100` **无效执行**，但含 **primary/results**（Δρ mean 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5 ρ/MAE/top-k、context-ablation/pure-cold、verdict=design_invalid）；**不得引用为结果**；正式 on3_exec.json 不存在 ≠ 无 result-like artifact；性质改为 **post-freeze, pre-valid-result**；删除"QUICK 仅说明/无结果/未读响应值/pre-result"。
2. **隔离+修订依据**：QUICK 已改名 `tmp/on3_exec_quick_debug.invalid.json`/`usage_on3_quick_debug.invalid.json`（quarantine）；AMEND 明确修订仅由同节 Δρ_null 定义/代数必然性决定，QUICK primary 未用于选择指标/门槛/方向；QUICK Δρ 0.0277<0.10，修复后仍 likely `no_increment`，不构成正结果。
3. **实现/schema diff**：`run_on3_exec.py` gate 用 `null_drho` + 字段 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`（old→new mapping）；`refimpl.py` 支持 `field_prefix`+`validate_null_gate_schema`；test_11 更新；**15/15 OK（2.867 s）**；两跑 selfcheck 一致；精确 diff `tmp/on3_amend001_1_code.diff`。
4. **freeze v1.1 全链 SHA（本任务修复）**：更新后 report/record/usage/record_amend/usage_amend（及 PEEK_DISCLOSURE）SHA 补入 `FREEZE_ON3_exec_v1_1_DRAFT.md`；全链重算；旧 SHA 不得用于批准；Lead 批准文本引用 **AMEND v0.3 `37D4BA11…` + 新 v1.1 freeze SHA**。
5. **peek 写死（本任务核心）**：AMEND v0.3/PROTOCOL v1.1/FREEZE v1.1/report/record/usage/record_amend/usage_amend 全部明确 non-blind/peeked、禁止措辞、QUICK 未用于选择；执行报告必须含 `peek_disclosure`。
6. **旧 QUICK 路径修复**：report/record/usage 等旧路径全部改 `.invalid.json`；旧路径不存在；quarantine 标注完成。

## 4. 决策/边界

- **不执行 ON3 full run**；QUICK invalid artifact 不作为结果；未新读原始响应值做统计（本次只改文档/实现/测试；QUICK 数值来自已有 artifact 的披露核对，不用于修订方向）。
- 修订仅 null gate + 实现字段名；成功标准/增量规则/MDE/其他全部不变；**不是换指标/门槛制造收益**（见 AMEND §4）。
- 未改旧冻结/批准文件；QUICK artifact 已 quarantine；不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结≠资源足够/关系成立/Stage1/效果。
- 下一步：endpoint-auditor 只读复核 **AMEND v0.3** + 本任务 delta + 代码 diff + 15/15 + 两跑 + **v1.1 protocol（含 peek）/freeze v1.1（全链 SHA）**；通过后 Lead 批准冻结 v1.1 并授权执行 ON3 一次（执行报告必须带 peek 披露）。

## 5. 产出/更正

- `AMENDMENT_ON3_EXEC-001.md`（**v0.3**，`37D4BA11…`）、`AMENDMENT_ON3_EXEC-001_delta.md`（本任务更新后新 SHA 见 FREEZE v1.1）、`PROTOCOL_ON3_exec_v1_1_DRAFT.md`（**`8C4B2D9B…`**，含 peek）、`PEEK_DISCLOSURE_ON3.md`（`B4CAD955…`）、`FREEZE_ON3_exec_v1_1_DRAFT.md`（本任务重算新 SHA）。
- 代码/测试/自检：`refimpl.py`/`run_on3_exec.py`/`test_refimpl.py`/`test_results.txt`/`selfcheck.py`/`selfcheck.json`（SHA 见 §2）；代码 diff `tmp/on3_amend001_1_code.diff`。
- 停止记录更正：`report_on3.md`/`record_on3.md`/`usage_on3.json` 已加 QUICK 完整披露（§0 更正）；本 record/usage 亦更新。
- 未执行 full run；正式 `on3_exec.json` 不存在；QUICK invalid artifact 不引用。

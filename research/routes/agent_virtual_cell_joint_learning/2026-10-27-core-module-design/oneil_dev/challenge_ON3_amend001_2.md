# R199-ON3-AMEND-001.2-C1 最终复核（challenge_ON3_amend001_2.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 AMEND-001.2 起草）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PEEK_DISCLOSURE_ON3.md, AMENDMENT_ON3_EXEC-001.md v0.3, AMENDMENT_ON3_EXEC-001_delta.md, PROTOCOL_ON3_exec_v1_1_DRAFT.md, FREEZE_ON3_exec_v1_1_DRAFT.md, report_on3.md, record_on3.md, usage_on3.json, record_on3_amend001.md, usage_on3_amend001.json, on3_refimpl/}` + `tmp/on3_exec_quick_debug.invalid.json`。
方式：**只读复核**（文档/全链 SHA/peek 覆盖/旧路径/测试/两跑；**不运行 ON3、不解析原始响应值做统计、不改产物**）；只写本文件与 `tmp/`。
完整性：`PEEK_DISCLOSURE_ON3.md` **`B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`**；`AMENDMENT_ON3_EXEC-001.md` v0.3 **`37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062`**；`PROTOCOL_ON3_exec_v1_1_DRAFT.md` **`8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4`**；`FREEZE_ON3_exec_v1_1_DRAFT.md` **`14A6E1E3A5204A1C17423F0491DFDCF9A4951A9A93AC2011DA12C4C127F89C25`**；delta **`37A2B7FF…`**；report **`9F2DC14E…`**/record **`2292C048…`**/usage **`38647AFF…`**；record_amend **`883E27E4…`**/usage_amend **`B2A6236B…`**；code/test 未变 `AD1C54D5…`/`41D2BC2C…`/`25B6E410…`/test_results `6282E395…`/selfcheck `7F3EDA17…`/`3EB44C25…`。全部与公告/FREEZE 表一致。

## 0. 总判决

**approve_to_lead。** AMEND-001.2 的 3 条必改已闭合：
1. **peek 披露全覆盖**：新增 `PEEK_DISCLOSURE_ON3.md` 规范文本；AMEND v0.3 §2A、PROTOCOL v1.1、FREEZE v1.1、report/record/usage、record/usage amend 均写明 QUICK invalid artifact 的 primary 事实（Δρ 0.0277068、CI [0.01828,0.03572]、4-of-5、per-fold B0–B5、verdict=design_invalid）、**non-blind/peeked**、**不得称盲验/盲预注册确认/独立确认**、结论仅 O'Neil 内部开发性描述并必须附 peek 披露、QUICK primary 未用于选择方向/指标/阈值/切分/mask/超参/比较器；usage/record 有 `peek_disclosure` 字段。
2. **旧 QUICK 路径已全部改 `.invalid.json`**；旧 `tmp/on3_exec_quick_debug.json`/`usage_on3_quick_debug.json` 不存在；历史原名只作为 provenance（"原 …"）出现。
3. **FREEZE v1.1 全链已补齐**：PEEK_DISCLOSURE、updated report/record/usage、record_amend/usage_amend、challenge 链等 31 项 SHA 均在表中；实际 SHA 与磁盘逐项一致；旧 8B4B8FCC/41BC637C/F514347B 仅标 invalid spec，不再用于批准。
代码/测试/selfcheck 未变，15/15 与两跑 `3EB44C25…` 仍有效；本轮仅文档/披露变更，无需重跑。**可提交 Lead 批准 v1.1 并执行一次（non-blind/peeked）。**

## 1. 逐条确认

### ① peek 限制全覆盖/一致性 —— **PASS**

- `PEEK_DISCLOSURE_ON3.md`（`B4CAD955…`）§1 写死 peek 事实：QUICK invalid `39868CE4…`、QUICK=1/N_PERM=20/BOOT_B=100、primary Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、verdict design_invalid；§2 写死 non-blind/peeked、不得称盲验/盲预注册确认/独立确认、结论仅 O'Neil 内部开发性描述并附 peek 披露、QUICK 未用于选择、执行报告必须含 `peek_disclosure`；§3 允许/禁止措辞。**PASS。**
- **覆盖**：AMEND v0.3 §2A（line61–70）、PROTOCOL v1.1（line6/16/91/111）、FREEZE v1.1（line11）、report_on3 §0.1、record_on3 §0.1、usage_on3 `peek_disclosure`、record_on3_amend001 §0、usage_on3_amend001 `peek_disclosure` 均写明/引用；内容一致：QUICK primary 未用于选择、不得称盲验/独立确认、结论仅开发性描述+peek。**PASS。**
- 无“盲验/独立确认/预注册确认”阳性表述；PEEK §3 明确禁止。**PASS。**

### ② 旧 QUICK 路径/隔离 —— **PASS**

- `tmp/on3_exec_quick_debug.invalid.json`/`tmp/usage_on3_quick_debug.invalid.json` 存在；旧 `tmp/on3_exec_quick_debug.json`/`usage_on3_quick_debug.json` 不存在。
- report/record/usage/amend/record_amend/usage_amend 中旧名仅作为 provenance（"原 …"）；无旧路径作为当前引用。**PASS。**

### ③ FREEZE v1.1 全链 / 旧 invalid —— **PASS**

- `FREEZE_ON3_exec_v1_1_DRAFT.md` 表 1–31 含 protocol 8C4B、AMEND 37D4、delta 37A2、refimpl/run/test/test_results/selfcheck/reconstruction/data_prep、code/text diff、budget 证据、旧 invalid spec、PEEK B4CA、updated report 9F2D/record 2292/usage 3864、record_amend 883E/usage_amend B2A6、challenge amend001 A800/amend001_1 926C。实际 SHA 逐项核过一致。**PASS。**
- 旧 protocol `8B4B8FCC…`、freeze `41BC637C…`、approval `F514347B…` 仅标 invalid spec/no valid execution，不出现在批准链。**PASS。**

### ④ 代码/测试/selfcheck 未变 —— **PASS（可接受）**

- `refimpl.py AD1C54D5…`、`run_on3_exec.py 41D2BC2C…`、`test_refimpl.py 25B6E410…`、`test_results.txt 6282E395…`（15/15 OK 2.867 s）、`selfcheck.py 7F3EDA17…`、`selfcheck.json 3EB44C25…`；与上一轮一致。
- 本轮只改文档/披露/FREEZE 全链，不改代码/测试，故 **15/15 与两跑无需重跑可接受**；若 Lead 要求在 freeze 前重跑亦可，但非本次 must-fix。**PASS。**

## 2. Lead 批准文本（建议直接采用）

> **批准 AMENDMENT_ON3_EXEC-001 v0.3，冻结 ON3 execution protocol v1.1，授权执行一次（non-blind/peeked，附 peek 限制）。**
> **修订/peek 依据**：`AMENDMENT_ON3_EXEC-001.md` v0.3 SHA `37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062`；规范 peek 文本 `PEEK_DISCLOSURE_ON3.md` SHA `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`。
> **v1.1 冻结文本**：`FREEZE_ON3_exec_v1_1_DRAFT.md` SHA `14A6E1E3A5204A1C17423F0491DFDCF9A4951A9A93AC2011DA12C4C127F89C25`；v1.1 protocol `PROTOCOL_ON3_exec_v1_1_DRAFT.md` SHA `8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4`；updated record `2292C048…`/usage `38647AFF…`/report `9F2DC14E…`；PEEK `B4CAD955…`；refimpl `AD1C54D5…`/run `41D2BC2C…`/test `25B6E410…`/test_results `6282E395…`（15/15 OK）/selfcheck `7F3EDA17…`/`3EB44C25…`（两跑一致）；旧 v0.3 protocol `8B4B8FCC…`/freeze `41BC637C…`/approval `F514347B…` 标 invalid spec。
> **唯一设计改动**：null gate 对象 `ρ_null` → `Δρ_null = ρ(B4_null)−ρ(B2)`，输出字段 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`；其余数据/切分/mask/端点/B2/B4/B5/纯冷/B6 1,000×5 refit_cu_only/bootstrap 5,000/指标/差值规则/MDE80/δ_min/schema（除 gate 字段名）/两跑/实测 wall/<15 min/失败类别/禁改项全部不变；成功标准未降。
> **peek（非盲）限制（写死）**：实现方已见 QUICK invalid artifact `tmp/on3_exec_quick_debug.invalid.json`（`39868CE4…`）的 primary/results（Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、per-fold B0–B5、verdict=design_invalid）→ **v1.1 有效执行是 non-blind/peeked**；**不得称盲验/盲预注册确认/独立确认**；结论仅写“O'Neil 内部、本设计下的开发性描述结果（non-blind/peeked），附 `PEEK_DISCLOSURE_ON3.md` 披露”；QUICK primary 未用于选择方向/指标/阈值/切分/mask/超参/比较器；QUICK invalid artifact 不得作为结果引用；执行报告必须含 `peek_disclosure`。
> **执行一次条件**：按 v1.1 执行 **full B6 1,000×5 refit_cu_only**、bootstrap **5,000**、**两跑逐字节一致**、实测 wall/bootstrap；不运行效果/更新器；结果仅开发性描述；冻结≠资源足够/关系成立/Stage 1/效果；发现实现偏差→停并重新预注册，不得执行时改协议。

## 3. 冻结清单（Lead 批准时逐项）

- **v1.1 冻结文本**：`FREEZE_ON3_exec_v1_1_DRAFT.md` `14A6E1E3…`；`PROTOCOL_ON3_exec_v1_1_DRAFT.md` `8C4B2D9B…`；`AMENDMENT_ON3_EXEC-001.md` v0.3 `37D4BA11…`；`PEEK_DISCLOSURE_ON3.md` `B4CAD955…`；delta `37A2B7FF…`；text/code diff `2AFF481E…`/`1F1AA05E…`。
- **实现/测试**：refimpl `AD1C54D5…`、run `41D2BC2C…`、test_refimpl `25B6E410…`、test_results `6282E395…`（15/15 OK）、selfcheck.py `7F3EDA17…`、selfcheck.json `3EB44C25…`（两跑）、reconstruction `DC93D4FE…`、data_prep `7C11B0C5…`。
- **stop/审计**：report `9F2DC14E…`、record `2292C048…`、usage `38647AFF…`、record_amend `883E27E4…`、usage_amend `B2A6236B…`；QUICK invalid `39868CE4…`/`60DB423C…`（不引用）。
- **预算**：frozen 306.722 s；raw `F81DCC09…`/`0ABE96F0…`/`38A3B9F3…`；budget `4D08670F…`。
- **禁改**：mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数/B6 语义 refit_cu_only/bootstrap B/seed/percentile/schema（除已修 gate 字段名）/报告模板；冻结后不改；偏差停并重新预注册。

## 4. 复核证据与本轮边界

- 实际 SHA 见页首；FREEZE 表 1–31 与磁盘一致；旧 QUICK 路径不存在、`.invalid.json` quarantine；peek 覆盖 AMEND/PROTOCOL/FREEZE/report/record/usage/amend；15/15 与两跑 SHA 未变。
- **本轮未运行 ON3、未运行效果/训练/更新器、未解析原始响应值做统计**；只读文档/SHA/既有 QUICK invalid artifact；只写本文件与 `tmp/`；未改冻结/草案产物。
- **approve_to_lead**；Lead 批准后冻结 v1.1，执行一次；执行仍仅 O'Neil 内部开发性描述，**non-blind/peeked，不得称盲验/独立确认**；冻结≠资源足够/关系成立/Stage1/效果。

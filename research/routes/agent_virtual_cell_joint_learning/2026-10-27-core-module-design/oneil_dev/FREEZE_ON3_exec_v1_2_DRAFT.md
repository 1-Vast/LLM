# FREEZE_ON3_exec_v1_2_DRAFT —— ON3 execution protocol v1.2 冻结文本（DRAFT；AMEND-001.3 溯源修复；待 Lead 复核/批准）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。**本文件是 v1.2 冻结候选文本**：仅修复 ON3 执行实现的 input 溯源字段（旧 invalid spec SHA → v1.2 protocol/freeze），**执行语义/设计/指标/B6/bootstrap/两跑要求与 v1.1 完全相同**。依据 Lead `DECISION_ON3_PROVENANCE.md`（SHA `6C2DFD55C89D2BE4989480307A7A538829E850627E784CB0F815EEE359EB00C3`；Option B 严格修复）。**文件不能自引用：本文件 SHA 由 Lead 批准/复核文本引用。**

## 0. 冻结声明/性质

> **ON3 execution protocol v1.2（provenance-only repair；non-blind/peeked）。**
> **唯一改动**：`on3_refimpl/run_on3_exec.py` 的 `protocol` / `inputs.protocol_on3_exec` / `inputs.freeze_on3_exec` 由旧 invalid spec 改为 **v1.2 protocol `B22A7FC7…` / v1.2 freeze 本文件**；**执行逻辑/数据/切分/mask M+seed 20261130/fraction/端点/Δ/B2/B4/B5/纯冷/超参 grid/rank/λ/ALS/LOO/B6 1,000×5 refit_cu_only/bootstrap 5,000/指标/差值规则/MDE80/δ_min/schema（除 gate 字段名）/两跑/实测 wall/<15 min/batch2 仅披露/top-k 附录/失败类别/禁改项全部与 v1.1 相同**。
> **v1.1 provisional 执行（on3_exec SHA `5698151968…`）因 input 溯源字段不符，已 quarantine、不得引用/登记；v1.2 重跑一次后以其正式产物为准。**
> **peek（非盲）限制（不变）**：实现方已见 QUICK invalid artifact 的 primary/results → v1.2 执行 **non-blind/peeked**；不得称盲验/盲预注册确认/独立确认；结论仅 O'Neil 内部开发性描述并必须附 peek 披露；QUICK primary 未用于选择方向/指标/阈值/切分/mask/超参/比较器；QUICK invalid artifact 不得引用。
> 旧 v0.3 `8B4B8FCC…`/`41BC637C…`/`F514347B…` 标 **invalid spec, no valid execution**（保留不改）；v1.1 协议/freeze `8C4B2D9B…`/`14A6E1E3…` 为已批准基线，仅 input 溯源字段被 v1.2 superseded（语义不变）。
> 不称迁移/决策收益/机制/独立确认/更新器优势/资源足够/新颖性；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**；阴性只能写"本资源/本设计下无描述性增量（non-blind/peeked）"。
> **执行一次条件**：Lead 批准 v1.2 → 按 v1.2 重跑 **full B6 1,000×5 refit_cu_only、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap**；报告含 `peek_disclosure` + **runtime deviation**（v1.1 provisional wall≈19.6/21.6 min > 冻结估计 <15 min，仅计时偏差、未改设计；v1.2 wall 另报）；发现实现偏差→停并重新预注册，不得执行时改协议。

## 1. 全链最终 SHA（v1.2 冻结引用）

| # | 文件 | SHA256 |
|---|---|---|
| 1 | `DECISION_ON3_PROVENANCE.md`（Lead Option B 裁定） | `6C2DFD55C89D2BE4989480307A7A538829E850627E784CB0F815EEE359EB00C3` |
| 2 | `AMENDMENT_ON3_EXEC-001_3.md`（AMEND-001.3 溯源修复） | `7AFCE1C9BA1FC73385EA6EFEEBC51009B7F258D20511B853A2137C118F1A1184` |
| 3 | `PROTOCOL_ON3_exec_v1_2_DRAFT.md`（v1.2 protocol） | `B22A7FC791B07C415DE8C8A48DF916DDAC7309A9ECD02CFBE567050F9099A2A8` |
| 4 | `on3_refimpl/run_on3_exec.py`（v1.2；仅溯源字段） | `B3A5569EC852AE6FD1B5D879336E44EC3F1F5F55D2BB420DF9D7EED41CEC8E39` |
| 5 | `tmp/on3_amend001_3_code.diff`（v1.1→v1.2 精确 diff） | `EF43ACDE57EB3DB574F2142CE9904E7F8D19651E3DAF9154486A795A13F0CCBA` |
| 6 | `on3_refimpl/refimpl.py`（未变） | `AD1C54D5AA915B35ADD6ED76ED393DC7DFC3CB5892895922A9006647D7FAE515` |
| 7 | `on3_refimpl/test_refimpl.py`（未变） | `25B6E410089E945EC1245A91BBE005F522CC4B058BE0211F7546222223D8A0CA` |
| 8 | `on3_refimpl/test_results.txt`（15/15 OK 2.626 s） | `D93AAA067C46B0836E7FD7F604F08CBE3B304F7F790121B669F5313C302E232F` |
| 9 | `on3_refimpl/selfcheck.py`（未变） | `7F3EDA177854D1877C7A5BBC805C7A30A9BE0FA822A7EDAEC5B19CCDA33B180A` |
| 10 | `on3_refimpl/selfcheck.json`（两跑逐字节一致） | `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A` |
| 11 | `on3_refimpl/reconstruction_audit.json`（target30 0/157,768；per fold 0） | `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315` |
| 12 | `on3_refimpl/data_prep.py` | `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510` |
| 13 | `budget_test/run_b6_full_raw.py`（raw 5,000 perms） | `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A` |
| 14 | `budget_test/b6_full_raw.json`（5,000 perms / 306.722 s） | `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A` |
| 15 | `budget_test/b6_full_raw.log` | `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D` |
| 16 | `budget_test/budget_test.json`（frozen 306.722） | `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8` |
| 17 | `budget_test/run_budget.py`（early history） | `5BCA9F93F0CB59512BAF0BED7276A486709C09035875FC8D648661DF844AB963` |
| 18 | `PEEK_DISCLOSURE_ON3.md`（peek 规范） | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| 19 | `AMENDMENT_ON3_EXEC-001.md`（v0.3；设计/peek） | `37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062` |
| 20 | v1.1 protocol（已批准基线；input 溯源被 v1.2 superseded） | `8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4` |
| 21 | v1.1 freeze（已批准基线；同上） | `14A6E1E3A5204A1C17423F0491DFDCF9A4951A9A93AC2011DA12C4C127F89C25` |
| 22 | 旧 v0.3 protocol（invalid spec） | `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336` |
| 23 | 旧 freeze（invalid spec） | `41BC637C6BE391E2609B478A717CBF367A10A0EC7A262CA7E12551178B34C2E1` |
| 24 | 旧 approval（invalid spec） | `F514347BA162A571D9FE9A9B7BC1B0012AAADCE46EA233778D6C6BC7A7866280` |
| 25 | `tmp/on3_exec_v1_1_provisional.json`（**quarantine；不得引用**） | `5698151968A10D7EA1E7735603690292640CFE7F880BFF58D19255805FB59C6F` |
| 26 | `tmp/report_on3_exec_v1_1_provisional.md`（**quarantine**） | `7AC71D57A00EF8E95995E381480B4FD24F1C474E12DF827F7B3A3E74A893B27D` |
| 27 | `tmp/record_on3_exec_v1_1_provisional.md`（**quarantine**） | `4BCC8BACAB86041CFFA87719BC728AFCB917D960D4513A9B14951340D5A03857` |
| 28 | `tmp/usage_on3_exec_v1_1_provisional.json`（**quarantine**） | `11DFF763EC9DB210EACA4BDB4AC25DBBB12981D2B59FF7E76FA3ACF105B732D6` |

> 本文件 `FREEZE_ON3_exec_v1_2_DRAFT.md` 自身 SHA 由 Lead 复核/批准文本引用（文件不能自引用）。

## 2. 执行/边界（不变）

- 仅 O'Neil 内部开发性描述（non-blind/peeked）；不称盲验/独立确认/迁移/决策收益/机制/更新器优势/资源足够/新颖性；阴性只能写"本资源/本设计下无描述性增量（non-blind/peeked）"。
- 仅 viability；技术重复≠独立培养；batch2 仅披露、batch3 全失；702 个 15 行 pair-cell 排除；无暴露时间/assay；单药参照未用；缺失机制未知。
- **provisional v1.1 结果 quarantine、不得引用/登记**；v1.2 正式产物产生后才可引用 v1.2 结果。
- 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数/B6 语义/bootstrap/schema（除已修 gate 字段名）/报告模板；发现实现偏差→停并重新预注册。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果。

## 3. 版本

v1.2-DRAFT，2026-10-27；依据 `DECISION_ON3_PROVENANCE.md` Option B；待 Lead 复核/批准后执行一次。v1.1 链作为已批准基线，仅 input 溯源被 v1.2 superseded。

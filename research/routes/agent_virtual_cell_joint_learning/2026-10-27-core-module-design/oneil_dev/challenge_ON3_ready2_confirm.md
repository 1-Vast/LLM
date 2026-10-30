# R199-ON3-READY.2-C1 最终确认（challenge_ON3_ready2_confirm.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 ON3-READY.2 实现）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON3_exec_DRAFT.md, record_on3_ready.md, usage_on3_ready.json, on3_refimpl/, budget_test/}` + 只读参照 `challenge_ON3_exec_confirm.md`、ON2/ON2-EX 冻结产物。
方式：**只读复核**（文档/SHA/测试结果/raw 日志/预算 JSON；**不运行 ON3 效果/训练/更新器/执行代码、不读响应值**）；只写本文件与 `tmp/`。
完整性：`PROTOCOL_ON3_exec_DRAFT.md` `05ADBD9F…B123`、`record_on3_ready.md` `1F5BC468…9BAC2`、`usage_on3_ready.json` `0B20686C…0671F`；`on3_refimpl/refimpl.py` `B5485B23…0FA4`、`test_refimpl.py` `B36D1FCF…9A0F`、`test_results.txt` `8E17572B…030E`、`selfcheck.py` `032F2149…BE48`、`selfcheck.json` `2B0537A1…35DBE`、`reconstruction_audit.json` `DC93D4FE…37315`；`budget_test/run_b6_full_raw.py` `F81DCC09…325A`、`b6_full_raw.json` `0ABE96F0…803A`、`b6_full_raw.log` `38A3B9F3…DC7D`、`budget_test.json` `D4703C99…B079`；均与 record/usage 声明一致。

## 0. 总判决

**revise（≤5 必改；当前仍不可 approve_freeze_exec，不是 stop）。**
ON3-READY.2 的 3 条闭合**大部分完成**：pure-cold 真单测（test_12/12b/13）与 15/15 OK；5,000-perm raw 预算证据与 693.34 撤回；新 SHA 全链实际一致；protocol 虚假声明已删；reconstruction target/fold 0；边界/冻结禁改项完整。
但仍有 **2 个冻结前必须修的记录/冻结文本不一致**：
1. **预算“冻结值”仍混用 308.086 与 306.722**：`budget_test.json` 的 `frozen_b6_semantics.wall_seconds_measured` 仍是旧 **308.086**（同时另有 evidence 306.722）；protocol line34 仍写 "1,000×5 实测 308.09"；record line23 写 308.086（早期）。虽然 protocol/record/usage 的冻结文本用 306.722，但**冻结 JSON 的冻结字段和 protocol/record 首段仍把 308.086 当 measured**，与 task ②"冻结预算用 measured 306.722"不一致；必须把 306.722 写为唯一冻结值，308.086 仅标早期/历史证据。
2. **冻结文本的新 SHA 链不完整**：protocol §8/record §8 冻结文本没有写全 **protocol 05ADBD9F…、record 1F5BC468…、usage 0B20686C…** 的完整 SHA（protocol 写"见 record/usage"；record 写"见 usage/复核方"）；task ③ 要求新 SHA 全链一致写入 freeze 文本。需补齐（含 data_prep/run_budget 等未变但属链的 SHA 可选）。
修完 2 条（只改文档/JSON 字段，不需重跑数据/效果）并重算新 SHA 后，可 **approve_freeze_exec**；当前不批准冻结。

**最致命 3 条**

1. **冻结预算值不一致（308.086 vs 306.722）**：`budget_test.json` 的 `frozen_b6_semantics.wall_seconds_measured=308.086`，而同一 JSON 的 `budget_raw_evidence.wall_seconds_measured=306.722`、`frozen_b6_semantics.measured_wall_seconds_evidence=306.722`；protocol line34 仍写 308.09，record line23 写早期 308.086。task ②明确"冻结预算用 measured 306.722 s"，冻结字段必须改 306.722，308.086 只能标"早期 run_budget.py 历史证据/计时噪声"，不能叫 measured/frozen。
2. **冻结文本缺全链 SHA**：protocol §8（line97）/record §8（line106）冻结文本没有完整列出 protocol/record/usage 的最终 SHA（分别写"见 record/usage"、仅短 05AD、"见 usage/复核方"）；Lead 批准文本要求引用最终 SHA。必须把 **05ADBD9F…、1F5BC468…、0B20686C…** 等全链写入 freeze 文本，并 remove placeholders；旧 7C573DE4/28EA7542/C2F23AAC/AFF399DA 不得出现于批准文本。
3. **修完需重算全链 SHA 并重跑自检**：改 `budget_test.json`/protocol/record/usage 会再次改变 SHA；需更新所有引用（record/usage/freeze text）并两跑 selfcheck 确认 `selfcheck.json` 仍同 SHA；Lead 批准文本只能引用重算后的最终 SHA。

## 1. 逐条确认（①–⑤）

### ① pure-cold 真单测 / 15 项 / test_04/05 角色 / selfcheck —— **PASS**

- `test_results.txt`：**Ran 15 tests OK（3.190 s）**；新增：
  - `test_12_pure_cold_path_uses_b2_only`：monkeypatch 禁用 `predict_b4` 后 `pure_cold_eval` 仍返回与手工 B2 相同的 ρ/MAE，且签名无 c/U；
  - `test_12b_schema_requires_pure_cold_cell`：schema 缺 `pure_cold_cell` 失败；
  - `test_13_b5_te_uses_only_training_cells_no_masked_responses`：5 折交叉拟合 rare pair 用 global backoff，无 masked/masked_y 参数。
- `test_04` 是 mask perturbation、`test_05` 是 context-ablation；protocol §1 line27 已明确其角色（不冒充 cold 单测）；**PASS**。
- `selfcheck.json` SHA `2B0537A1…` 与旧版一致，两跑逐字节；schema `pure_cold_cell`；**PASS**。
- `reconstruction_audit.json` target30 **0/157,768**；fold 0–4 **0/31,767–32,400**；**PASS**。

### ② 预算 raw evidence / 693.34 撤回 / 冻结值 —— **PASS 主体；冻结字段不一致（见致命 1）**

- `budget_test/b6_full_raw.json`：`semantics=refit_cu_only`、`n_folds=5`、`n_perm_per_fold=1000`、`total_real_permutations=5000`、`total_perms_match=true`、逐折 perms=1000、逐折 wall 60.846/59.927/59.841/63.067/63.04、合计 306.722 s、`budget_ok=true`、`response_values_read=false`。
- `b6_full_raw.log`：逐 100 perms 进度、每 fold DONE、FINAL `total_real_permutations=5000 wall=306.722s`；与 JSON 一致。
- `budget_test.json` `budget_raw_evidence` 含 raw JSON/log/script 路径+SHA、5,000 perms、逐折 wall；**`est_1000x5_refit_cu_only=693.34` 标 `retracted_superseded_by_full_measured_run`，PASS**。
- **但**：`frozen_b6_semantics.wall_seconds_measured=308.086`（旧），与 `measured_wall_seconds_evidence=306.722`/raw evidence 不一致；protocol line34/record line23 仍用 308.09/308.086 作为"实测"；task ②要求冻结用 306.722。**必须修字段/首段**；`full_1000x5_refit_cu_only.wall_seconds=308.086` 可保留为早期 run 历史，但要标"earlier"而非 frozen measured。
- full_refit 73.5min 不采用、执行总预算 <15min（用 306.722）——PASS。

### ③ 新 SHA 全链 / freeze 文本 —— **WEAK（SHA 实际一致；freeze 文本缺全链）**

- 实际核过：protocol `05ADBD9F…B123`、record `1F5BC468…9BAC2`、usage `0B20686C…0671F`、refimpl `B5485B23…0FA4`、test_refimpl `B36D1FCF…9A0F`、test_results `8E17572B…030E`、selfcheck `032F2149…BE48`/`2B0537A1…35DBE`、reconstruction `DC93D4FE…37315`、raw log `38A3B9F3…DC7D`、raw JSON `0ABE96F0…803A`、budget JSON `D4703C99…B079`——均与 protocol/record/usage 的表一致；**旧 SHA 7C573DE4/28EA7542/C2F23AAC/AFF399DA 未在 freeze 文本中使用**（仅历史提及）。
- **WEAK/FAIL**：protocol §8/record §8 freeze 文本未完整写 **protocol 05AD、record 1F5、usage 0B20686C** 的 SHA（分别"见 record/usage"/仅短 05AD/"见 usage/复核方"）；task ③ 要求全链写入 freeze 文本。需补齐，才能作为 Lead 批准文本。

### ④ 边界/冻结禁改项 —— **PASS**

- protocol/record 明确 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数冻结后不得改；仅 O'Neil 内部开发性描述；不称迁移/外推/决策收益/机制/独立确认/更新器/资源足够/新颖性；执行报实测 wall/bootstrap；发现实现偏差停并重新预注册。**PASS**。

### ⑤ 总判决 —— **revise（≤5）**

- 3 条 READY.2 修复主体已闭合，新 SHA 实际匹配；剩余 2 个记录/冻结文本问题（预算冻结字段 308.086 vs 306.722；freeze 文本缺全链 SHA）必须先修；修完可 **approve_freeze_exec**。当前不可批准冻结。

## 2. 必改（≤5；均文档/JSON 字段，不需跑数据/效果）

1. **统一冻结预算值为 306.722 s**：把 `budget_test.json → frozen_b6_semantics.wall_seconds_measured` 改为 **306.722**（或明确重命名为 earlier 308.086，并把 measured 306.722 作为唯一冻结值）；protocol line34/record line23 标清 308.086 是早期 run_budget.py 的历史/计时噪声证据，冻结值只写 306.722；保持 693.34 撤回状态。更新 `budget_test.json` SHA 及所有引用。
2. **补全 freeze 文本全链 SHA**：protocol §8/record §8/usage 的冻结文本写入完整 `PROTOCOL_ON3_exec_DRAFT.md` `05ADBD9F…B123`、`record_on3_ready.md` `1F5BC468…9BAC2`、`usage_on3_ready.json` `0B20686C…0671F`，以及 refimpl/test/test_results/selfcheck/reconstruction/raw log/raw JSON/budget JSON 的完整或唯一短 SHA；删除"见 record/usage/复核方"占位；确保旧 SHA 不出现在批准文本。
3. **重算全链 SHA 并重跑 selfcheck**：上述编辑会改 budget JSON/protocol/record/usage SHA；更新 usage/record/freeze 文本中的 SHA；两跑 selfcheck 仍应 `2B0537A1…`（若不变）并记录；最终 Lead 批准文本只引用新 SHA。
4. **（可选）把 data_prep.py 7C11… 与 run_budget.py 5BCA… 等未变但属审计链的 SHA 列入 freeze 清单**，便于全链核对；不阻断。
5. **（可选）record 标题/任务名统一为 ON3-READY.2**；不阻断。

## 3. 若修完，Lead 批准文本应引用的最终 SHA（当前版本）

- `PROTOCOL_ON3_exec_DRAFT.md`：`05ADBD9FD918AA8FF4C2FB02B3770F24D780331C0E44739D1DAD03EBAF61B123`（修完后会变，需以新为准）
- `record_on3_ready.md`：`1F5BC468A96E5AC426E25E700D7C3EA5B1085E1537ADCB03863CCC4D6519BAC2`（修完后会变）
- `usage_on3_ready.json`：`0B20686C6454E88CEDF90C756C144029AAC397B68613A65E56C3410910D0671F`（修完后会变）
- `on3_refimpl/refimpl.py`：`B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4`
- `on3_refimpl/test_refimpl.py`：`B36D1FCFDD31F1ED622455FF0610E1B4C50864B39A65641C315A9ED48B989A0F`
- `on3_refimpl/test_results.txt`：`8E17572B7C1C9EA3634870F4F7398A9EB847A35ABCF5E0B0CDF6EDA101D8030E`（15/15 OK）
- `on3_refimpl/selfcheck.py`：`032F21492F79B4C0CFD7870C4464F7691A3104C97E00DFC828C22FED71A8BE48`
- `on3_refimpl/selfcheck.json`：`2B0537A101A00276F96C89A319EC41488C3853DDBB933DCF5ADFEE33B6335DBE`
- `on3_refimpl/reconstruction_audit.json`：`DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315`（target0/157,768；fold各0）
- `on3_refimpl/data_prep.py`：`7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510`
- `budget_test/run_b6_full_raw.py`：`F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A`
- `budget_test/b6_full_raw.json`：`0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A`
- `budget_test/b6_full_raw.log`：`38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D`
- `budget_test/budget_test.json`：`D4703C99D5EE4838C61501E0C787FF6A334E63E8B88EDBE09454B2D2851EB079`（修完字段后会变）

## 4. 复核证据与本轮边界

- 实际 SHA 已逐个核过（见页首）；`b6_full_raw.log` 含逐 100 perms 进度/FINAL；`b6_full_raw.json` 5,000/306.722；`test_results.txt` 15/15；`selfcheck.json` 两跑同 SHA；`reconstruction_audit.json` target/fold 0。
- **本轮未运行 ON3 效果/训练/更新器/执行代码、未读响应值**；只读文档/JSON/SHA/日志；只写本文件与 `tmp/`；未改 ON3/ON1/ON2/ON2-EX 产物。
- **当前不可 approve_freeze_exec**；修完 1–3（不需跑数据/效果）后可再复核并给出 Lead 批准文本（引用重算后的最终 SHA）。冻结≠资源足够/关系成立/Stage 1/效果；DRAFT 仍不是执行依据。

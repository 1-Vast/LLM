# R199-ON3-EXEC-C1 最终复核（challenge_ON3_exec_confirm.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 ON3-READY 实现）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON3_exec_DRAFT.md, on3_refimpl/, budget_test/, record_on3_ready.md, usage_on3_ready.json}` + 只读参照 `challenge_ON3_v0_2.md`、`PROTOCOL_ON2.md` v2.2、`exec_calibration/report_calib.md`。
方式：**只读复核**（文档/SHA/预算 JSON/测试结果/自检 JSON；**不运行 ON3 效果/训练/更新器、不读响应值、不运行 ON3 执行代码**）；只写本文件与 `tmp/`。
完整性：`PROTOCOL_ON3_exec_DRAFT.md` SHA `7C573DE4…1711D6`；`record_on3_ready.md` `D9FDED86…18CE2`；`on3_refimpl/*` 与 `budget_test/*` SHA 与 record/usage 声明一致（refimpl `28EA7542…A0A1`、data_prep `7C11B0C5…4D510`、reconstruction `DC93D4FE…37315`、selfcheck.py `032F2149…BE48`、selfcheck.json `2B0537A1…35DBE`、test_refimpl `33534D15…55D6F6`、test_results `C2F23AAC…56D6B0`、budget_test.json `AFF399DA…E964A`）。

## 0. 总判决

**revise（≤5 必改；当前不可 approve_freeze_exec，不是 stop）。** ON3-READY 的 4 项冻结前必办**大部分已落实**：B6 `refit_cu_only` 语义/预算实测 308.086 s≤45 min、full_refit 73.5 min 排除；参考实现/12 单测/两跑/ schema；context-ablation 移出二元门；MAE/MDE、B5 TE、纯冷细胞 protocol/schema 基本修复；reconstruction target30/per fold 0 已修。
**但发现 2 个必须先闭合的问题**：
1. **纯冷细胞“单测”是虚假声明**：protocol §1 line27 说"单测 `test_04/test_05` 体系验证 cold 路径（`pure_cold_eval` 只调用 B2 静态预测，无 c/U）"；实际 `test_04` 是 mask perturbation、`test_05` 是 context-ablation，`test_results.txt` 的 12 项中**没有 pure_cold 单测**；只有 `selfcheck.py` 端到端 synthetic 跑过 pure cold。任务 ③ 要求纯冷细胞写入"protocol/schema/单测"，此项未完成，且 protocol/record 有错误声明。
2. **预算 JSON 的 measured/estimate 不一致且无原始日志**：`budget_test.json` 同时写 `est_1000x5_refit_cu_only=693.34 s` 与 `full_1000x5_refit_cu_only.wall_seconds=308.086 s`；protocol/record 采用 308.086。需要解释/附上实际 full 1,000×5 运行命令与 stdout，证明 308.086 是 **5,000 次真实 refit_cu_only 置换**（不是 100 次 pilot 外推），并确认执行总预算 <15 min 用的是 measured。否则预算认证不可审计。
修完 2 条（加 pure-cold 单测并重跑 12/13；补预算 raw evidence/解释）并更新 SHA 后，可 **approve_freeze_exec**。**当前不批准冻结。**

**最致命 3 条**

1. **pure-cold 单测缺失 + protocol 虚假声明**：`test_results.txt` 12 项无 pure_cold；`test_04` 是掩码扰动、`test_05` 是 context-ablation；`selfcheck.py` 虽调用 `pure_cold_eval`，但任务 ③ 明确要求"单测"。必须新增真正的 `test_12_pure_cold_path`（断言 `pure_cold_eval` 只调 `predict_b2`、不读 c/U、schema 允许），或在 test_04/05 中加断言；重跑并更新 `test_results`/usage/protocol/record 的"12 tests"与 SHA。否则冻结协议中的单测声明不实。
2. **预算证据不闭合**：`budget_test.json` 的 `est_1000x5_refit_cu_only=693.34` 与 `full_1000x5_refit_cu_only.wall_seconds=308.086` 不一致；protocol 采用 308.086。需提供实际 full 5,000 perms 的运行日志/命令/SHA，说明 pilot 外推 vs 实测差异，并确认 `refit_cu_only` 语义（训练结构固定、只重估 c/U）确实在该 full 运行中执行；否则 308.086 不能作为冻结预算证据。
3. **冻结审计链需重写**：上述两项修复会改变 `test_refimpl.py`/`test_results.txt`/`protocol`/`record`/`usage` SHA；当前 Lead 批准文本不能引用旧 SHA。需在冻结前重算全部 SHA、重跑 12/13 单测与两跑 selfcheck（若代码变更），并把最终 SHA 写入 record/usage/freeze 文本。

## 1. 逐条复核（①–⑤）

### ① 预算语义/实测 —— **PASS 主体，证据 WEAK**

- `refit_cu_only` 语义已写死：训练结构（μ/role/partner/member-pair 效应 + pair 因子 V）**每 fold 拟合一次**，每次置换仅重估 held-out `c_cell/U_cell`；`full_refit` 不采用（budget JSON/record/protocol §2 一致）。
- `budget_test.json`：**1,000×5 measured wall 308.086 s**（`full_1000x5_refit_cu_only`，total_perms 5,000，null Δρ mean 0.0001393、Q95 0.000917）；full_refit pilot 26.021 s → 外推 4,408.795 s（73.5 min）>45 min，排除；budget test 总 wall 351.353 s；synthetic shapes、未读响应值。
- **WEAK**：同 JSON 的 `est_1000x5_refit_cu_only=693.34 s` 与 measured 308.086 并存；无独立 raw log/命令证明 308 是 full 5,000 perms 实测；pilot 17.069 s（100 perms）按 per-perm 外推 693，而 full 实测 308，需解释（如实现/环境差异）。**冻结前必须补 raw evidence/说明**；否则预算不能作为可审计冻结值。
- `full_refit` 73.5 min 排除且不能执行时切换：protocol/record 已写；PASS。

### ② 单测/两跑/schema —— **WEAK/FAIL（pure-cold 单测缺失）**

- `test_results.txt`：**Ran 12 tests — OK（2.598 s）**，测试项与 task 列表一致（mask determinism/rule、reconstruction target/perfold、positive control、mask perturbation、context-ablation diagnostic、schema、two-run、fold inheritance、no Jaaks、no test tuning、B6 null gate）。
- `selfcheck.json`：两跑 byte-identical SHA `2B0537A1…`（usage/record 声明）；schema `missing=[]`；schema keys 含 `pure_cold_cell`（refimpl `EXEC_REQUIRED_KEYS`）。
- **FAIL（任务 ③）**：`test_04` 实际是 mask perturbation、`test_05` 是 context-ablation；**没有 single test for pure_cold path**；protocol §1 line27 却写"单测 test_04/test_05 体系验证 cold 路径"，与 `test_refimpl.py`/`test_results.txt` 不符；`record_on3_ready` line42 也写"纯冷细胞 … 单测"，实际只有 selfcheck。必须新增真正单测（或修改 test_04/05 并保留 12 项）并更新计数/SHA。
- 两跑 selfcheck 未独立复跑（避免改产物），但 selfcheck.json SHA 与 usage/record 一致；可接受为记录值；建议执行前由实现者再跑一次并记 SHA。

### ③ 4 项修复 —— **PASS（3 项）/ WEAK（pure-cold 单测）**

- **context-ablation 移出二元门**：protocol §1 line17-20 改为 9 项二元审计 + reconstruction=0 + 独立诊断；test_05 断言 diagnostic 无 "pass" 键；PASS。
- **MAE/MDE**：protocol line24 删除 `|ΔMAE|<MDE80`；MDE80 只 mean Δ；MAE 描述 + 配对 CI；PASS。
- **B5 TE**：line26 改为"训练 cell 的 member-pair target-encoding（训练 cell 内 5 折交叉拟合；绝不使用掩码单元响应）"；PASS（实现/测试覆盖有限，但 schema/措辞已修）。
- **纯冷细胞**：protocol/schema/selfcheck 已有 `pure_cold_cell`/`pure_cold_eval`；但**单测缺失**；任务 ③ 未完全闭合。
- **reconstruction 分母**：`reconstruction_audit.json` target30 **0/157,768**；fold 0–4 `31,767/30,824/30,876/32,400/31,901`，各 **0**；`data_prep.py` metadata/nullness only；PASS。

### ④ batch2/top-k/冻结禁改 —— **PASS**

- batch2 仅披露（5,214 行/1,129 单元/136 上下文；不进训练/指标/增量/敏感性）；top-k 附录（tie 归一名）；失败类别/阴性阳性模板；冻结后禁改 mask/seed/fraction/超参/rank/λ/指标/差值/B6 置换数；PASS。

### ⑤ 执行边界 —— **PASS**

- 仅 O'Neil 内部开发性描述；不称迁移/外推/决策收益/机制/独立确认/更新器/资源足够/新颖性；执行时报告实测 wall、不改冻结值；发现实现偏差须停并重新预注册；protocol §5/§6 明确。

## 2. 预算与执行总时长核对

- `budget_test.json`：B6 `refit_cu_only` **308.086 s**（1,000×5，5,000 perms）≤2,700 s；full_refit 外推 4,408.795 s >2,700；`frozen_b6_semantics` 写 freeze 1,000；PASS 主体。
- 执行总预算：B6 308 s + B4/B2 <10 s + bootstrap 1–3 min + 两跑 → **<15 min**（record/protocol）；余量足够；但 **需把 308 的 raw evidence 补上**（见必改 2）。
- full_refit 73.5 min 不得执行时切换；PASS。

## 3. 必改（≤5；当前不能 approve_freeze_exec）

1. **补 pure-cold 单测 + 修虚假声明（必须）**：新增真正 unit test（如 `test_12_pure_cold_path_uses_b2_only`）或修改 test_04/05 并保持 12 项；断言 `pure_cold_eval` 只调用 B2 静态预测、不读 c/U、schema 含 `pure_cold_cell`；更新 `test_results.txt`/`test_refimpl.py`/protocol §1 line27/record/usage 的计数与 SHA；重跑 12/13 单测。
2. **补预算 raw evidence（必须）**：附 full `refit_cu_only` 1,000×5 实际运行命令/stdout/计时日志；解释 `est_1000x5_refit_cu_only=693.34` vs measured 308.086；确认 full run 是 5,000 次真实 perms（不是外推），且执行总预算 <15 min 用 measured；若 308 不是 full 实测，则重跑/重算预算并在冻结前调整。
3. **重算冻结 SHA 与审计链（必须）**：修复 1/2 会改 `test_refimpl.py`/`test_results.txt`/protocol/record/usage SHA；重跑两跑 selfcheck（若代码变动）并记录新 `selfcheck.json` SHA；最终 Lead 批准文本引用新 SHA；当前旧 SHA 不能用于冻结。
4. **（可选但建议）在 protocol §1 单测覆盖列表写明 pure-cold test 的实际 test id**；确保 12/13 计数与 record/usage 一致；不要把 selfcheck 当 unit test。
5. **（可选）补 B5 TE 的单测/执行断言**（“不用掩码单元响应”），因为当前仅措辞/实现，12 项单测未覆盖 B5 TE；不阻断但建议加一条断言。

## 4. 复核证据与本轮边界

- SHA 见页首；`budget_test.json`/`reconstruction_audit.json`/`selfcheck.json`/`test_results.txt` 与 record/usage 一致。
- **未运行 ON3 效果/训练/更新器、未读响应值、未运行 ON3 执行代码**；只读文档/JSON/SHA；只写本文件与 `tmp/`；未改 ON3/ON1/ON2/ON2-EX 产物。
- **当前不可 approve_freeze_exec**；修完 1–3 后可再复核并给出含最终 SHA 的 Lead 批准文本。冻结≠资源足够/关系成立/Stage 1/效果；DRAFT 仍不是执行依据。

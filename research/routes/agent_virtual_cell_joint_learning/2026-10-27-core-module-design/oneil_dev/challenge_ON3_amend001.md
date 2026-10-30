# R199-ON3-AMEND-001-C1 独立复核（challenge_ON3_amend001.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 AMEND-001 起草）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{AMENDMENT_ON3_EXEC-001.md, record_on3_amend001.md, usage_on3_amend001.json, report_on3.md, record_on3.md, usage_on3.json, APPROVAL_ON3_EXEC.md}` + `tmp/on3_amend001_diff.json` + `tmp/on3_exec_quick_debug.json`。
方式：**只读复核**（草案/diff/停止记录/既有 QUICK 产物；**不运行 ON3、不解析原始响应值、不改冻结/草案产物**）；只写本文件与 `tmp/`。
完整性：`AMENDMENT_ON3_EXEC-001.md` SHA **5362C5A7D4A42AF2B87A1453A84A17405BFD7CAA874E47E4A4D02B4EE5532B8E**；diff `2AFF481E…`；`report_on3.md` `E9248536…`；`record_on3.md` `41F06FC3…`；`usage_on3.json` `02CD4B5D…`；`APPROVAL_ON3_EXEC.md` `F514347B…`；旧 protocol `8B4B8FCC…`、旧 freeze `41BC637C…`；`run_on3_exec.py` `34F3BA7B…`；QUICK 调试 `tmp/on3_exec_quick_debug.json` `39868CE4…`。

## 0. 总判决

**revise（≤5 必改；当前不可 approve_to_lead；不是 stop）。**
**缺陷本身真实**：旧冻结 §2 的 null 门用绝对 `ρ_null`，而 B6 `refit_cu_only` 的 null 预测含不变 `B2_static`，故 `ρ_null` 必然与 B2 同量级>0，2.5–97.5 不可能覆盖 0、mean|ρ_null| 不可能 ≤0.05；同节上一行已冻结 `Δρ_null=ρ(B4_null)−ρ(B2)` 为 null 定义，门与定义自相矛盾——**数学上必须修**。diff 也只改了 null 门对象，成功标准未降。
**但当前草案不能作为 "post-freeze pre-result / 无结果 / 非结果驱动" 直接送 Lead 批准**：QUICK 调试产物 `tmp/on3_exec_quick_debug.json` **不是只有 null 诊断**，而是包含完整 schema 的 **primary/results**（B0–B5 的 ρ/MAE、primary Δρ mean **0.0277068**、CI、top-k、context-ablation、pure-cold 等；QUICK N_PERM=20/BOOT=100，无效执行）。草案/报告/记录/usage 却写 "QUICK 仅说明、不引用为结果；无结果、未读响应值、pre-result"——这与实际产物不符；且 "实现仅一行" 未处理 null gate 输出字段语义（`p2_5_rho/p97_5_rho/mean_abs_rho` 仍以 rho 命名）。必须先修正披露/状态与实现 schema，才能 approve_to_lead。

**最致命 3 条**

1. **QUICK 调试不是"仅 null 诊断"：它含完整 primary/results，且未披露**。`tmp/on3_exec_quick_debug.json` 有 `primary`（`delta_rho_mean=0.0277068`、`delta_rho_ci95=[0.01828,0.03572]`、`positive_folds=4`、`delta_rho_min_rank=0.10`）、每折 `results` 的 B0–B5 ρ/MAE/top-k、context-ablation/pure-cold，以及 `verdict=design_invalid`。虽然它是 QUICK=1/N_PERM=20/BOOT=100 的**无效执行**（不是预注册 full run），但它是**真实数据上的 result-shaped 产物**；草案/`record_on3_amend001`/`usage_on3_amend001`/`record_on3` 却写 "QUICK 仅说明/不引用为结果、无结果、未读响应值"。"post-freeze pre-result" 因此至多只能写 **post-freeze、pre-valid-result（QUICK invalid）**；不能写 pre-result/无 result artifact。必须披露 QUICK 含 primary 结果、将其隔离为 invalid、并明确本次修订的正当性来自**数学缺陷**而非 QUICK 结果；不得用 QUICK Δρ/任何 primary 数字选择指标/门槛/方向。
2. **"实现仅一行"未覆盖 null gate 输出语义/schema**：`run_on3_exec.py` 当前 `null_gate` 输出键为 `p2_5_rho`、`p97_5_rho`、`mean_abs_rho`，条件是 `null_rho`；v1.1 若只改条件为 `null_drho` 而不改这些字段名/语义，输出会把 **Δρ 值放在 rho 名下**，schema/报告会误读。任务 ② 要求唯一改动与实现仅一行，但**代码级 diff 必须同时处理输出字段命名（如 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`）或明确冻结字段语义**，并更新 `test_11`/schema/记录；不能以"一行"掩盖字段错位。当前只有文本 diff，无代码 diff/单测。
3. **状态/版本/旧 SHA/v1.1 freeze 链需闭合**：旧 approval/protocol/freeze SHA 已标 invalid spec；但当前还没有 v1.1 协议/冻结文本/新 SHA；此刻不可批准执行。批准前需产出 v1.1 freeze（新 SHA），明确旧 `8B4B8FCC`/`41BC637C`/`F514347B` 为 invalid spec；v1.1 只改 null gate，成功标准/增量规则/其他全部不变；执行一次条件（full run、两跑、实测 wall、无 result-driven）写清；QUICK artifact 不得作为结果引用。

## 1. 逐条判决（对照 task-80 ①–⑤）

### ① 缺陷是否真实 / QUICK 性质 —— **FAIL（缺陷真实，但 QUICK 披露不实）**

- **缺陷真实 PASS**：
  - `B4_null = B2_static + c_perm + U_perm·V`；`B2_static` 不随 null 置换变化；`ρ(B4_null,y)` 与 `ρ(B2,y)` 同量级；`ρ_null` 2.5–97.5 不能覆盖 0，mean|ρ_null| 不能 ≤0.05。旧门对真实数据**必然 design_invalid**，与模型/数据有效性无关。
  - 同 §2 上一行已冻结 `Δρ_null=ρ(B4_null)−ρ(B2)` 为 null 对象；旧门却用 `ρ_null`，**门与定义自相矛盾**；正确修复对象是 Δρ_null；数学上成立。
  - 无正式 `on3_exec.json`；旧 protocol 标 invalid spec；`report_on3.md` STOP E9248536；这些 PASS。
- **FAIL（QUICK 性质/无结果声明）**：
  - `tmp/on3_exec_quick_debug.json` 含 **primary/results**（见 §0/最致命 1）。QUICK 是 `QUICK=1, N_PERM=20, BOOT_B=100` 的**无效执行**，但它是 result-shaped 输出；`report_on3.md` 还引用了 B2/B4 ρ 0.68–0.78；QUICK JSON 的 `null.n_perm=20` 与 `gate.n_perm=100` 也不一致。草案/record/usage 的 "QUICK 仅 null 诊断、无结果、未读响应值、pre-result" **不准确**。必须更正并把 QUICK artifact 隔离/明确不可引用；若保留，应完整披露字段。
  - 这不是说 QUICK 是"有效 ON3 结果"（它不是 full run、无两跑），但**不能声称无 result-like artifact**；也不能用其 primary 数字支撑修订方向。

### ② 修订唯一性 / diff / 实现 —— **PASS（diff 文本）/ WEAK（实现 schema）**

- `tmp/on3_amend001_diff.json`：`changed_fields=["null calibration gate object: rho_null -> delta_rho_null"]`；`unchanged_checklist` 覆盖数据/切分/mask/端点/B2/B4/B5/纯冷/B6/boot/metrics/Δ 阈值/MDE/schema/两跑/wall/失败类别/禁改项；**文本 diff 只看 null 门对象**，PASS。
- 成功标准未降：增量仍 `Δρ≥max(0.10,Q95_null(Δρ_null))`、≥4/5 folds、paired bootstrap 下界>0、B6 p≤0.05；MDE80/δ_min 不变；PASS。
- **WEAK/FAIL**：`run_on3_exec.py` 当前 null gate 输出键为 rho 命名；v1.1 若仅改 pass 条件，输出字段/报告会错位；"实现仅一行"目前只是草案声明，**无代码 diff、无改后单测/schema 验证**。需给出精确 diff（条件 + 输出字段/语义），并更新 test_11/schema；再跑 15/15 与两跑预检。

### ③ 性质/版本/旧 SHA/成功标准 —— **WEAK（post-freeze, 但非 pre-result；旧 SHA 已标 invalid）**

- 旧 `PROTOCOL_ON3_exec_DRAFT.md` 8B4B8FCC、`FREEZE_ON3_exec.md` 41BC637C、`APPROVAL_ON3_EXEC.md` F514347B 在 amendment/record/usage 标 "invalid spec, no valid execution"；**PASS**。
- **WEAK**：由于 QUICK 调试已产生 result-shaped primary/results，性质只能写 **post-freeze、pre-valid-result（QUICK invalid）**，不能写 pre-result/无结果；QUICK 是响应数据相关的，不能与"未读响应值"并列。修订的必要性仍可由**数学矛盾**独立证明；不依赖 QUICK 结果。
- 成功标准未降：PASS（见 ②）。
- v1.1 新 SHA 尚未生成；当前不可执行/批准执行；需先冻结 v1.1。

### ④ 能否证明不是换指标/门槛制造收益 —— **WEAK/PASS（数学上可证，但需隔离 QUICK）**

- 修复对象是 null gate 的**实现规格错误**，不改变 primary metric/增量阈值/成功标准；旧门对真实数据必 FAIL；正确对象与同节已冻结 Δρ_null 一致；**在数学上不是门槛制造收益**；PASS。
- **但** QUICK primary 结果已存在（Δρ mean 0.0277 <0.10，positive folds 4，null p=0；即使修复 gate，按冻结增量规则仍 likely `no_increment`），且未披露；"非结果驱动"不能仅靠声明证明。必须：  
  1. 完整披露 QUICK 含 primary/results、无效、不引用；  
  2. 说明修订由**代数矛盾**决定（即使 QUICK 也显示 gate 不可实现），不是由 QUICK primary 数字选择方向；  
  3. 禁止用 QUICK Δρ/ρ/CI 影响 v1.1 的指标/阈值/门/成功标准；修复后仍可能 `no_increment`/`evaluation_cannot_distinguish`，不得保证正结果。

### ⑤ 总判决 —— **revise（≤5）**

- 缺陷真实、文本 diff 唯一、成功标准未降；但 QUICK 披露不实 + 实现 schema 未闭合 + v1.1 freeze/SHA 链未生成；当前不可 approve_to_lead/冻结执行。修完 1–3 后可 approve_to_lead；不需要 stop（数学修复必要且非门槛放宽）。

## 2. 必改（≤5）

1. **披露 QUICK 完整性质**：在 amendment §1.3/§3/§4、report_on3/record_on3/usage_on3、record_on3_amend001/usage_on3_amend001 明确：`tmp/on3_exec_quick_debug.json`（SHA `39868CE4…`）是 **QUICK invalid execution**，但含 **primary/results**（Δρ mean 0.0277、CI、positive folds、B0–B5 metrics、top-k 等）；**不得作为结果引用**；"无 on3_exec.json"仅指正式文件，不等于无 result-like artifact；把性质改为 **post-freeze、pre-valid-result**；删除"未读响应值/QUICK仅null"等不准确表述（或限定为"草案写作未新读原始响应"）。
2. **隔离 QUICK + 明确修订依据**：将 QUICK artifact 标记/quarantine（tmp 内明确 invalid；不进入正式结果），在 amendment 增加 "修订由同节 Δρ_null 定义/数学必然性决定，QUICK primary 未用于选择指标/门槛/方向；QUICK Δρ=0.0277 <0.10 也不构成正结果" 的声明；不得引用 QUICK primary 作为支持/反对证据。
3. **实现/schema diff**：给出 `run_on3_exec.py` 精确 diff（仅 null gate 对象 + 输出字段命名/语义，如 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`），更新 test_11/schema/记录；重跑 15/15 单测与两跑预检；**不得仅改条件而保留 rho 字段名**。
4. **v1.1 freeze 链**：生成 v1.1 协议/冻结文本新 SHA；旧 8B4B8FCC/41BC637C/F514347B 标 invalid spec；v1.1 只改 null gate；成功标准/增量/MDE/其他全部不变；Lead 批准文本引用 AMENDMENT SHA `5362C5A7…` + v1.1 freeze 新 SHA；执行一次条件写清。
5. **（可选）将 QUICK artifact 从 tmp 改名/加 `.invalid` 标记并记录**，避免后续被误读；不阻断。

## 3. 若修完，Lead 批准文本（建议模板；当前不批准）

> **批准 AMENDMENT_ON3_EXEC-001，冻结 ON3 execution protocol v1.1，授权执行一次。**
> 修订依据：`AMENDMENT_ON3_EXEC-001.md` SHA `5362C5A7D4A42AF2B87A1453A84A17405BFD7CAA874E47E4A4D02B4EE5532B8E`；旧 protocol `8B4B8FCC…`/freeze `41BC637C…`/approval `F514347B…` 标 **invalid spec, no valid execution**。
> v1.1 冻结：null 门对象改为 `Δρ_null = ρ(B4_null)−ρ(B2)`，门条件为其 2.5–97.5 覆盖 0 且 mean|Δρ_null|≤0.05；其余 mask/seed/fraction/超参/rank/λ/指标/Δρ 规则/B6 1,000 refit_cu_only/B5/纯冷/schema/两跑/wall/失败类别/禁改项全部不变。
> 执行一次：full B6 1,000×5、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap；结果仅 O'Neil 内部开发性描述；不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结≠资源足够/关系成立/Stage1/效果；QUICK invalid artifact 不得引用。
> 新 v1.1 protocol/freeze SHA 由 Lead 批准文本引用（在 v1.1 冻结生成后填入，不能使用旧 SHA）。

## 4. 复核证据与本轮边界

- 实际 SHA：AMENDMENT `5362C5A7…`、diff `2AFF481E…`、report STOP `E9248536…`、old protocol/freeze/approval、QUICK debug `39868CE4…`/usage `60DB423C…`；均与 record/usage 记录一致。
- **本轮未运行 ON3、未运行效果/训练/更新器、未解析原始响应值**；只读草案/停止记录/既有 QUICK 产物以核对 post-result 状态；只写本文件与 `tmp/`；未改冻结/草案产物。
- 当前不可 approve_to_lead/冻结；修完 1–3 后可再复核并给 Lead 批准文本。冻结≠资源足够/关系成立/Stage1/效果。

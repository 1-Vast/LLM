# record_a2_exec.md —— R201-A.2-EXEC 执行记录（data-only P1 重跑）

角色：独立执行者（未参与 R197/R200 模型开发）· 任务 task-122（A.2-EXEC）· 日期 2026-10-28
只写 `mechanism_A/a2_exec/` 与 `tmp/`；**未改 A.1/A.2/P0P1 产物**；**0 新 wells**；未进入 P2/S1/S2/H_A2；non-blind/peeked 继承 ON3。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① D1–D7 先于 P1；失败→对应 design_invalid，不进 P1 | ✅ D1 PASS、**D2 FAIL**、D3 PASS、D6 PASS、D7 PASS；D4/D5 未评估（提前失败）→ `design_invalid: scale_mismatch`；**P1 未执行** |
| ② A.2 legal/σ：RMS≤1.96σ_obs_A2（σ_obs_A2=.0464595，阈值 .0910607）；n_legal_A2≥17,004.4 否则 coverage；σ_pair²_A2=0.5×mean||P⊥(f_h1−f_h2)||²/(K−1)；F_crit 仅 D2+D3 通过保留 | ✅ 实测阈值 0.09106062；n_legal_A2=176,934（PASS）；σ_pair²_A2=0.00110139（0.5×S2_raw=0.00220278；σ_pair²_A2/S1=1.0205）；F_crit **未保留**（D2 失败） |
| ③ P1（U=340,088、F_pair/T_c、N0 pooled、N1 per-cell、N_perm=500 seed=20261029、BH q=.05、阳性三条件） | ⛔ **未执行**（D2 提前失败，按预注册规则不进入 P1；`a2_exec.json → P1=None`） |
| ④ 执行前 pilot 预算测试；caps；超→compute_budget_exceeded | ✅ pilot PASS（投影 29.0–33.5 s；内存 0.653 GB）；实测 wall 57.4/58.0 s、CPU 55.95 s |
| ⑤ 两跑逐字节；实测 wall/CPU/内存；report/record/usage+SHA | ✅ json/rows 两跑逐字节一致；telemetry 见 usage/diagnostics |
| ⑥ 边界（0 新 wells；无 positive/negative；不称机制/迁移/决策/新颖性） | ✅ `verdict=design_invalid`、`failure_category=design_invalid: scale_mismatch`；无 P1 结论；A.1 不重判 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~01:24 | 读 task-122 并 claim；读 DECISION_R201_A2_EXEC、A.2 v0.2 链 |
| ~01:26 | **`PROTOCOL_A2_EXEC.md` 冻结**（D1–D7 顺序、σ/S2/legal 规则、N0/N1 实现、pilot、schema；`run_a2_exec.py` 尚不存在） |
| ~01:27 | 写 `run_a2_exec.py`；首跑 wall 59.9 s → **D2 FAIL（F_self_check median 0.4153 <0.5）** → design_invalid: scale_mismatch |
| ~01:29 | 补丁：gate-fail 分支不写 observed T_obs/不报告 observed 统计（仅 pilot 计时）；telemetry/D4/D5 not_evaluated 写入 diagnostics |
| ~01:30 | **run1** wall 57.4 s；**run2** wall 58.0 s；`a2_exec.json`/`a2_exec_rows.csv` 两跑逐字节一致 |
| ~01:33 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露（未改冻结规则）

1. **F_self_check 实现**：同 wells 两套半拆 A={1,2}/{3,4}、B={1,3}/{2,4}；`d_avg=(d_A+d_B)/2`；实测 mean 0.9700、median **0.4153**、FPR@2.60 0.0803；协方差诊断 `Cov(d_A,d_B)` 均值 0.0074/中位 0.0189（iid 期望 0）。代数上 `d_avg=(r1−r4)/2`，其尺度在 context 间强烈异方差（p25 0.17 vs p95 3.61）→ 单一全局 σ_pair²_A2 只能校准均值，中位被低方差 context 拉低；**预注册 D2 中位门捕获该不一致**。
2. **observed 统计披露**：`F_pair/T_c/pooled` 在 gate 前只为 pilot 计时计算过；**未解释、未报告**（`a2_exec.json → pre_gate_observed_statistics`；rows CSV 无 T_obs/p）；P1 未执行。
3. **gate-fail 输出补丁（已披露）**：首跑后把 gate-fail 分支的 rows 从"含 T_obs"改为仅 note，确保不泄漏/不暗示 P1 统计；结果 JSON 不含 observed 数值。
4. **未改冻结项**：阈值/F_crit/族/N_perm/legal 规则/N0/N1 定义均按 `PROTOCOL_A2_EXEC.md` 执行；未用 observed 选规则；未用 A.1 结果改 null/σ。
5. **预算**：pilot 实测 t_N1 0.0441–0.0504 s/rep、t_N0 0.0035–0.0054 s/rep、投影 29.0–33.5 s、内存 0.653 GB；caps 900 s/7200 s/8 GB → PASS；未减 N_perm。
6. **数据边界**：batch1 complete-case target30 完整 4×4；plan-cells 16,722（excluded 524/475）；702/315 排除；不插值；未拼 ΔEMAX；0 新 wells；non-blind/peeked。

## 3. 关键结果（与 report 一致）

- **verdict = design_invalid；failure_category = design_invalid: scale_mismatch**（D2 失败）；**P1=None，无 positive/negative**。
- **D1** PASS：σ_w_hat=0.092919、σ_obs_A2=0.0464595、S1=0.00107924、S2_raw=0.00220278、σ_pair²_A2=0.00110139（ratio 1.0205）。
- **D2** FAIL：F_self_check mean 0.9700（pass）/ median 0.4153（fail）；ratio pass。D3 PASS（FPR 0.0803）；F_crit 未保留。
- **D4/D5** 未评估；**D6** PASS（pilot/实测）；**D7** PASS（G1/G2/G4/G5，U=340,088）。
- **legal**：阈值 0.09106062；legal plans 11,188/16,722；n_legal_A2=176,934 ≥17,004.4 PASS。
- **预算/telemetry**：run1 57.4 s、run2 58.0 s；CPU 55.95 s；内存 0.653 GB。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_A2_EXEC.md` | `2F3D8CA325CDFC1FE9A854268CB872CFA274CF3673C6920F2B7B39763EC5CC78` |
| `run_a2_exec.py` | `748EE2C7D333E19FF5329AAF4BC4541032B352408778D7DEB34525EA35CCE760` |
| `a2_exec.json` | `26BF3B7A4C527C1486D1D649ACE6205FD19744CC5E0172D6A31F4EDCF9F3E038` |
| `a2_exec_rows.csv` | `4E7527A1381896360915F48555FDFE072904012C258A92202C631447F4C03DF6` |
| `a2_exec_diagnostics.json` | `1846BAD2992B17549592CA690A0A06A7BC5D529DD61FA58ABAE25F6C4CB65DC1` |
| report/record/usage | 见 `usage_a2_exec.json` |
| 冻结链（只读） | PROBLEM_A2_v0_2 `3B49A8AB…`、DESIGN_A2_v0_2 `3AB5A663…`、null_design_A2_v0_2 `96AE014D…`、DECISION_R201_A2_EXEC（SHA 见 json） |

## 5. 缺口与下一步

- **P1 未执行**（D2 预注册失败）→ 无 A.2 positive/negative；不得把 observed 预 gate 统计当证据；不得写"矛盾不存在/机制/迁移/决策"。
- **建议 A.2.2 新预注册**：针对 context 间半拆噪声异方差（d_avg=(r1−r4)/2 的尺度异质）设计 context 级/稳健尺度或 fuller-profile resampling 自检；通过前不进 P2/S2/H_A2。
- A.1 `p0p1_negative` 保持原样（仅"冻结 null 下未检出"）。

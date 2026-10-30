# R201-A.2.2-EXEC 执行报告：R4 异方差稳健 σ 的 data-only P1 重跑

2026-10-28。执行：`PROTOCOL_A22_EXEC.md`（运行前冻结）→ `run_a22_exec.py`。依据：`DECISION_R201_A22_EXEC.md`（Lead 批准仅 A.2.2 data-only P1 重跑）、`PROBLEM_A22.md`（`69605BBC…`）、`DESIGN_A22.md`（`EAC8EA10…`）、`sigma_robust_A22.json`（`12DC9855…`）。
**范围：A.2.2 data-only P1 重跑（0 新 wells；不进 P2/S1/S2/H_A2；A.1/A.2 不重判；不做生物学/机制/迁移/决策收益/新颖性主张）；non-blind/peeked 继承 ON3。**

## 0. 判定（按 A.2.2 预注册规则）

**`design_invalid: scale_mismatch`（D2 失败；D3 也失败）→ P1 未执行（P1=None）、无 positive/negative 结论。**

| 门 | 结果 | 实测 |
|---|---|---|
| **D1 σ 非退化** | **PASS** | σ_w_hat=**0.092919**；σ_obs_A2=**0.0464595**；A.2 legal 阈值=**0.09106062**；R4 σ² 全部 included context 有限/正；S1=0.00107924 |
| **D2 F_self（pair 级公式）** | **FAIL** | ① per-context 中位 coverage∈[0.5,2] = **0.6484 <0.85** ❌；② 全局中位 **0.5440 ∈[0.5,1.5]** ✅；③ overall F_self FPR@F_crit=**0.08741 ≤0.10** ✅；④ ratio 诊断：σ²_R4 中位/S1=**6.00**（p25≈0.0、p50 .01、p95 .03 ← 重尾/异质） |
| **D3 noise_calibration** | **FAIL** | ① overall FPR **0.08741 ≤0.10** ✅；② **worst-context FPR = 1.000 >0.25** ❌；③ **context-FPR p95 = 0.3184 >0.20** ❌ |
| **D4 null pooled** | 未评估 | 因 D2/D3 提前失败，P1 未执行 |
| **D5 null/obs T 比** | 未评估 | 同上 |
| **D6 预算** | **PASS** | pilot：t_N1=0.0154–0.0169 s/rep、t_N0=0.0030–0.0040 s/rep；投影 11.6–12.0 s；内存 0.674 GB；caps 900 s/7200 s/8 GB |
| **D7 G1–G5** | **PASS** | 30/30 细胞；plan-cells 16,722；**U=340,088**；G2 over-id 30/30≥16；G4/G5 断言（target30∩Jaaks=∅、端点仅 viability、batch1-only、702/315 排除、无新 wells、peek 打印）PASS |

**R4 前置门**：contexts 2,216（**included 2,149**，excluded 67 = <2 plans）；**excluded pair fraction = 0.0 ≤5%** PASS；A.2 legal：legal plans 11,188/16,722；**n_legal_A2=176,934 ≥17,004.4** PASS；infer pairs=176,934。
**F_crit=2.60 未保留**（D2/D3 失败）。

## 1. 关键实测与诊断

- **R4 σ 分布**：σ²_R4(c) 中位 **0.01**（=6.00×S1）、p25≈0.0、p75 .01、p95 .03、max .14 → 重尾/大量近零 context；full-profile plan-pair 差同时含真实 profile 差异与噪声，**不是纯噪声尺度**（resubstitution 披露；LOO 敏感性 `F_LOO/F` p5 .99 / p50 1.00 / p95 1.01，仅描述性）。
- **F_self（pair 级，D2/D3 用）**：n=176,934；全局 mean 0.9669、**median 0.5440**；分位 p5 .04 / p25 .21 / p50 .54 / p75 1.24 / p95 3.42；per-context 中位分位 p5 .18 / p25 .43 / p50 .63 / p75 .87 / p95 1.32；coverage 0.6484；overall FPR .0874；worst-context FPR 1.0；context-FPR p95 .3184。
- **描述性 A.2-style 半拆分诊断**（not used for gates）：F_self_check 中位 0.0679、FPR@2.60 0.0095 —— 因 σ²_R4 远大于半拆差方差（中位 6×S1）而被压小，进一步说明 R4 尺度混入了真实差异。
- **observed 统计**（仅 gate 前计时/诊断，未解释、未报告为 P1）：pooled_obs 0.087411（`P1=None`；rows CSV 只有 note）。
- **D2/D3 失败机制**：R4 σ 在真实数据上重尾且部分 context 近零（p25≈0），使 F_self 的 per-context 中位大量落在 [0.5,2] 外（coverage .6484），且小 context 出现全 F>F_crit（worst FPR 1.0）；合成校准假设"plans 共享 f、pair 差=纯噪声"在真实 S-add 违例/交互异质下不成立。**不是 A.1 的因子 2 重演**（D1/legal/pre-gate 均正常）。

## 2. 执行事实

- 数据：O'Neil batch1 complete-case target30 完整 4×4；plan-cells 16,722（excluded: incomplete_or_bad_grid 524、not_batch1 475）；702/315 pair-cell 排除；不插值；未拼 ΔEMAX；0 新 wells。
- **P1 未执行**（D2 失败即停；`a22_exec.json → P1=None`）；observed F/T/pooled 只在 gate 前为 pilot 计时计算，未解释/未报告。
- **预算/telemetry**：wall run1 **57.9 s**、run2 **58.4 s**；CPU（process）**56.23–56.56 s**；内存 **0.674 GB**；均远低于 caps。
- **两跑逐字节一致**：`a22_exec.json` SHA **`BD197811257D2D8EF0DB2026A91EF4B7BCCB0976742BABEF2C8B1A8A1F841F26`**；rows SHA **`4E7527A1381896360915F48555FDFE072904012C258A92202C631447F4C03DF6`**；结果 JSON 无 telemetry。
- 未进入 P2/S1/S2/H_A2；未改 A.1 `p0p1_negative` 与 A.2 `design_invalid: scale_mismatch`。

## 3. 解释边界（写死）

- 本轮 **没有** A.2.2 positive/negative：`verdict=design_invalid`、`failure_category=design_invalid: scale_mismatch`（D2 先失败；D3 亦失败）。
- **不写"矛盾不存在"、不写"机制 A 阴性"、不写"存在联合矛盾"**；observed 预 gate 统计不作证据。
- A.1 `p0p1_negative` 保持原样；A.2 `design_invalid: scale_mismatch` 保持原样；不称生物学/机制/迁移/决策收益/新颖性；pair 级仅描述性；non-blind/peeked；0 新 wells。

## 4. 产物与 SHA

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_A22_EXEC.md`（运行前冻结） | `4D19675451D67794BDE9AFE6430A8D4D55C5F81E9B6CEB06047DD331E55D6215` |
| `run_a22_exec.py` | `4E6F9CBAD6B5F5E1C770A460DB1AF849B53B62CF8F867DA373AE070974AAFDC2` |
| `a22_exec.json` | `BD197811257D2D8EF0DB2026A91EF4B7BCCB0976742BABEF2C8B1A8A1F841F26` |
| `a22_exec_rows.csv` | `4E7527A1381896360915F48555FDFE072904012C258A92202C631447F4C03DF6` |
| `a22_exec_diagnostics.json` | 见 usage（含 telemetry） |
| report/record/usage | 见 `usage_a22_exec.json` |

## 5. 建议

1. **登记 A.2.2-EXEC 为 `design_invalid: scale_mismatch`（D2 失败；D3 亦失败）**：P1 未执行，无 A.2.2 结论；不解释 observed。
2. **建议 A.2.3 预注册或停止 A 线**：R4 的 full-profile plan-pair 尺度在真实 S-add 违例下混入真实差异（重尾、近零 context），需改为**模型化噪声尺度**（如拟合 shared-f 后的残差/分层方差、或显式交互项的 null 模拟）+ 重设计 D2/D3；或由 Lead 决定停止 A 线、以 A.1/A.2/A.2.2 的 design_invalid 记录归档。
3. A.2.3 通过前不进 P2/S2/H_A2；不解释 A.1/A.2 negative；不写"矛盾不存在"。

# R201-A.2-EXEC 执行报告：A.2 data-only P1 重跑（校准 null/σ 后）

2026-10-28。执行：`PROTOCOL_A2_EXEC.md`（运行前冻结）→ `run_a2_exec.py`。依据：`DECISION_R201_A2_EXEC.md`（Lead 批准仅 A.2 data-only P1 重跑）、`PROBLEM_A2_v0_2.md`（`3B49A8AB…`）、`DESIGN_A2_v0_2.md`（`3AB5A663…`）、`null_design_A2_v0_2.json`（`96AE014D…`）。
**范围：A.2 data-only P1 重跑（0 新 wells；不进入 P2/S1/S2/H_A2；不重判 A.1；不做生物学/机制/迁移/决策收益/新颖性主张）。non-blind/peeked 继承 ON3 披露。**

## 0. 判定（按 A.2 预注册规则）

**`design_invalid: scale_mismatch`（D2 失败）→ P1 未执行、未判定；无 positive/negative 结论。**

| 门 | 结果 | 说明 |
|---|---|---|
| **D1 σ 非退化** | **PASS** | σ_w_hat=**0.092919**；σ_obs_A2=**0.0464595**；S1=**0.00107924**；S2_raw=**0.00220278**；**σ_pair²_A2=0.00110139**（=0.5×S2_raw；σ_pair²_A2/S1=**1.0205**，符合预期≈S1） |
| **D2 F_self_check** | **FAIL** | `F_self_check`（两套半拆 A={1,2}/{3,4}、B={1,3}/{2,4} 的 d_avg）：**mean 0.9700 ∈[0.5,2] ✅**；**median 0.4153 ∉[0.5,2] ❌**；ratio σ_pair²_A2/S1=1.0205 ∈[0.5,2] ✅ → **D2 失败** |
| **D3 半拆 FPR** | PASS | `F_self_check` FPR@F_crit=**0.08031** ≤0.10（但 F_crit=2.60 **未保留**，因 D2 失败） |
| **D4 null pooled** | 未评估 | 因 D2 提前失败，P1 未执行 |
| **D5 null/obs T 比** | 未评估 | 同上 |
| **D6 预算** | PASS | pilot：t_N1=0.0441–0.0504 s/rep、t_N0=0.0035–0.0054 s/rep；投影 29.0–33.5 s；内存 0.653 GB；caps 900 s/7200 s/8 GB |
| **D7 G1–G5** | PASS | 30/30 细胞；plan-cells 16,722；**U=340,088**；G2 over-id 30/30≥16；G4/G5 断言（target30∩Jaaks=∅、端点仅 viability、batch1-only、702/315 排除、无新 wells、peek 打印）PASS |

**A.2 legal 集**（冻结规则）：阈值 **0.09106062**；legal plans **11,188/16,722**；**n_legal_A2=176,934** ≥17,004.4（5%|U|）→ 合法集门 PASS（但未进入 P1）。

## 1. D2 失败的具体数字与诊断

- `F_self_check`（33,444 个 (plan,context)）：mean **0.9700**、median **0.4153**；分位：p5 0.04、p25 0.17、p50 0.42、p75 1.00、p95 3.61、max 67.18；FPR@2.60=0.0803。
- 同 wells 两套半拆的协方差诊断：`Cov(d_A,d_B)` 均值 0.0074、中位 0.0189（iid 期望 0；真实技术重复相关使其非零）。
- **解释**：`d_avg=(d_A+d_B)/2` 退化为 `(r1−r4)/2`（代数上 dA=(r1+r2−r3−r4)/2、dB=(r1+r3−r2−r4)/2，相加即 (r1−r4)/2）；因此 F_self_check 实际上只用了孔 1 与孔 4 的差，其尺度在 context 间**强烈异方差**（p25 0.17 vs p95 3.61），单一全局 σ_pair²_A2 只能使**均值**≈1，**中位**被低方差 context 拉到 0.4153。**预注册的 D2 中位门正确捕获了该尺度不一致** → 按 A.2 预注册规则判 `design_invalid: scale_mismatch`，**不进入 P1 判定**。
- **不是** A.1 因子 2 的重演：σ_pair²_A2/S1=1.0205（≈1），D1/D3/legal/D7 均通过；问题在**噪声尺度在 context 间异质**，一个全局 σ_pair² 不足以校准 F_pair 的 H0。该发现需在 A.2.2 重新预注册（异方差/context 级尺度或更稳健的自检），**不得**在本轮事后改阈值/口径。

## 2. 执行事实（不含 P1 判定）

- 数据：O'Neil batch1 complete-case target30 完整 4×4；plan-cells 16,722（excluded: incomplete_or_bad_grid 524、not_batch1 475）；702/315 pair-cell 排除；不插值；未拼 ΔEMAX；0 新 wells。
- **observed F_pair/T_c/pooled 只在 gate 前为 pilot 计时计算过，未解释**（`a2_exec.json → pre_gate_observed_statistics = not reported`；`a2_exec_rows.csv` 无 T_obs/p 值）；**P1 未执行**（`P1=None`）。
- 预算实测：wall run1 **57.4 s**、run2 **58.0 s**；CPU（process）**55.95 s**；内存峰值 **0.653 GB**；均远低于 caps；两跑 `a2_exec.json`/`a2_exec_rows.csv` **逐字节一致**。
- 未进入 P2/S1/S2/H_A2；未改 A.1 判定；未改冻结阈值/族/N_perm/legal 规则。

## 3. 解释边界（写死）

- 本轮 **没有** P1 positive/negative 结论：`verdict=design_invalid`，`failure_category=design_invalid: scale_mismatch`；**不写"矛盾不存在"、不写"机制 A 阴性"、不写"存在联合矛盾"**。
- A.1 的 `p0p1_negative` 保持原样、不重判（其解释边界不变：仅"冻结 null 下未检出"）。
- 不称生物学/机制/迁移/决策收益/新颖性；pair 级仅描述性；技术重复≠独立培养；non-blind/peeked。

## 4. 产物与 SHA

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_A2_EXEC.md`（运行前冻结） | 见 `a2_exec.json → protocol`；本地值见 usage |
| `run_a2_exec.py` | 见 `a2_exec.json → script` |
| `a2_exec.json` | `26BF3B7A4C527C1486D1D649ACE6205FD19744CC5E0172D6A31F4EDCF9F3E038` |
| `a2_exec_rows.csv` | `4E7527A1381896360915F48555FDFE072904012C258A92202C631447F4C03DF6` |
| `a2_exec_diagnostics.json` | 见 usage（telemetry 在此） |
| report/record/usage | 见 `usage_a2_exec.json` |

**确定性**：`a2_exec.json` 两跑一致 SHA `26BF3B7A…F9F3E038`；`a2_exec_rows.csv` 一致 `4E7527A1…F4C03DF6`；结果 JSON 无 telemetry（wall/CPU/内存只在 diagnostics/usage）。

## 5. 建议

1. **登记 A.2 执行结果为 `design_invalid: scale_mismatch`（预注册后果）**：P1 未执行，无 positive/negative；不解释 observed 统计。
2. **建议 A.2.2 新预注册**（data-only 可行）：针对 context 间半拆噪声异方差，预注册 context/剂量层尺度（如 per-context σ_pair²、稳健尺度、或基于 full-profile resampling 的自检），并重新校准 D2/D3/F_crit 条件；通过前不进入 P2/S2/H_A2、不解释 A.1 negative。
3. 若 Lead 决定不继续：A.2 以 `design_invalid: scale_mismatch` 归档；A.1 `p0p1_negative` 仍只是"冻结 null 下未检出"。

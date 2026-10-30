# R201-A P0/P1 执行报告（Lead 批准：data-only、0 新 wells；仅 P0/P1）

2026-10-28。执行：`PROTOCOL_P0P1_EXEC.md`（运行前冻结）→ `run_a_p0p1.py`。依据：`DECISION_R201_A_P0P1.md`（Lead 批准仅 P0/P1）、`DESIGN_A_v0_2.md`、`PROBLEM_A_v0_2.md`、`qualify_A_v0_2.json`。
**只执行 P0/P1；未执行 P2/S1/S2/H_A2；0 新 wells/plate/轮次；data-only；non-blind/peeked 继承 ON3。**

## 0. 判定（按冻结规则）

**`p0p1_negative`（= `no_joint_contradiction` 措辞）**：P1 阳性三条件中 ① ② 不满足、③ 满足：

| 条件 | 实测 | 结果 |
|---|---|---|
| ① BH q=0.05 拒绝细胞数 ≥5 | **0** 个细胞被拒绝（30 细胞；p 范围 0.2255–1.0） | ❌ |
| ② pooled `F≥F_crit=2.60` 比例 ≥ 置换零分布 Q95 | observed **0.153697** vs null Q95 **0.749105** | ❌ |
| ③ G1–G5 全 PASS | 全部 PASS（见 §1） | ✅ |

**但（必须同时读，§4）**：本轮冻结的**行置换零分布本身严重偏高**（null pooled 中位 **0.7457** vs observed **0.1537**；null median T **146.31** vs observed median **73–77**）→ 该负结果**不能解释为"没有联合矛盾"**；只能写"**本资源/本族/本设计（冻结零模型）下未检出**"。已记录为执行期发现 → 建议 A.2 重新预注册有效零模型后再解释；不得用当前结果支持"矛盾不存在/结构不存在/无迁移/无决策收益"。

## 1. P0 资格门（全部 PASS）

| 门 | 实测 | 判定 |
|---|---|---|
| **G1 覆盖** | target30 = 30/30 细胞；plan-cells **16,722**；**|U|=340,088**（=预注册值）；每细胞 plan-cells 中位 561 | PASS |
| **G2 可识别** | 加性设计 over-id 中位 **8,745**（30/30 ≥16，来自 v0.2 冻结审计） | PASS |
| **G3 噪声** | `σ_obs = sqrt(mean((half1−half2)²)/2)`（冻结公式）= **0.065704**；`σ_obs_alt = sqrt(mean((half1−half2)²))` = **0.092919**（诊断）；`σ_pair² = σ_obs²/2 = 0.00215849`；单独合法阈 1.96·σ_obs/2 = 0.06439 | PASS（1e-6≤σ_obs≤1） |
| **G4 泄漏/隔离** | batch1-only；target30∩Jaaks=∅；无 ΔEMAX/SYNERGY 列；无新 wells | PASS |
| **G5 边界断言（6 条）** | target30∩Jaaks=∅（交集 []）；端点仅 viability1–4（无 EMAX/SYNERGY）；batch1 only；702/315 pair-cell 排除；无新 wells；peek 披露打印 | PASS |
| **16 行可交换性** | 每 plan-cell 16 行 = 4×4 唯一剂量组合；无 plate/date/行序元数据列 | PASS |
| **技术半拆 FPR ≤0.10** | **0.08348**（33,444 个 (plan-cell,context) 半拆自检验；`F_self` 中位 0.4579；阈 F_crit=2.60） | PASS |
| **算子打乱检测 ≤0.10** | **0.0520**（500 次独立行置换 seed=20261031；检测=超 per-cell 行置换零分布 Q95） | PASS |
| **族错设 <5% → design_invalid** | 合法 plan-cells **8,260/16,722 = 49.4%**；合法 pair **110,523/340,088 = 32.50%**（≥5%，不触发）；additive RMS 分位 median 0.065、p95 0.19 | PASS |

**P0 结论：全部门 PASS**（G3 的 σ 公式量纲/尺度诊断见 §4）。

## 2. 预算预检与实际测量

| 项 | 值 |
|---|---|
| F 计算量（预注册） | **340,428,088**（340,088 × (1+500+500)） |
| 预算预检（运行前） | 1 次完整置换 0.0434 s（另一跑 0.051 s）；投影 wall **107–116 s**；内存 0.673 GB；**pass**（cap: wall 900 s / CPU 7,200 s / mem 8 GB） |
| 实测运行 | run1 wall **105.7 s**；run2 wall **107.3 s**；telemetry run wall **106.97 s**、CPU（total processor）**103.48 s**、峰值 RSS **0.673 GB** |
| N_perm | **500（行置换）+500（算子打乱）= 1,000**，未减；未换便宜分析 |
| 新 wells | **0**（data-only） |

**预算 PASS**，未触发 `design_invalid: compute_budget_exceeded`。

## 3. P1 结果（按冻结统计）

- **宇宙**：|U| = **340,088**；合法 pair（两计划均单独合法）= **110,523**（32.50%）。
- **观测统计**：`F_pair`（`[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`，K=4）；per-cell `T_c=max`；pooled `F≥F_crit` 比例 = **0.153697**；`T_obs` 中位 **73.43**、最大 **153.51**；逐细胞：min p = 0.2255、max p = 1.0。
- **置换零分布**（N=500、seed=20261029，合法 pair 集固定）：per-cell null Q95 范围 **97.46–264.72**；null `T` 中位 **146.31**；null pooled 中位 **0.745673**、Q95 **0.749105**。
- **BH q=0.05**：**0 个细胞拒绝**（rejected_cells = []）。
- **P1 阳性三条件**：① ❌（0<5）；② ❌（0.1537<0.7491）；③ ✅ → **`p0p1_negative`**。
- 逐细胞明细（T_obs/p/null Q95/BH/合法 pair 数）在 `a_p0p1_rows.csv` 与 `a_p0p1.json → P1.per_cell`；**pair 级计数仅描述性**（本轮 observed pair 级 `F≥F_crit` 15.4% 不构成证据，且可能反映 S-add 族错设/异质性）。

## 4. 执行期关键发现（必须与结果一起读；未改阈值/族/置换数）

1. **冻结行置换零分布严重偏高（校准失效）**：null pooled 中位 0.7457 ≫ observed 0.1537；null median T 146.3 ≫ observed 73–77。原因：行置换（每 plan-cell 内独立置换 16 个矩阵元素，见冻结执行协议）破坏剂量对齐的同时**制造了比真实共享 profile 更大的差异**，因此该零分布不对应"shared f 成立"的 H0；P1 在此零模型下**几乎不可能拒绝**（故 BH 0 拒绝、所有 p 偏大）。**结论：本轮 `p0p1_negative` 是"冻结零模型下未检出"，不能当作"无联合矛盾"的证据。**
2. **σ 公式/尺度诊断**：冻结公式 `σ_obs=sqrt(mean((half1−half2)²)/2)` 与 `σ_pair²=σ_obs²/2` 的配套；半拆自检 `F_self` 中位 **0.4579**（若量纲/尺度一致，H0 期望≈1）→ 说明 σ 尺度与 F 定义存在不一致（可能来自技术重复相关/半分法定标口径）；本轮按冻结公式字面执行，**未改阈值**；F 的绝对数值不可跨设计解释。
3. **族合法性**：additive 合法性 32.5% legal pairs（≥5% 门槛通过）；不触发 `design_invalid: family_misspecification`；但这不证明 S-add 正确（见 observed F 分布与 §4.1）。
4. **建议**：在解释/后续（P2/S2/H_A2）前，另立 **A.2 预注册**：(i) 用**参数化/残差型零模型**（如拟合共享算子后的残差置换/leave-dose-out/χ²₃ 校准）替换行置换；(ii) 冻结 σ 的配套尺度（well-level vs row-mean-level）与 F 归一化；(iii) 若需要，预注册 **角色敏感性** 与非加性族。**不得**在本轮结果上事后换零模型/阈值/族。

## 5. 解释边界（写死）

- 阳性（未来）：只写"本资源/本族/本设计下存在联合矛盾（开发性）"；**本轮为阴性**：只写 `no_joint_contradiction`（"本资源/本族/本设计（冻结零模型）下未检出"），**不写"矛盾不存在"**。
- pair 级仅描述性；non-blind/peeked（ON3 QUICK `39868CE4…` 已见）；不称生物学/机制/迁移/决策收益/新颖性；技术重复≠独立培养；不拼 ΔEMAX。
- 未执行 P2/S1/S2/H_A2（未批准）；无新测量/新 wells；未改冻结阈值/族/置换数/折清单。
- 本轮 P1 的负结果**不改变**"联合矛盾是否存在"的科学问题：它只表明**冻结零模型下无检出**，而该零模型经诊断不校准（§4）。

## 6. 产物、确定性、SHA

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_P0P1_EXEC.md`（运行前冻结） | `B201087385B647D573D856B55C17F6675A9EC9E465A94C85545BD9730ACCBA07` |
| `run_a_p0p1.py` | `2F0FE5A45745C3FCD923B7B3995A30F44AD80145C40BF0CD828A73873BF6B4A8` |
| `a_p0p1.json` | `4AEC5157651A634BEF8DF0D8B860349F1A678ED1F7DC181F157F678DC39595C5` |
| `a_p0p1_rows.csv` | `B2C6E77F68B46779DE1DFA42BDE1CCB8D6CF7C170E2045076A4674F02147F940` |
| `budget_precheck.json` | `7F0133EDF85B047BE92AAD5402E85C24387F0C308E1DF1CAF814BDC50127521C` |
| report/record/usage | 见 `usage_a_p0p1.json` |

**确定性**：同脚本两跑 `a_p0p1.json` 与 `a_p0p1_rows.csv` **逐字节一致**（SHA 相同；telemetry wall/CPU/内存只写 usage/budget，不进结果 JSON）；JSON 键排序/无时间戳/allow_nan=False。

## 7. 建议

1. **登记本轮 P0/P1 为已执行**：`p0p1_negative`（冻结零模型下）+ **零模型校准失效的执行期发现**；不升级为"矛盾不存在"。
2. **批准 A.2 预注册**（数据-only 可行）修正零模型/σ 尺度后再解释；A.2 通过前不进入 P2/S2/H_A2、不写机制/迁移/决策。
3. 若 Lead 只接受本轮冻结规则：结论仅限"本资源/本族/本设计（冻结零模型）下未检出联合矛盾"。

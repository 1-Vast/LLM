# record_a_p0p1.md —— R201-A P0/P1 执行记录（Lead 批准：data-only、0 新 wells）

角色：独立执行者（未参与 R197/R200 模型开发）· 任务 task-117（A-P0P1）· 日期 2026-10-28
只写 `mechanism_A/p0p1/` 与 `tmp/`；**未改 v0.1/v0.2 设计文件**；未改其它目录/INDEX/SYNTHESIS/git；**0 新 wells/plate/轮次**；**未执行 P2/S1/S2/H_A2**；non-blind/peeked 继承 ON3。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① P0 资格门（覆盖/over-id/半拆 σ_obs/σ_pair²/G5 六断言/两跑 schema/16 行可交换/半拆 FPR≤0.10/算子打乱≤0.10/族错设<5%→design_invalid） | ✅ 全 PASS（见 report §1；G3 σ 尺度诊断见 §3 发现） |
| ② 预算预检（3.40×10⁸ F；wall≤900 s/CPU≤2 h/8 GB；超→design_invalid 且不减 N_perm） | ✅ 预检 pass（投影 107–116 s）；实测 wall 105.7/107.3/106.97 s、CPU 103.48 s、RSS 0.673 GB |
| ③ P1（|U|=340,088、F_pair、F_crit=2.60、per-cell T_c、500 行置换 seed 20261029、p+BH q=0.05、阳性三条件） | ✅ 已执行；`p0p1_negative`（①0 拒绝、②0.1537<0.7491、③pass） |
| ④ 解释边界 | ✅ 仅"冻结零模型下未检出"；未写"矛盾不存在"；pair 级仅描述性 |
| ⑤ 两跑逐字节一致、实测 wall/CPU/内存、report/record/usage+SHA | ✅ json/rows 两跑 SHA 一致；telemetry 见 §4 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~00:57 | 读 task-117 并 claim；读 `DECISION_R201_A_P0P1.md`、DESIGN/PROBLEM v0.2、qualify v0.2 |
| ~00:58 | **`PROTOCOL_P0P1_EXEC.md` 冻结**（实现选择/σ 公式/半拆 FPR/算子打乱操作化/预算/失败模板；`run_a_p0p1.py` 尚不存在） |
| ~01:00 | 写 `run_a_p0p1.py` |
| ~01:02 | 修正：Windows 无 `resource` 模块 → CPU 用 `time.process_time`、内存用 psutil RSS；结果 JSON 去 telemetry（写 budget_precheck.json）、BH 排序改 mergesort（确定性） |
| ~01:03 | **run1**：wall 105.7 s；`a_p0p1.json` SHA `4AEC5157…9595C5`、`a_p0p1_rows.csv` SHA `B2C6E77F…47F940` |
| ~01:05 | **run2**：wall 107.3 s；两跑 json/rows 逐字节一致 |
| ~01:07 | telemetry run：wall **106.97 s**、CPU（total processor）**103.48 s**、峰值 RSS **0.673 GB**；json 仍同一 SHA |
| ~01:10 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与偏离（全部披露；未改冻结阈值/族/置换数/折清单）

1. **平台适配（非统计偏离）**：Windows 无 `resource` 模块 → CPU 用 `time.process_time()`；内存用 psutil RSS（0.673 GB）；预检 telemetry 写 `budget_precheck.json`，**结果 JSON 不含 wall/CPU/内存**（保证两跑逐字节一致）。
2. **确定性**：BH 排序用 `kind='mergesort'`（避免 ties 下排序不稳定）；JSON 键排序/无时间戳/allow_nan=False；两跑 `a_p0p1.json`/`a_p0p1_rows.csv` 逐字节一致。
3. **算子打乱零模型的操作化**：冻结执行协议中写明"独立行置换 seed=20261031"（因 F 只依赖数值 profile，标签置换在保支撑下等价于重排；原 v0.2 措辞多义，已在运行前写入 exec 协议）。属预注册实现选择，不改门限。
4. **执行期发现（不改阈值/判定）**：
   - **冻结行置换零模型严重偏高**：null pooled 中位 0.7457 ≫ observed 0.1537；null median T 146.3 ≫ observed 73–77 → 该零模型不对应"shared f" H0，P1 几乎不可能拒绝；本轮 `p0p1_negative` 只可读作"冻结零模型下未检出"，**不能读作"无矛盾"**。
   - **σ 尺度诊断**：半拆自检 `F_self` 中位 **0.4579**（若量纲一致 H0 期望≈1）→ 冻结 σ 公式/`F` 归一化存在尺度不一致（技术重复相关/半拆口径）；按冻结公式字面执行，未改阈值；F 绝对值不跨设计解释。
5. **数据边界**：只读 batch1 complete-case target30；plan-cells **16,722**（excluded: incomplete_or_bad_grid 524、not_batch1 475，其余为目标外细胞）；702 个 15 行/315 个 0 行 pair-cell 排除；不插值；未读单药工作簿；未拼 ΔEMAX。
6. **未执行**：P2/ΔW、S1 决策、S2/H_A2；无新测量/新 wells。

## 3. 结果摘要（与 report 一致）

- **P0**：G1–G5 全 PASS；16 行可交换 PASS；技术半拆 FPR **0.08348**（n=33,444；≤0.10）；算子打乱检测 **0.0520**（≤0.10）；族合法性 **32.50% legal pairs**（≥5%）。
- **P1**：|U|=340,088；合法 pair 110,523；observed pooled `F≥F_crit` = **0.153697**；`T_obs` 中位 73.43、max 153.51；null（N=500、seed 20261029）pooled 中位 0.745673、Q95 **0.749105**、median T 146.31；**BH q=0.05 拒绝 0/30**（p 范围 0.2255–1.0）→ 阳性三条件 ①❌②❌③✅ → **`p0p1_negative`**。
- **预算**：F 计算量 340,428,088；1 次置换 0.0434–0.051 s；投影 107–116 s；实测 wall 105.7/107.3/106.97 s；CPU 103.48 s；RSS 0.673 GB → PASS。
- **建议**：A.2 预注册修正零模型（参数化/残差/leave-dose-out/χ²₃）与 σ 尺度后再解释；本轮不升级为"矛盾不存在"。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_P0P1_EXEC.md` | `B201087385B647D573D856B55C17F6675A9EC9E465A94C85545BD9730ACCBA07` |
| `run_a_p0p1.py` | `2F0FE5A45745C3FCD923B7B3995A30F44AD80145C40BF0CD828A73873BF6B4A8` |
| `a_p0p1.json` | `4AEC5157651A634BEF8DF0D8B860349F1A678ED1F7DC181F157F678DC39595C5` |
| `a_p0p1_rows.csv` | `B2C6E77F68B46779DE1DFA42BDE1CCB8D6CF7C170E2045076A4674F02147F940` |
| `budget_precheck.json` | `7F0133EDF85B047BE92AAD5402E85C24387F0C308E1DF1CAF814BDC50127521C` |
| report/record/usage | 见 `usage_a_p0p1.json` |
| 冻结链（未改） | DESIGN_A_v0_2 `486272B2…`、PROBLEM_A_v0_2 `61EC2FC9…`、qualify_A_v0_2.json `D6AE3506…`、DECISION_R201_A_P0P1.md（SHA 见结果 JSON） |

## 5. 缺口（本轮明确未做）

- 未执行 P2/ΔW、S1、S2/H_A2（未批准）；无决策/迁移/机制结论。
- 冻结零模型校准失效 + σ 尺度诊断（§2.4）→ **在 A.2 修正前，P1 结果不可解释为"有/无矛盾"**。
- 未追加新测量/新 wells；若未来需要独立测量另立协议。

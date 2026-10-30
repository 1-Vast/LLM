# record_A2.md —— R201-A.2 预注册（零模型/σ 修正）执行记录

角色：独立审计/设计修订员（未参与 R197/R200 模型开发）· 任务 task-118（A.2）· 日期 2026-10-28
只写 `mechanism_A/a2_prenull/` 与 `tmp/`；**未改 A.1 产物**（p0p1/、DESIGN_A_v0_2、PROBLEM_A_v0_2、qualify 等均未动）；未改其它目录/INDEX/SYNTHESIS/git；**未运行 P1、未读 O'Neil 响应做效应**；non-blind/peeked 继承 ON3；0 新 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① C192 复述与不可解释性 | ✅ `PROBLEM_A2.md §0`；report §0 |
| ② 候选零模型预注册比较（N0–N5：H0/可交换性/实现/诊断；不读响应选） | ✅ `PROBLEM_A2.md §2`；合成校准表见 report §2；`null_design_A2.json → candidate_nulls/selection` |
| ③ σ 尺度修正（σ_pair 定义、F_self≈1、F_crit 方案；不事后改 A.1 阈值） | ✅ `PROBLEM_A2.md §3`；算术：σ_w_hat=0.092919、S1 σ_pair²=0.00107924、frozen=2.000×S1、F_self median=0.4579 |
| ④ A.2 执行设计（统计量/阈值/族/数据不变；仅 null/σ；诊断门；预算；失败类别） | ✅ `DESIGN_A2.md`；`null_design_A2.json → A2_design` |
| ⑤ 边界（A.2 前不进 P2/S2/H_A2；不称生物学/机制/迁移/决策收益/新颖性） | ✅ 各文件 §边界 |
| 完成标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~01:07 | 读 task-118 并 claim；读 C192/A.1 产物、DESIGN/PROBLEM v0.2、DECISION |
| ~01:09 | **`PROBLEM_A2.md` 冻结**（C192 问题界定、候选 null、σ 修正、A.2 要点；`null_design_A2.py` 尚不存在） |
| ~01:10 | 写 `null_design_A2.py`（C192 复述 + σ 算术 + 合成校准模拟） |
| ~01:11 | 修 bug：C192 字段键名（P1.pooled/f_calibration_diagnostic/G3 键）；N2 残差置换最初把**索引**当残差值（FPR 1.0）→ 改为 `resid[perm]`；N2/N4 配对曾跨组比较 → 改为组内配对；修后 N2 FPR 0.165（不 eligible） |
| ~01:12 | 首版结果：primary=N0（FPR .048/power .296）；两跑 `null_design_A2.json` 逐字节一致（SHA `7BCBA58D…E0D948`；wall 各 0.2 s） |
| ~01:15 | `DESIGN_A2.md` / report / record / usage 完成；标 completed + send_message |

## 2. 实现与偏离（全部披露；合成校准不改 A.1 设计/阈值）

1. **C192 键名修正（读取冻结产物）**：`a_p0p1.json` 的 P1 结构为 `P1.pooled.{null_median_frac,null_q95_frac,observed_frac_F_ge_Fcrit}`、`P1.f_calibration_diagnostic.median_T_null`；G3 键为 `sigma_obs/sigma_obs_alt/sigma_pair2`。首版按旧键读取失败（KeyError）→ 修正后复述数字与 A.1 报告一致。
2. **N2 残差置换 bug（修复）**：首版 `fit + perm.reshape(K,M)` 把**置换索引**当残差值（indices 0..15）加入，导致 null F 中位 ~7,000、FPR=1.0；改为 `fit + resid[perm].reshape(K,M)` 后 FPR=0.165、power=0.193（不 eligible）。属实现 bug，修复后按预注册规则继续；**未改变候选定义**。
3. **配对分组 bug（修复）**：N2/N4 首版配对跨 (cell,group) 比较（`sim` 全列表两两）→ F 失真；改为 `pair_F_within_groups`（组内配对）后 N4 FPR 0.947（无效对照，符合预期）。
4. **合成校准只用于选 null**：机制已知（S-add、iid 噪声、σ_w=0.10）、无 O'Neil 响应；FPR/power 为设计诊断，不是对 O'Neil 的效应。**选择规则仅看合成校准**（N0 primary），不读 A.1/A.2 observed 结果；N0/N1/N3/N5 eligible，N2 不 eligible，N4 invalid control。
5. **无响应读取**：本任务未读 O'Neil viability 数值做任何统计；C192 数字全部来自已冻结 `a_p0p1.json`/`a_p0p1_rows.csv`（A.1 结果产物，只读）。
6. **确定性**：同脚本两跑 `null_design_A2.json` 逐字节一致（SHA `7BCBA58D…E0D948`）；JSON 键排序/无时间戳/allow_nan=False；输入 SHA 写入 JSON。

## 3. 关键结果（与 report 一致）

- **C192**：null pooled 中位 0.7457 vs observed 0.1537；null median T 146.31 vs obs 73.43；F_self 中位 0.4579。
- **σ**：σ_w_hat 0.092919；S1 σ_pair² 0.00107924；frozen 0.00215849（ratio 2.000）；A.1 F 尺度为归一化一半 → A.2 必须整体重跑。
- **候选 null（合成 FPR/power）**：N0 0.048/0.296（eligible）；N1 0.054/0.289（eligible）；N2 0.165/0.193（不 eligible）；N3 0.042/0.296（eligible）；N4 0.947/0（invalid 对照）；N5 0.049/0.296（eligible）。**primary null = N0**；per-cell T_c 实现细化 = N1 bootstrap（保留相关结构）。
- **A.2 不变**：数据/U=340,088/单独合法规范/S-add 族/F_pair/per-cell T_c/F_crit=2.60（条件性）/N_perm=500/BH q=0.05/阳性三条件。
- **A.2 仅改**：σ_pair² S2（S1 敏感性）；null N0（pooled）+N1（per-cell T_c）；新增 D1–D7 诊断门；failure categories `design_invalid: scale_mismatch|null_calibration|compute_budget_exceeded`（+A.1 既有）。
- **预算**：data-only、0 新 wells；wall≤900 s、CPU≤2 h、内存≤8 GB；≈2,500 次模拟（primary 500 + pooled 500 + 候选 N2/N3/N5 各 500）；两跑逐字节一致。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A2.md` | `93C7613BDF7E218171C83A6FA3F371283E252C0F9249562E8830DD027C8237F1` |
| `DESIGN_A2.md` | `6BB3460E9FD2F44F35FEDF4B7815662728CA372BB1D67DADA8229AE4EA717D89` |
| `null_design_A2.py` | `BD281F122D407AB76D6DD40435A6B86CBB97A2233541A7016A738A0AE5E8F021` |
| `null_design_A2.json` | `7BCBA58DD26849345EB3143607BA95EF2329313417DD14F6E2C1D77295E0D948` |
| report/record/usage | 见 `usage_A2.json` |
| A.1 只读引用（未改） | `a_p0p1.json` `4AEC5157…9595C5`、`report_a_p0p1.md` `340D90BC…`、`record_a_p0p1.md` `C7723AB5…` |

## 5. 缺口（本轮明确未做）

- **未执行 A.2**（预注册草案；须独立挑战 + Lead 批准）。
- 未运行 P1、未读 O'Neil 响应做效应；合成校准不是 O'Neil 结论。
- 未执行 P2/S2/H_A2；无新测量/0 新 wells。
- A.2 若执行，须按新 SHA 整体重跑；A.1 的 `p0p1_negative` 原样保留、不重判。

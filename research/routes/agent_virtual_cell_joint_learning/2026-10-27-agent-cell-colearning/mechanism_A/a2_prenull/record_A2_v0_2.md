# record_A2_v0_2.md —— R201-A.2.1 修正预注册执行记录

角色：独立审计/设计修订员（未参与 R197/R200 模型开发）· 任务 task-120（A.2.1）· 日期 2026-10-28
只写 `mechanism_A/a2_prenull/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 A.2 产物**（PROBLEM_A2/DESIGN_A2/null_design_A2.py/json/report/record/usage 均未动）、未改 A.1/P0P1 产物、其它目录/INDEX/SYNTHESIS/git；**未运行 P1、未读 O'Neil 响应做效应**；data-only；0 新 wells；non-blind/peeked。

## 0. 要求与完成对照（challenge_A2 5 必改）

| 要求 | 状态 |
|---|---|
| 1 S2 因子 2 修正（0.5×；与 S1/A.1 倍数写清） | ✅ `PROBLEM_A2_v0_2.md §2`；JSON `S2_factor2_fix`：σ_pair²_A2=0.00107924、S2_raw=2σ_pair²、A.1 frozen=2.000×、校正后=S1 |
| 2 重写 F_self/D2/D3（与 F_pair 分子同方差的自检；重算 FPR/F_crit 条件） | ✅ `PROBLEM_A2_v0_2.md §3`；JSON `F_self_rewrite`：旧自检 mean=1 sd=0（作废）；新 F_self_check mean 1.0053、median 0.8001、FPR@2.60 0.0490；D2/D3+ratio 门重写 |
| 3 legal 规则与 σ 变更交互写死 | ✅ `PROBLEM_A2_v0_2.md §4` / `DESIGN_A2_v0_2.md §4`：A.2 规则 σ_obs_A2=σ_w_hat/2=0.0464595、阈值 0.0910607；重算 legal 集、不冻结 n_legal=110,523；门 ≥5%U；pooled/BH 口径 |
| 4 按修正尺度重算合成校准/必要时重选 | ✅ JSON `candidate_calibration_corrected`：N0 .0483/.2956、N1 .0578/.2889、N3 .0420/.2956、N5 .0475/.2956（eligible）；N2 .1652 不 eligible、N4 .9474 invalid；primary=N0；无合格→null_calibration |
| 5 预算/失败类别统一 | ✅ JSON `budget`（186 s 估计；caps 900/7200/8GB；两跑；JSON 无 telemetry）与 `failure_categories`（scale_mismatch/noise_calibration/null_calibration/compute_budget_exceeded 映射） |
| 边界不变 | ✅ 不运行 P1；A.1 negative 不重判；不称生物学/机制/迁移/决策收益/新颖性；A.2 前不进 P2/S2/H_A2 |
| 完成标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~01:14 | 读 task-120 并 claim；读 challenge_A2、v0.1 A.2 产物、C192/A.1 |
| ~01:16 | **`PROBLEM_A2_v0_2.md` / `DESIGN_A2_v0_2.md` 冻结**（`null_design_A2_v0_2.py` 尚不存在） |
| ~01:17 | 写 `null_design_A2_v0_2.py`（S2 算术、F_self 重写、修正尺度合成校准、legal 规则、预算/失败类别；只复用 v0.1 A.2 的合成函数，不读 O'Neil 响应） |
| ~01:18 | 修 bug：C192 键名（`P1.pooled`/`f_calibration_diagnostic`）、`sigma_obs_frozen` 键；首跑成功 |
| ~01:19 | 第二次运行 `null_design_A2_v0_2.json` 逐字节一致（SHA `96AE014D…76A24E5`；wall 各 0.2 s） |
| ~01:22 | report/record/usage 完成；标 completed + send_message |

## 2. 实现、假设与偏离（全部披露；未改 A.2 设计对象）

1. **v0.1 A.2 文件未改**：`PROBLEM_A2.md 93C7613B…`、`DESIGN_A2.md 6BB3460E…`、`null_design_A2.py BD281F12…`、`null_design_A2.json 7BCBA58D…` 保持原样；v0.2 为修正增量。
2. **合成校准复用**：v0.2 脚本通过 `importlib` 只读加载 v0.1 A.2 脚本的合成函数（synthetic_groups / pair_F_values / 候选 null 函数），未读 O'Neil 响应、未运行 P1；只用于零模型设计校准。
3. **F_self_check 的模拟理想化（必须披露）**：v0.2 的 F_self_check 合成演示中，两套半拆 A={1,2}/{3,4}、B={1,3}/{2,4} 使用**独立抽取的孔级噪声**（各 4×4×4 wells），因此 `Cov(d_A,d_B)=0` 严格成立；**真实 A.2 执行须在同一个 plan-cell 的同一组 4 wells 上构造两套半拆**（共享孔位），此时 iid 下乘积和仍为 0（代数已核：共享孔系数乘积和 = 0），但若有技术重复相关，Cov 非零；A.2 执行须报告两套半拆的相关诊断（预留 D2 敏感性），不影响本轮预注册目标（均值/中位/FPR 门）。
4. **N1 合成校准数值变化（0.0578 vs v0.1 0.0541）**：v0.2 对 N1 使用单次 bootstrap 运行（v0.1 拼接 3 次）→ 蒙特卡洛抽样差异；仍 eligible，不影响选择（N0 primary）。
5. **无响应读取**：C192 数字全部来自已冻结 `a_p0p1.json`/`a_p0p1_rows.csv`；本任务未读 O'Neil viability 数值做统计。
6. **确定性**：JSON 键排序/无时间戳/allow_nan=False；两跑逐字节一致；输入 SHA 写入 JSON。

## 3. 关键结果（与 report 一致）

- **S2**：Var(full)=0.00053962 → σ_pair²=0.00107924；Var(half diff)=0.00215849=2×；S2_raw 期望=2σ_pair²；**校正 σ_pair²_A2=0.00107924**；S1=0.00107924；A.1 frozen=0.00215849=2.000×。
- **F_self**：旧自检 mean=1.000000、sd=0（恒等，作废）；新 F_self_check mean 1.0053、median 0.8001、FPR@2.60=0.0490 → D2/D3 通过；加 ratio 门 σ_pair²_A2/σ_pair²_S1∈[0.5,2]；F_crit=2.60 条件保留。
- **legal**：A.2 σ_obs_A2=0.0464595、阈值 0.0910607（A.1 0.06438958）；重算 legal 集，不冻结 n_legal；门 ≥5%|U|=17,004.4；pooled/BH 口径 A.2。
- **合成校准（校正尺度）**：N0 .0483/.2956；N1 .0578/.2889；N2 .1652/.1933 不 eligible；N3 .0420/.2956；N4 .9474/0 invalid；N5 .0475/.2956；**primary=N0**（per-cell T_c 用 N1 bootstrap）；wrong-scale 诊断：observed F 减半 → FPR/power 崩塌。
- **预算/失败类别**：总估计 186 s（N1 500 fits、N0 pooled 500、诊断 2,000、observed 1）；caps wall 900 s/CPU 2 h/内存 8 GB；统一四类失败映射。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A2_v0_2.md` | `3B49A8ABA7FBA903C1C88CBE75318E55F5C3045512A058E4FF54AA5EF1F16104` |
| `DESIGN_A2_v0_2.md` | `3AB5A663AD485579A42B0C3BB09096D756CBD6F123A93815A7FC91EA2CF3142E` |
| `null_design_A2_v0_2.py` | `AC4DE4C7F1859E35E4BDFA49B428F1C2319390E611D822DF622FEF4AA58BD721` |
| `null_design_A2_v0_2.json` | `96AE014DA6B8E9E5CA7AF359CC3DAA0D683FE8F865655A468167AC16176A24E5` |
| report/record/usage | 见 `usage_A2_v0_2.json` |
| v0.1 A.2（未改） | PROBLEM_A2 `93C7613B…`、DESIGN_A2 `6BB3460E…`、null_design_A2.py `BD281F12…`、null_design_A2.json `7BCBA58D…` |

## 5. 缺口（本轮明确未做）

- 未运行 A.2/P1（预注册修正；须独立挑战+Lead 批准）。
- 未读 O'Neil 响应做效应；合成校准不是 O'Neil 结论；F_self_check 的同孔两套半拆相关诊断待 A.2 执行。
- 未执行 P2/S2/H_A2；0 新 wells。

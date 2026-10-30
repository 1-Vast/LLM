# DESIGN_M2_STAGE2 —— R204-M2 Stage2/3 执行设计（数据门 + 固定反馈/固定更新器；不运行效果）

2026-10-28。依据：[PROBLEM_M2_STAGE2.md](PROBLEM_M2_STAGE2.md)、`stage2_plan.json`、`stage23_schema.json`、`timing_m2_stage2_prep.json`、M2 v0.2 链、C206 Stage1、DATA1（C205）、R203-P1 链。
**状态：设计准备草案；Stage2/3 未执行；当前 `data_unavailable`；未运行方法比较/未报告效果；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells。**

## 0. 执行前核验与门顺序

1. **SHA 链**：M2 v0.2 + Stage1/C206 + DATA1 15 文件全部匹配（`stage2_plan.py` 本地已核验 chain_pass=true/mismatches=0）；执行时重核，失败→`design_invalid: chain_mismatch`。
2. **Stage1 状态**：C206 `failed_checks=[]`、`no_effect_results=true`、full K 75/75、same-U 3/3 → PASS；本设计不重跑 Stage1。
3. **数据就绪门（D1–D7，PROBLEM §1）**：全部满足才允许 Stage2；当前 **data_unavailable**（映射/numeric/独立培养标签缺失）；门失败只写 `data_unavailable`，**不**以合成/RNA 替代。
4. **数据冻结**：合格数据登记 SHA、数据字典版本、响应/功能角色、交换性/平衡诊断；冻结后才可生成分析计划。
5. **Stage2 通过后**：另立 Stage3 预注册（同一数据/更新器/合法实验包）+ 独立挑战 + Lead 批准；本设计不执行 Stage2/3。

## 1. Stage2 固定反馈比较学习（不执行）

### 1.1 流程

- 输入：合格多时间功能数据（D1–D7）；动作/剂量/时间/function readout；记录 π/标签；计数+RNA。
- 划分：**先留出程序（procedures）→ 再留出背景（backgrounds）**；训练/验证/测试按独立培养/板/批次 cluster；技术重复不独立。
- **固定反馈**：所有方法收到**同一** queried actions/feedback 流（学习比较；不比较 acquisition）。
- 新功能：所有方法**同样标定**；只换已观测功能权重=有限任务重组，不是零样本迁移。
- 每方法：相同 prior/初始数据/特征信息/query T=6/每轮 1 feedback/调参≤20/相同 compute caps；先记录预算审计再比较。
- 主端点：独立功能决策效用/后悔；δ=.05；headroom/MDE 先检；cluster CI；次端点预测校准/算子误差/RNA。

### 1.2 基线实现规格（输入/信息集/超参/流程/等预算审计）

| baseline | 输入/信息集 | 超参预算 | 训练-更新流程 | 等预算审计 |
|---|---|---|---|---|
| **M2 候选** | 小 φ 族；state/action 依赖 K_a；记录 π/动作 | ≤20 配置 | f_g 条件后继→任务方向选择→新矩闭合检验→K 乘积/重组 | 同 query/feedback/features/tuning |
| **B_full_history_retrain** | 全部历史/动作/function readout | ≤20 | 每轮从全部历史重训 | 同 query/feedback/features/tuning |
| **B_hierarchical_gp** | 同特征 + culture/background 随机效应 | ≤20 | 分层 GP 后验更新 | 同上 |
| **B_koopcell_disiko** | 同特征/cohort | ≤20 | KoopCell/DisKO 式未配对 cohort 算子适配 | 同上 |
| **B_td_jepa_successor** | 同特征；转移构造 successor features | ≤20 | TD-JEPA/后继特征适配 | 同上 |
| **B_state_space_pkpd** | 同剂量/时间/readout | ≤20 | 状态空间/PKPD 更新 | 同上 |
| **B_full_retrain** | 同 | ≤20 | 每轮从头重训 | 同上 |

- **接口**：只读冻结 formalism/Stage1 的 φ/K_a/记录态估计/闭合检验接口；不修改冻结代码；不重用 A/B 线资源；数据门通过前不拟合真实数据。
- **防泄漏**：特征不含 state/truth；oracle 仅评估；B2/EDMD 类基线同信息；数据划分/程序留出先于背景。

## 2. Stage3 固定更新器比较取证（不执行）

- **固定更新器**：所有 selector 共用同一 learner/updater；**selector 与 learner 分离**；禁止 selector 侧偷看更新器内部目标。
- **selector**：M2 主动干预选择 vs **random、GP acquisition、最优输入设计（受控弱 EDMD/系统辨识）、BATCHIE 适配**。
- **同成本/合法实验包**：相同 cohorts/plates/doses/timepoints/controls/feedback rounds；完整闭环账：培养物/板/对照/失败/重复/标定/计算/调参。
- **防选择性**：候选集/轮次/菜单先注册；先留出程序再背景；所有 selector 同菜单/成本包；不得用目标结果事后调 selector；报告全部 selector（不选优）。
- 主/次端点同 Stage2；Stage3 仅在 Stage2 PASS + 数据合格 + 另立预注册/挑战/Lead 批准后启动。

## 3. 基线骨架/单测/计时（本轮仅此可执行）

`stage2_plan.py` 实现**骨架 + 单测 + 计时**（不跑效果比较、不报告效果指标）：

- 骨架：full-history retrain（ridge 解）、hierarchical GP（核后验）、KoopCell/DisKO（线性算子适配）、TD-JEPA/successor（后继权重）、state-space/PKPD（一室 Euler）、selector 骨架（random/GP/optimal input/BATCHIE 索引合法性）。
- 单测：输出有限/形状正确、selector 返回合法动作、**等预算审计**（同 query 数、同 tuning≤20）；全部 PASS。
- 计时：单测/实例化 **0.03082 s/rep**；Stage2 投影 1.48 s、Stage3 投影 2.96 s（caps 1800 s）。
- 骨架不含真实数据/真实响应；不报告任何 effect/regret/方法差异。

## 4. 统计/端点/失败/停止

- 主端点：独立功能决策效用/后悔；δ=.05 normalized；headroom=U_max−U0 先检；配对 MDE=2.801585·SD/√n_eff；cluster 按培养物/背景/任务；**6,282 仅 Fisher-z、非通用门**；次端点仅 secondary。
- 规划表（SD(D) .10/.15/.20/.30；ICC .30；m=5；deff=2.2）：n_req cluster **71/157/278/623**；MDE 在 n_req 约 .0495–.0500；SD=.20 → n_req 278。
- 失败类别：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：数据门失败→data_unavailable（当前）；等预算复制/超过→撤主算法；闭合/随机化/测量失败→stop；仅 RNA/预测/算子误差收益→撤；成本超限→stop；CI 无法排除→inconclusive；跨任务失败→限当前任务；不换端点/降 δ。

## 5. 预算/种子/schema

- **Stage2**：wall≤1800 s/CPU≤2 h/内存≤8 GB；data-only、0 wells；当前不执行。
- **Stage3**：wall≤1800 s/CPU≤2 h/内存≤8 GB；实验成本进闭环账；不执行。
- **种子**：Stage2 `20261200..20261239`（40 组）；Stage3 `20262100..20262139`（40 组）；与 Stage1 脚本内 seed-like 数字交集 **[]**；执行时重核不与其他冻结 seed 重叠；不得执行时改 seed。
- **schema**：`stage23_schema.json` 冻结 Stage2/3 字段、per-method 字段、禁止字段（药理/真实决策/迁移/机制/新颖性/探索端点/RNA 当 primary）、无效果结果；两跑逐字节；失败只写类别。
- **telemetry**：仅 timing 文件；结果 JSON 无 wall/时间戳。

## 6. 批准清单（Stage2 执行前）

1. 数据就绪门 D1–D7 全满足 + 数据 SHA/字典/角色冻结；否则 `data_unavailable`。
2. 基线输入/信息集/超参/流程/等预算审计写死；固定反馈、先程序后背景、新功能同标定；EDMD 等价强基线纳入。
3. primary/δ/headroom/MDE/cluster CI/6,282 边界/次端点写死；失败类别/停止/预算/schema/两跑固定。
4. Stage2 不报效果；Stage2 后 Stage3 另立预注册+独立挑战+Lead 批准；真实数据/湿实验/药理/真实决策/迁移/新颖性不批。

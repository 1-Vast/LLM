# PROBLEM_M2_v0_2 —— R204-M2.1：任务驱动主动辨识群体功能算子（p 冻结修正预注册；不运行效果）

2026-10-28。对象：R204-M2（D1/M2 首选主线）。本文件修正 v0.1（[PROBLEM_M2.md](PROBLEM_M2.md) `4AF84EE0…`，保留不改）。依据：M2-C1 挑战（revise：p=5 vs p=4 冲突）、[challenge_M2.md](challenge_M2.md)、R204 BRIEF/report/evidence、R203-P1 链、ERRATA C197/C199/C201/C203。
**状态：预注册设计草案 v0.2；未运行效果比较/未声称增益；机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；不改 v0.1 产物；合成阶段 compute-only、0 wells。Stage 1 执行须另立独立挑战 + Lead 批准。**

## 0. M2-C1 必改落实（v0.1 → v0.2）

| # | v0.1 问题 | v0.2 修正（唯一 p=5） |
|---|---|---|
| ① **p=5 vs p=4 并存** | testbed `phi_dim_p=5`，但可辨识算术全为 p=4（full K 48=3×4²、mixed 40/48/nullity8、U 长度4、pure groups 24） | **冻结唯一 p=5**（与 testbed 一致，保留理由：v0.1 测试床已冻结 p=5 且 DA 线 d=4/A=3/p=5/T=3 已写入 BRIEF；p=4 需改测试床并重写 stage 规格，收益仅是把算术简化，不改科学问题）；**全文统一 p=5，无 p=4 数字残留** |
| ② **重算可辨识算术** | 48/48、40/48、nullity8 不是 p=5 证据 | **p=5 重算**（同一脚本 `formalism_M2_v0_2.py`，显式 Kronecker 设计）：**full K 参数 A·p²=75/75 可辨识**（30 个 pure 组，10/动作，每动作≥p=5 且 U_i 张成 R^5）；**mixed assignments（20 组、U 变化）rank=75/nullity=0**（构造性满秩；一般性仍需设计支撑，不声称任意混合都识别全部 K）；**same-U pure+mix rank=3/3**（K_aU 可辨识）；**U 向量长度=5**；**pure groups=30**；无支持动作不可辨识；gauge `K_a→M K_a M^{-1}` |
| ③ **代码/JSON/schema 更新** | formalism_M2.py 用 p=4，JSON 无 stage1 schema | 新 `formalism_M2_v0_2.py`（p=5、Gp=30、G=20，显式设计矩阵）、`formalism_M2_v0_2.json`、**`stage1_schema_v0_2.json`**（p/A/full K rank/mixed rank/nullity/param dim/U 长度/pure groups 写死）；两跑逐字节一致；JSON 无 telemetry；Stage 1 pilot 用最终代码重跑 |
| ④ 其余内容 | — | **形式化/记录态正确式/禁止边际捷径/EDMD 等价边界/三阶段/主端点/δ/headroom/MDE/6,282 边界/等预算基线/停止/数据/失败类别/边界保持不变**（见 §1–§8） |

## 1. 形式化（冻结）

- **状态 X**：培养物/cohort 状态，含必要历史与绝对数量（增殖/死亡计数；归一化 RNA 分布不能单独区分数量变化）。**φ(X)∈R^p**（**p=5**）：可观测小函数族（独立功能读数 + 计数 + 预注册历史项）；基在拟合前固定。
- **闭合声明（待检验）**：`E[φ(X_Δ)|X_0=x,a]=K_aφ(x)`，`K_a∈R^{p×p}`；是模型假设，须在真实新矩上检验，不是恒等式。
- **固定随机分配 π 的群体矩**：`V_i=Σ_aπ_i(a)K_aU_i`（`U_i=Eφ(X_0|i)`、`V_i=Eφ(X_Δ|i)`；π 已知、各组起始分布相同）。
- **记录态分配正确估计**：`V_i=Σ_aK_aE[1{A=a}φ(X_0)|i]`；**禁止**边际 π×均值捷径（p=5 设计算术 bias 范数 **0.2643** 非零）。动作标签完整使用；π=cohort 间分配，非单培养物细胞自由给药、非联用。
- **任务驱动闭环**：从已测独立功能 f_g 拟合合法动作条件后继 → 依功能目标选起始条件/给药/时点辨识任务相关作用方向 → 真实新矩拟合+闭合检验 → 闭合：多步程序由 **K 乘积**计算/已测功能范围内重组；失败：报告**哪一作用/时程不可复用**。**函数选择/何时增补/有限样本误差控制仍是待发展算法问题，不声称已解决。**

## 2. 与 KoopCell/DisKO/受控 EDMD 的差异边界（不变）

- **固定 φ 线性闭合由受控弱 EDMD/系统辨识+最优输入设计直接覆盖，必须作等价强基线**；同预算复制/超过 → **撤主算法主张**（`no_increment`/`rename_edmd`）。
- KoopCell/DisKO（未配对群体学习）、TD-JEPA/后继特征（转移/目标复用）、BATCHIE（模型后验+反馈+批量选择）已覆盖部分，**不声称新**。
- 拟研究交叉点仅为**破坏性群体测量下由功能任务主动选择实际干预辨识可复用作用**；若等预算无独立功能决策增量 → 撤主创新主张。
- 生物兼容：起终姐妹制备可交换；不伪配同细胞轨迹；计数保留；策略反馈需策略加权闭合；新药无输入特征/反馈无自动迁移保证。

## 3. 受控真值测试床（Stage 1；p=5 冻结）

- **合成群体系统**：隐藏状态 d=4（含历史）；非线性/非闭合反例；**已知 K_a 真值**（seed 固定，方法不可见）；A=3、**φ 维 p=5**、cohorts=200、timepoints=3；三例（线性闭合 positive control、非线性非闭合 negative control、部分支持不可辨识 negative control）。
- **可辨识算术（p=5，本设计）**：
  - same-U pure+mix：assignment design rank **3/3（A=3）** → `K_aU` 全部可辨识；仅 mixture 时只组合可辨识。
  - **full K**：参数 `A·p²=3×25=75`；每动作 ≥p=5 个纯分配组且 `U_i` 张成 R^5（共 **30** pure 组、10/动作）→ design rank **75/75**，full K 可辨识。
  - **mixed assignments**（20 组、U 变化）：rank **75/nullity 0**（构造性满秩；条件为设计支撑/变化足够；不声称任意混合/有限观测都识别全部 K）。
  - **same-U** U 向量长度 **5**；无支持动作 → positivity 违反 → K_a 不可辨识；gauge `K_a→M K_a M^{-1}`。
- **非闭合反例**（与 p 无关，保留）：φ=(1,x) 线性动态 → 闭合残差 **2.7e-15**；φ=(1,x,x²)、`x'=x+a+cx²+ε` → 出现 x³/x⁴ 项、残差 **3.7577**（不闭合）。
- **正交设计示例**：同 U 下 pure (1,0)/(0,1) 分离 K_aU；.5/.5 只给平均；不同 mix 可分离二者但**不能识别所有 K、不保证混合优于纯药组**（不声称）。
- **随机化/可交换性合同**：π 先于结果、与隐藏状态独立（给定记录历史）、各组起始分布可交换；分配依赖记录 X0 → 用记录态估计式；检查平衡/支持/交换性；失败→`design_invalid: randomization`。
- **pilot 计时（最终 v0.2 代码）**：10 replicate 设计/估计算术 **0.00228 s/rep**；投影 stage1 **0.1 s**、stage2 **0.3 s**、stage3 **1.1 s**（Stage1 caps 600 s/CPU 2 h/内存 8 GB）。

## 4. 最小验证三阶段（预注册，不运行）

1. **Stage 1 受控真值系统**：可辨识性/非闭合/随机化检查；**只报检查结论、不报增益**；合成 compute-only 0 wells。
2. **Stage 2 多时间功能数据、固定反馈比较学习**：合格多时间功能数据（同培养物/背景/批次可交换、剂量/时间/function readout、记录 π/动作、独立培养/板重复、计数保留）上**相同固定反馈**比较候选 vs full-history retrain / hierarchical GP / KoopCell-DisKO 适配 / TD-JEPA 后继特征适配 / state-space PKPD；同信息/同预算/同调参；**先留出程序，再留出背景**；新功能所有方法同标定；只换已观测功能权重=有限任务重组，不是零样本迁移。
3. **Stage 3 固定更新器比较取证**：候选主动干预选择 vs random/GP/最优输入设计/BATCHIE 适配；同固定更新器与预算；最后**完整闭环**（计培养物/板/对照/失败/重复/标定/计算/调参）。

## 5. 主端点/δ/功效（不变）

- **Primary**：独立功能下的实际决策效用/后悔（per endpoint 分别规划）；δ=**0.05 normalized**；先检 `headroom=U_max−U0`（<δ→`unreachable_gate`；近满分→另立 budget-to-target，不静默换端点）。
- **配对功效**：`MDE80=2.801585·SD(D)/√n_eff`；`n_req=ceil((2.801585·SD/δ)²)`；cluster 按独立培养/背景/任务；**6,282 仅 Fisher-z 参考、非通用门**。
- **次端点**（仅 secondary）：预测校准、算子/K_a 误差、RNA 误差；**RNA 提分/内部一致性不能替代**独立功能决策。

## 6. 等预算强基线/停止（不变）

- **基线**：受控弱 EDMD/工具变量系统辨识+最优输入设计（等价强基线）、KoopCell/DisKO 适配、TD-JEPA/后继特征适配、state-space/PKPD、hierarchical GP、full-history retrain；同信息/同预算/同调参/同合法实验包。
- **停止/撤主张**：标准方法同预算复制/超过→撤主算法（`no_increment`/`rename_edmd`）；闭合/随机化/测量合同失败→stop；仅 RNA 收益无独立功能决策→撤主创新；成本超上限→stop；CI 无法排除无收益→`inconclusive`；跨任务失败→限当前任务。

## 7. 失败类别/预算/数据需求/边界

- **失败类别**：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **预算**：Stage 1 合成 compute-only、**0 wells**、caps **wall≤600 s/CPU≤2 h/内存≤8 GB**；Stage 2/3 计划 ≤1800 s；真实阶段需合格多时间功能资源并单列预算。
- **真实数据需求**：多时间功能/群体快照（同培养物/背景/批次可交换；剂量/时间/function readout；记录 π/动作标签）、独立培养/板重复、正交功能（apoptosis/caspase/靶点参与/regrowth）在声称时、计数与 RNA 并存；**AZ 数据字典/功能数值当前未取得（C203）→ 真实阶段 `data_unavailable`**，不得由导出缺失推断"只能新湿实验"。
- **边界**：机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；**Stage 1 执行须另立独立挑战+Lead 批准**；不批准 Stage 2/3 执行。

## 8. 产物

`PROBLEM_M2_v0_2.md`（本文）、`DESIGN_M2_v0_2.md`、`formalism_M2_v0_2.py`、`formalism_M2_v0_2.json`、`stage1_schema_v0_2.json`、report/record/usage v0.2、`timing_M2_pilot_v0_2.json`；v0.1 产物保留不改。

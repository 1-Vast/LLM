# PROBLEM_DECISION —— R203-P1 决策终点、可达空间、配对功效与两本账（设计，不运行）

2026-10-28。对象：R203-P1。**状态：设计/规划，不运行效果、不拟合预测、不读响应/功能数据。**
本文件把“下一项独立研究”的**决策终点、成功门可达性、配对功效、机制 vs 药理两本账**写死；不降旧门槛、不改旧判定、不晋升代码、不恢复已停止实验；不称新颖性/机制/迁移/决策收益。

## 0. 核心修正（按用户复核 §3–§4 / ERRATA C197/C199）

1. **撤“≈6,282 细胞通用决策门”**：它只适用于**独立相关系数 Fisher-z 比较**（`N_req=2×(2.801585/δ)²+3`；δ=.05→6,283；δ=.10→1,573）。净效用、误选率、后悔、top-k、达标预算各有自己的独立单位/方差/配对结构，必须**按端点分别规划**。
2. **成功门必须先做可达性预检**：T1 的 `C7_experiment_only 451/500=.902`，`max_gain=1−.902=.098<δ=.10`；通过需**501/500**——**本批对任何算法不可达**，不是功效不足。保留 T1 `partial_decision_benefit` 与原 CI，**不事后降 δ**。
3. **机制验证与真实药理确认两本账**：合成/已知 ground-truth 可验证形式与计算能力，但**不取得药理证据**；真实决策收益需合格实测功能、暴露、独立评估、配对功效与预算。
4. **技术重复不是独立生物单位**；30 cells 是否够取决于**端点 SD/D、配对相关、ICC、δ**，不能用一个数字统一裁定。

## 1. 终点清单与定义（每个端点独立规划）

**独立单位**：独立生物单位（细胞系/患者来源培养/独立分化/独立培养批次）；**wells、技术重复、单细胞、计划行都不是独立生物单位**。**配对**：同一独立单位/同一决策上下文上的 D；**聚类**：同一单位内重复决策、同一培养/批次/板。以下“需实测功能”指需要合格 functional endpoint（viability/apoptosis/regrowth 等）；“合成可测算法”只表示可在合成 ground-truth 上验证算法，**不等于药理/决策收益**。

| id | 端点 | 定义（每个独立单位 i） | 独立单位/配对/聚类 | 需实测功能/预算 | 合成可测算法 | 备注 |
|---|---|---|---|---|---|---|
| E1 | **净决策效用** | `D_i=U_i(M*)−U_i(C)`；U=预注册净效用（收益−成本） | 独立培养/细胞背景；同单位配对；按单位聚类 | **是/是** | 是（仅算法） | 真实决策收益 primary；合成不得称药理 |
| E2 | **误选率** | `m_i=1[action≠best]`；`D_i=m_i(M*)−m_i(C)`；lower better | 同单位配对二值；按单位聚类 | **是/是** | 是 | 天花板/headroom 先检；T1 式不可达 |
| E3 | **后悔** | `r_i=U_i(best)−U_i(selected)`；`D_i=r_i(M*)−r_i(C)`；normalized | 同单位配对；按单位/背景聚类 | **是/是** | 是 | 分布不同于准确率；n 不能从 accuracy 推 |
| E4 | **top-k 命中** | `h_i=1[best in top-k]`；`D_i=h_i(M*)−h_i(C)` | 同单位配对二值 | **是/是** | 是 | 天花板先检 |
| E5 | **达标预算** | 达到预注册决策质量目标所需 wells/成本；paired log/ratio | 独立实验/单位；按单位/板/日聚类 | **是/是** | 仅计算成本 | 基线近满分时的**另立问题**；不能静默换终点救 T1 |
| E6 | **机制检测/可辨识性** | 检测 power/FPR/参数恢复/J 检测 | 合成 replicate/seed；按 generator cluster | **否/否** | **是** | **机制账 only**；绝不药理/决策 |

## 2. 通用“成功门可达性”预检

### 2.1 公式

对二值成功率（accuracy/mis-selection/top-k）：

```
max_gain = U_max − p0                 # U_max=1（或预注册上限）
required_successes = ceil(n × (p0 + δ))
reachable ⇔ (δ ≤ max_gain) 且 (required_successes ≤ n)
```

对连续端点（net utility/regret/budget log-cost）：

```
MDE80 = 2.801585 × SD(D) / sqrt(n_ind)
precision_ok ⇔ MDE80 ≤ δ
headroom_ok ⇔ δ ≤ U_max − U0       # 对 lower-better 端点取方向对应
```

**二者必须同时通过**：headroom 不过 → 端点在该基线/总体下**不可达**（不是“算法差”）；MDE 不过 → **精度不足**（不是“效果不存在”）。**立项前**完成；**不得看结果后降 δ/换基线/换终点**（若换问题，须新预注册）。

### 2.2 T1 反例（保留旧判定）

- `n=500`；`C7_experiment_only` 成功 451/500=.902；`π_dual` 456/500=.912；δ=.10，要求两主差≥.10 且 Holm 显著。
- `max_gain=1−.902=.098<.10`；`required_successes=ceil(500×1.002)=501>500`；**本批对任何候选不可达**；**通过需 501/500**。
- **结论**：保留 T1 `partial_decision_benefit` 与原 CI；不能解释为“算法增益不足”；该上界只对本批固定基线成立，不证明总体不可能，也不证明 π_dual 有效；不降 δ。
- **未来**：先做 headroom+MDE 预检；若基线近满分，可另立“**达标预算**（E5）”问题，并新预注册；不能静默换终点救本轮。

### 2.3 预检流程（立项前）

1. 冻结端点/动作集/效用或成本/独立单位/总体/δ（δ由决策相关性定义，不由结果反推）。
2. 用预注册 pilot/已有资源估计 `p0`/`U0`、`U_max`、`SD(D)`、`ICC/簇大小`、discordance；**不得用目标 outcomes 选择 δ/端点**。
3. 计算 headroom；若 `δ>headroom` → `unreachable_gate`（stopped，不降 δ）。
4. 计算 `MDE80`/`n_req`；若 `MDE80>δ` 或 `n_available<n_req` → `precision_insufficient`/`data_unavailable`（不是算法失败）。
5. 两门均过 → 冻结 n/分析/预算；否则不立项或另立**新问题**（如 E5）并重走预检。

## 3. 配对功效规划（按端点）

### 3.1 连续配对（net utility/regret）

- `MDE80=2.801585×SD(D)/√n_ind`；`n_ind=ceil((2.801585×SD(D)/δ)²)`。
- 聚类：`n_cluster=ceil(n_ind×[1+(m−1)ICC])`；优先在 cluster 水平构造 D。
- 技术重复只降低测量噪声，**不降低独立单位 n**；不能拿 technical replicate 乘 n。
- 示例（δ=.05）：SD(D)=.20→**126**；SD=.30→**283**；加入 6 个/簇、ICC=.5→设计效应 3.5→**441**；regret SD=.15→**71**。

### 3.2 二值配对（mis-selection/top-k）

- D∈{−1,0,1}；`Var(D)=(p10+p01−(p10−p01)²)/n`；`n=ceil(2.801585²×(p10+p01−(p10−p01)²)/δ²)`。
- 示例 δ=.05：`p10=.20,p01=.10` → **911**；`p10=.15,p01=.05` → **597**。
- 先检 `p0+δ≤1`（headroom）；否则 rate 改善不可达。

### 3.3 Fisher-z 相关系数（仅此含义）

- `N_req=2×(2.801585/δ)²+3`；δ=.05→**6,283**、δ=.10→**1,573**；n=30 时 `MDE=2.801585√(2/27)=.7625`。
- **只用于独立相关系数比较**；**不是**净效用/误选率/后悔/top-k/达标预算的通用门。
- 30 cells：对 Fisher-z 比较，δ=.05/.10 远不足（MDE .7625）；对连续配对，只有 `SD(D)≤δ√30/2.801585` 才够（δ=.05→SD≤.0978；δ=.10→SD≤.1955）且无 cluster inflation；**典型 net utility/regret SD .15–.30 → 30 远不足**。**反向不成立**：不能因 6,282 被撤而称 30 足够。

### 3.4 达标预算（E5）

- 无通用闭式；需 pilot 的 paired log-cost SD 或 event-time/ratio 分布；**独立实验/单位**，按板/日/培养聚类；预算成本要单列。
- 仅在“准确率增益近 ceiling 不可达”时另立问题；不能把 E5 当作 E1 的替代来救旧轮。

### 3.5 端点规划速查

| 端点 | 主统计 | 单位 | 需实测功能 | 允许合成 | 备注 |
|---|---|---|---|---|---|
| 净效用 | paired mean ΔU | 独立培养/细胞背景 | 是 | 算法 only | δ由效用定义 |
| 误选率 | paired risk difference | 独立单位 | 是 | 算法 only | headroom 先检 |
| 后悔 | paired mean ΔR | 独立单位 | 是 | 算法 only | 分布另估 |
| top-k | paired risk difference | 独立单位 | 是 | 算法 only | 天花板先检 |
| 达标预算 | paired log-cost/event | 独立实验 | 是 | 计算成本 only | 另立问题 |
| 机制检测 | power/FPR/J | 合成 replicate | 否 | 是 | 机制账 only |

## 4. 机制验证 vs 真实药理确认（两本账）

### 4.1 机制验证账（合成/计算）

- **证据**：明确生成过程、已知噪声、形式可辨识、检测 power/FPR、参数恢复、算法在已知 ground-truth 下行为。
- **可声称**：形式一致性、计算能力、在已知 generator 下的算法差异。
- **不可声称**：药理、真实药物决策收益、生物机制、独立确认、迁移。
- **预算**：仅 compute；无 wells/培养。
- **停止**：generator/校准/detection/parameter recovery 失败 → stop；**不得看结果改 generator**。

### 4.2 真实药理确认账（实测/预算）

- **证据**：合格 measured functional endpoint（viability/apoptosis/regrowth 等）、暴露/剂量/时间、独立培养/生物单位、独立评估、配对功效/MDE/headroom。
- **可声称**：在该资源/总体/决策下的实测结果；需独立验证与 power；不能由合成/viability 单独推机制。
- **预算**：真实 wells/plates/cultures；独立生物单位与批次；成本单列。
- **停止**：功能终点不 qualified、headroom<δ、MDE>δ、无独立培养/暴露 → stop；**不得用合成/6,282 替代**。

### 4.3 分账规则

- **决策收益/净效用/误选/后悔/预算**：药理账；合成只能做算法验证，不能升级为药理/决策证据。
- **机制/形式/检测**：机制账；不可包装成药理确认。
- **两账预算/停止分别报告**；同一实验若同时含两账，必须预注册**双重终点/双重停止**，不得用机制账的成功替代药理账。

## 5. 下一项独立研究建议（1–2 个；设计，不运行）

### N1（机制账）：合成状态依赖共享算子的决策后悔基准

- **问题**：在预注册的**合成已知 ground-truth（状态/序列依赖、非静态 S-add）**中，计划对冲突信号 + **一次反馈统一修订**策略能否在 held-out **决策后悔**上优于等计算/等信息预算基线？
- **与已停止静态 S-add 的实质区别**：动态/状态依赖算子；**决策后悔**终点；合成机制账；**不是**静态 4×4 S-add 联合矛盾存在性检验的改名重做。
- **数据**：合成 generator（已知状态转移/非加性交互/已知噪声）；**不读 O'Neil 响应**；无药理。
- **算法差异**：plan-pair conflict + unified revision of state-dependent operator vs static S-add/full retrain。
- **等预算基线**：full-history retrain、static S-add、hierarchical/EB、GP、random plan-pair、decision AL；同计算/查询预算。
- **终点/MDE/δ**：primary paired **decision regret**；δ=.05 normalized utility；headroom preflight（非 ceiling）+ paired MDE≤.05；n 按 3.1；同时报 mis-selection/detection power/FPR/parameter recovery。
- **失败类别/停止**：`design_invalid: generator/calibration`；`unreachable_gate`；`evaluation_cannot_distinguish`；`no_increment`；无检测/后悔增量→stop；**不事后改 generator**；不称药理。

### N2（药理账）：新合格功能资源上的净决策效用确认

- **问题**：在一个**新合格的实测功能资源**上，同一策略能否在配对独立生物单位上提高**净决策效用**，优于等 wells/计算的全历史/普通基线？
- **与 T1 的实质区别**：真实 measured function/暴露/独立培养；**不是** T1 合成 dual-budget；**不是**静态 S-add；药理账；决策终点。
- **数据**：新独立 viability/apoptosis/regrowth 等功能资源，匹配暴露/剂量/时间/独立培养；**当前本地不 available**；不拼 ΔEMAX；不读旧响应冒充。
- **算法/基线**：same policy vs full-history retrain/hierarchical/GP/AL/static+optimizer；等信息/预算。
- **终点/MDE/δ**：primary **net utility**；δ=.05 normalized；paired independent units；headroom/MDE preflight；独立培养/细胞背景为 n；技术重复不算 n。
- **失败/停止**：`data_unavailable`（无合格功能）、`unreachable_gate`、`evaluation_cannot_distinguish`、`no_increment`、`no_decision_benefit`；无功能/暴露/独立培养或 headroom/MDE 不过→stop；不降 δ；不用合成替代。

**顺序建议**：先做机制账 N1（合成/计算，低成本，验证算法与校准）；同时做 **AZ 2024 记录覆盖审计**（ERRATA 修正 4）以确认当前导出缺失 vs 论文已做；药理账 N2 只在合格功能/独立培养资源取得后立项。**本轮均不运行。**

## 6. 边界（写死）

- 不降旧门槛、不改旧判定（T1 partial、A.1 静态 S-add stop 保留）、不晋升代码、不恢复已停止实验、不做 A.2.3。
- 不称新颖性/机制/迁移/决策收益/独立确认；合成≠药理；技术重复≠独立培养；6,282 只作 Fisher-z；不拼 ΔEMAX。
- 设计 only；任何执行须另立预注册 + 独立挑战 + Lead 批准。

## 7. 产物

`power_scope.py`（规划算术）/`power_scope.json`/`DESIGN_SCOPE.md`/`report_scope.md`/`record_scope.md`/`usage_scope.json`；本文件为问题定义。

# DESIGN_SCOPE —— R203-P1 下一项独立研究的决策/功效预注册模板（设计，不运行）

2026-10-28。**状态：设计/预注册模板，未执行任何效果或预测。** 本文件把“先可达性、再配对功效、再两本账”的流程写成可复用模板；不降旧门槛、不改旧判定、不晋升代码、不恢复已停止实验。

## 0. 适用范围

用于**未来独立任务**的决策/机制终点设计；**不是**对 T1、A.1/A.2、D3 等已停止实验的重跑或重新解释。任何未来执行须：① 本模板预注册；② 独立挑战；③ Lead 批准。

## 1. 立项前强制预检（不可跳过）

### 1.1 端点定义冻结

- 端点 ∈ {net utility, mis-selection, regret, top-k hit, budget-to-target}（机制任务可另设 detection/parameter recovery）。
- **独立生物单位**：独立培养/细胞背景/患者来源培养/独立分化；**不是** well/技术重复/计划行/单细胞。
- **配对结构**：同一单位/同一决策上下文；重复决策作 cluster；报告 ICC/簇大小。
- **总体**：明确外推总体（哪些细胞背景/患者/培养条件）；不能把 O'Neil 39 细胞当作通用总体。
- **δ**：由决策相关性/成本定义，**先于结果**；不得事后降 δ。

### 1.2 可达性检查（二值）

```
headroom = U_max − p0
required = ceil(n × (p0 + δ))
reachable = (δ ≤ headroom) AND (required ≤ n)
```

- T1 实例：p0=.902，δ=.10，n=500 → headroom=.098，required=501 > 500 → **unreachable**；保留 partial，不降 δ。
- 若 headroom<δ：**不得**把结果解释为算法失败；可另立 **budget-to-target** 新问题并新预注册。

### 1.3 配对功效（连续/二值）

- 连续：`MDE80=2.801585×SD(D)/√n`；`n=ceil((2.801585×SD(D)/δ)²)`；cluster：`×[1+(m−1)ICC]`。
- 二值：`Var(D)=(p10+p01−(p10−p01)²)/n`；`n=ceil(2.801585²×var/δ²)`；先检 `p0+δ≤1`。
- **n 必须是独立单位**；技术重复只做精度，不作 n；cluster 要计 ICC。
- **MDE>δ** 或 **n_available<n_req** → `precision_insufficient`/`data_unavailable`，不是算法失败。

### 1.4 Fisher-z 的边界

- `N_req=2×(2.801585/δ)²+3` **只适用于独立相关系数比较**（6,283 at δ=.05；1,573 at δ=.10）；**撤通用决策门**。
- 30 cells：Fisher-z MDE=.7625（δ=.05/.10 不足）；连续配对只有 `SD(D)≤δ√30/2.801585`（δ=.05→≤.0978；δ=.10→≤.1955）且无 cluster inflation 才够；**典型 SD .15–.30 不足**；不能因撤 6,282 而称 30 足够。

## 2. 端点预注册表（每个独立研究必须填）

| 字段 | 要求 |
|---|---|
| 主端点 | 唯一 primary；其余 secondary/descriptive，预指定多重性 |
| 定义 | 效用/动作/成本/后悔/误选/top-k/预算的公式与归一化 |
| 独立单位/配对/cluster | 生物单位、同单位配对、ICC/簇大小；技术重复不作 n |
| 总体/外推 | 细胞背景/患者/培养；不可外推须写死 |
| 基线/上限 | p0/U0/ceiling；来自 pilot/已有资源，不用目标 outcomes 选 |
| headroom | `U_max−p0` 或 ceiling 等价；δ≤headroom |
| SD(D)/discordance/ICC | pilot 或预注册保守值；来源与不确定性 |
| MDE/δ/n | 按 1.3；MDE≤δ 且 n_available≥n_req |
| 基线算法 | full retrain/hierarchical/GP/AL/random/static 等；同信息同预算 |
| 预算 | wells/培养/轮次/compute；全计费；cap |
| 失败类别/停止 | unreachable_gate / precision_insufficient / evaluation_cannot_distinguish / no_increment / no_decision_benefit / data_unavailable |
| 两本账 | 机制（合成/计算）或药理（实测/预算）；不得混账 |

## 3. 两本账执行模板

### 3.1 机制账

- 数据：合成 generator（已知状态转移/噪声/非加性）；**无 O'Neil 响应、无药理**。
- 终点：detection power/FPR/parameter recovery/held-out decision regret on synthetic tasks。
- 基线：static S-add、full retrain、hierarchical、GP、random/AL；同 compute/query 预算。
- 预算：仅 compute；记录 generator seed/校准。
- 停止：generator/校准/detection 失败→`design_invalid`；无增量→`no_increment`；不得看结果改 generator/δ。
- 可声称：形式/计算能力；不可声称：药理/真实决策收益/机制/迁移。

### 3.2 药理账

- 数据：合格实测功能（viability/apoptosis/regrowth）+暴露/剂量/时间+独立培养/生物单位；**没有就 `data_unavailable`**。
- 终点：net utility primary（或预注册 preferred）；secondary mis-selection/regret/top-k/budget-to-target。
- 基线：full retrain/hierarchical/GP/AL/static+optimizer；等 wells/compute。
- 预算：真实 wells/plate/culture；独立单位计 n；成本全计。
- 停止：功能/暴露/独立培养不合格、headroom<δ、MDE>δ→stop；不降 δ；不用合成/6,282 替代。
- 可声称：在该资源/总体/决策下的实测结果；需独立验证；不能由 viability 单独推机制/迁移。

## 4. 下一项研究（设计；不运行）

### N1（机制账）

- **问题**：合成已知 ground-truth（状态/序列依赖、非静态 S-add）下，plan-pair conflict + one-feedback unified revision 是否提高 held-out **decision regret**（vs 等预算基线）？
- **数据**：合成 generator，已知状态转移/非加性/噪声；无 O'Neil；无药理。
- **算法差异**：state-dependent shared operator + unified revision vs static S-add/full retrain。
- **基线**：full retrain、static S-add、hierarchical/EB、GP、random plan-pair、decision AL；同 compute/query。
- **终点**：primary regret（δ=.05 normalized，paired synthetic units）；secondary mis-selection/detection power/FPR/parameter recovery；headroom+MDE preflight。
- **失败/停止**：generator/calibration→design_invalid；unreachable→stop；no_increment→stop claim；no post-hoc generator/δ。
- **状态**：未运行；建议独立挑战。

### N2（药理账）

- **问题**：新合格实测功能资源上，同一策略能否提高配对独立生物单位上的 **net utility**（vs 等 wells/compute 基线）？
- **数据**：新独立 viability/apoptosis/regrowth +暴露/独立培养；当前本地 **data_unavailable**；不拼 ΔEMAX。
- **算法/基线**：same policy vs full retrain/hierarchical/GP/AL/static；等预算。
- **终点**：primary net utility（δ=.05 normalized）；secondary mis-selection/regret/top-k/budget；independent cultures n。
- **失败/停止**：数据不 available/unreachable/MDE>δ→stop；不降 δ、不用合成替代。
- **状态**：未运行；仅在合格功能资源取得后立项。

## 5. 失败类别与停止（统一）

- `unreachable_gate`：headroom<δ（T1 式）；停止，不降 δ。
- `precision_insufficient`：MDE>δ 或 n 不足；停止/扩资源，不称算法失败。
- `data_unavailable`：无合格功能/独立培养/暴露；停止。
- `evaluation_cannot_distinguish`：CI 不能分辨 δ/0；不作阴性。
- `no_increment`：门通过、效应<δ且 CI 排除 0/等效；撤回增量主张。
- `no_decision_benefit`：decision endpoint 无变化；停决策创新。
- `design_invalid`：泄漏/端点混用/预算超限/generator 失败；停/重预注册。

## 6. 边界

- 设计 only；不运行效果/不拟合/不读响应/功能数据。
- 不降旧门槛/不改旧判定/不晋升代码/不恢复已停止实验；不做 A.2.3。
- 不称新颖性/机制/迁移/决策收益/独立确认；合成≠药理；技术重复≠独立培养；6,282 仅 Fisher-z。
- 任何执行须另立预注册 + 独立挑战 + Lead 批准；先完成 AZ 2024 记录覆盖审计（ERRATA 修正 4）再决定药理账。

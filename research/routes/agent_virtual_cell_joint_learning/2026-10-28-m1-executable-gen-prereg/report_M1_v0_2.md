# report_M1_v0_2 —— R204-M1.1 三项执行前必补落实报告（设计；不运行）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者（endpoint-auditor）。
**状态：M1-C1 三项必补已落实；仅设计/预注册；未运行效果比较/训练/真实数据/湿实验；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性。Stage1 执行仍须另立挑战+Lead 批准。**

## 1. 三项必补落实

| # | M1-C1 必补 | v0.2 落点 | 状态 |
|---|---|---|---|
| 1 | **G 编号不一致**（文档 G1–G5 vs JSON G1–G6） | 统一 **G1–G6**：G1 条件药效保持；G2 支持/程序；G3 投影/近似；G4 无泄漏；G5 两跑；G6 schema/预算。同步 `PROBLEM/DESIGN`、`formalism_M1_v0_2.json`、`stage1_m1_schema_v0_2.json`、失败类别/报告 | PASS |
| 2 | **等预算基线规格未冻结** | `DESIGN_M1_v0_2` §2 + `stage1_m1_schema_v0_2.json` 的 `equal_budget_baselines`：B1 random MPC/B2 max-ent/B3 conditional MC/B4 constrained SB/B5 same-info DF；目标函数/信息集/调参≤20/计算 cap/停止/等价审计逐项写死；Stage1 检查性比较可复现 | PASS |
| 3 | **Stage1 生成器/容差未冻结** | `PROBLEM_M1_v0_2` §5 + `DESIGN_M1_v0_2` §1 + schema：有限 X=4/A=3/Y=4；Pθ softmax generator seed 20261112；eval seed 20261113；r(y)=y；τ=1.0；π0 full/constrained；样本量/容差/S1-a–e 判据写死 | PASS |

## 2. G1–G6（统一表）

| 门 | 名称 | 容差/失败 |
|---|---|---|
| **G1** | 条件药效保持（target 不改 Pθ；样本不作标签；可执行条件核=Pθ） | ≤1e-12；失败 `design_invalid: calibration` |
| **G2** | 支持/程序（无支持 π*=0，受限程序合法） | exact；失败 `design_invalid: support` |
| **G3** | 投影/近似（KL/采样误差） | KL gap≤1e-8；TV≤.02；失败 `design_invalid: projection` |
| **G4** | 无泄漏（target 样本/plan 不作标签；holdout 不参与 guidance/model selection） | 结构；失败 `design_invalid: leakage` |
| **G5** | 两跑（result JSON 逐字节；telemetry 单独） | byte-identical；失败 `design_invalid: two_run_mismatch` |
| **G6** | schema/预算（schema/失败模板先写；caps 1800s/2h/8GB/0 wells） | schema+cap；失败 `design_invalid: compute_budget_exceeded` |

## 3. 等预算基线规格（摘要）

共同合同：同数据/物理反馈、同信息集（目标样本不作标签；无额外 holdout）、同计算 cap 1800s/2h/8GB/0 wells、同调参预算（每法≤20 configs）、同 seed 20261112/20261113；只比正确随机控制目标；等效/≤容差→`rename_maxent`/撤主算法。

| id | 方法 | 实现/目标 | 调参/计算 | 审计 |
|---|---|---|---|---|
| B1 | random MPC | legal actions 均匀随机 rollout；不 target 选动作 | 0 configs；20,000 actions | 只检测“赢随机” |
| B2 | max-entropy control | `π_ME∝π0 exp(E_P[r]/τ)` 闭式 | τ 固定；精确 | 与候选 π* 解析等价→rename_maxent |
| B3 | conditional density+MC | 每动作 20,000 采样估计均值，plug-in | 0 configs；20k/动作 | SE>0.02→precision；TV≤.02 等价 |
| B4 | constrained SB | one-step entropic OT：`min_R KL(R||π0⊗Pθ)`，约束 action marginal/exit target | ≤5 ε configs；Sinkhorn | 不收敛/约束违反→projection；等效不称增量 |
| B5 | same-info DF | 同 `(X,a,y)` 训练条件生成/DF 代理；target guidance 只在 planning | ≤20 configs；同 cap | 训练/生成/泄漏→calibration/leakage；等效不称增量 |

**Stage1 只做检查性比较，不输出效果/增益。**

## 4. Stage1 生成器/容差（冻结）

| 项 | 值 |
|---|---|
| 有限系统 | X=4（0..3）、A=3、Y=4（0..3） |
| Pθ | 每个 (x,a) logits~Normal(0,0.6²)，softmax；generator seed **20261112** |
| eval seed | **20261113** |
| reward | `r(y)=y`；有界 |
| τ | **1.0** |
| π0 | full `[1/3,1/3,1/3]`；constrained `[.5,.5,0]`；action2 无支持 |
| 版本 | full + constrained；同一 Pθ 表 |
| 样本量 | S1-a 20,000/x；S1-b 20,000/condition；S1-d/e 精确 |
| 容差 | S1-a TV≤.02；S1-b max TV≤.02；S1-c ≤1e-12；S1-d exact；S1-e KL gap≤1e-8 |
| 失败 | projection/calibration/support/leakage/two_run_mismatch/compute_budget_exceeded |

## 5. 算术复核/两跑/计时

- 反例：target A 概率 **0.99665795**、B **0.00334205**；E_A=1<E_B=2；π*_B≈**0.73105858**；只证风险。
- 投影：`KL(Rπ*||Q_g)=0.24038053 < KL(uniform)=0.45067680`；可执行条件核差 **1.11e-16**；target joint within-action tilt **0.43647** 标为不可执行 proposal。
- 支持/Doob：无支持 π*=0；Doob 核非药物。
- **两跑**：`formalism_M1_v0_2.json` 逐字节一致 **`B72986535F3839E2BE058250DEA9D61F560DF0243AFF86329845DD361988A7AE`**；timing 单独。
- pilot：**5e-6 s/rep**（10 reps）；projected **0.0053 s**；caps 1800 s/2 h/8 GB；0 wells；实际远低。
- **未运行效果/未比较方法增益/未称新颖性**。

## 6. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_v0_2.md` | 见 usage |
| `DESIGN_M1_v0_2.md` | 见 usage |
| `formalism_M1_v0_2.py` | 见 usage |
| `formalism_M1_v0_2.json`（两跑一致） | `B72986535F3839E2BE058250DEA9D61F560DF0243AFF86329845DD361988A7AE` |
| `stage1_m1_schema_v0_2.json` | 见 usage |
| `timing_M1_pilot_v0_2.json` | 见 usage |
| `report_M1_v0_2.md` / `record_M1_v0_2.md` / `usage_M1_v0_2.json` | 报告/记录/用量 |

## 7. 建议/边界

- **三项必补已修；建议轻量复核 G 表/基线表/生成器容差表后，Lead 可批准 M1 Stage1 合成实现（仅机制账、compute-only、0 wells）**；本文件不批准 Stage2/3/真实数据/效果。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 一步投影=最大熵控制、SB 近邻；公式不称创新；候选新意未验证。
- N1 `no_increment` 仅其 own primary，不作 M1 证据；M2 机制账不混同。
- Stage1 执行仍须另立预注册+独立挑战+Lead 批准；Stage2/3 需要合格数据（当前 data_unavailable，C203）。

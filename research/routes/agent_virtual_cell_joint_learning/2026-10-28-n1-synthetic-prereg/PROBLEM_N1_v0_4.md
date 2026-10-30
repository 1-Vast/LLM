# PROBLEM_N1_v0_4 —— R203-N1.3：非静态 S-add 合成机制预注册（v0.4 V4 独立验证修正；设计，不运行效果）

2026-10-28。对象：R203-N1（机制账）。本文件修正 v0.3（[PROBLEM_N1_v0_3.md](PROBLEM_N1_v0_3.md) `E404C5FE…`，保留不改）。依据：N1.2-C1 复核（revise，3 必改）、[challenge_N1_v0_3.md](challenge_N1_v0_3.md)、R203-P1 链。
**状态：设计/预注册草案 v0.4；未运行任何效果比较/结论；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。**

## 0. 3 必改落实（v0.3 → v0.4）

| # | N1.2-C1 问题 | v0.4 落实 |
|---|---|---|
| ① **V4 不是独立 gate**（首轮 FAIL −456.6 后改模型、同 seed=20261061 重跑 PASS=post-hoc model selection） | **V4 最终模型规格在运行前冻结**（`V4_MODEL_SPEC`：soft state responsibilities + weighted ridge λ=1.0；features 21+12；初始化 1/S；更新规则 forward posterior；无调参）；**独立 seed=20261062、200 组全新训练样本**重跑 V4：**mean ΔELPD=503.0425、SE=64.4214、95% CI=[376.779, 629.306] → PASS**；**首轮 FAIL −456.6、oracle 诊断 +4147.6、模型改动均披露**；**只有独立 V4 PASS 作为 rename_static_Sadd gate**（dev seed 20261061 的 306.16 标为 post-hoc 诊断，不作 gate）；oracle-state 检验（seed 20261063：4988.236/248.226/[4501.72,5474.75] PASS）作为补充/降级 fallback，**不用于替换独立 gate** |
| ② **代码注释残留 359/288** | `generator_n1_v0_4.py` 注释改为 2-active-basis h 的正确维数（compact 107/312、full 143/600）；**grep 359/288 已无残留**；129 仅在明确标注的 v0.1 历史算术上下文出现，不作为 full 摘要 |
| ③ **PROBLEM/DESIGN 未披露 V4 adaptive 历史** | 本文件 §4 写清：首轮 FAIL −456.6、oracle 诊断 +4147.6、filter 从等权→soft-responsibility/weighted ridge(λ=1) 的改动、规则/阈值/seed/n_rep/held-out 未改但**模型实现是在看到 V4 失败后改变**；并报告**独立 seed=20261062 新样本 PASS**（503.04/64.42/[376.78,629.31]）作为 gate 依据；dev seed 20261061 的 306.16 明确标为 post-hoc 诊断 |

## 1. 与已停止静态 S-add 的实质区别（不变）

- 静态 S-add（A 线对象）：`y=f_a(d_a)+g_b(d_b)+ε`；无状态/历史/共享动态核/conflict。N1 在 `S=1,P=I,β_s=γ_s=0,h=0` 时严格退化。
- N1 非静态生成：S=3 隐藏状态；state-specific 历史/动作依赖转移（β_s=[−1.5,0,1.5]、γ_s=[1,−1,0]）；计划对共享同一轮 state；状态依赖 f/g/h（plan-pair conflict）；一次反馈统一修订；held-out decision regret 终点。
- **V1–V4 + `design_invalid: rename_static_Sadd`**：V1 状态可检测；V2 历史/动作依赖（KL≥.10）；V3 plan-pair conflict（E_h≥.20）；**V4 独立验证 PASS**（§4）。任一失败即停。

## 2. 生成器冻结（v0.4）

| 组件 | 冻结值 |
|---|---|
| **n_units** | **300（单一值；全部文件一致）** |
| 隐藏状态/序列 | S=3、π0~Dirichlet(1,1,1)；T=6（fit 4/held-out 2）；每轮 1 反馈 |
| 计划/菜单/剂量/噪声 | universe 12 plans（A=3×B=4）；m=5；4×4 归一化剂量；σ=.15 |
| 算子 | f/g 三基；h 两活跃基（double-centered）；状态依赖 |
| ground-truths | GT-static（S=1,β=γ=0,h=0）→ G1；GT-nonstatic（S=3,β_s/γ_s≠0,h≠0,Δ_f/σ=2）→ G2/V4 |
| pilot telemetry（v0.4 final implementation） | **per-rep 0.05622 s、main 25.3 s、memory 0.037 GB**；逐方法 B1 .00376/B2 .00254/B3 .00251/B4 .03587/B5 .00038/B6 .00275/M .00841 s；B2 等价审计 PASS |

## 3. 可辨识性/gauge（v0.4 唯一维数）

- compact 6-pair（v0.1 代表设计）：params **107**、obs **312**、rank **95**、nullity **12**（参数 gauge 3+结构 9）。
- **full 12-pair（执行宇宙）：params 143、obs 600、rank 140、nullity 3（参数 gauge=3）** → 可辨识维 140。
- 函数空间冗余：compact 3+126=**129**（v0.1 历史算术）、full 3+252=**255**；**不作为参数方向**；离散状态标签 S! 由 Var 排序固定。
- **G3（只依 full 143/600/140/3）**：参数恢复门（状态核差相关≥.90、transition TV≤.10、β_s/γ_s CI 不含 0、interaction 相关≥.90）；只在可辨识子空间（140 维）判定；目标不可辨识→`design_invalid: nonidentifiable`。

## 4. V4 独立验证（pre-effect gate；已实际执行）

- **最终模型规格（运行前冻结，见 `V4_MODEL_SPEC` / `V4_validation_v0_4.json`）**：static S-add ridge（21 特征，λ=1e-2）vs nonstatic state-dependent filter（33 特征=21+12 interaction，soft state responsibilities 作回归权重，weighted ridge λ=1.0；forward posterior 更新；初始化 1/S；无调参）。
- **首轮历史（披露）**：初始 filter 把观测等权分配给三状态 → V4 **FAIL（mean −456.6）**；oracle-state 诊断 **+4147.6**（确证生成器状态信号强）；随后改 soft-responsibility/weighted ridge；**规则/阈值/seed/n_rep/held-out 未改，但模型实现是在看到 V4 失败后改变**；dev seed=20261061 重跑得 306.1577/65.4612/[177.856,434.459] PASS —— **该结果标为 post-hoc 诊断，不作 gate**。
- **独立验证（gate 依据）**：**seed=20261062、n_rep=200、全新样本（非 20261061、非同一 200 组）**：**mean ΔELPD=503.0425、SE=64.4214、95% CI=[376.779, 629.306] → PASS**（mean>0 ∧ mean≥2SE ∧ CI lower>0）。
- **补充 oracle gate（fallback，不替代独立 V4 gate）**：seed=20261063、n_rep=200：mean **4988.236**、SE **248.226**、95% CI **[4501.72, 5474.75]** → PASS；若未来独立 V4 无法验证，可降级 V4 为诊断并使用该 oracle 统计（均值≥2SE 且 CI lower>0）。
- **失败路径**：独立 V4 FAIL 且 oracle FAIL → `design_invalid: rename_static_Sadd`、不进入效果；不得同 seed post-hoc PASS 当 gate、不得迭代到通过。

## 5. 主终点/headroom/MDE（不变）

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better）；δ=**0.05** normalized；菜单 m=5、U∈[0,1]、held-out 仅评价；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- **MDE**：`MDE80=2.801585·SD/√n_eff`，n_eff=300/2.2=**136.36**；SD=.20 → **MDE80=0.04798≤.05**；n_req=**278≤300**。
- **headroom**：GT-nonstatic 目标 0.10≥δ；GT-static≈0；headroom<δ→`unreachable_gate`；近满分→另立 budget-to-target；不静默换端点/不降 δ。

## 6. 等 compute/query 基线 + B2 等价审计（不变）

B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method；统一 prior/初始数据/feedback/query T=6/调参≤20/特征信息/seed/wall。**B2 等价审计 PASS**（same initial-data hash、menus、query count=6、prior、tuning=20、shared seed）；审计失败→`generator_misspecified`；任何基线等效→`no_increment`。

## 7. 资格门/失败类别/预算

- **G1** 实测 point .0488（976/20000）≤.05、Wilson .05187≤.075 → PASS；**G2** powers 1.000/1.000/1.000 → PASS；**G3** full 143/600/140/3 + 参数恢复门；**G4** 无泄漏；**G5** 两跑逐字节；**G6** schema；**G7** 预算（v0.4 pilot：per-rep .05622 s、main 25.3 s、memory .037 GB ≤caps 1800 s/2 h/8 GB）→ PASS；**V4** 独立验证 PASS（§4）。
- **失败类别统一**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`；失败只写 `design_invalid`、不报 regret/效果。
- **预算**：main n_units=300、R=50、methods=7、T=6；wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only；两跑/schema/无 telemetry（结果 JSON）。

## 8. 边界

机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复停止实验；不改旧门槛/判定；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本文件不运行效果。

# DESIGN_N1_v0_4 —— R203-N1.3 执行设计（V4 独立验证修正；机制账；不运行效果）

2026-10-28。修正 v0.3（[DESIGN_N1_v0_3.md](DESIGN_N1_v0_3.md) `A65158D7…`，保留不改）。依据：N1.2-C1 复核（3 必改）、[PROBLEM_N1_v0_4.md](PROBLEM_N1_v0_4.md)、`generator_n1_v0_4.json`、`V4_validation_v0_4.json`、`timing_n1_pilot_v0_4.json`、R203-P1 链。
**状态：预注册草案 v0.4（未执行效果）。N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本文件不含效果结论。**

## 0. 3 必改落实

| 必改 | v0.4 落实 |
|---|---|
| ① V4 独立验证 | **V4_MODEL_SPEC 在运行前冻结**（soft responsibilities/weighted ridge λ=1、features 21+12、初始化 1/S、forward posterior、无调参）；**独立 seed=20261062、200 组新样本 V4 PASS：mean 503.0425、SE 64.4214、95% CI [376.779, 629.306]**；**首轮 FAIL −456.6、oracle 诊断 +4147.6、模型改动全披露**；dev seed 20261061 的 306.16 标为 post-hoc 诊断，**不作 gate**；oracle gate（seed=20261063：4988.236/248.226/[4501.72,5474.75]）仅 fallback/补充 |
| ② 代码注释残留 | `generator_n1_v0_4.py` 注释/摘要修正为 2-active-basis h（compact 107/312、full 143/600）；grep 无 359/288 作为 full 摘要；129 仅明确标注 v0.1 历史算术 |
| ③ PROBLEM/DESIGN 披露 | PROBLEM §4 / DESIGN §4 写入首轮 FAIL、oracle、filter 改动、post-hoc 性质、独立验证 PASS 数字；执行者可见完整 adaptive 历史 |

## 1. 冻结对象

- **n_units=300**（唯一值）；S=3、T=6（fit 4/held-out 2）、m=5、plans=12（A=3×B=4）、4×4 剂量、σ=.15、f/g 三基、h 两活跃基、state-specific β_s/γ_s 转移。
- Ground truths：GT-static（S=1,β=γ=0,h=0）→ G1；GT-nonstatic（S=3,β_s/γ_s≠0,h≠0,Δ_f/σ=2）→ G2/V4。
- 主终点：paired held-out regret `D_i=R_i(M)−R_i(B2)`，δ=.05 normalized；U∈[0,1]；菜单 m=5；held-out 不更新；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- 预算：n_units=300、R=50、methods=7、T=6；wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only。

## 2. 预检（不变）

- headroom：GT-nonstatic 目标 0.10≥δ；GT-static≈0；执行前 calibration pilot 估 headroom/SD(D)。
- MDE：`MDE80=2.801585·SD/√n_eff`，n_eff=136.36；SD=.20→**0.04798≤.05**；n_req(cluster)=**278≤300**；SD=.30→623>300→precision_insufficient。
- 不通过：headroom<δ→unreachable_gate；MDE>δ/n_req>300→precision_insufficient；不降 δ、不静默加 n、不换端点。

## 3. 可辨识性/gauge（唯一维数）

- compact 6-pair：107/312/rank95/nullity12（参数 gauge 3+结构 9）。
- full 12-pair（执行宇宙）：**143/600/rank140/nullity3（参数 gauge=3）**；可辨识维 140；函数空间冗余 compact 129（v0.1 历史算术）/full 255（非参数方向）。
- **G3**：full 143/600/140/3；参数恢复门（状态核差相关≥.90、transition TV≤.10、β_s/γ_s CI 不含 0、interaction 相关≥.90）；仅可辨识子空间判定；目标不可辨识→`design_invalid: nonidentifiable`。

## 4. V4（独立验证 gate；已实际执行）

- **模型规格冻结（V4_MODEL_SPEC）**：static S-add ridge（21 特征，λ=1e-2）vs nonstatic filter（33 特征，soft state responsibilities 权重，weighted ridge λ=1.0，forward posterior，初始化 1/S，无调参）。
- **历史披露**：首轮 FAIL −456.6（等权 filter）→ oracle 诊断 +4147.6 → 改 soft-responsibility/weighted ridge（规则/阈值/seed/n_rep/held-out 未改，但模型实现是看到失败后改变）→ dev seed=20261061 PASS 306.1577（**post-hoc 诊断，不作 gate**）。
- **独立验证（gate）**：**seed=20261062、n_rep=200 新样本** → **mean 503.0425、SE 64.4214、95% CI [376.779, 629.306] PASS**；只有该独立 PASS 作为 `rename_static_Sadd` gate。
- **fallback oracle gate**：seed=20261063、n_rep=200 → 4988.236/248.226/[4501.72,5474.75] PASS；仅当独立 V4 无法验证时降级使用（V4→诊断），不得同 seed post-hoc PASS 作 gate、不得迭代到通过。
- **失败路径**：独立 V4 FAIL 且 oracle FAIL → `design_invalid: rename_static_Sadd`、不进入效果。

## 5. 方法/基线（不变；B2 等价审计）

统一 prior/初始数据/feedback（每轮 1 次）/query T=6/调参≤20/特征信息/seed/wall：B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method。**B2 等价审计 PASS**（initial-data hash、menus、query count=6、prior、tuning=20、shared seed）；失败→`generator_misspecified`；任何基线等效→`no_increment`。

## 6. 校准/资格门 G1–G7 + V4（先于效果；失败只写 design_invalid）

| 门 | v0.4 规则 | 失败类别 |
|---|---|---|
| G1 | point≤.05（实测 .0488）且 Wilson upper≤.075（实测 .05187） | `calibration_failed`/`rename_static_Sadd` |
| G2 | GT-nonstatic power（state/interaction/history）≥.80−mc_tol；实测 1.000/1.000/1.000 | `calibration_failed` |
| G3 | full 143/600/140/3 + 参数恢复门 | `nonidentifiable` |
| G4 | 无泄漏 | `leakage` |
| G5 | 两跑逐字节 | `design_invalid` |
| G6 | schema/失败模板 | `design_invalid` |
| G7 | 预算（v0.4 pilot：.05622 s/rep、25.3 s main、.037 GB）≤caps | `compute_budget_exceeded` |
| V4 | **独立 seed 20261062 PASS**（503.04/64.42/[376.78,629.31]） | `rename_static_Sadd` |

## 7. 预算与运行

- **pilot telemetry（v0.4 final implementation）**：per-rep **.05622 s**、projected main **25.3 s**、memory **.037 GB**；逐方法 B1 .00376/B2 .00254/B3 .00251/B4 .03587/B5 .00038/B6 .00275/M .00841 s；B2 审计 PASS；G7 引用同一 snapshot。
- **主预算**：n_units=300、R=50、methods=7、T=6、每轮 1 反馈；caps wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only；不使用 A/B 资源。
- 两跑逐字节一致（结果 JSON 无 telemetry；timing/telemetry 单独文件）；schema/失败模板预注册。
- **失败类别**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 任何 N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本文件不运行。

## 8. 批准清单

1. V4 独立验证：V4_MODEL_SPEC 运行前冻结；首轮 FAIL/oracle/模型改动完整披露；**独立 seed=20261062 新样本 PASS（503.04/64.42/[376.78,629.31]）**作为 gate；dev post-hoc 306.16 不作 gate；oracle fallback 写死。
2. 代码注释/摘要无 359/288 作为 full 摘要；full 143/600/140/3 唯一维数；函数空间 129/255 单列。
3. n_units=300/MDE .04798/n_req278；G1 .0488/.05187；G2 1.000；B1–B6/B2 审计；v0.4 pilot 25.3 s/.037 GB；caps 1800 s/2 h/8 GB/0 wells；两跑/schema/失败类别。
4. 机制账边界：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复停止实验；不改旧判定。

# report_n1_gates —— R203-N1-IMPL 实现+资格门报告（**仅机制账；不报效果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 Lead `DECISION_R203_N1_PREREG.md`（SHA `930F1567…`）批准范围：**仅 N1 执行预注册实现+资格门**；不批效果执行/外推。**本报告只报告实现与资格门；未运行方法比较、未报告 regret/top-k/selection accuracy、未读真实响应、未用 A/B 资源、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码。**

## 0. 判定

**N1 冻结 generator+七方法实现完成；V1–V4 + G1–G7 资格门全部 PASS；`verdict = qualification_pass`。**
- V4 **只用独立 seed=20261062/n=200 作 gate**：mean ΔELPD **503.04246827**、SE **64.42138097**、CI95 **[376.77888173, 629.30605481]** → PASS。
- G1：k=**976/20000**，point **0.0488≤.05**，Wilson upper **0.05187≤.075** → PASS。
- G2：powers state/interaction/history **1.000/1.000/1.000** → PASS。
- G3：full **143/600/140/3**；可辨识子空间恢复 state kernel corr **0.94317**、interaction corr **1.0**、transition TV **0.0** → PASS。
- G4/G6/G7 PASS；G7 final pilot projected main **20.48 s**、mem **0.04 GB**、B2 audit PASS；caps 1800s/2h/8GB/0 wells。
- **G5 两跑 `n1_gates.json` 逐字节一致** SHA256 **`529C1D2EE1E4B4039F4BBD10115C362EEE419D4BEF62A07FEC5A3C4046CBA0E0`**。
- **未运行效果比较/regret/top-k/selection accuracy**；失败类别无（qualification_pass）。

## 1. 冻结链/实现范围

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_4.md` | `5C513D9461FAEDBD3372463A4FDD1868C927EB48501BC0CDEB7643FF6FA0649A` |
| `DESIGN_N1_v0_4.md` | `94BAB8052EF4864BD745986326F4869D9054C2935794FEDAD8733733B57C029C` |
| `generator_n1_v0_4.py`（只读导入；未改） | `AA5D454A82366BF3B7FC9E7F67FAA3499098621FAD45B84804485550E6EDCC97` |
| `generator_n1_v0_4.json` | `35E41136E344AAF6C51A73B19418FF5CBEAD9460697BB8B1EE92F9E16D610263` |
| `V4_validation_v0_4.json` | `254BEBAB201AA8A0EA33AEA8A47BC7D37A99ADE1436319D159603061DC8E2ECF` |
| `timing_n1_pilot_v0_4.json` | `A4C7E0F675B0020B99A93CC022572B3E85F30A26E391493AF45FAA3C005586C7` |

- 实现方式：新目录 `run_n1_gates.py` **只读导入冻结 `generator_n1_v0_4.py`**（回放 S=3 隐藏状态/state-specific β_s/γ_s/plan-pair 共享同轮 state/状态依赖 f/g/h/两套 GT/gauge 固定），运行 V4/V1–V3/G1–G4/G7 资质；未改冻结 generator/λ/特征/初始化/V4 spec；B1 full retrain、B2 static S-add、B3 EB、B4 GP、B5 random、B6 decision AL、M=N1 均由冻结模块提供（`METHOD_CLASSES`）。
- 统一 prior/初始数据/feedback（每轮 1）/query T=6/调参≤20/特征/seed 由冻结模块固定；B2 等价审计 PASS（G7 pilot）。
- 未用 A/B 资源；0 wells；compute-only；未读 O'Neil/真实响应。

## 2. V1–V4（逐项）

| 门 | 结果 |
|---|---|
| **V1 状态可检测** | PASS：Δ_f/σ_max **11.6554≥2**；LRT power state **1.000≥.80**（df=3、n_mc=20000、noncentrality=153600）。 |
| **V2 历史/动作依赖** | PASS：action/history context vs baseline max KL **0.61703≥.10**；β_s design **[-1.5,0,1.5]**、γ_s **[1,-1,0]**（各 2 个非零状态）；β/γ CI-excludes-0 由 G3 可辨识子空间精确恢复覆盖。 |
| **V3 plan-pair conflict** | PASS：E_h_max **0.50891≥.20**；interaction LRT power **1.000≥.80**（noncentrality=7680）。 |
| **V4 static cannot absorb（唯一 gate）** | PASS：**独立 seed=20261062、n_rep=200、n_units=8**；mean ΔELPD **503.04246827**、SE **64.42138097**、CI95 **[376.77888173, 629.30605481]**。**dev seed=20261061 仅 post-hoc、oracle seed=20261063 仅 fallback，未用于 gate；本次未运行/未替代。** |

## 3. G1–G7（逐项）

| 门 | 结果 |
|---|---|
| **G1 GT-static FPR** | PASS：LRT χ²₃ α=.05，n_mc=20000；k **976**、point **0.0488≤.05**、Wilson upper **0.05187354≤.075**（point gate 收紧，mc_tol 仅 CI/敏感性）。 |
| **G2 GT-nonstatic power** | PASS：state/interaction/history powers **1.000/1.000/1.000**，mc_tol **0.005657**，均≥.80−mc_tol。 |
| **G3 identifiability/parameter recovery** | PASS：full **143/600/140/3**（可辨识维 140，gauge 3）；无可调参数可辨识性目标；noiseless linear recovery on identifiable subspace + additive gauge fixing：state kernel corr **0.94317≥.90**、interaction corr **1.0≥.90**、transition TV **0.0≤.10**。不可辨识方向按 gauge/结构处理；未发现非可识别目标。 |
| **G4 无泄漏** | PASS：特征不含 state/truth；methods update 签名不接收 truth；B2 等价审计 PASS；oracle 仅评估；成本账全含；无 A/B 资源。 |
| **G5 两跑逐字节** | PASS：两跑 `n1_gates.json` 逐字节一致 SHA `529C1D2E…`；wall/计时只在 `timing_n1_gates.json`。 |
| **G6 schema** | PASS：required top/gate keys 完整；`schema_n1_gates.json`；无 effect-result 字段。 |
| **G7 final implementation pilot** | PASS：真实 generator+7 methods pilot（2 reps×20 units）；per-rep **0.0455 s**、projected main **20.48 s**、mem **0.04 GB**、B2 audit PASS；caps **1800 s/2 h/8 GB/0 wells**；projected_pass=true。 |

- **G7 说明**：pilot 投影定义按冻结实现 `run_pilot` 的 main scale（n_units/20 × 50/n_rep ×1.2）；只计时/审计，不读效果。
- 总 gate-only wall：run1 **3.74 s**、run2 **3.70 s**（V4 ~3.3s 为主；无方法效果比较）。

## 4. 两跑/实现备注

- 两跑结果 JSON 逐字节一致；V4 独立 seed 固定；V1/V2/V3/G1–G3 使用固定诊断 seed（见脚本）；G7 pilot 计时仅在 timing 文件。
- 实现采用**只读导入冻结 generator**，不复制/改冻结代码；G3 的 recovery 是结构/可辨识子空间检查，不是效果指标；V2 KL 是基于冻结 β_s/γ_s 的 transition context 诊断；G7 为真实最终实现 pilot。
- 未报告 method comparison/regret/top-k/selection accuracy；无失败类别；若任何门失败只写 `design_invalid`。

## 5. 产出 SHA

| 文件 | SHA256 |
|---|---|
| `run_n1_gates.py` | `D2AA831F26AE8882F2B5B60C4C3FB2ACCAEA327AA381A4F949D32D23B276D7B8` |
| `n1_gates.json`（两跑一致） | `529C1D2EE1E4B4039F4BBD10115C362EEE419D4BEF62A07FEC5A3C4046CBA0E0` |
| `n1_gates_rows.csv` | `78457E1F97B85D1D70918BFCE28AB0E79123225E5D9BD3589EACF951B587F6EB` |
| `timing_n1_gates.json` | `5A52E42F845A4127E2FB09E0DA9061FB591C83DE474E8C5286380CF17F7F75AC` |
| `schema_n1_gates.json` | 见文件 |
| `report_n1_gates.md` / `record_n1_gates.md` / `usage_n1_gates.json` | 见各文件 |

## 6. 边界/建议

- **仅机制账（合成、compute-only、0 wells）**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧门槛/判定；不恢复停止实验。
- **V1–V4/G1–G7 全 PASS**；N1 效果执行（方法比较/regret）**须另立执行预注册 + 独立挑战 + Lead 批准**；本报告不批准/不运行效果。
- 建议：可进入效果执行预注册的**独立挑战**阶段；执行前需 Lead 明确批准，且仍不得外推真实决策/生物结论。

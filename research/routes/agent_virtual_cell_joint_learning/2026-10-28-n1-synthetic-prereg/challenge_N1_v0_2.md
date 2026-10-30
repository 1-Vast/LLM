# R203-N1.1 轻量复核（task-134）：v0.2 修正预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 N1、不运行效果结论/不拟合/不读 O'Neil）。对象：[PROBLEM_N1_v0_2.md](PROBLEM_N1_v0_2.md)（SHA `C66FD8F4…`）、[DESIGN_N1_v0_2.md](DESIGN_N1_v0_2.md)（`1B179AB9…`）、[generator_n1_v0_2.py](generator_n1_v0_2.py)（`F1EFD8D8…`）、[generator_n1_v0_2.json](generator_n1_v0_2.json)（`045DEE05…`）、[timing_n1_pilot_v0_2.json](timing_n1_pilot_v0_2.json)（`7F57BB1D…`）、report/record/usage v0.2、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能提交 approve_n1_v0_2_to_lead；也不是 stop）。**

v0.2 已修好 v0.1 的三大实质问题：
- **n_units/MDE**：全部文件冻结 **n_units=300**（无360）；`n_eff=300/2.2=136.36`；SD=.20→**MDE80=.04798≤.05**；n_req=278≤300；公式/文件一致 ✓。
- **G1**：χ²_df=3、crit=7.8147279、α=.05、n_mc=20,000、mc_tol=.003082；实测 **k=976/20000、point=.0488、Wilson 95% upper=.05187354**；按预注册门（point≤α+mc_tol 且 Wilson upper≤.075）PASS；G2 三项 power=1.000 ✓；`chosen_amplitudes_meet_gates` 由实测决定 ✓。
- **G3/V4/pilot**：full 12-pair 143 params/600 obs/rank140/nullity3；compact 107/312/95/12；参数 gauge S=3、函数空间交互冗余 129/255；V4 ELPD 规则已冻结；真实 pilot（7方法含B2）+ B2 等价审计 PASS；caps 1800s/2h/8GB/0 wells ✓。

**但仍有两处可复核的内部矛盾，且都在“冻结摘要/预算”层，必须先修：**
1. **full-h 参数化/观测数在文档摘要里仍是 v0.1 的 359/288**：`PROBLEM_N1_v0_2.md §1` 的修正表写 `f27+g36+h288+transition8=params 359、obs 288`；`DESIGN_N1_v0_2.md §0` 也写 `params=359、obs=288`；但 `PROBLEM §3`/`DESIGN §3`/`generator JSON` 实际是 **full 12-pair params=143、obs=600、rank=140、nullity=3**。**同一份预注册出现两套参数维数**，G3/gauge 的批准依据不一致，必须统一。
2. **真实 pilot 数字在文本与 timing JSON 之间不一致**：`PROBLEM §8`/`DESIGN §8`/report 写 **per-replicate .0282 s、main≈12.7 s、内存 .038 GB**，逐方法计时写 B1 .0005/B2 .00201/B3 .0015/B4 .01914/B5 .00025/B6 .0015/M .00327；但 `timing_n1_pilot_v0_2.json` 实际是 **per_replicate_total .02603、projected_wall 11.72 s、memory .037 GB**，逐方法 B1 .00109/B2 .00133/B3 .001/B4 .01731/B5 .00083/B6 .00139/M .00308。两者都远低于 caps，但**冻结文本必须与 telemetry 一致**，G7/预算不能引用另一套数字。

在这两处修好前，**不能提交 Lead 批准 N1 执行预注册**。

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | n_units/MDE 统一 | **PASS** | 全文件 n_units=300；n_eff=136.36；MDE80=.04798≤.05；n_req278≤300；`MDE=2.801585·SD/√n_eff` 写清；300/360 冲突已消除 ✓。 |
| ② | G1/G2 | **PASS（建议收紧 point 门）** | χ²3 crit 7.8147279、n_mc20,000、k976、point .0488、Wilson upper .05187、mc_tol .003082；按预注册规则 PASS；G2 power 1.000。注：规则允许 `point≤.05308`（α+mc_tol），实际 .0488 低于 .05；建议把 point 门收紧到 ≤.05，Wilson upper≤.075，以免名义 FPR 被 MC 容差放宽。 |
| ③ | gauge/Jacobian | **FAIL（文档摘要矛盾）** | 实际/代码/JSON：compact 107/312/95/12（3 gauge+9 structural），full 143/600/140/3（参数 gauge=3）；函数空间 compact 126+3=129、full 252+3=255；但 **PROBLEM §1/DESIGN §0 仍写 full params=359、obs=288、gauge=129**，与 §3/JSON 的 143/600/140/3 冲突；必须统一。 |
| ④ | V4 | **PASS（规则冻结）** | static ridge vs nonstatic filter；fit T=4、ELPD T_hold=2；GT-nonstatic n_rep=200、seed=20261061；ΔELPD=non−static、SE=sd/√200；PASS ⇔ mean>0 ∧ mean≥2SE ∧ 95%CI lower>0；失败→rename_static_Sadd；V1–V4 全 PASS 才进入效果 ✓。当前尚未实测（执行前 gate），不是本次审批的效果结果。 |
| ⑤ | 真实 pilot/B2 | **FAIL（数字不一致）** | 真实 generator+7方法含B2、n=20/R=2/T6/m5/plans12、B2 等价审计（同 initial-data hash/menus/query6/prior/tuning20/seed）PASS；但 timing JSON 实际 **.02603s/rep、11.72s main、.037GB**；文本/report 写 **.0282/12.7/.038**；逐方法计时也不同；G7 应引用实际 telemetry，不能两套。 |
| ⑥ | 边界 | **PASS** | 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；N1 效果执行另立预注册+挑战+Lead 批准；0 wells/compute-only ✓。 |
| ⑦ | 总判决 | **revise** | 见 §2–§3。 |

## 2. 关键算术/一致性

### 2.1 n_units/MDE（正确）
- n_units=300；deff=1+(m−1)ICC=1+4×.30=2.2；n_eff=300/2.2=136.3636；
- MDE80=2.801585×.20/√136.3636 = **.04798268≤.05**；
- n_req(SD=.20)=ceil((2.801585×.20/.05)²)=126；cluster×2.2=277.2→**278≤300**。
- 与 PROBLEM/DESIGN/JSON/record 一致；v0.1 的 300/360、√n_units 错误已修。

### 2.2 G1（实际 PASS，但 point 门可收紧）
- crit=χ²_{.95,3}=**7.8147279**；n_mc=20,000；k=976；point=**0.0488**；Wilson 95% upper=**0.05187354**；mc_tol=2√(α(1−α)/20000)=**0.003082**。
- 预注册门：point≤α+mc_tol=.053082 ∧ Wilson upper≤.075；实际 .0488/.0519→PASS；G2 power1.000。
- 建议把 point 门收紧为 **point≤.05**（实际 .0488 通过）而非 .05308；否则名义 5% FPR 可被 MC 容差放宽。Wilson upper .075 仍很宽，但作为 MC 上界可接受并已预注册。

### 2.3 gauge/Jacobian（实际正确，摘要需改）
- compact 6-pair：params **107**、obs **312**、rank **95**、nullity **12**（参数 gauge 3 + 结构 9）；full 12-pair：params **143**、obs **600**、rank **140**、nullity **3=加性参数 gauge**；可辨识维 140。
- 函数空间交互冗余：compact 6-pair `(2K−1)·pairs·S=7×6×3=126`，+加性3=**129**；full `7×12×3=252`，+3=**255**；**不是参数空间的 gauge**。
- 但 `PROBLEM §1`/`DESIGN §0` 仍写 **full params=359/obs=288/gauge=129**；这与实际 143/600/140/3 冲突；必须把摘要改成“full 143/600/rank140/nullity3；参数 gauge=3；函数空间 compact129/full255”。

### 2.4 pilot/B2（实际通过，数字需统一）
- `timing_n1_pilot_v0_2.json`：pilot n=20/R=2/T6/m5/plans12；per_replicate_total=**.02603 s**；main projected **11.72 s**；memory observed **.037 GB**；B2 audit PASS（hash/menus/query6/prior/tuning20/seed）。
- 文本/report 写 .0282/12.7/.038；逐方法计时也不同；必须统一到 telemetry 实际值；G7 用实际投影；任何 <caps 均成立，但不能两套数字。

## 3. 必改（≤5，Lead 批准 N1 执行预注册前）

1. **统一 full-h 参数化摘要**：把 PROBLEM §1 修正表、DESIGN §0 中的 `params=359、obs=288、gauge=129` 改成实际 `params=143、obs=600、rank=140、nullity=3（参数 gauge=3）`；函数空间冗余单列 compact129/full255；与 §3/JSON/代码一致。
2. **统一 pilot/预算数字**：用 `timing_n1_pilot_v0_2.json` 的 **.02603 s/rep、11.72 s main、.037 GB** 与逐方法实际值替换文本/report 的 .0282/12.7/.038 和旧逐方法计时；G7/预算表引用同一 telemetry。
3. **收紧 G1 point 门**：建议 point≤.05（实际 .0488 通过）且 Wilson upper≤.075；`mc_tol=.00308` 仅用于 CI/敏感性说明，不作为 point 放宽到 .05308 的理由；若保留 .05308，必须明写理由并由 Lead 确认名义 FPR 控制。
4. **V4 执行前实测**：V4 仍是预注册 gate，不是本次结果；N1 执行预注册需在 effect 前实际跑 V4（200 reps、seed20261061、T_hold=2、static ridge vs nonstatic filter）并 PASS；失败→rename_static_Sadd，不进入效果。
5. **保持其余冻结**：n_units=300/MDE .04798/n_req278、G2 power、B1–B6 等预算、B2 等价审计、caps 1800s/2h/8GB/0 wells、机制账边界、两跑/schema/失败类别不变。

## 4. 修完后建议的 Lead 批准文本（仅 N1 执行预注册；不是效果执行）

> **批准范围**：在必改 1–5 完成并复核后，批准 R203-N1 **执行预注册**（机制账、合成、compute-only、0 new wells）；不批准效果结论/药理/真实决策/迁移/机制/新颖性。
>
> **冻结**：n_units=300；MDE80=2.801585·SD/√n_eff（n_eff=136.36，SD .20→.04798≤.05；n_req278≤300）；δ=.05 paired held-out regret D_i=R_i(M)−R_i(B2)、U∈[0,1]、m=5、held-out不更新；GT-static/nonstatic、V1–V4+rename_static_Sadd；G1–G7（G1 实际 k=976/20000、point .0488、Wilson .05187；G2 power1.000；G3 full 143/600/rank140/nullity3；V4 ELPD gate）；B1–B6 等预算（B2 同信息同预算强基线 + 等价审计）；真实 pilot telemetry（.02603s/rep、11.72s main、.037GB）与 caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry；失败类别统一。
>
> **禁止**：效果外推/药理/真实决策/迁移/新颖性；用 A/B 资源；改旧门槛/判定；恢复停止实验；晋升代码；在 G1–G7/V1–V4 未全 PASS 前报 regret；用旧 .0282/12.7/.038 或 359/288 的摘要数字；N1 效果执行须另立预注册+独立挑战+Lead 批准。

## 5. 声明

- **本轮不运行效果结论/不拟合/不读 O'Neil**：只读 N1 v0.2 预注册/JSON/pilot 与 R203-P1 链；只写本文件与 `tmp/`；未改 N1 产物。
- **总判决：revise**。v0.2 已修 n_units/MDE、G1 MC 规则、gauge/Jacobian 主体、V4、pilot/B2；但 **PROBLEM §1/DESIGN §0 仍写 full params=359/obs288/gauge129（实际143/600/140/3），且 pilot 文本 .0282/12.7/.038 与 timing JSON .02603/11.72/.037 不一致**；两者都是可复核的内部矛盾，不能按当前冻结文本批准。修完上述 1–5 后可提交 Lead 批准 N1 执行预注册（机制账/0 wells；不批效果/药理/真实决策/迁移/新颖性）。

**一句话：v0.2 的 n_units=300/MDE .04798/n_req278、G1 .0488/Wilson .0519、full 143/600/rank140/nullity3、V4 规则、真实 pilot+B2 等价都基本到位；但摘要仍残留 v0.1 的 359/288/129，pilot 文本 .0282/12.7/.038 与 timing JSON .02603/11.72/.037 冲突，且 G1 point 门可放宽到 .05308——判 revise：统一摘要与 telemetry、收紧 G1 point 门、V4 执行前实测后再提交 Lead 批准 N1 执行预注册。**

# R201-A.2.1 轻量复核（task-121）：v0.2 零模型/σ 修正

2026-10-28。角色：同一独立挑战者（非提案者、未参与 A、不运行 P1/不拟合/不读 O'Neil 响应做效应）。对象：[PROBLEM_A2_v0_2.md](PROBLEM_A2_v0_2.md)（SHA `3B49A8AB…`）、[DESIGN_A2_v0_2.md](DESIGN_A2_v0_2.md)（`3AB5A663…`）、[null_design_A2_v0_2.json](null_design_A2_v0_2.json)（`96AE014D…`）、[report_A2_v0_2.md](report_A2_v0_2.md)（`E874AEEE…`）、[record_A2_v0_2.md](record_A2_v0_2.md)（`E596DA6B…`）、v0.1 [challenge_A2.md](challenge_A2.md)。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_a2_to_lead（仅 A.2 data-only P1 重跑；0 新 wells；不进入 P2/S2/H_A2）。**

v0.2 已修掉 v0.1 的三个阻断问题（S2 因子 2、F_self 恒等自检、legal 规则 σ 来源矛盾），并把合成校准/预算/失败类别按修正尺度重算。核验项全部 PASS：
- **S2**：`σ_pair²_A2=0.5×mean ||P⊥(f_h1−f_h2)||²/(K−1)`；`Var(full)=0.00053962`、`σ_pair²=0.00107924`、`Var(half)=0.00107924`、`Var(half-diff)=0.00215849=2σ_pair²`；校正后 **0.00107924=S1**；A.1 frozen 0.00215849=**2.000×**；v0.1 因子 2 已消除。
- **F_self_check**：旧恒等自检作废；新 `d_avg=(d_A+d_B)/2`，A={1,2}/{3,4}、B={1,3}/{2,4}，Var(d_avg)=σ_pair²（iid 下 Cov=0），与 F_pair 分子同方差；mean **1.00526139**、median **0.80008628**、FPR@2.60 **0.0490**；D2=mean/median∈[0.5,2] + ratio `σ_pair²_A2/S1∈[0.5,2]`（失败 scale_mismatch）；D3=FPR≤0.10（失败 noise_calibration）；D2+D3 通过才保留 F_crit=2.60，不缩放 observed/不改阈值 ✓；JSON 明确披露旧恒等 sd=0 与新自检的合成演示/执行期同组半拆。
- **legal 规则**：A.2 `RMS≤1.96·σ_obs_A2`，`σ_obs_A2=σ_w_hat/2=0.0464595`，阈值 **0.0910607**（A.1 阈值 0.0643896，差异来自行均值噪声 SD 的正确化）；A.2 重算 legal 集、不冻结 A.1 n_legal=110,523；门 `n_legal_A2≥5%|U|=17,004.4` 否则 design_invalid: coverage；pooled 分母=n_legal_A2、BH q=0.05 不变；A.1 legal 集仅描述 ✓。
- **修正尺度校准**：N0 .04825/.2956、N1 .05778/.2889、N3 .042/.2956、N5 .0475/.2956 eligible；N2 .16519 不 eligible；N4 .94741 invalid；primary null=N0（规则不变；无合格→design_invalid: null_calibration）；per-cell N1；wrong-scale 诊断（F_pair 减半时 N0 FPR .00175/power .1378）记录 ✓。
- **预算/失败类别**：186 s（N1 500 fits≤50s、N0 pooled 500≤1s、诊断 2,000 sim≤75s、observed≤60s）；caps wall≤900s/CPU≤2h/8GB；超→compute_budget_exceeded（不减 N_perm）；两跑/schema/无 telemetry；失败映射统一（D1/D2/ratio/F_crit→scale_mismatch；D3→noise_calibration；D4/D5→null_calibration；D6→compute_budget_exceeded；D7→A.1 类别）✓。
- **边界**：A.2 通过前不进 P2/S2/H_A2；A.1 negative 不重判；阳性仅开发性存在性、阴性仅 `no_joint_contradiction`；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked ✓。
- **SHA/一致性**：v0.2 六份 SHA 与 report 一致；`PROBLEM/DESIGN/JSON` 三处 S2/F_self/legal/校准一致；`challenge_A2` 作为输入 SHA 正确。

## 1. 逐条判决

| # | 项 | 判决 |
|---|---|---|
| ① | S2 因子/数值 | **PASS**：0.5× 修正、0.00107924=S1、A.1 2.000×、v0.1 因子 2 已消除；`Var(full)=.00053962`、`Var(half)=.00107924`、`Var(d)=.00215849`。 |
| ② | F_self_check/D2/D3/ratio | **PASS**：d_avg 与 F_pair 同方差；mean 1.0053/median .8001/FPR .049；D2/D3/ratio 门写死；旧恒等作废；F_crit 条件化。 |
| ③ | legal 规则/阈值/重算 n_legal/≥5%U | **PASS**：A.2 σ_obs=.0464595、阈值 .0910607；重算 legal、不冻结 A.1；n_legal≥17,004.4；pooled/BH 口径写死。 |
| ④ | 校准表/primary N0 | **PASS**：N0 .04825/.2956、N1 .05778/.2889、N3 .042/.2956、N5 .0475/.2956 eligible；N2 .16519 不 eligible；N4 invalid；primary N0；wrong-scale 诊断。 |
| ⑤ | 预算/失败类别 | **PASS**：186 s/caps/两跑/无 telemetry；失败映射统一。 |
| ⑥ | 边界 | **PASS**：仅 A.2 data-only P1；0 新 wells；不进 P2/S2/H_A2；阴性措辞；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked。 |
| ⑦ | 总判决 | **approve_a2_to_lead**。 |

## 2. 批准文本（建议 Lead）

> **批准范围**：仅批准 R201-A.2 的 **data-only P1 重跑**（0 新 wells；不读取新响应做效应；不做生物学/机制/迁移/决策收益/新颖性主张）；不批准 P2/S2/H_A2，不重判 A.1。
>
> **冻结**：数据/O'Neil batch1 complete-case/target30/完整 4×4/|U|=340,088；A.2 legal 规则 `RMS≤1.96·σ_obs_A2`（σ_obs_A2=σ_w_hat/2=.0464595，阈值 .0910607）、n_legal_A2≥17,004.4；`σ_pair²_A2=0.5×mean||P⊥(f_h1−f_h2)||²/(K−1)`（预期 .00107924）；F_self_check 用 A/B 两套半拆的 d_avg；D1–D7 先于 P1；F_pair/per-cell T_c/pooled/BH q=.05/F_crit=2.60（仅 D2+D3 通过时保留）；N_perm=500；primary null=N0（合成校准规则；无合格→design_invalid: null_calibration）；per-cell=N1 bootstrap；阳性三条件同 A.1。
>
> **预算/失败**：data-only、0 新 wells；wall≤900s/CPU≤2h/8GB；≈2,500 模拟；两跑逐字节一致；JSON 无 telemetry；失败类别统一（scale_mismatch/noise_calibration/null_calibration/compute_budget_exceeded + A.1 既有）。
>
> **禁止**：用 A.1 结果改 null/σ/阈值；用 A.2 observed 选 null/legal 规则；减 N_perm 或换便宜分析；把 negative 写“矛盾不存在”；把 positive 写生物学/机制/迁移/决策收益/新颖性；在 A.2 通过前进入 P2/S2/H_A2。

## 3. 非阻塞实现备注（写入实现/记录）

1. `F_self_check` 的 A/B 两套半拆必须按 **well 索引 {1,2}/{3,4} 与 {1,3}/{2,4}** 在同一 4-well 行内、同一排序/seed 下计算；d_avg 的 Cov=0 仅在 iid/同组技术重复下成立；实现记录应保留原始 well 索引与两套 d 的计算。
2. A.2 legal 规则的 σ_obs_A2 是**行均值噪声 SD**（σ_w_hat/2）；`σ_w_hat` 用 `sqrt(mean((h1−h2)²))` 半拆；不要把 A.1 的 `σ_obs/2` 或 A.1 threshold 混入。
3. N0 pooled null 的 pair 级 χ² 需按 A.2 **n_legal_A2** 生成（不是 A.1 110,523）；N1 per-cell bootstrap 的每细胞 legal 数也用 A.2 规则；n_legal<5%U 即 coverage fail，不继续。
4. 预算 186 s 估计需在实现后做一次 pilot 预算测试；若 N1 500 fits 实际 >50s，按 caps 处理，但不得减 N_perm/换分析；两跑输出 SHA/JSON 无 telemetry 保持。
5. A.2 结果解释：阳性仅开发性存在性；阴性仅 `no_joint_contradiction`；A.1 不重判；A.2 通过前不进 P2/S2/H_A2；non-blind/peeked 披露。

## 4. 声明

- **本轮不运行 P1/不拟合/不读 O'Neil 响应做效应**：只读 A.2 v0.1/v0.2 产物与 C192 记录；只写本文件与 `tmp/`；未改 A/A.1/A.2 产物。
- **总判决：approve_a2_to_lead**。v0.2 已修 S2 因子 2、F_self 恒等、legal 规则矛盾，并按修正尺度重算校准/预算/失败类别；可提交 Lead 批准 **仅 A.2 data-only P1 重跑**（0 新 wells；不进入 P2/S2/H_A2）。执行前实现需按 §3 记录 A/B 半拆、legal σ、N0/N1 口径与预算；执行后仍需资格门先于结果。

**一句话：v0.2 的 S2=0.5×（.00107924=S1；A.1 frozen 2.000×）、新 F_self_check（mean 1.0053/median .8001/FPR .049；与 F_pair 同方差）、legal 规则（σ_obs_A2=.0464595/阈值 .0910607/重算 n_legal≥17,004.4）、修正尺度校准（N0 primary；N1 per-cell）、预算/失败类别/边界均已核验一致——判 approve_a2_to_lead，仅批准 data-only P1 重跑（0 新 wells；不进入 P2/S2/H_A2）。**

# R201-B.2 最终确认挑战（task-109）：v0.3 T1 预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 B、不运行效果/不拟合/不读响应）。对象：[PROBLEM_B_v0_3.md](PROBLEM_B_v0_3.md)（SHA `753B9CF8…`）、[DESIGN_B_v0_3.md](DESIGN_B_v0_3.md)（`183BE5DE…`）、[design_B_v0_3.json](design_B_v0_3.json)（`50E6EE30…`）、[report_B_v0_3.md](report_B_v0_3.md)（`012026AD…`）、[record_B_v0_3.md](record_B_v0_3.md)（`77AB57BE…`）、v0.2 [challenge_B_v0_2.md](challenge_B_v0_2.md)、R201 BRIEF、A5/ON2-EX/ON3/PEEK/C187/C190。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_mvp_to_lead，也不是 stop）。**

v0.3 已把 v0.2 的五个未冻结点基本修好（primary=(1200s,16 keys,κ=1,σ=0.10)、500 replicate=500 decision units、MDE 0.088594≤0.10；敏感性 17×50 仅描述；整数 key+blank/QC 无信息 filler；H_B AND；T1 旋钮/资格门/wall；T2/T3/PEEK 边界），SHA 与大多数算术一致。**但 v0.3 的 equal-cost 表仍有可算的公式错误：κ≠1 的 sensitivity 行出现负 filler；wall/arm-run 计数又漏掉了 π_dual / C7 两臂；T1 的 x1/x2 特征与 EV 离散世界网格仍未定义。** 这三项不修，T1 预注册不能冻结（尤其 filler 为负、arm-run 数不足以覆盖 H_B 两对比）。

**不能提交 approve_mvp_to_lead；修完必改 1–3 后可以。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | primary 配置/500 | **PASS** | primary=`(B_C=1200s, B_E=16 integer keys), κ=1, σ=0.10`；500 独立 replicate=500 decision units，seed=`20261130+id`；MDE=**0.088594≤0.10**；敏感性 17 格×50=850、seed=`20261131+cell_index*1000+r`，仅描述/cost_sensitive、不进 H_B/Holm；固定预算对 (300,4)/(1200,16)/(3600,64)×κ{0.1,1,10}×σ{0.05,0.10} 统一；JSON `primary_config`/`sensitivity`/`config_table` 一致 ✓。 |
| ② | 整数 key + filler | **FAIL（公式/单位错误）** | 规则写对：experiment-only `n0=B_E+floor((B_C/κ)/363.6)` 整数 key，残余用 blank/QC/已知标准品 filler，`|spend−T|≤1 well-equivalent`；primary 例 19 keys=6908.4 CU+filler 109.2 CU ✓。**但 JSON/报告把 filler 写成 `filler_CU=T−n0×363.6`（秒−CU 混用）**：primary κ=1 时数值巧合正确；κ≠1 的 sensitivity 行直接 **负 filler**（例：B_C=300,B_E=4,κ=0.1 → `blank_QC_filler_CU=-3917.76`）。正确公式应为 **`filler_CU=(B_E_CU+B_C/κ)−n0×363.6`**（该行应为 4454.4−4363.2=**91.2 CU**）。这不是舍入问题，是单位/公式错误；18 格中的 12 格 κ≠1 行都需要重算。 |
| ③ | H_B AND | **PASS（但依赖正确的 arm-run 覆盖）** | H_B 成立 iff `Δ1=dual−compute-only-filler`、`Δ2=dual−experiment-only-filler` 两对比均正且 Holm 显著且点估计均≥δ_min=0.10；只赢一个→`partial_decision_benefit`；都不成立→`no_decision_benefit`；显著但低于 δ→`below_delta`；主检验只在 primary；best-single 仅 inner validation；测试集不 max；敏感性只描述 ✓。**但必须实际运行 dual 与两个 C7 臂**（见 ④）。 |
| ④ | T1 冻结/资格门/wall | **FAIL（arm-run 计数）** | T1 旋钮（宇宙40/O20/M10/σ0.10/τ0.20/θ/证书阶梯/EV/R_max=5/seed/两跑/schema/资格门）已冻结 ✓；wall 规则（pilot 10 replicate、单次≤45min、两跑≤90min、pilot>45→design_invalid、total>45 但 primary≤45→只跑 primary 跳过敏感性）合理 ✓。**但 arm-run 计数错误**：T1 要比较 `π_dual` vs C7 的 **两个**单预算臂（compute-only、experiment-only），且 C0–C7 本身包含 8 个 label（C0,C1,C2,C3,C4,C5,C6,C7；C7 拆两臂则更多）。按最少口径：`π_dual + C0–C6 (7) + C7 两臂 (2) = 10 arm-runs/replicate`（若 C7 作为一 label 但必须输出两个臂的结果，也至少 **9**）；报告/DESIGN JSON 的 **8 arm-runs**（primary 500×8=4,000；sensitivity 17×50×8=6,800；total 10,800）**漏了 π_dual（及 C7 两臂之一）**。正确至少：primary 500×9=**4,500**（C7 拆臂则 5,000）；sensitivity 17×50×9=**7,650**（或 8,500）；total **12,150**（或 13,500）。wall/pilot/45/90min 必须按正确 arm-run 数重算；否则预注册门与 45min fallback 是错的。 |
| ⑤ | T2/T3/边界 | **PASS** | T2 仅描述/操作、不判 H_B、PEEK `B4CAD955…`、n=6/30 不作主检验；T3 data_unavailable/cost_uncalibrated、R primary=5（393×5×363.6=714,474.0 CU）、r=1/10 敏感性、不执行；T1 仅计算证据；不称新颖性/机制/迁移/决策收益/独立确认；D1/D3/A1/C187 不重复 ✓。 |

## 2. 三个必须改的具体问题

### 2.1 equal-cost filler 公式单位错误（敏感性 12 行负 filler）
- 报告 §1②/§2 写 `filler_CU = T − n0×363.6`；`T` 是 **synthetic seconds**（`B_C + κ·B_E_CU`），`n0×363.6` 是 **CU**；二者单位不同。
- 正确：experiment-only 的总实验预算（CU）是 `B_E_eff_CU = B_E_CU + B_C/κ`；整数 key 后 `filler_CU = (B_E_CU + B_C/κ) − n0×363.6`。primary κ=1 时 `B_E_eff_CU=T` 数值相同，所以 109.2 巧合正确；sensitivity κ=0.1/10 全部错误。
- JSON 证据：`equal_cost.rows[0].experiment_only.blank_QC_filler_CU = -3917.76`（B_C=300,B_E=4,κ=0.1）；正确应为 4454.4−12×363.6=**91.2**；其他 κ≠1 行也需重算；`|spend−T|≤1 well-equivalent` 必须按 CU 一致定义。
- 修复：改公式、重算 18 行、更新 JSON/report/record/SHA；primary 例不变（109.2）。

### 2.2 wall/arm-runs 漏 π_dual（及 C7 两臂）
- T1 的 H_B 需要 `π_dual` 作为被测臂；C7 是 **compute-only/experiment-only 两个单预算臂**（H_B 分别对比），C0–C7 label 为 8 个但 C7 拆两臂，`π_dual` 再加 1 → **10 arm-runs/replicate**（若把 C7 两个子臂合并成一次运行也不低于 9，且必须同时输出两个结果）。
- 报告/DESIGN v0.3 写 primary `500×8=4,000`、sensitivity `17×50×8=6,800`、total **10,800**；这恰好等于 C0–C7 的 8 个 label，但 **π_dual 不在 C0–C7 中**，所以漏了主被测策略（及 C7 拆臂的一臂）。
- 正确至少：primary `500×9=4,500`（C7 拆臂则 5,000）；sensitivity `17×50×9=7,650`（或 8,500）；total `12,150`（或 13,500）。必须更新 wall/pilot 外推、45min/90min 门与 fallback；否则 pilot 预算与总 wall 低估 12.5–25%，T1 45min 门不可信。

### 2.3 T1 两个"如/未定义"仍未冻结
- `f=θ0+θ1x1+θ2x2+θ3x1x2+θ4dose` 中 **x1/x2 是什么特征**未定义（cell/pair/plan 元数据的哪一种；如何从 40-plan 宇宙生成）；`θ` 固定但特征映射不冻结，模拟器实现者仍需自由选择。
- **EV"在固定离散世界网格上精确枚举"**，但该网格（θ/γ/噪声的离散化、点集、权重）没有定义；γ∼N(0,τ²) 是连续分布，没有网格就无法"精确枚举"。
- 这两项不影响数学框架，但影响 T1 能否**可复现地**实现；T1 预注册冻结前必须给出特征映射与 EV 网格表（或明确 EV 用解析/有限枚举近似并预注册误差）。

## 3. 必改（≤5，T1 预注册前完成）

1. **修正 equal-cost filler 公式并重算全部 18 行**：`filler_CU=(B_E_CU+B_C/κ)−n0×363.6`；禁止负 filler；`|spend−T|≤1 well-equivalent` 统一定义；更新 JSON/report/record/SHA；primary 例 109.2 保持。
2. **修正 arm-run 计数/wall**：明确 T1 臂至少 `π_dual + C0–C6(7) + C7 两臂(2)=10`（或证明 9 口径并给出每个臂输出）；primary 500×9=4,500/×10=5,000；sensitivity 17×50×9=7,650/×10=8,500；total 12,150/13,500；按正确数字重算 pilot 外推、45min/90min 门与 fallback；不得用 8 arm-runs。
3. **冻结 x1/x2 与 EV 网格**：给出 plan 特征映射、θ/x/dose 生成、40-plan 宇宙；给出 EV 离散世界网格（θ/γ/噪声点、权重、误差）或明确解析近似；写入 JSON/SHA。
4. **复核 $|T|$ 与 dual 残余**：dual 名义花费 1200s+16 keys=5817.6 CU（T=7017.6）已满；C7 两臂 conversion/filler 重算后与 dual 的 T 对齐；确保所有臂 `|spend−T|≤1 well-equivalent`，不只 primary 例。
5. **文字/记录一致**：报告 §2 的 8 arm-runs 与 JSON `wall_budget` 必须同步修正；primary 500/MDE 0.0886 不变；T2/T3/PEEK/边界保持；资格门先于结果；T1 批准仅实现+资格门。

## 4. 若完成必改 1–5，建议的 Lead T1 批准文本（仅实现+资格门）

> **批准范围**：仅批准 R201-B.2 T1 合成模拟器**实现 + 资格门**；不批准 T1 结果解释/决策收益主张、不批准 T2/T3 执行、不批准任何真实响应读取/湿实验；T1 仅计算证据。
>
> **冻结**：primary `(B_C=1200s,B_E=16 integer keys),κ=1,σ=0.10`；500 独立 replicate=500 decision units；MDE=0.088594≤0.10；敏感性 17×50 仅描述/cost_sensitive；`T=B_C+κ·B_E_CU`、整数 key+blank/QC 无信息 filler、正确 filler 公式、**π_dual+C0–C7（至少 10 arm-runs/replicate）**、H_B AND（两 Holm 对比均正且显著且≥δ=0.10；只赢一个=partial；显著低于 δ=below_delta）、best-single 仅 inner validation、测试集不 max；T1 所有旋钮（O=20/M=10/universe=40/σ=0.10/τ=0.20/θ/x 映射/证书阶梯/EV 网格/R_max=5/wall 预算）按修订后冻结；资格门先于任何结果（oracle/null/cost/leak/C0–C7/两跑/schema/wall/hash）；失败只写 `design_invalid`，不报结果。
>
> **禁止**：T2/T3 执行；O'Neil/Validation 响应读取；把 T1 合成结果外推生物/真实决策收益/迁移/机制/新颖性；改 primary/δ/MDE/config 后救结果；把敏感性配置赢的某一格当 H_B。

## 5. 声明

- **本轮不运行效果/不拟合/不读响应/无湿实验**：只读 v0.3 与 v0.2 产物；只写本文件与 `tmp/`；未改 B 产物。
- **总判决：revise**。v0.3 修好了 v0.2 的 primary/500、H_B AND、T1 旋钮/资格门、T2/T3/PEEK 边界；但 **equal-cost filler 公式在 κ≠1 的 12 行给出负 filler、wall/arm-run 计数漏掉 π_dual/C7 两臂、x1/x2 与 EV 网格仍未定义**——这三项是可复核的算术/定义错误，不能冻结 T1 预注册；修完可提交 `approve_mvp_to_lead`（仅模拟器实现+资格门，不批结果/T2/T3）。

**一句话：v0.3 把 primary/500/整数 key/H_B AND/旋钮/T2–T3 边界修到位，SHA 与多数算术一致；但 equal-cost filler 写成 `T(seconds)−keys_CU(CU)`，κ≠1 的 12 个 sensitivity 格出现负 filler（正确应为 `(B_E_CU+B_C/κ)−n0×363.6`，如 91.2 而非 −3917.76），wall 的 8 arm-runs 漏了 π_dual + C7 两臂（至少 9–10；primary 4,000 应为 4,500–5,000，total 10,800 应为 12,150–13,500），x1/x2 与 EV 网格也未冻结——判 revise：修完 1–5 后可提交 approve_mvp_to_lead（仅 T1 实现+资格门，不批结果/T2/T3）。**

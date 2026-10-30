# R203-N1.2 最终复核（task-136）：v0.3 修正预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 N1、不运行效果结论/不拟合/不读 O'Neil）。对象：[PROBLEM_N1_v0_3.md](PROBLEM_N1_v0_3.md)（SHA `E404C5FE…`）、[DESIGN_N1_v0_3.md](DESIGN_N1_v0_3.md)（`A65158D7…`）、[generator_n1_v0_3.py](generator_n1_v0_3.py)（`B4E93415…`）、[generator_n1_v0_3.json](generator_n1_v0_3.json)（`1577DDD1…`）、[timing_n1_pilot_v0_3.json](timing_n1_pilot_v0_3.json)（`94A3646E…`）、report/record/usage v0.3、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_n1_v0_3_to_lead；也不是 stop）。**

v0.3 已修好 v0.2 的两处文档/telemetry 矛盾：
- **full-h 维数**：文档/JSON 统一为 compact 107/312/rank95/nullity12、full 143/600/rank140/nullity3（参数 gauge3；函数空间 compact129/full255）；**但代码注释仍残留 359/288**（见 §2.2）。
- **pilot telemetry**：.02603 s/rep、11.72 s main、.037 GB、逐方法一致；G7 引用同一 snapshot ✓。
- **G1**：point≤.05、Wilson upper≤.075；实测 **.0488/.05187** PASS；G2 1.000 ✓。
- **n_units/MDE/n_req**：300、.04798、278≤300；B1–B6、B2 审计、caps、边界 ✓。

**但 V4 的“实测 PASS”不是独立 gate**：首版 nonstatic filter 等权分配观测 → V4 FAIL（mean −456.6）；用 oracle-state 诊断（+4147.6）后，把 filter 改成 **soft-responsibility/weighted ridge**，**用同一 seed=20261061 重跑**得到 mean 306.1577/SE65.4612/CI[177.856,434.459] PASS。规则/阈值/seed/n_rep/held-out 未改，但**模型实现是在看到 V4 失败后改的**；这属于 **model selection after gate failure**，不能作为独立的 rename_static_Sadd gate。**任务明确要求确认“实现修正而非规则漂移、不得迭代到通过”——目前只能确认规则未漂移，不能确认 V4 PASS 不是迭代到通过。** 必须独立验证或降级 V4。

**结论：不能提交 Lead 批准 N1 执行预注册；修完 §3 的 1–3 后可提交。**

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | full-h 维数唯一 | **PASS（文档/JSON）+ FAIL（代码注释）** | 文档/JSON：compact 107/312/95/12；full 143/600/140/3；函数空间 129/255；G3 依 full ✓。**但 `generator_n1_v0_3.py` line 556 仍写 “Full h (16 per pair,state): params f27+g36+h288+transition8=359; obs 288”**；与代码实际 `n_h=n_pairs*S*2`（full h72，obs600）矛盾。全文仍有 359/288 残留。 |
| ② | pilot telemetry 一致 | **PASS** | `timing_n1_pilot_v0_3.json`：per-rep **.02603 s**、main **11.72 s**、memory **.037 GB**；逐方法 B1 .00109/B2 .00133/B3 .001/B4 .01731/B5 .00083/B6 .00139/M .00308；文本/JSON 一致；G7 引用同一 snapshot；旧 .0282/12.7/.038 已废弃 ✓。 |
| ③ | G1 | **PASS** | point=.0488（976/20000）≤.05；Wilson upper=.05187354≤.075；G2 1.000/1.000/1.000；mc_tol 仅说明；失败→calibration_failed/rename_static_Sadd ✓。 |
| ④ | V4 实跑/披露 | **FAIL（独立性）** | 数值：mean306.1577、SE65.4612、CI[177.856,434.459]，mean≥2SE（306≥130.9）、CI lower>0；规则/seed/n_rep/held-out 未改 ✓。**但**首版 filter FAIL（mean −456.6）→oracle-state 诊断 +4147.6→改 **soft-responsibility/weighted ridge**→**同一 seed=20261061** 重跑 PASS；这是**看到 gate 失败后改模型实现**，不是独立预注册的 V4；`−456.6→306` 的符号翻转说明 PASS 高度依赖模型选择。PROBLEM/DESIGN 也未披露首版 FAIL/模型改动（仅 report/record 有）；V4 不能作为干净的 rename_static_Sadd gate。 |
| ⑤ | 其余冻结 | **PASS** | n_units=300/MDE .04798/n_req278≤300；G2；B1–B6；B2 等价审计 PASS；caps 1800s/2h/8GB/0 wells；两跑/schema/失败类别/边界 ✓。 |
| ⑥ | 总判决 | **revise** | 见 §2–§3。 |

## 2. 关键问题

### 2.1 V4 “PASS”是 post-hoc 模型选择，不是独立 gate
- 首版：nonstatic filter 把每个观测等权加入三状态回归（无 responsibility），V4 **mean −456.6 FAIL**。
- 诊断：oracle-state（true state）mean **+4147.6**，证明生成器有强状态信号——但这只说明 generator 非静态，不验证 filter。
- 修复：改成 **soft state responsibilities + weighted ridge（λ=1）**，**同 seed=20261061 重跑**，mean306.1577/SE65.4612/CI[177.856,434.459] PASS。
- 规则/阈值/seed/n_rep/held-out 确实未改；但 **模型实现变了**，且是在看到 V4 失败之后。**V4 的独立解释已破坏**：PASS 可能是“换模型直到通过”，不能证明 generator 一定能被预注册 nonstatic 模型区分。任务要求的“实现修正而非迭代到通过”**无法确认**。
- 正确做法（二选一）：
  (a) **预注册最终 V4 nonstatic 模型**（soft responsibilities/weighted ridge、λ、features、初始化/调参）**在 V4 运行之前**；然后在一个**未用于首轮 fail 的独立 seed 集/新 calibration 样本**上重跑 V4，并同时报告首轮 FAIL 与最终 PASS；
  (b) 把 V4 降级为 **诊断性证据**，不作为 rename_static_Sadd gate；用**预注册的 oracle-state/生成器已知参数检验**作为 gate（oracle 不是效果，也不依赖 filter 调参）。
- 当前同 seed 重跑不是独立验证；oracle-state 也不是 V4 的替代 gate。

### 2.2 代码注释仍残留 359/288
- `generator_n1_v0_3.py` line 556：`# Full h (16 per pair,state): params f27 + g36 + h288 + transition8 = 359; obs 288`。
- 实际代码：`n_h = n_pairs * S_ * 2`；full12：h=72、params=27+36+72+8=143；obs=`n_pairs*S*K*K + 4*S*(S−1)`=576+24=600。**注释与代码/文档/JSON 矛盾**；任务要求全文无 359/288/gauge129，当前不满足。

### 2.3 V4 披露不完整
- `report_N1_design_v0_3.md`/`record_N1_design_v0_3.md` 披露首版 FAIL、oracle 诊断、模型修复；**但 PROBLEM/DESIGN 的 V4 节只写最终 PASS/soft responsibilities**，未写首版 FAIL/模型选择；预注册正文应包含该披露，否则执行者/审计者看不到 V4 的 adaptive 历史。

## 3. 必改（≤5，Lead 批准 N1 执行预注册前）

1. **V4 独立验证**：预注册最终 nonstatic filter（soft responsibilities/weighted ridge、λ、features、初始化/调参、更新规则）并 **在 V4 运行前冻结**；在**独立 seed 集/新 calibration 样本**（不是 20261061，也不是同一 200 组数据）重跑 V4，报告首轮 FAIL 与最终 PASS；只有该独立 V4 PASS 才能作为 rename_static_Sadd gate。若不能独立重跑：**把 V4 降级为诊断**，改用预注册的 oracle-state/生成器参数检验作为 gate，不得用当前同 seed PASS 充当 gate。
2. **修代码注释/全文 359/288**：`generator_n1_v0_3.py` line 556 改为 full 143/600（h72）；全局 grep 确认 359/288/gauge129 只在“历史披露”上下文出现，不得作为 full 摘要；与文档/JSON 一致。
3. **V4 披露进预注册正文**：PROBLEM/DESIGN 的 V4 节写清首版 FAIL（−456.6）、oracle 诊断（+4147.6）、修改为 soft-responsibility/weighted ridge、规则/seed/n_rep/held-out 未改但模型实现改变；明确最终 PASS 是 **post-hoc 模型选择后的结果**（或降级为诊断）。
4. **保持其余冻结**：n_units=300/MDE .04798/n_req278、G1 .0488/.05187、G2 1.000、B1–B6、B2 审计、caps 1800s/2h/8GB/0 wells、边界/两跑/schema/失败类别不变；最终实现重跑 pilot/G7。
5. 若 V4 无法独立验证且 Lead 不愿降级，则 **stop**（不得以同 seed 的 post-hoc PASS 批准；不得迭代到通过）。

## 4. 修完后建议的 Lead 批准文本（仅 N1 执行预注册；不是效果执行）

> **批准范围**：在必改 1–3 完成并复核后，批准 R203-N1 **执行预注册**（机制账、合成、compute-only、0 new wells）；不批准效果结论/药理/真实决策/迁移/机制/新颖性。
>
> **冻结**：n_units=300、MDE .04798、n_req278；δ=.05 paired held-out regret、U∈[0,1]、m=5；GT-static/nonstatic；V1–V4（V4 的最终 nonstatic filter 必须在 V4 运行前预注册；独立 seed/calibration 重跑；首轮 FAIL/模型选择披露保留）；G1–G7（G1 .0488/.05187；G2 1.000；G3 full 143/600/rank140/nullity3）；B1–B6 等预算+B2 等价审计；canonical pilot .02603s/11.72s/.037GB；caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry；失败类别统一。
>
> **禁止**：效果外推/药理/真实决策/迁移/新颖性；用 A/B 资源；改旧门槛/判定；恢复停止实验；晋升代码；在 V4 独立验证/G1–G7 未 PASS 前报 regret；用同 seed 的 post-hoc V4 PASS 或 359/288 残留作为冻结依据；N1 效果执行须另立预注册+独立挑战+Lead 批准。

## 5. 声明

- **本轮不运行效果结论/不拟合/不读 O'Neil**：只读 N1 v0.3 预注册/代码/JSON/pilot 与 report/record；只写本文件与 `tmp/`；未改 N1 产物。
- **总判决：revise**。v0.3 的 full-h 文档/JSON、pilot telemetry、G1、n_units/MDE、B1–B6/B2/caps 基本到位；但 **V4 是首轮 FAIL 后改模型、同 seed 重跑的 PASS，不能作为独立 rename_static_Sadd gate（规则未漂移但模型实现有 post-hoc 选择）**；且 **代码注释仍写 359/288**、**PROBLEM/DESIGN 未披露首轮 FAIL/模型修复**。修完 1–3 后可提交 Lead 批准 N1 执行预注册；若不能独立验证 V4，应降级 V4 或 stop。

**一句话：v0.3 把 full 143/600/140/3、telemetry .02603/11.72/.037、G1 .0488/.05187 修齐了；但 V4 首版 FAIL −456.6→oracle +4147.6→soft-responsibility/weighted ridge 同 seed 重跑 PASS 306.16/65.46，规则/seed/n_rep/held-out 未改却是在看到失败后改模型——这是 post-hoc 模型选择，不能算独立 V4 PASS；代码注释还残留 359/288，PROBLEM/DESIGN 未披露首轮 FAIL/修复——判 revise：先独立重跑 V4（或降级 V4 为诊断）、修注释/披露，再提交 Lead 批准 N1 执行预注册。**

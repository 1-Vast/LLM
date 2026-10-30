# record_diag_m1_s2 — R204-M1-S2-FAIL-DIAG 过程记录（diagnostic only）

2026-10-28 · 角色：独立诊断实现者（endpoint-auditor）。对象：C216 [m1_stage2_rerun.json](../2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json)（SHA `B2CD0195…72107`；`design_invalid: projection`；H1 0/16）。**本诊断不改变 C216；不救结果；不输出效果/决策收益；未执行 Stage2 其它阶段/Stage3/真实数据/湿实验。**

## 1. 输入与范围

- 只读输入：C216 report/json/diagnostics、`DECISION_R204_M1_S2_RERUN.md`、`DESIGN_M1_STAGE2_v0_2.md`/`PROBLEM_M1_STAGE2_v0_2.md`、exec prereg/schema、C215 invalid_run 记录（不引用）。
- 新建目录只写：`research/2026-10-28-m1-stage2-fail-diag/` 与 `tmp/`；C216/C215/M1 设计链/其它产物未改。
- 诊断协议先冻结（[PROTOCOL_DIAG.md](PROTOCOL_DIAG.md)，SHA `F4206B09…721C`）→ 实现 [diag_m1_s2.py](diag_m1_s2.py)（`DC9AD39C…EEF8`）→ 两跑逐字节 → 报告/记录/usage。

## 2. 诊断设计（冻结；详见 PROTOCOL）

- 冻结环境严格同 C216（c .5²/M .1²/d .1²、σ 公式、box[-2,2]^4、K=3/[.5,.3,.2]、param/train/eval seeds 20261301/02/03、H1 cell seeds 20261310..25、d/N 网格与容差表）；未改尺度/容差/顺序/种子。
- 逐 16 格（同 eval 2048/seed 20261303）：
  1. **C-MDN TV**：引用 C216 `H1[].TV_256bin`（不重训）。
  2. **oracle 真值两样本 TV**：用真实 Pθ 从同一 eval X[:, :d]、A 抽 2048 个 Y；R=200 次独立重复；与 eval Yev 计算同一 256-bin histogram TV；报告 mean/median/q05/q95/max。
  3. **有限样本 floor**：由每行 256 个 oracle 样本（524,288/格）得 p_pop 直方图；eval-vs-pop TV；从 p_pop 抽两个 multinomial(2048) 样本 1000 次得 floor mean/q95；解析近似 `sqrt(1/(πN))Σsqrt(p(1−p))` 仅报告。
  4. **容量敏感性（non-frozen）**：预注册 6 格，hidden=256/epochs=400 重训，报告 ΔTV。
  5. **保真核验**：2 格冻结配置重训 vs C216。
- 逐格归因规则（预注册）：floor q95≥tol → `estimation_limit_unreachable`；否则按 floor/C-MDN excess 分 at-floor / fit_or_capacity / mixed / mostly_noise；容量敏感性仅支持性证据。**不用于改判定。**

## 3. 决定与理由

1. **用 oracle 真值两样本 TV 作主诊断**：H1 是"真实样本 vs 候选样本"的 256-bin/2048 TV；完美模型的 TV 不会为 0，而有抽样 floor。用同一 X/A、同一 N、同一 metric 的 oracle 两样本 TV 正好度量"可达到的 TV 下界"，可区分"拟合不足"与"容差不可达"。
2. **p_pop + multinomial floor MC**：直接按 eval 行混合分布估计抽样分布，避免仅用正态/√(K/2N) 粗略近似；解析近似仅作量级校验。
3. **容量敏感性只做预注册 6 格、标注 non-frozen**：避免把"多做容量"当救结果；5/6 变差，说明不是简单容量问题。
4. **保真核验**：两格冻结配置重训 ΔTV +.00195/−.00684；后者超 0.005 → 记录 fidelity caveat（torch 线程/优化非严格复刻）；主诊断用 C216 引用 TV，不以重训 TV 为主证据。
5. **不改 C216**：H1 0/16 仍是 `design_invalid: projection`；本诊断只把失败归因写清楚。

## 4. 结果摘要

- **16/16 格：floor q95 ≥ 冻结容差；13/16 格 oracle 均值 > 容差** → **主导归因 = (c) 冻结容差低于有限样本可达下界**。
- C-MDN TV 相对 oracle 均值 16/16 为正（中位 +.0599，最大 +.2037）→ **次要 (a) 拟合/容量 excess 存在**。
- 容量×（6 格）5 格变差、1 格 −.0020 → 不支持简单容量修复。
- floor 均值 0.118–0.176、q95 0.134–0.192；解析近似 0.123–0.179。
- **未声称 H1 通过；C216 verdict 未变。**

## 5. 两跑/预算/产物 SHA

- run1：wall 105.67 s、CPU 105.33 s、RSS 0.2724 GB；run2：wall 113.54 s、CPU 113.36 s、RSS 0.2710 GB（外部 wall 111.8/119.4 s）；wells=0；caps 1800 s/7200 s CPU/8 GB **PASS**。
- **`diag_m1_s2.json` 两跑逐字节一致**：SHA **`6FBD101677728945F0721713391DEBA5F2747DC7F652F1EF4E0FAB0DBD2FBB54`**；telemetry 只在 stdout/usage，不在 diag JSON。

| 产物 | SHA256 |
|---|---|
| `PROTOCOL_DIAG.md` | `F4206B0977FE16FA3080D18E4AD7007DFC16076716D4AA2BC1D4718EC0FD721C` |
| `diag_m1_s2.py` | `DC9AD39CCC25C2EAD95F0F33A6178CD53E38AC62BB39A002C71936C49695EEF8` |
| `diag_m1_s2.json` | `6FBD101677728945F0721713391DEBA5F2747DC7F652F1EF4E0FAB0DBD2FBB54` |
| `report_diag_m1_s2.md` | `261D37C8C541E8F427F4416A68DD63AAB595EE44FEB1DFA780BB6FAEDA334FA0` |
| C216 输入（只读） | `B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107` |
| `record_diag_m1_s2.md` / `usage_diag_m1_s2.json` | 自引用（外部复算） |

## 6. 局限

- C-MDN TV 引用 C216 数值，未在本诊断重训主模型（除容量/保真子集）。
- oracle floor 用 eval 行固定混合分布的 p_pop 近似；floor MC 假设 bin 计数近似 multinomial（大体成立；仅用于量级/归因）。
- 保真核验 1/2 格 ΔTV 超 0.005（fidelity caveat）；容量敏感性 non-frozen、子集非全部 16 格。
- 未做多 seed 平均/更大 eval/更少 bins 的可达性分析（那会改判据，须另立预注册；不得在本诊断中执行）。
- 单机 CPU、torch 单线程设置（为两跑可复现）；与 C216 默认线程可能不同，已记 fidelity caveat。

## 7. 边界与建议

- **不改变 C216**：`design_invalid: projection` 保持；不称 H1 通过；不把诊断当资格/效果证据；不输出 decision utility/regret/top-k/方法比较/效果；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **建议**：将本归因写入 R204 阴性报告的"失败归因"节（主因=c 容差低于 oracle floor；次要=a C-MDN excess；容量/epochs 不改善），**不改变 C216**。若要使 H1 可判定，须另立预注册（例如增大 eval N/多 seed 平均/更少 bins）并由 Lead 批准；本诊断不执行、不改判据。

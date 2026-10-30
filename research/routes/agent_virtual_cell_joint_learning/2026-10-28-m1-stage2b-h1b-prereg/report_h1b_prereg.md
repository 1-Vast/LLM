# report_h1b_prereg —— R204-M1-S2B H1b 可分辨测量预注册报告（floor 校准先行；不运行方法）

2026-10-28。对象：R204-M1 H1b 测量协议（新单独预注册）。依据：C215/C216/C217、M1 Stage2 v0.2 设计链、M1 Stage1/C208、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C208/C209/C213/C215/C216/C217。
**状态：预注册草案；仅 floor 校准（解析/MC）与协议设计；未运行 C-MDN、未报效果、未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；H1b 执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_H1B.md](PROBLEM_H1B.md)（`AE8BEE2A…`）
- 执行设计：[DESIGN_H1B.md](DESIGN_H1B.md)（`10EF642A…`）
- floor 校准：[floor_calib_h1b.py](floor_calib_h1b.py)（`9A0380B5…`）→ [floor_calib_h1b.json](floor_calib_h1b.json)（`88715AA8…`）
- schema：[schema_h1b.json](schema_h1b.json)（`A077BCCD…`）
- 记录/用量：[record_h1b_prereg.md](record_h1b_prereg.md)、[usage_h1b.json](usage_h1b.json)

## 1. 旧/新协议分离（写死）

- **C216 旧 H1 0/16 FAIL、`design_invalid: projection` 不变**；**C217 归因（旧容差低于 oracle 有限样本 floor）不变**；**旧 H1 容差表不改**。
- **H1b 是全新的、单独预注册的测量协议**；不是修正/重跑旧 gate，不得用 H1b 改判 C216/C217；H1b 失败也不改旧判定。
- 本任务**不运行 C-MDN**、不产生 H1b 方法结果。

## 2. floor 校准（先于方法结果）

- **Pθ**：param_seed **20261301**；c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；固定 a=0、X~N(0,I_d)、截断采样。
- **测量**：hash 分箱 TV（8-bit/维→code→cell=code mod B）；grid B∈{16,32,64,128,256}×N_eval∈{2048,8192,16384,32768}×K∈{1,4,16}×d∈{8,16,32,64}；MC reps 300；p 估计 400k/d。
- **选择规则**（预注册）：q95_worst≤0.02 中最小化 B·N_eval·K，再 q95 tie-break；无满足且 min q95>0.03→`precision_insufficient`；结果 **selected**。
- **选定测量参数**：**B=16、N_eval=32768、K=1**；oracle floor **mean 0.01221141、q95 0.01642609**（worst-case over d）。
- **容差规则**：`tol_d=ceil(3·floor_q95_d·1000)/1000`；floor_q95≤tol/3；表 d8 **.049**、d16 **.050**、d32 **.049**、d64 **.048**（global .050）；**不得按 M1 结果调**。

## 3. 可判定性

- C-MDN 需达到的 TV 才 pass：**d8≤.049、d16≤.050、d32≤.049、d64≤.048**。
- 可检出 excess（高于 floor）：**d8 .03288、d16 .03357、d32 .03278、d64 .03219**。
- 旧 C217 C-MDN excess：median **.0599**、max **.2037** → 远大于可检出 excess；近似 **power≈1**（在 old-excess 下 pass≈0）；H1b 对旧量级误差可检出且不被 floor 噪声判死。
- selected 参数满足 floor q95≤tol/3；**无需 precision_insufficient/stop**。

## 4. H1b 预注册（执行时实现；本任务不运行）

- 16 cells：d∈{8,16,32,64}×N_train∈{512,1024,2048,4096}；每 cell 训练候选 C-MDN（执行时），以 a=0、X~N(0,I_d) 采样 N_eval=32768 候选 Y，独立 oracle 同 N_eval；hash B=16；TV 与 tol_d 比较；pass ⇔ TV≤tol_d。
- **独立 seeds**：floor 校准 **20261801–20261810**；H1b 数据 **20261811**、eval **20261812**、cell seeds **20261821–20261836**；与旧 Stage2 seeds disjoint；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；失败类别 projection/calibration/leakage/two_run_mismatch/chain_mismatch/compute_budget_exceeded/precision_insufficient/inconclusive。
- 不输出 decision utility/regret/top-k/方法比较/效果；H1b 仅测量近似协议。

## 5. 边界

机制账 only；不运行 C-MDN/不报效果；不改 C216/C217/旧容差/旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；H1b 执行须另立独立挑战+Lead 批准。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_H1B.md` | `AE8BEE2A66DC8ABDBB80839B01A61AA8C432BEC474B406C28E1209D318A48B66` |
| `DESIGN_H1B.md` | `10EF642AD62707ADE406E458657FCC8D53D2B4AA69423234C1E86769E8E598D1` |
| `floor_calib_h1b.py` | `9A0380B551173F2E2C1F96942745314B4591C4FACDC3DED0487E97DE65F13663` |
| `floor_calib_h1b.json` | `88715AA8C60613AB7675923A67BC919B1B2F9361112EBCF9B29CD9BB33AB3214` |
| `schema_h1b.json` | `A077BCCDF793192861EB1E725FCE16FA70C2627652DF298A50D3633CF57C5F31` |
| report/record/usage | 见 `usage_h1b.json` |

**确定性**：`floor_calib_h1b.json` 两跑逐字节一致；JSON 无 telemetry；floor 校准 wall≈16–17 s 仅记录在 usage/报告，不进 result JSON。

## 7. 建议

1. **提交独立挑战**：重点旧/新协议分离、floor 校准网格/MC/选择规则、选定 B=16/N=32768/K=1 与 q95 .016426、tolerance 由 floor 推导且不按 M1 结果、H1b 16 格测量/seeds/两跑/caps/schema/失败/停止、可判定性 required TV/detectable excess/power、边界。
2. 挑战通过 + Lead 批准后才可执行 **H1b 测量**（不运行 C-MDN 本任务；执行时按预注册）；H1b 结果不改 C216/C217；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性。
3. **不做**：运行 C-MDN/效果/真实数据/代码晋升/旧判定修改/恢复停止实验；不把 H1b 通过挂钩真实功能/决策收益。

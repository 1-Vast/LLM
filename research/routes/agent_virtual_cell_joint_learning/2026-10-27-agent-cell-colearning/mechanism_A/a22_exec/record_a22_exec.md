# record_a22_exec.md —— R201-A.2.2-EXEC 执行记录（R4 异方差稳健 σ；data-only P1 重跑）

角色：独立执行者（未参与 R197/R200 模型开发）· 任务 task-125（A.2.2-EXEC）· 日期 2026-10-28
只写 `mechanism_A/a22_exec/` 与 `tmp/`；**未改 A.1/A.2/A2-EXEC/A.2.2 预注册/P0P1 产物**；0 新 wells；未进入 P2/S1/S2/H_A2；non-blind/peeked 继承 ON3。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① D1–D7 先于 P1；失败→design_invalid 不进 P1 | ✅ D1 PASS、**D2 FAIL（coverage .6484<.85）**、**D3 FAIL（worst-context FPR 1.0>0.25；p95 .318>0.20）**、D6 PASS、D7 PASS；D4/D5 未评估 → `design_invalid: scale_mismatch`；**P1 未执行（P1=None）** |
| ② R4 σ/前置门（每 context≥2 plans、σ² 有限/正、排除 pair≤5% 否则 coverage；F_pair 共享 context σ²；A.2 legal 不变；F_crit 仅 D2+D3 PASS 保留） | ✅ contexts 2,216（included 2,149；excluded 67 <2 plans）；excluded pair fraction **0.0** ≤5%；A.2 legal 阈值 0.09106062，n_legal_A2=176,934≥17,004.4；F_crit **未保留** |
| ③ P1（U=340,088、N0-strat、N1-R4、N_perm=500 seed 20261029、BH q=.05、阳性三条件） | ⛔ **未执行**（D2 提前失败；按预注册规则不进入 P1） |
| ④ pilot 预算测试（caps 900s/2h/8GB、≈2,500 模拟、超→compute_budget_exceeded 不减 N_perm） | ✅ pilot PASS（t_N1 .0154–.0169 s、t_N0 .003–.004 s、投影 11.6–12.0 s、内存 .674 GB） |
| ⑤ 两跑逐字节；实测 wall/CPU/内存；report/record/usage+SHA；失败类别；实现备注 | ✅ json/rows 两跑一致；wall 57.9/58.4 s、CPU 56.23–56.56 s、内存 .674 GB；披露 R4 resubstitution、LOO 仅描述、F_self 公式、候选选择仅合成、C194 仅诊断 |
| ⑥ 边界（0 新 wells；不进 P2/S2/H_A2；阳性仅开发性、阴性仅 no_joint_contradiction；不称机制等） | ✅ `verdict=design_invalid`；无 P1 结论；A.1/A.2 不重判 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~01:37 | 读 task-125 并 claim；读 DECISION_R201_A22_EXEC、A.2.2 预注册链 |
| ~01:39 | **`PROTOCOL_A22_EXEC.md` 冻结**（D1–D7、R4 σ/前置门、F_self pair 级公式、N0/N1 实现、pilot、schema；`run_a22_exec.py` 尚不存在） |
| ~01:40 | 写 `run_a22_exec.py` |
| ~01:41 | **run1** wall 57.9 s → D2 FAIL（coverage .6484<.85）、D3 FAIL（worst-context FPR 1.0、p95 .318）→ design_invalid: scale_mismatch；P1 未执行 |
| ~01:42 | 检查 diagnostics：σ²_R4 中位=6×S1、p25≈0、重尾；F_self 全局中位 .544、coverage .6484；LOO 描述性 p50 1.0 |
| ~01:43 | **run2** wall 58.4 s；`a22_exec.json`/`a22_exec_rows.csv` 两跑逐字节一致 |
| ~01:46 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露（未改冻结规则）

1. **F_self 精确公式（按 Lead 决定）**：`F_self(p,q)=[||P⊥(f_p−f_q)||²/(K−1)]/σ²_R4(shared context)`（pair 级 full profile；与 F_pair 同式）；D2/D3 用 legal pair 的该值；另报 A.2-style 半拆分诊断（描述性，**不参与** D2/D3）。
2. **R4 σ（resubstitution 披露）**：每 context 的均值包含被检验 pair（finite-sample 校准，**不称"独立尺度"**）；LOO 敏感性：`F_LOO/F` p5 .99 / p50 1.00 / p95 1.01（仅描述，不作判定）。
3. **R4 实测分布**：σ²_R4(c) p25≈0.0、p50 .01、p95 .03、max .14；中位/S1=**6.00** → full-profile pair 差混入真实 profile 差异（非纯噪声），重尾/近零 context 使 D2 coverage 与 D3 worst-context FPR 失败。
4. **观测统计披露**：observed F/T/pooled 只在 gate 前为 pilot 计时计算，**未解释/未报告**（`P1=None`；rows CSV 仅 note）。
5. **未改冻结项**：阈值/F_crit/族/N_perm/legal 规则/R4 公式/D2/D3 门均按 `PROTOCOL_A22_EXEC.md`；未用 observed 选规则；未用 A.1/A.2 结果改 null/σ。
6. **预算/telemetry**：pilot PASS；run1 57.9 s/run2 58.4 s；CPU 56.23–56.56 s；内存 0.674 GB；未减 N_perm。
7. **数据边界**：batch1 complete-case target30 完整 4×4；plan-cells 16,722（excluded 524/475）；702/315 排除；不插值；未拼 ΔEMAX；0 新 wells；non-blind/peeked。

## 3. 关键结果（与 report 一致）

- **verdict=design_invalid；failure_category=design_invalid: scale_mismatch**（D2 先失败；D3 亦失败）；**P1=None，无 positive/negative**。
- D1 PASS：σ_w_hat=0.092919、σ_obs_A2=0.0464595、legal 阈值 0.09106062；D7 PASS（U=340,088；G1/G2/G4/G5；conclusions 同 A.1）。
- D2 FAIL：per-context median coverage .6484<.85；全局中位 .5440（pass）；overall F_self FPR .08741（pass）；σ²_R4/S1 中位 6.00。
- D3 FAIL：overall FPR .08741（pass）；worst-context FPR 1.0（fail）；context-FPR p95 .3184（fail）。
- D4/D5 未评估；D6 PASS（pilot 11.6–12.0 s 投影、内存 .674 GB）；D7 PASS。
- 两跑 SHA：json `BD197811…1F841F26`、rows `4E7527A1…F4C03DF6`。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_A22_EXEC.md` | `4D19675451D67794BDE9AFE6430A8D4D55C5F81E9B6CEB06047DD331E55D6215` |
| `run_a22_exec.py` | `4E6F9CBAD6B5F5E1C770A460DB1AF849B53B62CF8F867DA373AE070974AAFDC2` |
| `a22_exec.json` | `BD197811257D2D8EF0DB2026A91EF4B7BCCB0976742BABEF2C8B1A8A1F841F26` |
| `a22_exec_rows.csv` | `4E7527A1381896360915F48555FDFE072904012C258A92202C631447F4C03DF6` |
| `a22_exec_diagnostics.json` | 见 usage（含 telemetry） |
| report/record/usage | 见 `usage_a22_exec.json` |
| 冻结链（只读） | PROBLEM_A22 `69605BBC…`、DESIGN_A22 `EAC8EA10…`、sigma_robust `12DC9855…`、DECISION_R201_A22_EXEC（SHA 见 json） |

## 5. 缺口与下一步

- **P1 未执行**（D2/D3 预注册失败）→ 无 A.2.2 positive/negative；不得把 pre-gate observed 当证据；不写"矛盾不存在/机制/迁移/决策"。
- R4 的 full-profile plan-pair 尺度在真实 S-add 违例下混入真实差异（重尾/近零 context）→ 建议 **A.2.3** 改为模型化噪声尺度（拟合 shared-f 后残差/分层方差、显式交互项 null 模拟）+ 重设计 D2/D3；或由 Lead 决定停止 A 线。
- A.1/A.2 保持原样（A.1 仅"冻结 null 下未检出"；A.2 design_invalid: scale_mismatch）。

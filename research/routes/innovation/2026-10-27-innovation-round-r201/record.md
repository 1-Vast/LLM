# R201 轮记录：Agent × 虚拟细胞共同学习（2026-10-28）

## 0. 本轮主line（用户 2026-10-28 指示）
**Agent 提需要辨别的反事实关系；虚拟细胞维护跨计划一致干预模型；真实反馈统一修订、再改变 Agent 选择。**
优先组合=方向1（跨计划一致反事实模型）+方向2（计算/真实实验双预算），方向3验证；先例 CoMap/LAWM/MDA/COPEx 覆盖一般概念→**不声称新颖性**；新意须落到具体共享对象与更新运算。

## 1. 先例/创新边界（R201-P，`agent-cell-colearning/prior_art_new.md`）
- 已覆盖：模型+策略共同更新（CoMap）；动作/状态/动力学联合（LAWM/CoLA/HIJP）；任务摘要/模型发现/机制池/VoI（MDA）；动态约束/预算非短视实验设计（COPEx/BOR）；反例→模型修订（OPINE CEGIS/MDA）；选实验区分竞争模型（经典 OED）；集合成员/部分识别+约束生成；决策聚焦 acquisition（GoBOED/EVSI）。
- 部分覆盖：多实验共享算子一致性（普通共享参数联合拟合已保持）；计算 vs 实验双预算（单侧先例多；同一账本联合分配未在已核范围发现）。
- 未发现（题录级）：计划对联合不可行作为主动选择信号+反馈统一修订。
- 不可声称清单 10 条；可能空白 G1（联合不可行证书+主动实验）、G2（计算/实验同账本）、G3（统一修订对未测计划的独立决策收益）。

## 2. 机制 A（跨计划一致反事实模型）：设计→P0/P1→三次校准失败→停止归档
- 设计（A/A.1）：形式化 J=ε_pq−max(ε_p,ε_q)、证书 θ*、over-id≥1、反事实 V、最坏简单后悔、一次反馈统一修订；O'Neil qwc（complete-case 363,090/98.44%；22,035×16/702×15/315×0 pair-cell；计划对 441,867；每细胞 over-id 中位 8,745）；**决策终点 evaluation_cannot_distinguish**（30 cells rank MDE .7625；需 ≈6,282 独立细胞 δ=.05）。
- A.1 P0/P1（data-only、0 新 wells）：P0 全 PASS；P1 冻结规则 `p0p1_negative`（BH 0/30；pooled .1537<null Q95 .7491），但 **null 校准失效**（null pooled 中位 .7457≫obs .1537；F_self 中位 .4579≠1）→ negative 不可解释（C192）。
- A.2（修正 null/σ）：候选 null 合成校准；S2 因子 2 错误 → 修正为 0.5×；A.2-EXEC **D2 失败**（F_self median .4153∉[.5,2]；异方差）→ `design_invalid: scale_mismatch`，P1 未执行（C194）。
- A.2.2（异方差稳健 R4 σ）：合成 eligible（coverage .875），真实执行 **D2 失败（coverage .6484<.85）+ D3 失败（worst FPR 1.0；context-p95 .3184>.20）**；机制=R4 σ² 混入真实 profile 差异（中位 6×S1、重尾）→ `design_invalid: scale_mismatch`，P1 未执行（C195）。
- **Lead 裁定停止 A 线（`mechanism_A/DECISION_R201_A_CLOSE.md`）**：不做 A.2.3 迭代（换零模型会把违例吸收进 null、违反预注册纪律）；根本原因=O'Neil 4×4 技术重复不足以独立估计噪声；A.1 negative 仅"冻结 null 下未检出"，A.2/A.2.2 为 design_invalid，**均不能写"无联合矛盾/矛盾不存在"、不构成机制 A 阴性证据**；不进入 P2/S2/H_A2。
- 升级测量：同一 plan 的独立 wells/plates/培养/日重复；更大 4×4 网格+重复；或合成 ground-truth（已知无/有违例）验证 type-I/power；决策收益需 ≈6,282 独立细胞（δ=.05）。

## 3. 双预算（方向2）：设计→T1-MVP 资格门→主 T1→partial
- 设计 v0.1→v0.4（4 轮修订+3 轮挑战）：primary=(1200s,16 integer keys,κ=1,σ=0.10)、10 arms、H_B AND、整数 key+无信息 filler、EV 有限离散近似、wall 10,800→13,500 arm-runs、资格门先于结果。
- T1-MVP：9 项资格门全 PASS（oracle/null FP/EV 近似门/成本账/无泄漏/10 arms/wall；pilot 100 arm-runs 6.97s，外推 primary≈5.81min、两跑≈11.6min；两跑一致 A50A1E96…）。
- 主 T1（500 decision units、10 arms、Holm α=.05）→ **H_B = `partial_decision_benefit`（未支持 H_B）**：dual vs C7_compute_only **+0.022 CI[0.006,0.040] Holm p=.01117**（显著正但<δ=.10）；dual vs C7_experiment_only **+0.010 CI[−0.006,0.026] p=.11252**（不显著）；per-arm mean selection accuracy π_dual .912 等（描述）；敏感性 17 格 dual−C7 均值约 −.04…+.04；两跑 58E290A7… 逐字节；wall 974.96/956.73s；失败类别 `partial_decision_benefit`（预注册分类）。
- 边界：仅合成计算证据；不称新颖性/机制/迁移/决策收益/独立确认；不外推 O'Neil/生物/药物决策；T2/T3 未执行（C193）。

## 4. 本轮结论与下一步
- 可执行最小实验已跑：B-T1 给 partial（合成证据）；A 线三轮校准失败后按纪律停止归档；D5 描述性（C191）、ON3（C190）此前已收束。
- **不能声称**：机制 A 成立/否定、联合矛盾存在/不存在、双预算决策收益、迁移、新颖性。
- 下一步（若有新资源）：① A 线所需独立重复/更大网格/合成 ground-truth；② B 线若继续须 T2（O'Neil 仅描述、PEEK）或 T3（需真实报价/湿预算，当前 data_unavailable/cost_uncalibrated）；③ 用户优先的方向3（药物程序组合迁移）需真实顺序与功能数据（本地不存在）；方向4/5 需材料数据。
- 证据登记：C188–C195；`EVIDENCE_REGISTER`/`CLAIM_STATUS_AUDIT` 均 195 条、无缺号。

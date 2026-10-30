# Lead 裁定：D5 批准 **descriptive_only** 单次执行（confirmatory 不批准）

2026-10-28。依据：D5 经 v0.1→v0.4 五轮修订与两轮独立挑战；confirmatory 不可行（G3 MDE 上界 0.865/0.826/0.826 vs δ_min=0.10；需每药约 1,571 独立细胞系或认证 r_err≥0.987/0.985；配对/功能/batch 新测量缺失）；挑战者建议修完 D5.3 后 approve_to_lead_exec_descriptive。

## 批准范围（仅描述性，非 confirmatory）
- 冻结对象：`PROTOCOL_D5_v0_4.md` SHA `8a317664…`、`d5_v0_4.json` SHA `3d6fbf82…`、`d5_revision_v0_4.py` SHA `d4d627a1…`、report `67e02b0a…`、record `d6c3fcd9…`、usage（输出 SHA）；E7 tuning-grid SHA `4d3b6d02…`；v0.1–v0.3 冻结不改。
- 执行：EX-G0a（3 active drugs ≥20 合法线 22/24/24）→ **EX-G0b 先核**（compound identity/actual dose µM/vehicle identity/source/assay；失败→`active_dose_identity_unverified` STOP）→ synthetic timing test（不读表达/响应）→ 两跑逐字节一致 → 只报描述性字段。
- 硬约束：3,600 fits/run（6 tuned models×600）；1000×零模型（N1/N2/N3/N4/N6）；CPU cap **120 min**；超→`protocol_deviation` STOP（不得放宽 cap）；禁止 confirmatory/G3/G4 通过失败/`evaluation_cannot_distinguish` 推断；禁止 biology/功能/迁移/决策/机制/新颖性/真实轨迹；BRD3379 永不回 primary；功能 not_qualified、time_axis_unverified、RNA 代理≠功能。
- 解释边界（写死）：**本分析不检验时间预测是否成立；只描述 3 active drugs 的 per-drug Δρ/CI/MDE/room/reliability/per-fold 与 V2 exploratory；MDE/room 仅 precision descriptor；不推断 biology/时间预测/迁移/决策收益。** 冻结≠资源足够/关系成立/Stage1/效果。

## 若 Lead 需要 confirmatory
→ **stop**，记录测量规格（每药约 1,571 独立细胞系或认证 r_err≥0.987/0.985；配对/同细胞/批次/暴露设计；匹配晚期功能结局 viability/凋亡/再生长；V2 15–19 线仅 exploratory）。

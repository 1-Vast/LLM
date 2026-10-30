# Lead 裁定：R201-A 线停止归档（A.1/A.2/A.2.2 三次校准失败；不做 A.2.3 迭代）

2026-10-28。事实链：
- **A.1 P0/P1**：`p0p1_negative` 但**冻结行置换 null 校准失效**（null pooled 中位 .7457≫obs .1537），σ 尺度不一致（F_self 中位 .4579≠1）→ negative 不可解释（C192）。
- **A.2**：修正 σ 因子 2 与零模型选择后，A.2-EXEC **D2 失败**（F_self median .4153∉[0.5,2]；context 间半拆差强异方差；单一全局 σ 只校准均值）→ `design_invalid: scale_mismatch`，P1 未执行（C194）。
- **A.2.2**：R4 fuller-profile resampling 合成 eligible（coverage .875），但真实数据 **D2 失败（per-context coverage .6484<.85）+ D3 失败（worst-context FPR 1.0；context-FPR p95 .3184>.20）**；机制=**R4 σ² 在 S-add 违例下混入真实 profile 差异**（σ²_R4 中位 6×S1、p25≈0、重尾）→ 噪声尺度与真实差异不可分离 → `design_invalid: scale_mismatch`，P1 未执行（C195）。

## 裁定：停止 A 线（P0/P1）归档
- **不做 A.2.3 迭代**：三次失败的共同结构原因是 **O'Neil 4×4 技术重复不足以独立估计噪声**——任何基于 plan-pair 差或半拆的 σ 都只能把真实 profile 差异与噪声混在一起；改为"拟合 shared-f 后残差"会把待检违例吸收进 null，导致检验不可证伪。继续迭代零模型属于**在结果解释前不断换规则**，违反预注册纪律。
- **A.1/A.2/A.2.2 结果按下述解释归档**：A.1 `p0p1_negative` 仅"冻结 null 下未检出"；A.2/A.2.2 为 `design_invalid: scale_mismatch`；**均不构成"无联合矛盾/矛盾不存在"、不构成机制 A 阴性证据**；A 线未产生可解释的 P1 结论。
- **不进入 P2/S2/H_A2**；不称生物学/机制/迁移/决策收益/新颖性。
- **所需测量规格（升级条件）**：① 对同一 plan 的独立重复（独立 wells/plates/培养/日）以独立估计噪声，使 σ 与真实 profile 差异可分离；② 或更大 4×4 网格+重复以支持 per-context 噪声；③ 或合成 ground-truth（已知 shared-f 无违例/已知违例）验证检验的 type-I/power 后再用于真实数据；④ 决策收益需 ≈6,282 独立细胞（δ=.05）等（C189/C192/C194/C195）。

# report_scope —— R203-P1 决策终点/可达性/配对功效/两本账（设计报告）

2026-10-28。**状态：设计/规划；不运行效果、不拟合预测、不读响应/功能数据。**

## 1. 结论

1. **撤“≈6,282 细胞通用决策门”**：仅保留为**独立相关系数 Fisher-z 比较**的规划近似（δ=.05→6,283；δ=.10→1,573；n=30 MDE=.7625）；净效用/误选率/后悔/top-k/达标预算按各自独立单位/配对/cluster 分开规划。
2. **成功门先做可达性预检**：T1 `C7_experiment_only 451/500=.902`；`max_gain=.098<δ=.10`；通过需 **501/500** → **本批不可达**；保留 T1 partial、原 CI，不降 δ；未来先 headroom+MDE 预检。
3. **配对功效**：连续 `n=ceil((2.801585×SD(D)/δ)²)`，cluster `×[1+(m−1)ICC]`；二值用 discordant variance；技术重复≠独立背景；30 cells 仅在 `SD(D)≤δ√30/2.801585` 且无 cluster inflation 时够，典型 net utility/regret SD .15–.30 不足。
4. **机制 vs 药理两本账**：合成/计算只验证形式/算法/校准，不取得药理证据；真实决策收益需实测功能/暴露/独立培养/评估/功效/预算；两账预算/停止分开。
5. **下一项建议**：N1 合成状态依赖共享算子 + 决策后悔（机制账；与静态 S-add 停止配置不同）；N2 新合格功能资源 net utility（药理账；当前 data_unavailable）；均未运行，建议独立挑战。

## 2. 关键数字（规划算术；`power_scope.py`）

| 项 | 值 |
|---|---|
| T1 p0 / max_gain / δ / required | .902 / **.098** / .10 / **501/500** → **unreachable** |
| Fisher-z n δ=.05/.10 | **6,283 / 1,573**（仅相关比较） |
| Fisher-z MDE n=30 | **.7625** |
| net utility SD=.20 δ=.05 | n=**126**（cluster 6/ICC .5 → **441**） |
| net utility SD=.30 δ=.05 | n=**283** |
| regret SD=.15 δ=.05 | n=**71** |
| mis-selection p10=.20,p01=.10 δ=.05 | n=**911** |
| top-k p10=.15,p01=.05 δ=.05 | n=**597** |
| 30 cells 连续可检 SD 上限 δ=.05/.10 | .0978 / .1955（无 cluster inflation） |

## 3. 端点清单

| 端点 | 独立单位/配对 | 需实测功能 | 合成允许 |
|---|---|---|---|
| 净决策效用 | 独立培养/细胞背景；同单位配对 | 是 | 算法 only |
| 误选率 | 独立单位；配对二值 | 是 | 算法 only |
| 后悔 | 独立单位；配对连续 | 是 | 算法 only |
| top-k 命中 | 独立单位；配对二值 | 是 | 算法 only |
| 达标预算 | 独立实验；paired log-cost | 是 | 计算成本 only |
| 机制检测 | 合成 replicate/seed | 否 | 是（机制账） |

## 4. 两本账

- **机制账**：合成已知 ground-truth/噪声/可辨识/检测 power/FPR/参数恢复；compute-only；不能称药理/真实决策/机制/迁移；generator/校准失败→stop，不事后改 generator。
- **药理账**：合格实测功能/暴露/剂量/独立培养/独立评估/配对功效；真实 wells/plate/culture；headroom<δ 或 MDE>δ→stop；不降 δ；不用合成或 6,282 替代。
- **分账**：decision utility/regret/mis-selection/budget 属药理账；机制账不能升级；同一实验若两账并存须双终点/双停止，不得互相替代。

## 5. 下一项研究建议（未运行）

**N1（机制账）**：合成 state/sequence-dependent 非静态 S-add 的共享算子 + plan-pair conflict/unified revision；primary held-out decision regret（δ=.05）；等 compute/query 基线 full retrain/static S-add/hierarchical/GP/random/AL；同 generator/seed；headroom+MDE preflight；calibration/no increment→stop。**与已停止静态 S-add 检验的实质区别**：动态/状态依赖 + decision regret + 合成机制账，不是改名重做。

**N2（药理账）**：新合格实测功能资源上的 net utility（δ=.05）；独立培养/细胞背景为 n；同 wells/compute 基线；当前 data_unavailable；不拼 ΔEMAX；无功能/暴露/独立培养/功效→stop。

**顺序**：先 N1（低成本机制验证） + **AZ 2024 记录覆盖审计**（ERRATA 修正 4）；N2 仅在合格功能/独立培养资源取得后立项。均**不运行**；建议独立挑战。

## 6. 边界

- 不降旧门槛/不改旧判定（T1 partial、A.1 静态 S-add stop 保留）/不晋升代码/不恢复已停止实验/不做 A.2.3。
- 不称新颖性/机制/迁移/决策收益/独立确认；合成≠药理；技术重复≠独立培养；6,282 仅 Fisher-z；不拼 ΔEMAX。
- 设计 only；任何执行需另立预注册 + 独立挑战 + Lead 批准。

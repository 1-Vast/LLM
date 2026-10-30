# R203-P1 独立挑战（task-129）：决策终点/可达空间/配对功效/两本账

2026-10-28。角色：独立挑战者（非提案者、未参与 R203-P1、不运行效果/不拟合/不读响应或功能数据）。对象：[PROBLEM_DECISION.md](PROBLEM_DECISION.md)、[power_scope.py](power_scope.py)、[power_scope.json](power_scope.json)、[DESIGN_SCOPE.md](DESIGN_SCOPE.md)、[report_scope.md](report_scope.md)、[record_scope.md](record_scope.md)、用户复核 `2026-10-28-blocked-conclusion-review/report.md`、`ERRATA_R201_R202.md`、T1/A.1/R202 记录。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_scope_to_lead（仅批准"决策终点/可达性/配对功效/两本账"的范围与规划算术；不批任何效果执行、不批 N1/N2 执行、不恢复已停止实验、不改旧判定）。**

核验 PASS：
- **撤 6,282**：只保留 Fisher-z 独立相关系数比较 `N_req=2×(2.801585/δ)²+3`；δ=.05→**6,283**、δ=.10→**1,573**；n=30 MDE=**0.7625**；净效用/误选/后悔/top-k/达标预算按各自单位/配对/cluster 分别规划，不反推 30 细胞足够，技术重复≠背景数 ✓。
- **T1 可达性**：C7_experiment_only **451/500=.902**；`max_gain=U_max−p0=.098<δ=.10`；`required_successes=ceil(500×1.002)=501>500` → **unreachable_gate**；保留 T1 partial/原 CI、不降 δ；未来先 headroom+MDE 预检；基线近满分时"达标预算"另立问题 ✓。
- **配对功效**：连续 `n=ceil((2.801585×SD(D)/δ)²)`：SD .20→**126**，SD .30→**283**，regret SD .15→**71**；cluster `×[1+(m−1)ICC]`：m=6/ICC=.5→**441**；二值 discordant variance：p10=.20/p01=.10/δ=.05→**911**；top-k .15/.05→**597**；30 cells 连续可检 SD 上限 δ=.05→**.0978**、δ=.10→**.1955**（无 cluster inflation）——我逐项重算一致；假设（paired、同单位、iid/cluster）写清 ✓。
- **端点清单**：净效用 U(M*)−U(C)、误选率、后悔、top-k 命中、达标预算、机制检测；独立单位/配对/cluster/天花板/headroom；需实测功能 vs 合成可测的标注 ✓（个别定义需预注册细化，见 §2）。
- **两本账**：机制账（合成 ground-truth/噪声/可辨识/power/FPR/recovery；compute-only；可声称形式/计算能力，不可声称药理/真实决策/机制/迁移；generator 失败→stop，不事后改）vs 药理账（实测功能/暴露/剂量/独立培养/独立评估/配对功效；real wells；headroom<δ 或 MDE>δ→stop；不降 δ、不用合成/6,282 替代）；decision utility/regret/mis-selection/budget 归药理账；两账预算/停止分开 ✓。
- **N1/N2 建议**：N1（机制账）合成 state/sequence-dependent 非静态 S-add + plan-pair conflict/unified revision；primary held-out decision regret δ=.05 normalized；等 compute/query 基线（full retrain/static S-add/hierarchical-EB/GP/random/AL）；headroom+MDE preflight；generator/校准/no increment→stop；N2（药理账）新合格实测功能资源 net utility δ=.05，当前 data_unavailable，不拼 ΔEMAX，功能/暴露/独立培养/功效缺失→stop；顺序 N1+AZ 覆盖审计、N2 有资源后再立项 ✓。
- **边界**：不降旧门槛/不改旧判定/不恢复已停止实验/不晋升代码/不称新颖性/机制/迁移/决策收益；不运行效果 ✓。
- **算术/SHA**：power_scope.json 与 report 数字一致；`power_scope.py` 只做规划算术、无数据读取；`attestation` 与边界一致。

**结论：批准本范围/规划算术；N1、N2 仅可进入"预注册讨论"，不得执行；N1 必须先补生成器/可辨识/基线等价/等预算等细节；N2 当前 data_unavailable。**

## 1. 逐条判决

| # | 项 | 判决 |
|---|---|---|
| ① | 撤 6,282/Fisher-z-only | **PASS**：N_req 6,283/1,573；n=30 MDE .7625；端点分别规划；不反推 30 细胞；技术重复≠背景。 |
| ② | T1 可达性 | **PASS**：.902/max_gain .098/required 501>500 → unreachable；partial/CI/δ 保持；headroom+MDE 预检。 |
| ③ | 配对功效 | **PASS**：连续/二值/cluster/30 cell 上限算术正确；假设写清；示例一致。 |
| ④ | 终点清单/定义 | **PASS（个别需预注册细化）**：净效用/误选/后悔/top-k/达标预算/机制检测；独立单位/配对/cluster/headroom；合成 vs 实测标注；U/归一化/天花板需冻结。 |
| ⑤ | 两本账 | **PASS**：机制 compute-only vs 药理实测/预算/独立培养；决策收益归药理；两账停止/预算分开；合成不升级。 |
| ⑥ | N1/N2 建议 | **PASS（有条件）**：N1 方向可讨论，但"非静态 S-add"目前只是声明，需 generator/可辨识/基线/等预算证明；N2 资源当前 data_unavailable；未执行。 |
| ⑦ | 边界 | **PASS**：不降门槛/改旧判定/恢复停止实验/晋升代码；不称新颖性/机制/迁移/决策收益；设计 only。 |
| ⑧ | 总判决 | **approve_scope_to_lead**（范围/规划；N1/N2 预注册前不得执行）。 |

## 2. 下一步必须先补的实现/预注册细节（N1/N2 预注册前）

### 2.1 N1（机制账；合成）
1. **Generator**：明确定义 state/sequence-dependent 非静态共享算子（隐藏状态转移、时间/顺序依赖、plan-pair conflict 的生成方式、unified revision 的更新规则）；不得只是给静态 S-add 加一个静态分组标签。必须给出生成器代码/参数/seed/可复算 oracle。
2. **可辨识/校准**：已知 ground truth 下 state/参数恢复、噪声/FPR/校准、headroom/MDE；若 generator/校准失败→stop，不事后改 generator 或看结果换基线。
3. **基线等价/等预算**：full retrain、static S-add、hierarchical-EB、GP、random、AL 全部同 generator/seed/信息/参数调优预算/query 预算；static S-add 必须是**同信息同预算**的强基线；N1 只有在等预算下优于 static S-add 才可称"非静态"机制。
4. **Primary/决策终点**：held-out decision regret（δ=.05 normalized；归一化 U/utility scale 预注册）；headroom<δ 或 MDE>δ→stop；误选/top-k 只作 secondary/描述；不得把 regret 当准确率替代。
5. **实现/确定性**：两跑逐字节一致；JSON schema（每 replicate/seed/arm 的 state/regret/决策/成本）；无 telemetry 入核心 JSON；generator/校准失败类别；若 N1 只是静态 S-add 改名→`design_invalid: rename_static_Sadd`（或 stop）。

### 2.2 N2（药理账；真实测量）
1. **资源门**：新合格实测功能资源（独立培养/细胞背景、暴露/剂量、功能端点、独立评估），当前 data_unavailable；不得用 ΔEMAX/Jaaks 拼接、合成数据或同资源换端点。
2. **端点/功效**：net utility δ=.05（U 定义/成本/headroom 预注册）；独立单位 n、paired/cluster/ICC、MDE/headroom preflight；MDE>δ/headroom<δ→stop，不降 δ。
3. **预算/停止**：real wells/plate/culture 与 compute 同预算；无功能/暴露/独立培养/功效→stop；不进入 P2/S2/H_A2（保持 A 线边界）。
4. **顺序**：N1+AZ 覆盖审计先；N2 有合格资源后再立项；本轮不运行。

### 2.3 端点/算术的预注册细化
- `net_utility`：明确 U（收益−成本）、成本口径、独立生物单位、配对/同 context；headroom=U_max−U0；若 headroom<δ→unreachable。
- `mis_selection`/`topk`：p0 天花板、discordance p10/p01 来源（不得从目标结果估）、配对二值 MDE；若 p0 已近 1，达标预算另立端点。
- `regret`：归一化尺度（与 U 同单位）、配对/ICC、MDE；不得从准确率推 n。
- `budget_to_target`：paired log-cost、独立实验单位、预注册目标阈值；不是 6,282 的替代。
- `mechanism_detection`：合成 replicate/seed、检测 power/FPR/参数恢复；只属机制账。
- 所有端点：独立单位 ≠ well/technical replicate/key/plan；cluster 单位/ICC 预注册；30 cells 不是通用充分条件。

## 3. Lead 批准文本（建议）

> **批准范围**：批准 R203-P1 的**范围/规划算术**：撤"6,282 细胞通用决策门"（仅保留 Fisher-z 独立相关系数 6,283/1,573 的规划含义）；确认 T1 C7 451/500=.902、max_gain .098<δ=.10、required 501/500→**unreachable**，保留 T1 partial/CI、不降 δ；采纳配对功效公式（连续/cluster/二值/30-cell 上限）与端点清单；采纳机制/药理两本账分离（合成只验证形式/计算；真实决策收益需实测功能/暴露/独立培养/独立评估/配对功效；decision utility/regret/mis-selection/budget 归药理账；两账预算/停止分开）。
>
> **不批准**：任何效果执行、N1/N2 执行、旧门槛/旧判定修改、已停止实验恢复、代码晋升、合成升级为药理、6,282 作为通用决策门。
>
> **N1/N2 仅进入预注册讨论**：N1 必须先补 generator（state/sequence-dependent 非静态 S-add + plan-pair conflict/unified revision）、可辨识/校准、与 static S-add/full retrain/EB/GP/random/AL 的等信息/等预算/等 query 基线、regret δ=.05 normalized 的 headroom/MDE preflight、两跑/schema/失败类别；若只是静态 S-add 改名→stop/design_invalid。N2 在合格实测功能/独立培养资源取得前 data_unavailable；不拼 ΔEMAX，无功能/暴露/独立培养/功效→stop。N1/N2 均不得在本批准下运行；执行须另立预注册+独立挑战+Lead 批准。

## 4. 声明

- **本轮不运行效果/不拟合/不读响应或功能数据**：只读 R203-P1 产物与 T1/A.1/R202/ERRATA 记录；只写本文件与 `tmp/`；未改 R203 产物。
- **总判决：approve_scope_to_lead**（范围/规划算术批准；不批效果/N1/N2 执行；不改旧判定）。N1/N2 可进入预注册讨论，但 §2 细节必须先补；N2 当前 data_unavailable。

**一句话：6,282 撤得对（仅 Fisher-z 6,283/1,573、n=30 MDE .7625）；T1 .902/max_gain .098/required 501/500→unreachable 且保留 partial；配对功效（126/283/441/71；911/597；30-cell 上限 .0978/.1955）算术正确；端点/两本账边界清楚。N1 目前只是"非静态 S-add + conflict + regret"的声明，必须补 generator/可辨识/等预算 static-S-add 基线证明不是改名重做；N2 当前无合格实测功能资源——判 approve_scope_to_lead（仅范围/规划；N1/N2 仅预注册讨论，不执行）。**

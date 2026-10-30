# Lead 批准：R203-P1 范围与规划算术（仅范围；不批效果执行）

2026-10-28。依据：R203-P1-C1（i003）判 **approve_scope_to_lead**；算术逐项重算一致（6,283/1,573、n=30 MDE .7625、T1 .902/max_gain .098/required 501/500→unreachable、配对功效示例、30 cells SD 上限 .0978/.1955）；机制/药理两本账与边界 PASS。

## 批准内容（仅范围/规划）
- **撤"≈6,282 细胞"通用决策门**：仅保留为独立相关系数 Fisher-z 比较规划（δ=.05→6,283、δ=.10→1,573；n=30 MDE .7625）；净效用/误选率/后悔/top-k/达标预算分别规划；不反推 30 细胞足够；技术重复≠背景数。
- **T1 可达性**：C7_experiment_only 451/500=.902；max_gain .098<δ=.10；required ceil(500×1.002)=501>500→**unreachable_gate**；**保留 T1 partial/CI、不降 δ**；未来 headroom+MDE 预检；基线近满分时"达标预算"另立问题。
- **配对功效公式与端点清单**：连续 `n=ceil((2.801585×SD/δ)²)`；cluster ×[1+(m−1)ICC]；二值 discordant variance；端点=净效用/误选/后悔/top-k/达标预算/机制检测；各自独立单位/配对/cluster/天花板/headroom。
- **机制/药理两本账**：机制账=合成 ground-truth/噪声/可辨识/power/FPR/recovery（compute-only；可声称形式/计算能力；不可称药理/真实决策/机制/迁移；generator 失败→stop 不改）；药理账=实测功能/暴露/剂量/独立培养/独立评估/配对功效（real wells；headroom<δ 或 MDE>δ→stop；不降 δ、不用合成/6,282）；decision utility/regret/mis-selection/budget 归药理账；两账预算/停止分开。

## 不批准
- 任何效果执行、N1/N2 执行、旧门槛/旧判定修改、已停止实验恢复、代码晋升、合成升级为药理、6,282 作为通用门。

## N1/N2 仅进入预注册讨论
- **N1（机制账）**：须先补 generator/隐藏状态转移/plan-pair conflict 生成定义、可辨识/校准、**"static S-add 同信息同预算强基线"等价实验**；primary held-out decision regret（δ=.05 normalized）；headroom+MDE preflight；两跑/schema/失败类别（含 `design_invalid: rename_static_Sadd`——若 generator 实际退化为静态即停）；generator/校准/no increment→stop；**不是静态 S-add 改名重做**。
- **N2（药理账）**：当前 data_unavailable；须先有合格实测功能/暴露/独立培养/独立评估/配对功效资源；不得用 ΔEMAX/合成/6,282 替代；资源门/功能端点/功效/预算通过后才立项。
- 顺序：N1 预注册设计（不运行）+ AZ 2024 导出覆盖审计；N2 资源取得后另立；均须独立挑战 + Lead 批准。

# Lead 批准：R204-M3 Stage2 合成分配诊断执行（支撑研究/机制账；compute-only；0 wells）

2026-10-28。依据：R204-M3-S2.1-C1（i003）判 **approve_exec_v0_2_to_lead**；13 失败类别、per-arm 13 字段/判据、R=10 sample 语义/每 arm 预算、17 文件链/Stage1、独立 seeds/两跑、G1–G6、caps/schema/边界均 PASS。

## 批准范围（仅 Stage2 合成分配诊断执行一次）
- 批准 M3 Stage2 **合成分配诊断执行**（支撑研究/机制账、compute-only、0 wells）；**不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- 冻结 v0.2 链：PROBLEM_M3_S2_EXEC_v0_2 `FE9180FA…`、DESIGN_M3_S2_EXEC_v0_2 `2569079C…`、exec_plan_m3_s2_v0_2.py `C85C1AEA…`、json `F16D1C04…`、schema `987089F8…`、report `0B473A50…`、record `9E934D80…`；执行前重核 17 文件 SHA（含 Stage1），不匹配→`design_invalid: chain_mismatch`。
- 执行 seeds：data **20261401**、replicate **20261401–20261410**、arm a,r seed=**20261411+10a+r**（20261411–20261470）；与禁用集交集 []/unique；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独；不得改 seed。
- Stage2 环境：一步 DR H=3/A=3/Y∈{0,1}；p/μ/b/π/m/C_H=20 冻结；R=10；每 replicate initial/behavior 300 units + 6 arms×300 alloc → **2,100/replicate**、总 **21,000 units**、allocation/feedback **18,000**；每 arm n_alloc=300/feedback=300/tuning≤20/caps/合法包；六 arms（shared-score/random/GP uncertainty/decision_AL/optimal_experimental_design/DR+MLE）同 learner/updater/预算。
- G1–G6；**per-arm 13 字段/判据/失败映射**；13 失败类别（含 chain_mismatch）；caps **1800s/2h/8GB/0 wells**；schema 先写；**final-implementation pilot（2 reps×6 arms×300 alloc）实测并冻结 canonical**；JSON 无 telemetry；π=b/截断/共线/分离/支持规则。
- **不输出 decision utility/regret/top-k/学习效果比较**；分配诊断不得解释为决策收益/学习效果；标准 DR/TMLE+最优分配等预算复制/超过判定留 Stage3。
- 非阻塞执行备注：DR gap 报告统一写 0.0/≤1e-12；Stage1 pilot 仅历史参考不得当执行 pilot；per-arm allocation_Q/variance/clipping/equal_budget_audit 仅诊断字段；每 arm 独立 300 alloc/feedback 不共用评价。

## 不批准
- Stage3/真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把分配诊断写成学习效果比较；把 DR/TMLE+最优分配等预算复制/超过写成本轮结论（留 Stage3）；改公式/阈值/端点救结果；代码晋升；旧判定修改；恢复已停止实验。

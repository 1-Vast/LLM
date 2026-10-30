# Lead 批准：R204-M1 Stage2 合成诊断执行（仅机制账；compute-only；0 wells）

2026-10-28。依据：R204-M1-S2-EXEC-C1（i003）判 **approve_exec_to_lead**；12 文件链、独立 seeds/两跑、唯一 Pθ/reward 有界、C-MDN、H1 容差表/H2/H3、G1–G6、B1–B5 spec-only、caps/schema、停止/边界均 PASS。

## 批准范围（仅 Stage2 合成诊断执行一次）
- 批准 M1 Stage2 **合成诊断执行**（机制账、compute-only、0 wells）；**不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- 冻结链：PROBLEM_M1_S2_EXEC `F7ED4520…`、DESIGN_M1_S2_EXEC `503618F4…`、exec_plan_m1_s2.py `CFF1C734…`、exec_plan_m1_s2.json `3DC88FEF…`、schema_m1_s2_exec.json `181A77E3…`、report `24D7BE22…`、record `B6D1DA69…`；执行前重核 12 文件 SHA，不匹配→`design_invalid: chain_mismatch`。
- 执行 seeds：Pθ param/train/eval 20261301/02/03；H1 16 cells 20261310–25（d/N 固定顺序、容差表 N 顺序写死）；H2 ε 20261326–30；H3 20261331–32；two-run reps 20261340–49；禁用 C208/Stage1 20261112–13、M1 v0.2 20261201–03、M2 Stage2 20261200–39、M2 Stage3 20262100–39、M3 20261500–99；overlap=[]/unique；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独；不得改 seed。
- 执行内容：唯一 Pθ（X64/A4/Y4 box[-2,2]^4；3 分量截断 GMM/对角协方差/条件异方差/无 Student-t；train4096/eval2048）；reward r∈[−5.2,.375]；target Q GL64/dim、target 样本不作标签、Doob 不可执行；C-MDN 规格；**G1/G2/G4/G5/G6 门 + G3/H1/H2/H3 诊断**（H1 超容差→projection；H2 至少一 ε 收敛/marginal≤1e-8；H3 small-case TV≤.05 仅诊断）；B1–B5 仅规格不执行比较；**不输出 decision utility/regret/top-k/方法比较**。
- 预算：caps 1800s/2h/8GB/0 wells；**执行前用最终实现实测训练+规划 wall/CPU/内存并冻结 canonical timing**（不得只用 planning/单测数字；Q_g GL64/dim、H3 GL128/dim、H1 16 个 C-MDN 需实测；仍须<8GB）；schema/失败模板先写；失败只写 12 类 design_invalid。
- 非阻塞执行备注：H3 仅 small-case、不得当高维 oracle；H1 容差 N 顺序不可反序/转置；pilot 参考非实测；两跑逐字节。

## 不批准
- Stage3/真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把一步投影/B2 等价写成 M1 增量；把 H1–H3 合成诊断当效果；H3 small-case 当高维 oracle；改公式/阈值/端点救结果；代码晋升；旧判定修改；恢复已停止实验。

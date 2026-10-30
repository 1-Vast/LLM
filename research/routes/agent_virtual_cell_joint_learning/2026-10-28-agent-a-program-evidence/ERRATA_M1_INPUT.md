# M1 输入资格更正

2026-10-28。原 report.md 与 verification_v1.json 使用 SHA `90DE7498…22C57` 的旧 M1 输出。该运行的生成器尺度偏离冻结协议，已登记 `invalid_run: protocol_deviation`。原报告的 H1 16/16、H2、H3 数字只是在无效输入上的算术核对，**全部不作为资格通过证据**。此前协调者核了保存数字，却漏查生成器尺度，现明确纠正。

正确冻结尺度的 [C216 重跑](../2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json) 为 H1 **0/16**、H2 **5/5**、H3 **0.0134035243**，判定 `design_invalid: projection`。不改变旧输出或门槛，不将实现/评估失败解释为药理机制失败。详见[共享纠正](../parallel-coordination/root-corrections-20261028/CORRECTIONS.md)与[本轮实证资格报告](../2026-10-28-agent-a-proximal-program-pilot/report.md)。

原报告的精确反例“汇总 TV=0，背景×动作条件 TV=1”独立于这个无效运行，仍可反驳汇总指标足以保证条件预测的推论；它不证明实际拟合模型发生过反转。后来的 H1b 是另一项统计量，不能追认旧 H1 通过，须按其实际可见维度另读。

# 运行前澄清与保留分歧

2026-10-22。后读 root 的最终数值前澄清；`PRE_RUN_REVIEW.md` 保持原样，不回写为无条件赞同。此文与后续审计均不读 raw CSV、不重新拟合、不追加检索。

前两项已解决：所有 log readout 为 `log2(raw mean+1)`，比率为 raw D/(raw L+1)；选 direct/kinetic family 使用 6-dose-trained、refit 前 validation score。最终代码亦如此实现。

第三项保留实质分歧：反方倾向 selected optimizer 未收敛时 abort，以免长外推建立在未完成的局部解上。root 在数值前选定另一明确规则：300 nfev 是有界 forecast program 的一部分；有限可行的 status0 迭代可出预测，保留 success=False，不声称参数收敛；异常/invalid/nonfinite abort。四个 start 全不收敛则标 `UNQUALIFIED_FOR_MECHANISM`，不得依赖这类结果推广机制/core，禁止按后期分数加 cap 或换 start。

反方接受这种规则可以定义一个可审计的**有界预测程序**，不接受将其结果表示为已优化的动力学参数或强 BESTDR 基线。数值前明示、完整报告 cap/winner 统计、固定预算，足以允许其作为预声明 forecast diagnostic；primary direct 信息对比与参数收敛不同。若一个未来科学结论依赖 capped kinetic 收益，仍须补独立、预注册、优化质量合格的检验，而不能静默晋升。

root 另报告一次真实数据前 synthetic failure：重复 rate 附近的旧 matrix-exponential fallback 使改变 clearance 影响 L。已保存原失败输出；改为 exprel 的 exact S/I 及固定 32-node positive convolution 计算 D，独立 solve_ivp 核对随机/退化参数，9 tests 均过。修复未改变科学模型、参数边界、start、cap、split、终点或阈值；属于 pre-data numerical repair，不是科学失败后调整。

后续审查观察到实测已在 prefix cache 完成、首次读取训练标签时因 `invalid_observed_readout` abort。此为预声明数据完整性规则生效，尚无主要或支持性信息对比分数；当前不能写 biological/conditional-information null。详细事实与 hashes 将另存 POST_RUN_REVIEW/AUDIT，不改 frozen protocol 或失败产物。

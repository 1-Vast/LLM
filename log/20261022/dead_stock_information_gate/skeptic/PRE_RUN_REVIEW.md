# HCT116 gate 运行前独立反方审查

2026-10-22。审查对象：`HCT116_GATE_PROTOCOL.md`，本次读取版本 SHA256 `85983bddc7aef7db96a4c1d98590004fa5e030d8169565d4adbca27535ee0675`。已完成独立稿并在之后读支持方独立稿；与支持方真实交叉问答正在进行。本审查未读任何数值 CSV、响应数组、模型实现或拟合/预测结果，未拟合、未追加 GET。先前 source-only 阅读不等于未暴露于作者公开结论。

**结论：对这一窄条件信息 gate 给 conditional GO。** 当前没有新算法或已辨识的新生物机制。下列三处实现含义须在第一次响应数值访问前书面锁定；这属于消除实施歧义，不建议增加候选模型、时间点、搜索预算或事后分组。

1. **特征数值语义。** `log2D0`/`log2D24`/全部 logD 必须明确是 `log2(raw mean D+1)`；`D/(L+1)` 中 D、L 均为固定三 img 的原始算术平均，而非其 log 值。该比率仅是 readout 特征，不是死亡概率。浓度 canonical string 的确定规则亦应写进可审计实现，避免同一数值因字符串格式改变内验证组。
2. **pooled-family 内验证访问。** 选择 direct/kinetic 家族时，direct 的 inner-validation 预测必须来自只在 6 个 inner-training dose 拟合的选中配置。不能使用选后在 7 个 outer-training dose 上 refit 的预测作为该 validation 成绩，因为其中包含 validation 目标。refit-on-7 仅服务该 fold 的 outer-dose 预测。kinetic 的验证与 outer 局部拟合均只读本孔前缀。
3. **动力学求解失败语义。** `least_squares` 达 max_nfev 但给出有限参数/预测，仍可能 `success=False`。须预定对各 start 和最终被选中 start 的处理，保存全部状态，不能见后期 LIVE 误差后决定是否接受。最小可审计办法是用既定 prefix robust loss 按规则选定 start，若 selected fit unsuccessful 或非有限则显式 abort；允许其他预锁规则，但不能默默去掉失败孔或增加 starts/budget。每孔 live-only 的 L 预测不能从 D0 或 c 获益，实施应测试这种隔离。

## 已充分约束的关键点

- DoseResponse-only，并明确不用可能复用的 Replicates 数据补外部 n；同孔三 img/时点不拆分，mean ROI readout 不冒称全孔真实细胞总数。opaque seed 不解释为独立 run、密度或生物背景。
- 同一完整 0–24h L 前缀、时间、剂量和 context 给全部臂；唯一主要信息差是合法 D 前缀。relative 72h 是未来 exported live-labeled readout，不假称给药后时间或真实 viability。
- 八 dose LOCO 及固定 hash 的内验证，是同药物/细胞/来源且已见 context 下的未训练浓度预测；不是全局未触碰测试或八个独立研究任务。代码整体数值前冻结、本 fold 标签不进本 fold 拟合/选择、先存全体预测再统一评分，是适当的边界。
- 14 个 direct 配置/臂/fold、公平标签和 scaler、train-only 特征处理、独立内验证选参/选族、固定混合均已声明。无总 equal-compute 或 agent/RSI 的越界声称。
- 有未知参数、受伤存活 compartment 和 clearance 的普通动力学对照，比只给“已知固定 r、D 旁观”的三角方程更合理。固定 r 的非作用测试只是代数结构审计，不是生物证据。该小 ODE 不替代完整 BESTDR 的随机/测量噪声/层级后验强控制，阳性需后续补充。
- 主要终点是未来 LIVE；D0、D24 对照阻止将静态校准包装成死亡历史贡献。主要阈值 `.05 log2` 且 `10%` 是预定实用门槛，不是噪声下限或显著性。逐 dose 结果和 bootstrap 只能描述这八个 dose 的敏感性。
- direct null 不能证明所有额外 D 无信息；动力学/pooled 明显受益时如实记 mixed/model-dependent。所有预定臂均无实用收益则停止此 24→72h 应用，不换未来 D、joint score、端点或新模块救结果。

## 仍然无法由本 gate 解决的科学解释

即使 full D history 超过 L-only、D0、D24，仍可能是噪声/标记/分割的时间变化校准，或普通未知参数联合推断，不能直接辨识高 turnover、真实损伤、phase 或 D→L 因果。来源文本目前未证明 live 是 total−dead，也未证明不存在共享测量误差；只能保留可能性，不把缺元数据写成生物阴性。不同 dose 的受控预测也不等于跨药物或跨实验运输。

本 gate 若阳性，当前只能推进“该 readout 前缀有条件预测信息”的独立复核与观测机制鉴别；若阴性，只停止已注册应用。世界模型同信息优势、agent、普通重训/CL/AL、继承、联合收益与 improvement-of-improver 均未被测，宏观目标仍未完成。

审查范围限制：本稿仅审设计与科学解释，尚未做实现审计或结果审计。响应数值前需由 root 留存最终协议和代码哈希及上述澄清。

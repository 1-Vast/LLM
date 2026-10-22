# OASIS G0 开放数值前独立代码审查

2026-10-22，Asia/Shanghai。审查对象为 `research/oasis_dev_g0_20261022/dev_qc.py`、`test_dev_qc.py` 及本目录 `PROTOCOL.md`。仅阅读代码、协议和此前开放的身份汇总；没有打开任何新 raw/count/CNN 数值、selection/reserve 或其他封存结局，没有运行数值实验。本审查记录的是开值前状态，后续修补应另记 amendment/复核。

## 决定

**数值访问边界未发现需要重设计的阻塞。一个资格失败报告可被 NaN/零方差破坏的小缺陷应在开值前修复，再可执行 G0a。** 这不是算法或生物证据放行；是否通过由冻结门槛和实际 dev 结果决定。

## 实际缺陷：无动态范围数据可能无法形成失败报告

`repeat_summary` 直接把 Spearman、2000 个 bootstrap 的 `np.quantile` 以及 `mean(discrepancy²)/variance` 放进 JSON。恒定 endpoint 会产生 NaN correlation/CI，variance=0 还会产生除零；即便全体有变化，某些 bootstrap 若不包含少量提供变异的组，也可出现不可定义相关。`save_json(...allow_nan=False)` 和最后 `json.dumps(...allow_nan=False)` 会拒绝 NaN/Infinity，导致本来应该清楚记录 G0a FAIL 的数据情形以异常结束。

最小修补：非有限相关、不可定义 bootstrap CI 或非正 variance 均明确作为资格失败处理，诊断值用 JSON null 配合原因标识；保留冻结阈值，不用删掉不利 bootstrap draws 或改 seed 来使其通过。若 summary 无有效变异，输出 failure reason 与计数，不宣称通过。对这个退化分支加一个小型合成不变量测试即可；无需开放任何真值来重现。

## 已审查通过的关键数据流

- dev 名称由冻结 reservation 中 `role=dev` 的已开放身份表导出，只附加 exact-name `DMSO`；`scan_allowed` 使用明确输入列与 compound predicate。数值导出前再次要求角色集合包含且仅包含 dev/control。selection/reserve/quarantine 不会因共享 plate 被整板导出。
- 原始 raw 文件及 count 来源按已有 manifest SHA256 核验。Parquet 混合 page 物理解码与向优化导出的区别已在代码/协议中如实披露。
- 去重按规范化 batch/plate/well 的物理键；同孔 compound、dose、四个 raw 值须相同才允许保留一次。count 来源也按物理孔核身份/浓度/count 冲突，join 声明 one-to-one，并核对 raw/count compound-dose 相同。
- controls 统计仅用 DMSO；药物数值不会改变其他药物的 plate 归一化。MT log ratio、LDH robust-centered asinh、count log-centering 与协议一致。没有使用作者 ridge-normalized 结局。
- 非有限值、非正 MT、无 count 及失败 plate 的 acquired dev observations 均计入原始 denominator，报告失败而非标为阴性。大于等于 90% 覆盖、至少 100 paired chemical groups、双 endpoint 的 correlation/CI 门槛是事先声明的可证伪配置。
- bootstrap 重抽样单位是 chemical group，dose/repeat 没有被误称独立药物。五折分配直接依赖 group_id，角色与组来源固定；现有 fold 测试只重写了 hash 公式，删除它不会减少主数据流已有证据，正式 G0b 应直接检查实际模型预测表的组/折完整性。

## 非阻塞边界与需要保留的限制

1. `pairs_for_repeat` 接收 `eligible`，因此实际是先按 QC 保留再选 lexicographic first two plate。若一个动作存在第三个 plate，早先失败的 plate 可能被替换，和协议“独立于值选 first two”有潜在差异。此前身份审计显示 dev action 都是两物理孔/plate，八孔例外处于 quarantine，当前无需因此改变设计。若身份事实不符，应先在 full dev identity 上冻结 pair 再评价有效性，不得用第三个良好响应替代失败孔。
2. 每个 endpoint 报告的是 pooled technical reproducibility。共享 plate、位置效应或 dose 梯度可贡献相关，chemical-group bootstrap 不能证明培养独立或完全消除 plate 依赖。G0b 中所有对照共有 row/column/batch，并单独报告技术因素是必要条件。无认证 positive injury control，不做 Z-prime 或生物 dynamic range 宣称。
3. `raw_ldh_net_identity_max_abs_difference` 目前是诊断，没有冻结容差或 pass/fail；它不参与资格通过，不能事后把差值小解释成独立测量链认证。现有源审计 raw 非缺失；如果重新取得的源出现 NaN，此诊断也要以 null/失败原因安全输出，不能扩展 allow_nan。
4. 程序读取固定文件路径并认证源资产；开值前的执行记录仍应保存 reservation、protocol、code、manifest 和导出 schema 的 hash。仅代码里存在固定路径不等于输入文件内容不可更改。
5. G0b 尚未在本文件实现，不能根据 G0a 单元测试宣称其训练折预处理、CNN 白名单、group-weighted OOF 指标或 simultaneous gate 已通过审查。

## 后续最小动作

修复非有限 summary/零方差分支并保留失败输出；重新运行原不变量与一个退化数据测试，冻结新代码 hash。随后依照既定 protocol/opening receipt 仅开放 dev/control，执行 G0a；门槛失败就停止该配置，不能通过改 endpoint、QC、CI 或保留更佳 plate 救结果。未发现需要在开值前下载大数据、运行新世界模型或调用 LLM 的理由。

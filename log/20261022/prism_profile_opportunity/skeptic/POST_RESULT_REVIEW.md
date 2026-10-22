# 独立结果复核与停止建议

2026-10-22。结论：**STOP_BULK_PROFILE_COVERAGE；不拟合，不调整本合同。** 这是固定两池→大部分剩余面板配置的可观测性失败，不是任何预测模型的性能阴性，也不否定整个 partial-profile、world 或 RSI 研究方向。总体科研目标仍未完成，本阶段未发现或验证新核心。

## 独立执行和可复核性

本代理先封存独立协议稿、实际 cross、counter-only 程序与三项合成测试，再接受 root 对 COVERAGE_FREEZE.json 的一次执行授权。独立实现是在看过 root 代码后编写，不能宣称盲写；它不 import root 程序。真实源只运行一次，maestro Python `-B`，exit 0，elapsed 3.0418256 秒，stdout/命令/耗时在 INDEPENDENT_EXECUTION.json。

执行后、阅读 root/peer 数字之前，独立结果已封存为 SHA256 `f37f5968323872e6d7b366b7749e75cb743cb8290c73fcbf8f03343992055471`，见 INDEPENDENT_RESULT_SEAL.json。随后才阅读 root 结果与 INDEPENDENT_COMPARISON.json：**50,575 项精确整数/身份检查通过，0 mismatch**，包含全部化合物资格、四组计数、逐 pool 计数、七板分母和全局门。本人再次核对 freeze 中 28 个绑定文件，全部未变。没有重复运行比较脚本覆盖 root 已保存的比较文件。

## 冻结门实际结果

| 集合 | 原始化合物数 | 化学 purge 后固定数 | 联合合格数 | 冻结最低门 |
|---|---:|---:|---:|---:|
| source | 763 | 565 | 54 | 300 |
| development | 256 | 211 | 0 | 80 |
| test | 255 | 255 | 33 | 179，即原始分母 70% |

test 七板 PREP040/PREP026/PREP038/PREP035/PREP024/PREP041/PREP033 的原始分母分别为 38/33/40/31/39/35/39；合格数分别为 **0/0/0/0/0/33/0**。所以六板各十例、全部七板非零两个门也同时失败。五项全局门全部 FAIL，无边界模糊。

每个化合物必须同时满足：P933 X1≥19/23，P904 X1≥20/25，unpaid X2≥347/433，unpaid X3≥347/433。不能以单独的 replicate 通过数、某一板或总体有限比例代替四条件联合门。

实际检查 retained 1031×914＝942,334 个许可槽，其中 705,191 finite。总体约 74.8% 只能描述这些槽，不满足按化合物、反馈池和审计面板联合定义的任务资格，也不能推翻上述停止决定。

## 信息权限与成本

独立程序对所允许 token 瞬时执行 float→isfinite→计数；没有存储 response 数组、强度、相关、排名或预测分数。读取 CSV 时会对整行全列进行词法 tokenize，因此不能声称完全没有接触未购字节；数值转换严格限于 retained compounds 的 48 paid-X1、433 unpaid-X2、433 unpaid-X3 槽。未购 X1-unpaid、X2/X3-paid 和 purged compounds 不转换，合成 poison 测试已覆盖该权限。

1031 个尝试任务的全部 942,334 槽与对应 39,178 个逻辑 pool bundles 应保留记录，不能只对最终 87 个跨集合合格化合物收费。原始 test 的 255 个任务均保留 acquisition attempts/分母。该计数包含 evaluator audit；不等于政策可用反馈，更不等于 39,178 次真实湿实验。相同发布数据的独立 counter 复核只增加读取/CPU，不产生新的生物观察。source 的未来完整三 profile 训练若发生应另计 60 bundles/compound；本阶段没有训练，不能将它冒称已执行。

数据审计方通过消息报告其直接对既有 bool mask 的独立地址/分母/逐 pool 复核 **41,423 检查 PASS**，未重读 raw response、未 import root 程序。此为对方实际报告；本人的独立 raw finite-counter 与 root 的一致性由已读 50,575-check artifact 支撑。

## 结果后的实际双向交叉

支持方同意停止这个 fixed two-paid-pool→433-context bulk 配置，不拟合、不换 pool/板/阈值，也不把 PREP041 的 33 例重包装成新 test；全局有限比例不能替代逐化合物门。其最强反驳是：这只是 coverage 失败，不能外推所有 partial catalog 不可能；当前 33 例仅可作既定 mask 描述，不能据此判断 update-value 异质性、C4 或 world/RSI；P904 的零通过数不能归因生物机制或 assay 损坏。

本人实际答复：全部接受。尤其“0 个通过 paid-pool 门”不是“所有 response 值为零”，本阶段没有计算响应强度，不能作药物无效或实验损坏归因。

数据方同意所有尝试不退款，区分 logical payload、parser contact 与额外复核计算。本人追问：既然 missingness 已知，未来按它挑新 pool 是否仍可叫预注册/fresh holdout？数据方实际答复：不能。那是 post hoc / selection-exposed 的新任务，必须在新合同列出选择历史和数据权限，不能回写、复活或重新命名这次 STOP。本人同意；没有剩余实质分歧。

## 后续边界

当前不进入普通模型机会实验，不提出 world/agent/selector/继承/RSI 收益。PREP041 的 33 例不能替代原七板合同；不能看现有 missing 模式换池后宣称原资格成功。如果未来选择 partial-profile 或另一数据源，需要独立记录新应用、暴露/选择历史、观测权限、强直接模型与公平成本、可证伪主张和新的成功/停止条件。已有阶段的失败应继续保留，而非用新定义擦除。

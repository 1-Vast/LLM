# OASIS G0a 独立结果审计

2026-10-22，Asia/Shanghai。评定：**Ready within reviewed scope / Share with caveats；Complete（限本次开发区 G0a 算术、来源、配对及结论边界）**。未修改既有研究代码、协议、门槛或结果。应用 data-analytics:validate-data 的数据验证流程，交付形态遵守本任务指定的仓库审计记录，不另建网站或商业报告。

## 独立结论

**原 G0a FAIL 已复现；没有发现导致该失败的数值计算、dev 过滤或配对错误。** 覆盖和化学组数量通过，但两个 endpoint 均不满足冻结的 Spearman/区间门槛。不能据此推进原协议的 G0b，也没有下载 CNN。

MT 的 Spearman 0.324 与 repeat MSE/pooled variance 0.094 并不矛盾：MT 的 Pearson 是 **0.95337**，但绝大多数振幅集中在近零区域，少量极端读出承担大部分幅度方差。可称为**测得的响应幅度稀疏/重尾**；尚不能称为稀疏真实损伤、稳定生物学机制或临床安全可预测性。

## 原始来源与独立计算覆盖

本审计未 import 或调用 `dev_qc.py` 的任何函数。两个独立脚本只读取已开放 dev 导出、固定名单的 dev/DMSO 原始 raw 及 count 来源谓词；原始源可能内部解码混合 Parquet pages，但未导出或使用其他角色数值。没有打开 OASIS selection/reserve/quarantine outcome，没有读取 CNN、原图或其他封存来源。

- 对 68 个原始 biochem 来源重新核 hash，仅按冻结 dev 药名或 exact DMSO 投影 raw/身份列；所有 10,256 个 dev 物理键与四项 raw 值和导出逐项相同。
- 所有 dev 名称的角色与化学组核回 v2 reservation。不存在重复物理孔扩样、dev 分区误混或 raw/count 条件不一致。
- 重新计算每个 plate 的 DMSO MT 中位数、MT robust CV、LDH 中位数/MAD，和 controls CSV 相符；最大浮点差小于 `1e-16` 量级。独立重读 dev/DMSO count 投影后，count、控制中心与 count_input 全部重合。
- 用导出全菜单先按身份选择首两板，再独立 pivot 形成 compound-dose pairs；5128 个身份 pair 的值和 `pair_pass` 与 CSV 对齐。CSV 浮点剂量以 `1e-12` 相对容差匹配，无数值或响应大小参与选择。
- Spearman 用平均秩的 Pearson 独立实现；组 bootstrap 重新抽样 2000 次、原冻结 seed，未复用研究的 summary helper。两个相关和两个区间逐值复现。
- `PRE_OPEN_FREEZE.json` 的 **80 个输入 hash 全部一致**。hash 检查读取文件字节而不解码其数值角色。

完整可执行计算分别为 `research/oasis_dev_g0_20261022/independent_result_audit.py`、`independent_count_audit.py`；独立结果在本目录 `independent_audit/RESULTS.json` 与 `COUNT_AND_FREEZE.json`，控制台另存。主重算约 13.2 秒，无拟合、API 或新下载。

## 复算结果与冻结决策

| 项目 | 独立结果 | 冻结判据与决定 |
|---|---:|---|
| dev 菜单 | 641 标签、400 化学组、10,256 物理孔 | 与原报告一致 |
| 合格物理孔 | 9,708 / 10,256 = 94.6568% | >=90%，通过 |
| 缺失 count | 548 孔 | 全部作为失败观测计费/报告，非阴性 |
| 身份 pair / 合格 pair | 5,128 / 4,581 | 547 pair 未通过固定 QC，无第三板替换 |
| 合格 pair 化学组 | 400 | >=100，通过 |
| MT Spearman [95% group bootstrap] | 0.324329 [0.258492, 0.397231] | <0.60，且下界<0.50，失败 |
| LDH Spearman [95% group bootstrap] | 0.170898 [0.132922, 0.217167] | <0.60，且下界<0.50，失败 |
| MT repeat MSE / pooled variance | 0.0540101 / 0.574700 = 0.0939797 | 原本是诊断，不能替换主要门槛 |
| LDH repeat MSE / pooled variance | 1.875849 / 1.194336 = 1.570620 | 同上 |

543 个 count 缺失来自先前身份阶段已见的三块显微镜/metadata 排除 plate：`41002695` 194 孔、`41002696` 170 孔、`41002698` 179 孔；其余五孔分散四板。因此覆盖损失可追到 metadata 来源，不是本轮按不利 MT/LDH 挑样。

全部 4,581 个合格 pair 跨 batch：prod25/prod26 563、prod25/prod27 1805、prod26/prod27 782、prod26/prod30 1431。现有 CI 条件于这些 plate/control 以及固定配对；化学组 bootstrap 没有重新采样新培养批次，也不认证独立培养、重复实验或供体。

## MT 指标差异：幅度损失与排名稳定性不同

若两次读数的方差接近且均值偏差较小，`MSE / pooled variance` 约等于 `2*(1-Pearson r)`。这里 Pearson r=0.953370，与 0.09398 的幅度误差比例一致；它不要求 Spearman 也很高。

MT 两侧中位数均约 0.008；两侧四分位范围分别约 `[-0.085, 0.105]`、`[-0.094, 0.117]`，而下端极值到约 -6.8。两板在强幅度尾部相当一致，中央多数近零值的精细排序却较不稳定。以下完全是事后解释，按 pair 的 `max(abs(x),abs(y))` 排序，不定义可发表的 injury 子群，也不修改合格集。

| MT 幅度最极端的 pair 比例 | 对全部 pooled squared deviation 的贡献 | 去掉后剩余 Pearson / Spearman | 去掉后 repeat MSE/variance |
|---:|---:|---:|---:|
| 1% | 52.353% | 0.90896 / 0.30356 | 0.18282 |
| 5% | 92.017% | 0.40915 / 0.21734 | 1.18415 |
| 10% | 93.465% | 0.16726 / 0.13480 | 1.66690 |

LDH 不呈现同样的高幅度一致性：全体 Pearson 仅 0.22097，最极端 5% 的 pooled deviation 贡献为 18.574%。不能用 MT 的重尾解释替 LDH 达标。

**门槛与用途存在需要保留的差别。** G0a 注册的是全菜单 rank reproducibility，G0b 注册的是平方误差信息增益；前者不是后者的数学必要条件。在以极端响应幅度为效用的未来独立任务中，低全菜单 Spearman 不必等于完全没有可预测信息。因此本次适当结论是“这套已冻结的双 endpoint、全菜单排名入场配置失败”，不应扩大成“OASIS 无法预测”“形态没有信息”或“世界模型不可能有价值”。这项解释不改变本次 FAIL，不许可事后换 Pearson 放行。

## 观察问题与审计覆盖

以下分母是本次审计定义的组件/结论单位，不是全面软件测试率；没有图形或交互页面，相关项不适用。

| 科研审计表达质量 | Observed defects | Assessment |
|---|---|---|
| 问题/停止条件完整性 | 0 / 2 | 原 rank gate 与停止动作均可复算；未来 MSE 用途的边界需随报告保留 |
| 指标表达清晰度 | 0 / 2 | MT/LDH 各自完整；幅度和排名的差别已说明 |
| 图形/交互一致性 | N/A | 本次未生成图形或交互页面 |

| 分析正确性与稳健性 | Observed defects | Assessment |
|---|---|---|
| 来源与角色 | 0 / 3 | raw/count/reservation 三条来源核验；没有证明 OS 级保密 |
| 数值计算 | 0 / 5 | 覆盖、controls、变换、pair、bootstrap 独立复算 |
| 数据质量边界 | 0 / 3 | 缺失、重复、技术重复单位均保留；生物学真值未认证 |
| 结论支持 | 0 / 3 | FAIL 成立；未声称形态、世界模型或 RSI 被否证 |

优先后续处置：保留原停止决定；本次不运行 CNN/G0b，不新设阈值或评价终点挽救结果。若将来研究真正不同的幅度/决策任务，应先重新明确独立用途、噪声/损失、强基线和未触及数据，再另立协议；不能把本次事后尾部诊断写成预注册支持。

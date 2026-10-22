# 最终反方实现审查：GO 一次已界定普通结构试验

2026-10-22。基于已保存独立意见、实际双向交叉问答、最终协议、实现静态阅读和合成测试执行记录，支持根代理冻结并执行当前配置一次。未读取真实 DATA/ROWS/ZIP response 或 targets；未运行真实 prepare/fit/GET；没有数值表现或创新性成功结论。本结论不撤销任何历史阴性冻结。

## 已闭合的关键问题

1. **单位与对称信息。** 固定 inhibitory fraction identity；保留有限越界；所有方法共享两 witness 的完整 paid 输出。target attached mono 在所有 role 禁止源字段访问，test target inhibition 在 inputs 阶段不转换。paid 另一 partner 的任一 drug-dose mono 均值缺失现在也触发共同整 episode 弃权，避免 offset 为 None；不换 witness，仍计费两 bundles。
2. **推荐动作与共同样本。** nominal 全网格 top5 仅用 predictions/paid u/v，global row tie 规则稳定；predictions/actions/selection 三者在 testtarget 转换前封存并校验。U panel 是 valid_input AND 整 nominal matrix target finite，分母全部 nominal episodes；forecast/U 都要求每个预分 MASTER 至少贡献一个 episode，否则资格 STOP。
3. **强比较者与预算。** 48 次 train-only selection 的所有 validation predictions 用于 MAE/U 分别选参；候选同规则；offset config×eta 共同选，mixture 用对应 endpoint 组件与固定五权重。ordinary comparator 按对应 endpoint 验证成绩锁定；唯一 `(base arm, config)` 最终 refit 缓存最多 14 次，所有组件都记录成本。两个终点可选择不同参数，只能支持同家族两策略。
4. **指标与推断。** driver 已使用 `forecast.mae`、`recommendation.utility/regret` 统一 accessor；bootstrap lower 返回字段已一致。MAE/U 都按 episode→MASTER→macro，配对 bootstrap 10,000 次、seed 20261022，双主门交集要求绝对/相对实用增益及 lower>0；baseline regret≤.02 关闭推荐扩展。load 对照 DESIGN.role_cells 和 nominal episode 完整性，不能静默丢 MASTER 后缩小人群。
5. **报告义务。** 全 arms 与 effect/dose、full/combo_direct 的配对比较、mixture/enumerator、missingness by role/cell/pair/input reason、logical/unique paid 成本、fit 和全阶段耗时均有输出。plateau 由有效 nominal inputs 定义，再分别计双有限 response pair 与缺失 pair；支持盒来自 train+validation 有限训练点。诊断为相关行/点对描述，不改变主 panel 或发现规则。

## 实际检查与验证证据

实际读过最终 `MEASURED_PROTOCOL.md`、`design.py`、`prepare.py`、`models.py`、`metrics.py`、`driver.py`，以及 prepare/driver 的合成测试源和以下执行记录：

- `PREPARE_SYNTHETIC_TESTS_04.txt`：9 项 PASS，覆盖禁止字段 guarded access、targetmono/testtarget/reserve poison、canonical axis/精确剂量均值、观察零/缺测/结构 padding、共同弃权（含 partner mono 缺失）、角色冲突、三封存哈希先于 ZIP open、无覆盖。
- `MODELS_SYNTHETIC.json`：6 项 PASS，11 次合成 pipeline fit/16 次内部 solve、四次合成 reference estimator fit；不是实际 source 表现。
- `METRICS_SYNTHETIC.json`：9 项 PASS，nominal top5、完整 U panel、显式 MASTER/零贡献、宏聚合/paired bootstrap 等合成合同。
- `DRIVER_SYNTHETIC_03.txt`：6 项 PASS，真实 metrics 参与的 MAE/U 不同配置、config×eta 共同选择、角色与唯一 paid means、历史预测隔离/lex tie、fit→seal→evaluate 全路径、48+去重 refit、nominal global actions、封存篡改在 evaluation marker 前拒绝、预分 MASTER 缺失拒绝、目标混入输入拒绝、门的绝对/相对/headroom/CI/coverage 边界。

这些测试的执行者是相应实现代理；我实际检查源与保存输出，没有重复跑相同测试或声称独立生物数值复算。完整 pipeline synthetic 使用 fake estimators，真实 sklearn 模型合同由独立 models synthetic 覆盖，不能将两者称作真实生物 fits。

## 此次审查快照 SHA256

根代理随后应把代码、schema、设计、协议及评审证据一并纳入 pre-response freeze；若实质方法改动，应更新审查，不能沿用本结论掩盖变化。

| 文件 | SHA256 |
| --- | --- |
| driver.py | `f6de7623f8f138505bd08a223cd857741a74a1d9f4bb6f051134678cfa6f1d97` |
| metrics.py | `19cc673a3f61e531a736759d5a55b3bab07f42c3af827a0206b9d4fbfd3468b7` |
| models.py | `a30dae2ead97c1171c2cc09f1d09e02b624ba4c6a4a2879a446efc1eb5879253` |
| prepare.py | `a4d8c84bf66700c9778252dc371cad21ff0c5207a3cbff6f7ade953635b5024e` |
| test_driver_synthetic.py | `32be8c88a44b6c4744263ccc467df3d0bad6514031551bbe409325bb7a11aef9` |
| MEASURED_PROTOCOL.md | `ea0680bf410ec77a074d1adf67643df74a0ccee30971450ec3f56a54293c8f3d` |

## 科学结论边界

这是一项源内静态 functional-state compression/transport 的普通结构机会试验，effect/RBF、offset、mixture、枚举都属于普通方法。mixture 与 enumerator 能复制 effect；匹配不能写成战胜它们，也不抹掉结构实证。episode-balanced 拟合不同于 cell-balanced；模型单位不是独立培养实验；complete-case 覆盖不证明缺测可忽略；.02 不是实测噪声/临床阈值；U 不是 source HSA 或因果/临床 synergy。

解析上每 episode 的 local offset 是常数，不改变 `Yhat−max(u,v)` 的 top5 排序；mixture 中这项也只是常数平移。它是预测校准对照，不能称作新的推荐动作适配。浮点近 tie 不能支持额外机制。

最终落盘期间根代理已把这一解析等价补入协议；我实际复读该段并更新上表协议 hash。advocate 随后实际交叉确认相同代数结论。该解释性补充没有改变数值菜单或停止规则。

双主门任一失败则停止当前配置对后续复杂扩展的支持，保留小正效应，不重调已暴露 test。即使通过，也至多支持普通 source-specific 结构性质；新核心、世界模型、研究智能体、继承收益、联合收益和改进策略的 RSI 仍 NOT_ESTABLISHED/NOT_TESTED，需要后续保留任务与实质新机制。413 reserve contexts 本阶段保持数值未开。

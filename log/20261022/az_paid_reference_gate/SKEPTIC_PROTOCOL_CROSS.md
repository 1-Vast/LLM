# 反方实际交叉问答与修订协议审查

2026-10-22。保留 `SKEPTIC_INDEPENDENT.md` 和 `SKEPTIC_PROTOCOL_REVIEW.md` 原稿。本记录在实际双向消息后写入；不把预想问答当成独立评审。反方未读取真实 DATA/ROWS/ZIP response、未运行真实 prepare/fit、未发起 GET，也未独立复算生物学结果。

## 与 mechanism_advocate 的实际双向质疑

1. 我问：effect、local offset、mixture 和枚举若被普通方法准确复制，是否仍会将结果包装为新改进算子或胜过等预算搜索？对方接受所有这些方法均普通；mixture 可在端点复制 effect，枚举可选择 effect。结构偏置的实证不因匹配消失，但不能据此声称新算子、程序搜索优势或 RSI。

2. 我问：训练每 episode 总权重相同、评价每 MASTER 总权重相同是否被错误叫成 cell-balanced？双方接受预定 episode-balanced 拟合，明确这与 cell-macro 评价目标不同，所有方法同规则即可，不在数值结果后改权重。

3. 我问：已支付 48 组配置的 validation predictions，为什么推荐比较者只在 MAE 优化后的四个模型中选？对方接受对所有已付费配置按 endpoint 分别选参；offset 共同选择 config×eta，mixture 使用该 endpoint 对应组件，重复 refit 缓存并计费。根代理已实际修订为最多 14 个唯一最终 refit，而非旧四次承诺。

4. 对方反问：若只评价固定 top5 的 U，是否有必要要求全部 nominal matrix target finite？我的回答：没有数学上的普遍必要；当前完整 matrix 是同时支持预封动作 U 与 full-grid oracle/regret 的简单充分规则。另一个纯 fixed-action U 设计可预先定义所有臂动作并集的共同可评分规则，但不是本次协议。当前不得目标开后从 finite 菜单重新挑 top5，也不得声称 95% 覆盖证明 MCAR。双方接受整矩阵共同 panel 和条件解释。

5. 我继续反问：分别按 MAE/U 选两个 effect 配置，只能支持同一家族的两项任务策略，不能说一个同参模型同时胜出，是否同意？对方明确同意；单模型双终点主张需要以后在未暴露任务上预定单一配置或多目标规则。这也不能替代智能体、联合或继承收益。

## 与 functional_auditor 的实际双向质疑

1. 我要求 U 完整覆盖分子必须是 `valid_input AND all nominal target finite`，分母全部冻结 nominal episodes；两个独立 95% 门不能代替交集 95%。数据审计方同意，根代理的修订协议已写明此交集。

2. 我问：零贡献 MASTER 如何处理 bootstrap？对方建议每个已分配 MASTER 在 forecast/U 各自至少贡献一个 episode，否则 qualification STOP；bootstrap 在通过后使用完整预分 cells。双方同意，避免事后缩小宏评价人群。

3. 我要求确认 train 残差也不能用 target attached mono、各 role 的 target mono 禁止访问、direct 获得全部 paid 输出。对方实际检查 prepare：scanner 只有 paid 转换 lib1_y/lib2_y；train/validation target 只转 inhibition；test target 在 inputs 不转任何 outcome。paid 残差只用 paid 自身分组平均观察 mono。direct/without_mono 的信息合同由代码与合成测试检查；episode reset 仍需 driver。

4. 我问：episode-balanced 与 cell-macro 的差异是否可接受？对方同意明确命名且全臂共享，无需现阶段更改为 cell-balanced。

5. 对方反问：按 U 从所有普通配置选推荐比较者会改变旧四 refit 预算，是否接受先限定为 MAE 优化策略中的最佳 U？我的回答：较窄规则本身合法，必须准确限定 claim；但当前根代理已采更强版本：既有 48 次 selection fit 的 predictions 分 endpoint 选参，候选同规则，config×eta 共同选，unique(base arm,config) 缓存最多 14 次最终 refit，所有成本记录。因此 selection fits 没增加，额外实际 refit 前置计费，解决该预算问题，不再维持旧四 refit 承诺。

## 已实际审查的修订与代码

已读当前 `MEASURED_PROTOCOL.md`、`design.py`、`prepare.py`、`test_prepare.py`、`models.py`、`metrics.py`，以及 `PREPARE_SYNTHETIC_TESTS_01.txt`、`MODELS_SYNTHETIC.json`。此处对测试 PASS 的记载来自已保存执行记录与测试源代码审查，不声称我重复运行或已独立数值审计。

- 固定 inhibitory fraction identity，不依数值分布自适应除 100；有限越界保留，.02 是源单位实用代理阈值。
- canonical 药物 ID/Decimal 剂量、按目标 A/B 端点选 witness、query/target pair 全局隔离、MASTER 角色隔离，静态合同一致。
- scanner 禁止 target mono/fitted fields 的 raw 索引；`canonical(target)` 仅对空的已过滤 observed 字典 `.get`，并不读取源 target mono。
- paid encoding 包含完整 mono/combo、零值与 missing observation mask、结构 padding mask；without_mono 删除 paid mono 和 u/v。mono poison 改变 full 而不改变 without_mono。
- prepare 合成测试九项 PASS，包含 guarded field access、禁止字段与 testtarget/reserve poison 不变性、缺测共同弃权、方向互换、精确剂量均值、封存先于目标访问、禁止覆盖。它们只证明合成接口，不是实际数据表现。
- models 静态实现：共享 episode 权重；effect/dose 同 26 基函数和 residual；ridge intercept 同罚；direct 两家族/网格如协议，训练 mask 内先切片再访问 y。合成 model 测试记录 PASS。
- metrics 静态实现：`make_actions` 不接收 y；所有 nominal rows 上 stable global-index top5；`evaluate` 要求每有效 episode 有固定动作。U 只计 valid input 且整 nominal matrix finite；forecast 用共同 finite rows；覆盖分母保留全部 nominal；MASTER 显式列表并返回零贡献；bootstrap 要求全部对齐有限 MASTER 向量。

## 当前判断与剩余边界

四项主要协议接口问题已在文本解决。静态 prepare/models/metrics 及已保存合成结果支持继续完成 driver 审查，**此记录尚非全流水线最终 GO**。仍需实际检查 driver 的 48 次 selection、endpoint-specific comparator/config/eta/mixture、最多 14 个唯一 refit 缓存及成本、test nominal action 与 prediction 一并封存、testtarget 后资格 STOP 不排名、完整预分 MASTER bootstrap、训练 rectangle/plateau 的前置定义与不筛主 panel。

保留局限：源内回顾 oracle、观察 mono 与 target 的噪声/归一化谱系、与历史 Jaaks 来源重叠、complete-case 选择、固定 seed/单次 source 切分、无临床剂量约束。不得将这些局限误写成已证明泄漏或永远不可学；也不得将普通结构 pilot 通过写成新颖核心、世界模型、研究智能体、继承、联合或 RSI 已建立。上述能力仍 NOT_ESTABLISHED/NOT_TESTED。

## Driver 首次静态 cross 发现（真实输入前）

根代理首次提供 `driver.py` 后，我实际读取并即时反馈两项问题；当时未运行 driver，故这是静态发现而非已发生的数值失败。根代理正在并行修订，最终结论另存最终实现审查。

1. 初版 driver 将 score 结果当成顶层 `mae/utility/regret`，而实际 metrics 返回 `forecast.mae` 和 `recommendation.utility/regret`；bootstrap 返回 `lower/upper`，初版却读取 `ci95`。若不修正，将在 model selection 或最终分析 KeyError。要求使用统一 accessor 并真实 metrics 联调，不能仅用形状不符的 stub 通过测试。
2. prepare 的 valid 只检查 target-required mono 与完整 paid combo；另一个 witness partner 的全部 mono 缺失可能仍 valid，但 mean_residual 为 None，offset_values 会在 valid episode 上 raise。要求根代理与数据审计在真实数值前明确共同缺测合同并补反例，不在见数值后选择性修复。

其余初版 driver 结构符合预期：48 次 train-only selection；config×eta 共同选择；endpoint 各自 ordinary comparator；唯一 `(base, config)` 缓存最多 14 次 train+validation refit；test 不参与拟合；nominal action/prediction/selection 一并写 hashseal。仍待真实 metrics 接口修复、合成 pipeline、完整成本/归因/支持及 plateau 诊断。

后续实际闭合：已读更新 `prepare.py/test_prepare.py` 与 `PREPARE_SYNTHETIC_TESTS_04.txt`。任一 paid drug×exact dose 缺有限 mono 均值会通过 `all_mono_doses_finite` 触发共同整 episode 弃权，保留所有原 purchases，不换 witness；个别 raw mono 缺失但同剂量仍有有限观察可照预定均值使用。新增 partner_mono 反例通过。目标打开前现在同时验证 predictions/actions/selection 三个哈希，篡改在 ZIP open 前拒绝的合成断言通过。上述 offset None 合同缺口已解决。

已实际读更新 driver：nested metric accessor 与 bootstrap lower 接口已修；新增全部 paired arm 比较、支持/plateau 诊断与成本输出。`DRIVER_SYNTHETIC_01.txt` 的四项合成测试通过并执行了 fit→seal、48+去重 refit 与 nominal action 索引检查，但该版测试尚未运行 evaluate stage。已要求补真实 metrics 参与的 synthetic evaluation、已注册 missingness by role/cell/pair/reason、stage 完整耗时，并澄清 plateau flag 用 nominal input 定义而非由目标 finite mask 改变。最终审查另存。

额外解析等价已发根代理和 advocate：`eta×offset` 在每 episode 内是常数，给 `Yhat−max(u,v)` 的全部 nominal row 加同一常数，数学上不会改变 top5；因此 offset 只校准预测 level，不能实现新的推荐动作适配。mixture 中的 offset 也仅贡献 episode 常数。统一 grid 可保留并完整计费，但不能把该分支的 U 表现误称为决策更新或智能体贡献；浮点近 tie 不构成科学反例。

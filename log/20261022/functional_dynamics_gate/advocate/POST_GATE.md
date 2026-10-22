# HTS001 measured gate：支持方最终裁决与实际交叉

2026-10-22。**STOP_THIS_SIMPLE_CONFIGURATION；总 goal 仍未完成。** 保留实际反馈和常规收缩的小观察，不推进本 scalar net-growth/shrinkage 作为新世界模型／agent／RSI 核心。

独立审查先存 `POST_GATE_INDEPENDENT.md`，之后主动向 scientific_skeptic 问两题并回答其反问。实际原始消息为 `POST_GATE_RAW.md`。双方无核心结论分歧。本次只读冻结协议、结果、模型冻结与 hash；没有 fit、network、test retuning、HCT116 response access 或新实验。初次完整读取 RESULT／MODEL_FREEZE 已暴露其中 test target／prediction 数值，随后改用字段投影避免无关数组输出；不声称这些结果仍未见。

## 决策依据

| 已冻结 test 比较 | macro MAE / 差异 | 结论 |
|---|---:|---|
| local ψ0 → inherited ψ1 | .303590122 → .230026401；改善 .073563721／24.23% | 相对门槛通过，预定 .10 绝对门槛未过 |
| fixed .5 mixture、same-grid search | 均 .230026401，逐项预测相同 | 完整复现；历史学得此规则的必要性／算法新颖性不成立 |
| ordinary full-prefix refit | .229255816 | 此配置平均误差略低于 ψ1，未见独有修复收益 |
| validation-selected direct | .179085944 | 此配置平均误差低于 ψ1；候选不达推进门槛 |
| direct/world .5 blend | .178211404；较 direct 仅低 .000874539 | 不支持有用联合收益；osimertinib 反而从 .170624 变到 .220531 |

真实观察不能因 failed gate 删除：共同 fresh θ、同 feedback 时，三留出药的收缩 ψ1 相对全信局部斜率 ψ0 都有较低 MAE。但 osimertinib 差仅 .000601333，整体只有3 drug clusters；420 wells 不增加到420独立研究任务。三药 bootstrap 正下界不作为确认性统计支持。

保留的措辞是：**此 screen 的既定34h→约60h外推中，结合早晚斜率比全信最近斜率的平均误差更低；固定 .5 混合即可取得这一表现。** 不扩写为普遍可靠 inheritance、适应新生物机制或程序递归改进。

direct 在 train+validation refit、ψ在 train only 选 alpha 是已冻结的训练资料使用不对称，限制“世界模型结构普遍不如direct”的解释；不能据此普遍否定 world bias。它不挽救本配置：普通 full refit／preset mixture／same-grid search 的比较已阻止独有贡献，且协议不允许事后给ψ补validation再测试同test。

## 实际交叉与裁决

我问：是否可保留上面的小观察，同时停止 learned-rule 必要性？反方答可以，fresh-start gain 不能抹去；fixed mixture/search 完整复现已足够停止新操作／必要性主张，absolute gate 仍失败。我接受。

反方问：是否把 bootstrap 正下界或 blend 微小变化当继承／joint 支持？我明确拒绝；三药只 descriptive，ordinary full refit 更低、blend 对 osimertinib 变差，均不支持 joint framework／extra agent。

我问：HCT 双通道应有什么新增可检验问题，才不是重命名本次失败？双方确认：**另一个 gate 应先问真实 dead-stock 是否在相同 live-prefix／起点下，对后续真实 live/dead readout 有额外信息价值。** 需要 live-only vs live+dead，并与同信息 multivariate direct、普通 BESTDR 含 clearance/measurement/refit/层级共享、simple mixture／equal-budget search 比较。先锁 endpoint／联合评分／预算，不能只把一个 alpha 换两个 κ 以挽救本失败。

HCT stock 不等于累计 death events，没有累计事件时不得称真实 b/d 定位；单 cell line、单 cisplatin 的 doses/wells 不是跨药物任务流，未认证 run 也不能宣称 cross-run inheritance／RSI。这个新问题有可能值得另测，但本次审查没有打开HCT数值或执行该实验。

## 本次结论边界

被停止：这个单率 linear net-growth＋一标量 shrinkage 配置的扩展；其新算法／智能体必要性与达到 useful-gain 门槛的主张。不得改 split、window、endpoint、alpha grid 或阈值重测同 test。

未测试：birth/death 双通道增量、dead clearance 的解释能力、完整 stochastic BESTDR、实际 acquisition／AL、完整 CL、research-agent 行为、跨 biological run 的程序继承及 Ω 学习 ψ 的效率。不能将它们写成因本次失败而全被否定。

可保留：真实 prefix→later count 的数据与同信息 strong direct baseline、readout refresh／refit 的作用、普通收缩的有限观察、freeze/search-equality 的可审查结果。这些是研究证据与后续基线，不是用户总体目标已达成。

freeze 中三项 script/protocol/source SHA256 经本地 read 核对一致；root 报告7项 synthetic tests通过，skeptic最终48项不重拟合核查通过。我没有把这些软件核查等同生物机制或跨run性能确认，也没有重复执行已经通过的测试。

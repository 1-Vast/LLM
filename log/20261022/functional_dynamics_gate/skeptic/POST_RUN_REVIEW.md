# HTS001：实现与已冻结结果的独立审查

2026-10-22。仅读 `hts_gate.py`、对应 synthetic tests/执行文本、冻结协议、identity split、MODEL_FREEZE 与 RESULT。**不重跑 fit，不导入 gate 模块、不载入 pickle、不打开原始生物 CSV、不新增网络。** 另写 `research/functional_dynamics_gate_20261022/skeptic_postrun_audit.py`，仅对现有 artifact 作独立分组计分、hash、选择和静态调用顺序审计；`POST_RUN_AUDIT.json` 的48项检查全部通过。根代理原有七项 synthetic tests 的文本为 pass，本代理读了其代码，但没有重跑。

**裁决：这一次 within-screen exploratory gate 的数值与主要结论有效，可保留；STOP_THIS_SIMPLE_NET_GROWTH_SHRINKAGE_CONFIGURATION。** 未发现需要重跑拟合的泄漏、模型选择或计权错误。该停止不能扩大为“反馈/继承无用”“无预测 headroom”或所有功能动力学任务失败。

## 有效性检查

- 当前实现与协议 SHA256 均匹配 MODEL_FREEZE。identity split 为14药按预定 hash 分8/3/3，整药不交叠；1960个 eligible 非控制孔，没有结构性排除，train1120、validation420、test420。
- `prefix_features` 只转换 initial<=24h 和 feedback24–34h 的计数；target time 可用作已知时间/预测 horizon，但 target count 只在独立 `targets` 调用中转换。其他 future count 保持原 CSV 字符串，既不参加插值也不参加归一化。`np.interp` 对 prefix 区间外采用边界携带，未借用未来端点。所有输入都来自合法前缀；direct 同样取得 r0/r1、最新状态、时间/剂量/背景。
- alpha 的11个 trial 只含8个 train drugs，最小训练宏 MAE 对应0.5；普通搜索单独遍历同11项并选择0.5。direct 的14个预定配置只用3个 validation drugs 选择，赢家为 `extratrees_None_3`，随后 train+validation refit。未保存/选择其他配置的 test scores，没有 best-test direct 选择。
- 代码先保存选定模型与所有 test predictions 的 MODEL_FREEZE，再读取 test target 计数，之后没有 fit。文件本地顺序亦相符。静态代码、hash与冻结记录支持该执行顺序；这不是密码学封存/可信外部时间戳证明，`test_target_values_accessed:false` 本身也不是独立泄漏证明。
- 独立重算13种已保存预测的 drug→background→dose→well 宏 MAE 及逐药分数，与 RESULT 一致。test 为3药×7背景×10剂量×2孔，420个唯一孔；macro 没有把孔/帧当药物 n。样本权重实现与指定层级一致；direct 的 scaler 只使用允许训练资料，regressor 收到对应拟合权重。训练时完整合法 prefix 的多时点只产生每孔一个 forecast example。
- 独立检验 inherited 的仿射预测等式、search逐项相等、fixed half-mixture逐项相等及direct/world half-blend等式均通过。本次保存预测均有限且 `log2(N+1)>=0`，没有出现负 count 反变换边界问题；不因此把线性 log-count 斜率解释为 birth/death rate。
- RESULT 的三组 contrast 与预冻双条件阈值、`advance_signal=false` 一致。原始 count 诊断只覆盖实际访问的 prefix/目标；本审查未认证全部未用 future/control count 的数值质量。

## 结果与必须保留的正、负信息

目标为 `log2(cell.count+1)`，越低越好：

| 方法 | Test macro MAE |
| --- | ---: |
| 局部 refit ψ0 / alpha1 | 0.303590122 |
| 继承 ψ1 / alpha0.5 | 0.230026401 |
| 普通全 prefix refit | 0.229255816 |
| validation-selected direct | 0.179085944 |
| direct/world固定半混合 | 0.178211404 |

**共同 fresh start 下，ψ1 确实比 ψ0 改善0.073563721，即24.23%。** 三个 heldout drug 的宏改善都为正：dactolisib0.080037694、osimertinib0.000601333、temsirolimus0.140052135。可以保留“本screen三个预留药物上，温和混合早期与近期斜率比完全信任近期斜率更好”的小观察。不能因为更强方法获胜抹掉这一描述性反馈/更新收益，也不能把全正方向变成可靠总体继承证据。

但该收益没有达到预冻0.10绝对阈值；相对强 direct，ψ1反而多0.050940457 MAE，且普通全 prefix refit 也略优于 ψ1。更关键的是，ψ1 的420项预测与**预定固定0.5混合、普通同网格搜索完全相同**。这足以否定本轮“需要继承学习此规则”“新 updater/search 算法”的特有效果；历史调参的成本未换来超出固定半混合的收益。不能要求候选胜过自己的等价实现。

固定 direct/world 混合相对 direct 仅改善0.000874539（约0.488%），且 osimertinib MAE由0.170624变差到0.220531；不能据此宣称 joint framework 值得扩展。它也不是被训练的 agent，三个药的结果不足以稳定估计一般组合收益。

## 预算、外推与物理限制

direct 获得14配置 validation 选择并最终 train+validation refit，updater 只用 train 学一个 alpha；这是已明示的、更有利于 direct 的共享训练条件，不是严格相同总训练信息或墙钟预算。无需为挽救失败削弱 direct；结果只停止这份配置。ordinary search 的“等预算”是同11项程序和同训练计分，不是证明整个世界模型/agent 与 direct 的总计算成本相同。RESULT 约7.35s是整个 gate 时间，不是每方法独立成本，也没有证明真实 assay/query、API或实验时间节省。

只有3个 test compounds、同一 screen、每背景只有一 plate，background 与 plate 混淆。3-drug bootstrap 为条件性描述；观察到三个 gain 都正会使其重采样下界也正，这不提供独立-run继承的统计确认。420孔不是420个研究任务，也不能当生物 run。多药亲缘/共同靶点还可能存在；按整药分割不等于 scaffold/MoA 外推。

测量是 nuclei/live-count proxy，状态是 `log2(N+1)`，r 是该坐标每小时斜率。本试验不测 death events、dead stock、clearance或潜在状态转换；既不验证真实 birth/death 通道归因，也不能否定另有合格 readout 的双通道研究。若将来另考察 HCT116，必须先建立新增 dead-stock 信息对真实后续功能的价值，并与同信息多输出 direct、普通 BESTDR clearance/measurement/refit/共享及简单混合比较；不能只把一个 alpha 换为两个 κ 来逃避本轮停止。

## 可宣称与不可宣称

可宣称：这一次完整预定测试上，常规收缩较局部 refit 有描述性更新收益，但由固定混合/普通搜索解释；强直接预测更好，预定扩展门槛失败，因此停止当前简单配置。存在可利用预测信息，不以某一个模型或对照成败断言无 headroom。

不可宣称：新算法、必要 learned updater、可靠跨 run/细胞背景继承、birth/death机制、world-model独立优势、agent改进、AL节约、完整 CL、joint框架、或改进器进一步变得更会改进。后六类在此没有对应实证归因。普通更新继承的狭窄描述结果已经测过；其独立生物泛化和用户要求的 RSI 仍未建立。不得把本次审计或七项 synthetic tests 当作这些能力证据。

实际 postgate 交叉消息也已完成：支持方确认保留共同起点的小收益、停止 learned-rule必要性，不把三簇 bootstrap 当统计确认，并接受将来双通道必须先验证新增真实信息的要求。其独立 postgate 稿在本代理发送审计结论前未读取；原始协作消息由双方分别保留。没有用代理一致性代替生物证据。

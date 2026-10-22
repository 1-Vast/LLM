# 独立倡议：早期 dead stock 对后续 LIVE count 的条件信息价值

2026-10-22，mechanism_advocate。已读本轮 ROOT_PROTOCOL，**未读本轮其他 agent 稿、数值或新 DeepSeek 输出**。无网络、响应 body、代码实现或拟合。只提出一个窄经验候选，不复活 HTS001 scalar shrinkage／two-κ。

**独立判断：值得一次预冻结的真实信息增量 gate；当前新算法 NONE，独有生物机制未成立。** 主张是 early dead-stock 是否在完整 live prefix、剂量、初始读数、相对时间和合法 context 之外，对后来真实 LIVE count 有实用外样本增量。预测 dead 更好、拟合 b/d 更漂亮、joint loss 被 dead 项改善，都不能代替这个主张。

## 1. 唯一候选经验性质与一个可能解释

经验性质：

> 在 HCT116/cisplatin 的既定 assay 中，早期 live trajectory 近似相同但 dead-stock histories 不同的条件，其后续 LIVE count 有可外推的差异；这一差异不是只靠浓度、起始读数或 opaque context 标签已能解释的，而且足以降低预设 LIVE endpoint 的误差。

这是条件预测性质，不是 `D→L` 的因果断言。Dead 是染料／成像定义的 stock，不是累计事件，不能把 ΔD 当死亡数；未确认 treatment zero 时只作从首次可用观测起的相对时间预测。

一种有明确假设的解释是**早期被净增长掩盖的高周转，遇到后期增殖抑制后分开**。设早期 `r0=b0-d`；若后期出生率变成 `q*b0`、死亡率仍近似 d，q<1，则 `r_late=q*r0-(1-q)*d`。同 r0 时，较高 d 将有更低后期 live growth。早期 stock 若经正确 clearance／marker 模型能提供 d 的额外证据，便可能预测这一差异。

这要求 q、死亡持续性和 observation model 等额外假设；**常率 `Ldot=rL` 的未来完全由 L 与 r 决定，加入 D 不会在已知 r 时凭空产生作用。** Dead 如有帮助，可来自 latent-state、time-varying 参数或有限样本下联合参数学习，也可能仅来自测量／背景校准。上述周转解释是候选而非“已识别机制”；现有 counts 不足单独区分它们。

预期可检验方向只是：在 frozen live-only 模型的未来 residual 上，合法前缀 D 特征是否有可迁移预测作用。不能用 test residual 拟合新关系；test 仅裁决历史已学的预测器。若方向在不同浓度／context 不一致，不按结果挑机制分组补救。

## 2. 与 BESTDR／普通 multivariate forecast 的差异边界

BESTDR 已联合 live/dead、clearance、measurement noise、分支过程和层级共享；multivariate direct forecaster 也可使用两个通道。因此“加 dead”“改 time-varying birth/death”“共享参数”“做 latent-state”都不是新操作。

本 gate 只有原作未必直接回答的经验 contrast：**在完全相同 live prefix 和 metadata 下，揭示早期 dead stock 是否改善未用于训练／选择的 later LIVE functional readout。** 它是否已被最邻近一手工作同条件验证尚未查明，不以本稿声称新颖。即使通过，也首先是 assay 内新信息价值／适用范围观察，而非算法创新；必须说明相对原作的新问题。

若普通 multivariate regression、BESTDR 或简单混合完整解释收益，应保留额外通道的信息价值，停止“需要新世界模型／智能体”主张。若 dead 不改善 LIVE endpoint，则停止这个 extra-channel 应用的推进；不能转报 joint-dead loss 以绕开失败。

## 3. 给 root 的最小可执行 gate 建议（不是已冻结的数值分析）

应用：从同一 well 的首个合法时间起24h的已测 live/dead-stock prefix，预测约72h时同一种 **LIVE readout**；目标 `log2(L_target+1)`。首选 target 为相对72h附近预先固定窄容差内的最近实际观测（例如[70,74]h、ties取较早），不插值未来目标。若身份时点不支持这个窗口，应在数值开启前由 root 改成确实覆盖的一个窗口并重新冻结，不能开响应后换 endpoint。

观测聚合须由 exporter 身份决定。同 well 的3 images 不当独立重复；若只能认证为同孔视野，则预测其固定平均 live-object readout，不能称绝对全孔总细胞数。图像可能重叠不禁止预测这个固定平均，但禁止直接相加后声称计数守恒。所有 wells/images 一致聚合，不根据 future 数值筛选。

**主来源：8 concentrations ×4 opaque contexts ×3 wells 的 dose-response 文件。** 主 split 建议按 context ID 的固定 SHA256 排序，前2 train、第3 validation、第4 test，保留每个 context 下全部浓度／孔。这样不把同 context 的孔随机拆出虚假的独立验证；它检验 dataset 内未用于拟合的一个 opaque context，**不是 independent biological run**，也不是 unseen drug。训练浓度在 test 见过必须明说。context 当 nominal label，不强加 seeding／batch／数值排序解释；合法 initial live readout 同时给所有模型。

用这一最小 split 的 test 只有1 context／8 concentrations，主分数按 concentration→well 等权，结果为 conditional descriptive sensitivity，不做跨run CI／显著性承诺。可报告逐浓度方向；不能把24 wells或大量frames当24研究任务。另2 concentrations ×3 opaque contexts ×16 wells 的 replicates 文件**不直接pool、不硬join context**；若 source/time/readout相同且 root 事先冻结，可作为后续具名 source-transfer 描述，不能借其 wells 补足 primary 的独立 run 或用来调参后仍称外部测试。最小 gate 本身不要求使用第二文件。

prefix 只用合法当前读数：同一固定相对时间网格的 `log2(L+1)`，以及所有实际时点／time gaps、last state、初值、早晚斜率；L+D 模型另加同网格 `log2(D+1)` 和事先固定的 dead/live readout ratio。Ratio 只是特征，不称死亡概率／hazard。不能给 live-only 模型仅末值而给 dual 模型完整历史。浓度／metadata 完全共享。若同孔前缀完整性不足，按数值前身份规则处理；负／非有限 count 为显式数据诊断，不 outcome筛除。

## 4. 强对照与归因

主信息 contrast 是 **best validation-selected L+D direct vs best validation-selected L-only direct**，相同模型家族、调参次数、history／metadata和切分；只多一个明确通道。这不是同信息算法比较，而是有意的 channel ablation。两边均含 regularized full-prefix ridge、一个强 nonlinear prefix predictor、local trend／persistence；训练 scaler只fit train，select只用validation。

所有声称 world-model 优势的模型必须再与相同 L+D 信息的 direct 比，至少包含：

- 常率／局部 net-growth：D不影响固定 r 的 L 预测，只作结构正确性参考，不故意当弱唯一基线。
- 普通 time-varying net-growth／state-space 与 BESTDR 式 live/dead/clearance/measurement likelihood、预算内层级共享；不把作者已有模型当新物理模块。
- 简单 late fusion／固定混合，并给它同样 validation access；equal-budget ordinary feature／model search可选相同配置。

本最小 gate 没有 active query／agent；全部读数是已存在的前缀。没有额外 acquisition unit 就不宣称湿实验节省。refit／CL／AL／程序继承／RSI 总比较留在后续明确任务上，不在这个信息资格 gate 里虚构。

一个可选 **负对照诊断** 是锁定模型后在同 concentration/context 的 wells 之间交换整段 dead prefix，保持其时间结构，检查 alignedD 是否比 misalignedD 更有用。只有3 wells，条件交换性与 live-prefix依赖均未必满足；这不是有效条件独立随机化 p 值，也不能单独证明机制。若 aligned/misaligned同样有效，可能只学到 action/context的群体校准；仍不自动否定额外读数的预测价值，但不声称 well-specific latent-state sensing。

## 5. 阈值与停止建议

建议 root 在响应前将 useful LIVE gain 设为同时达到 **.05 log2(L+1)绝对 MAE 降低与10%相对降低**，相对最好 validation-selected L-only direct；阈值是约3.5% `(L+1)` 因子的实用候选，不是实测 assay noise floor、统计显著性或小细胞数 L 的相对误差保证。root 应根据身份／成本事先决定这个门槛是否合适，不在读值后移动。

主结果如果小于任一门槛则 stop extra-channel application in this frozen setting；可保留预测资料和描述，不更换 target 为 dead 或 joint score。逐浓度正负可解释异质性但不重定义通过条件。

若超过门槛，仍需区分：①D 的信息价值；②某模型的同信息优势；③物理机制的识别；④跨实验／任务的研究程序改进。这四个成功不能互相替代。单 context holdout 的观察不升级成 biological reproducibility。shared/noise-specific observation 对照、起点不确定性和普通 multivariate方法必须给出，不能将 measurement calibration 称新 turnover biology。

## 6. 当前新颖性裁决和最便宜反证

**当前算法 NONE，独特机制 NONE；可保留一个具体可证伪的条件信息性质。** 它比“两个 κ 比一个好”更基础：先问 dead stock 对未来 LIVE 是否有足够额外信息。已有 physical／multivariate 模型可以完整实现本检验，这不消灭一个尚未被同条件测过的经验问题，但不产生新算法。

最便宜反证就是上述一次同 split／capacity 的 L-only vs L+D 实测 forecast；若无实用 gain，停止当前测量通道的额外应用，不启动 latent-state／修复程序以救结果。若有 gain 但 direct／BESTDR／mixture同样取得，则已识别的是通道价值；新world／agent／RSI核心仍NONE。若生物解释要深入，需后续可区分高周转、clearance、marker drift与参数学习的真实对照，不能从本 gate 的预测差直接定因果。

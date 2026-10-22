# STACK 单次结果：支持方独立判断

2026-10-22。独立稿先于读取 peer post-result 稿。仅阅读本轮 RESULTS、FINAL_COVERAGE、SELECTED、RESOURCES_AND_EXPOSURE、TERMINAL；未读取 raw 新字段，未拟合，未修改 freeze 文件。

## 独立裁决

**`PRIMARY_USEFUL_GAIN_FAIL`，停止把当前精确固定剂量 24→72h 配置升级为核心框架。可以保留小幅、方向一致的注册预测增益，不能将其写为达到用途门槛或新机制。** 我不同意把结果概括成“死亡通道完全无信息”，也不同意因为 bootstrap 区间在零以上就绕过前瞻阈值。

## 有资格保留的具体证据

1. 资产与执行合格：单次运行 exit0，75 fits（每臂 14 trial+1 refit）。全部 role×screen complete coverage >=98.36%，超过注册 95%；fully contributing groups 为 train 1093、validation 360、test 364，均满足组数要求。测试共 1098 scored entry-screen rows，来自 367 role groups，不能说有 1098 个独立实验或独立科研任务。
2. live-only MAE=.22744998，full history=.21948950，差 .00796048，即 3.50%。三个 screen 的差分别约 .00844、.00515、.01029，均为正。按既定组 bootstrap 的 95% percentile 区间为 [.00273610,.01361260]。这支持已选 pipeline 在这批记录条目中的小幅正向预测差；不是独立生物重复或 retraining/seed 稳定性的置信保证。
3. 联合端点 MAE=.22269771，full history 对它的差 .00320821，即 1.44%；三个 screen 均正，组 bootstrap 区间 [.00020512,.00621054]。因此“full history 可能只是两个端点联合”的简单解释，在这些注册预测器的点结果中不完全覆盖观察差异；但差值很小，区间下端接近零，不能据此主张五个中间点各自必要、时间顺序机制或 causal state。
4. D0-only=.22743888，几乎等于 L-only；D24=.22308711，联合端点=.22269771，full history=.21948950。这是有价值的分解：目前主要不是单纯基线 D0 库存；锚点 D24 与额外中间观测各有小的可获得预测差。它仍可能来自状态代理、共同测量过程或有限模型归纳偏置，不是死亡事件/turnover 的认证。
5. 五臂均选择相同 `extra_depthNone_leaf5`，故观察增益不是由某一臂选择了完全不同模型族这一简单变化解释。相同模型类别并不消除输入维度及 feature geometry 的影响，也不把固定 family 的对比变成条件互信息估计。

这些证据应原样保留，尤其不能因当前不够强而删除联合端点的小正差。另一方面，不应把“区间不含零”写成对独立生物体系的显著改进。bootstrap 重新抽样的是当前固定 screens 下的 recorded-entry groups，不是模型训练重复、实验批次或新 cell-line 采样。

## 为什么仍必须停

primary 差 .00796 远小于注册 .05，3.50% 小于 10%。history 对 D0、D24、联合端点的全部 practical comparisons 也未通过。三个 screen 同向仅满足方向条件，不能代替全局双阈值。即便 primary bootstrap 上端 .01361 也低于 .05；在本定义的 entry-resampling sensitivity 中，没有证据接近注册绝对用途量级。

小预测信号与足够大的应用贡献是不同问题。当前 MAE 不测 top-k hit enrichment、剂量效力、选择性、前瞻 wetlab 成本或时间收益，因此既不能证明实用 triage，也不能据其未达本阈值宣称任何实际决策绝无价值。正确结论是：没有达到本次明确预设的用途代理门槛，不再用这个精确配置支撑大框架。

固定 persistence/log-growth MAE 约 1.08049/1.05637，明显高于训练后的 L-only .22745。这支持任务需要比固定外推更好的数据驱动预测，不证明所有机制/世界模型均差；本轮根本未拟合世界模型。强 L-only 已解释大量可预测结构，D 的额外部分很小，额外通道本身不足以担当核心技术贡献。

## 覆盖、预算与边界

共同 dual-prefix eligibility 的条件限制仍在。U2OS train/validation/test 的 D 额外 prefix failures 分别为 6/5/2，另有少量 live-prefix/target 不合法；不应把这些行插补、重新放回 L-only 或删去重新比较。测试 U2OS complete 为 364/367，另两个 screen 各 367/367，表明本次不是像 HCT116 那样资格中止，但也不等于无条件全库 utility。

实际总 gate 约 84.46 秒，full-history trial+refit fit 时间约 17.19 秒，L-only 约 13.73 秒。试验选择预算相同，计算时间不相等。没有新下载、联网、DeepSeek 调用或 wetlab，不能把 75 fits 称为 75 个研究循环或自我改进。

世界模型、普通重训/CL/AL、简单混合、等预算程序搜索、智能体、继承、联合收益与 improvement-of-improver 全部 NOT_TESTED。没有研究程序在多个独立任务之间学习并继承，也没有比较“改进策略自身变好”；通道 ablation 不能替代这些验证。

## 后续不同科学问题的最低条件

值得继承的是效应量和竞争基线：在这三个源内，额外 SG 信息并非必然为零，但很大程度上有限，任何更复杂机制要解释并超越这个强直接对照。它是限制未来主张的证据，不是启动下一轮搜索的自动许可。

只有先有独立科学理由与可获得数据，才值得提出不同问题。例如经认证的功能终点及独立实验批次，或明确需要预测额外干预/测量决策的任务，才可能检验潜在状态与世界模型的必要性。必须在新任务结果前明确测量意义、训练/测试独立性、公平预算、可证伪贡献和停止条件；若任务仍主张中间历史价值，保留联合端点基线。不能把已打开的这套 L72 换成有利 subgroup、top-k 指标、阈值、模型搜索或另一个 endpoint 来救当前门检验。

目前不据此推荐某一具体 latent 机制或 RSI 架构。支持方保留的小正信号与反对升格的理由应同时进入最终记录，等待反方实际质询。

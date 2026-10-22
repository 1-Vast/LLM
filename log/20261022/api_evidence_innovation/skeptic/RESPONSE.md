## 1. 只推荐一个候选：Residual-Cone Feedback（RCF，残差锥门控的状态—功能反馈）

与草案关系：保留“早期响应几何决定功能残差跨条件可迁移性”的核心，但把它收紧为**两轴残差 + 状态方向门控 + 拒绝迁移**：DNA/LDH 残差分解为共同生存轴与 DNA–LDH 分离轴；只有 later 药 L/M bundle 的功能残差落在 source 学到的可迁移锥内，且早期 RNA 响应方向与 source 锥一致时，才外推到未测 H 剂量；否则只修 state branch 或拒绝。

一句可证伪主张：**在未见 chemical parent/scaffold 的 24h 最高有效剂量上，DNA/LDH 相对生存残差中可从 later 药 L/M 功能 bundle 外推的部分，必须由 source 学到的共同/分离残差轴与 early-RNA 状态方向共同门控；错误门控或随机旋转该锥不会优于同信息 direct，并会增加负迁移。**

实际用途：later 药买到 L/M bundle 后，决定是否值得做 H 剂量确认，以及动作是 **F：只修 function head / S：只修 state branch / R：拒绝迁移**。不声称这是新算法；若同信息 conditional kernel/多任务回归精确复现，则否证 operator 首创性，只保留经验结构贡献。

## 2. 精确操作（≤12行）

1. D0 冻结 47 labels、parent/scaffold 分组、L/M/H 有效浓度、官方 relative survival 定义、logit 变换、缺失规则；不读 later H 数值。
2. 以 parent/scaffold 为抽样单位做 source/development/later 固定哈希分层；later 组与 source/development 不重叠。
3. source 训练强 direct 与 factorized `f(z,d,L/M RNA)->s`、`g(s,z,d)->(DNA,LDH)`；development 选轴数、shrinkage、门阈值；later H function 与 H RNA 封存。
4. later 每个 compound 只给 L/M bundle：早 RNA 重复 + 24h DNA/LDH；H RNA 必须由 `f` 预测，不能作为免费输入。
5. 对 source/development/later 计算 L/M 功能残差 `r=y-\hat y`，分解 `c=(r_DNA+r_LDH)/2`、`q=(r_DNA-r_LDH)/2`。
6. source 学低秩 `T:[c_L,c_M,q_L,q_M,state-direction stats]->[c_H,q_H]`；共同轴与分离轴分开，强 shrink 到 direct。
7. source/development 学门 `G`：用 early-RNA 响应方向、L/M 状态位移一致性、残差锥对齐，输出 F/S/R。
8. later：G=F 时只在 function head 加 `T r_LM`；G=S 时沿 source 状态—功能 Jacobian 修预测 state 再过冻结 `g`；G=R 时退回 direct。
9. 所有阈值、轴数、shrinkage、F/S/R 规则在 development 冻结；later 只评估一次，不回调。
10. 主终点：H 的 DNA/LDH 联合归一化 MSE；次终点：负迁移率、F/S/R 决策准确率、确认优先级。
11. 同信息跑强 direct、conditional kernel、factorized、offset/dose-curve refit、shuffle/rotate/random-gate、等预算搜索。
12. source grouped-CV 无预注册增益或 later 失败即停止；不得转写成 RSI 成功。

## 3. 分工、反馈单位、门与首个 cheap decisive check

- **source/development/later 分工**：source 学 `f,g,T,G` 的候选结构；development 只选轴数、shrinkage、门阈值和 F/S/R 规则；later 为未见 parent/scaffold，H function 与 H RNA 不可见。若 parent/scaffold 独立性未认证，只能做 leave-one-parent-out pilot，不能宣称“未见 parent/scaffold”。
- **反馈单位**：一个 later compound × 一个 L/M dose 的 condition bundle（早 RNA 重复 + 24h DNA/LDH），不是单细胞、不是标量。L/M 功能可见；H function 隐藏；H RNA 隐藏并由 world 预测。若所有方法都给 H RNA，只能作为另一个应用，不隔离状态预测价值。
- **47-label power 限制**：47 是有界 small-N pilot；剂量/技术重复不能当新 task。若独立 later parent/scaffold 组不足以支持 ≥12 个 later tasks 和 ≥3 轮 C4，则不得报告 RSI 成功。
- **化学门**：later parent/scaffold 必须与 source/development 分离；报告 later 到 source 的化学相似度分布。若 later 全是近邻，结论仅限近邻外推；若过远且基线无 headroom，停止。
- **数值门**：只用官方 DNA(%)/LDH(%) relative survival；不把 LDH 当泄漏率或 birth/death；不把标签设 85%；预注册 logit/缺失规则，Low/Middle/High 均严格正且完整。
- **headroom 门**：H 功能不能饱和或 baseline 已无误差空间；用 source/development 的重复/条件均值噪声下限检查。若 baseline MSE 不高于噪声下限加预注册 margin，停止。
- **首个 cheap decisive check**：先只读 source/development，做 leave-one-parent-out。对每个 held-out compound 隐藏 H function，用 L/M bundle 计算 `c,q,state-direction`，按 `T,G` 预测 H 残差。成功条件预注册为：相对最强同信息 direct 的 H 联合 MSE 降低 ≥5%，paired bootstrap 95% 下界 >0，且 shuffle/rotate/random-gate 对照至少损失一半增益；拒绝子集不得比 direct 更差。未过则停止。该检查只是 source-only 诊断，不是生物验证；通过后再一次性读 later。

## 4. 最接近 ordinary explanation 与同信息对照

必须同跑：chemical+dose direct；拿同样 source H RNA 与 later L/M RNA/function 的 direct；完整已付 RNA/function/mask/history direct；ordinary factorized `f(drug,dose)->state->function`；conditional kernel/多任务回归/贝叶斯 shrinkage；offset/dose-curve refit；全量重训练；AL；等预算程序搜索。若这些同信息模型复现 RCF 增益，则不能声称残差锥结构有效。

关键否定性对照：  
- early-RNA 在化合物/剂量层内置换或保持协方差的旋转；  
- L/M 功能残差跨 compound 置换；  
- 学习到的残差轴随机旋转，保持秩、范数、参数量；  
- random gate 匹配接受率；  
- 去掉分离轴 q，只保留共同轴；  
- 去掉门，始终迁移；  
- 同参数量随机低秩 `T`。

新颖性边界：不声称新 RNA→毒性预测器、新 stress signature、新动态网络或 RSI；不声称临床疗效、donor transfer、birth/death 机制。最多声称：在一个 bounded out-of-parent pilot 中，该门控拒绝结构相对同信息 ordinary 模型改变了 H 剂量确认决策并减少负迁移。若 conditional kernel/rotate 对照复现，则否证候选核心。

## 5. world/agent/model/program/joint inheritance 的分别识别

所有臂 common-start：同一 source-frozen `f,g,T0,G0,π0,P0`、同一 later task 顺序、同一 L/M bundle、同一 H 反馈时点、同一计算/API/查询预算。只允许指定状态跨 task 携带；其他全部重置。

- **W（world）继承**：携带 base `f,g` 参数；重置 `T/G,π,P`。对照把 `f,g` 重置到 source prior。结构消融是“有/无 T-G 或 rank-matched random T”，不是标签比较。
- **A（agent）继承**：携带动作策略 `π`（F/S/R 与确认优先级）；重置 `f,g,T/G,P`。对照 source `π` 或同动作率的随机 `π`。
- **M（model/feedback operator）继承**：只携带 `T,G` 及其校准；重置 base `f,g,π,P`。对照为同秩同接受率的随机 `T`/随机门。若实现中 `T,G` 已嵌入 world，则 W 与 M 合并，只做 `T-G` 结构消融，不把同一模型当两个方法。
- **P（program）继承**：携带经 meta-validation 接受的程序编辑（特征集、门族、停止规则等）；重置参数。对照做同等数量候选编辑的 equal-budget random/grid search，不继承反馈选出的编辑。
- **Joint**：全携带。与最佳单继承臂及等预算 ordinary search 比较；若 Joint 只等于某个单臂，归因该组件，不报联合 RSI。

## 6. RSI C4 可执行 common-start 合同

- **前置门**：至少 12 个独立 later parent/scaffold tasks，且 ≥3 轮“编辑→继承→评估”，每轮 ≥4 个独立 parent tasks；不足则 C4 直接 NOT_ACHIEVED，只报 pilot。
- **共同起点**：相同 source-frozen `f,g,T0,G0,π0,P0`；相同 later predictor、程序、历史、权限、API/计算/查询预算；相同 task 顺序；每个 task 先看 L/M bundle，做 H 预测/动作，随后揭示 H function 作为实验反馈。
- **两个明确 improver**：  
  1. `I1=T/G`：从累计 H 反馈更新残差转移系数与门阈值/拒绝规则；改变的是 function/state 修正与是否迁移。  
  2. `I2=π`：从已实现 H 损失更新 F/S/R 动作选择与确认优先级；改变的是研究动作策略。  
  `P` 只作程序继承消融，不冒充第三个 improver。
- **improvement efficiency 指标**：主指标为累计 H 反馈 bundle 数对 held-out H 联合归一化 MSE 的 learning-curve AUC；次指标为达到预注册 MSE 阈值所需 H bundle 数、负迁移率、F/S/R 决策损失。效率比 = `(AUC_no-inherit - AUC_arm)/AUC_no-inherit`，按同等预算归一。
- **等预算 ordinary search**：每轮在相同候选空间随机/网格评估同样数量配置，用当轮及历史 H 反馈选当前最佳，但不跨轮继承 `T/G/π` 的结构状态；计算、H 反馈次数、权限完全相同。
- **成功条件**：Joint 或某单继承臂相对 no-inheritance 和等预算 ordinary search，AUC 降低 ≥10%，paired bootstrap 95% 下界 >0；且至少一个组件单独可重复改善。若只有标签差异、同信息对照复现、或独立 task 不足，不报 RSI 成功。失败则保持整体 NOT_ACHIEVED。
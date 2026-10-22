## 一、交叉质疑与我自己的错误

**对 CAF 候选（constructive）**：我同意它有真实功能终点和可检验的配对实验，但它的“\(\lambda=0\) 即瞬时静态响应”表述错误。root 的确定性审计显示：\(\kappa=1\) 时从 \(s_0=0,1\) 到 \(t=1\) 仍有 \(e^{-1}\) 的历史差；\(\lambda=1\) 严格单调、唯一平衡；\(\lambda=5\) 才有三平衡。因此，慢松弛、平衡滞回、细胞因子 carryover、供体差异和组成变化在现有 n=3/4 功能实验里不能靠一个后验 \(\lambda\) 区分。把 \(\lambda\) 后验压到 0 当作机制无效也不充分；CI 排除 0 也不等于应用有用增益。CAF 现在**只够做来源资格检查**，不足以数学实现，更不足以生物实现；必要模块是同一供体的“预处理—洗脱—再刺激”配对菜单、供体随机效应和技术重复。缺失 join 正是该配对历史菜单；本环境无湿实验，不能把建议实验当已执行。

Lorch 的 latent causal diffusion/CLIPR 是通用因果—动力学耦合的近距离先验，但它的 stationary noisy RNA 和单时间点快照不识别洗脱历史或双稳态，不能证明也不能否定 CAF 滞回。足细胞全文显示零基因过 FDR<0.05，nominal hits 只是探索性，不能当已验证靶点。

**对空间 CST 候选（skeptic）**：root 的修正成立。固定丰度头时 \(\sum_b n_b=N\) 与 \(T,s\) 无关，运输只改位置；目的格常数标量条件会被 softmax 消掉，向量 logits 可修但修后更像标准 shared-embedding / unbalanced-OT 多任务。未见扰动若只靠学到的 \(E[p]\) 表，无法预测真正 held-out 扰动；必须有化学/靶点/组成描述子，否则 leave-one-perturbation-out 不成立。更严重的是他的置换失败逻辑反了：正确生物信号在 action/spatial permutation 下**本来就应消失**；若增益仍在，才更像泄漏或 nuisance。有效对照应是 nuisance-only baseline、同板/批次内保留边际的负对照、oracle 上界、同信息直接多任务；消失是特异性证据，不是泄漏证据。counts+localization 同时增益也只是模型级联合，不等于 world+agent 联合收益；C4 的 old/new improver 同起点比较另是一门。故 CST 目前只能做数学修复和来源资格，不作为优先级。

**对我自己的 EACT-DQ**：我必须明确撤回“决策翻转查询是决策规则”的表述。root 的精确反例已证明：正翻转概率可对应负净价值（\(0.005-0.1=-0.095\)），且翻转分数可把低价值查询排前（B 翻转 0.9、净 \(-0.0091\)；C 翻转 0.1、净 \(+0.09\)）。\(p_{\text{noise}}\) 不修复效应量缺失，也不处理处理组/对照噪声不对称。正确说法：\(q=(p_{\text{flip}}-p_{\text{noise}})/\text{cost}\) 只是启发式；若声称决策价值，必须用显式效用和 EVSI/knowledge gradient，但那是普通贝叶斯设计，不是新机制。我的低秩端点对齐与 supervised factorization/PLS 很接近，我找不到精确附加差异，应降级为常规基线。凸包内只表示外推域，不保证功能运输。我的“vehicle bootstrap/CI 排除 0”只是统计判据，不是应用有用增益；不能称 utility。另有修正：NCI-ALMANAC 虽无 RNA，仍可支持**静态 action-conditioned functional world**；但不得虚构未释放的可查询 assay bundle。LabCompass 只有 synthetic README、JATS 429，不能拟合。

## 二、唯一优先级与记录

我选择唯一优先：**对 NCI-ALMANAC 做来源资格检查，作为“常规 action-conditioned 功能世界”试点的前置；不实施 EACT-DQ 机制，不拟合 CAF/CST。** 这是明确标注的 conventional pilot，不是新机制声明。

- **支持性证据**：root 已指出 NCI-ALMANAC 在正确 scoped 下可支持静态 action-conditioned 功能世界；它直接关联药物组合—viability 决策，具药物发现相关性。CAF 缺配对历史/洗脱 join，CST 缺 schema 且修后近标准，EACT-DQ 缺 whole-bundle/vehicle/action 数据。
- **最强反对**：NCI-ALMANAC 是静态、无分子 \(\delta\)、无查询闭环；标准矩阵分解/PLS 同信息很可能追平；“contrastive action conditioning”可能只是常规正则化。因此只能作为 conventional baseline，不能包装成新贡献。
- **分歧**：CAF 主张现在可数学实现，我认为当前只够来源资格；skeptic 把置换下增益消失当泄漏，我认为相反；我此前把 flip/cost 当决策规则，现降为启发式。
- **必要模块**：可解析 manifest/data dictionary，含 plate、cell line、drug/combination、dose、vehicle/control、replicate、viability；随后同信息比较直接 action-conditioned 模型、矩阵分解/PLS 与 nuisance-only，按药物/组合留出。
- **缺失 source/data join**：每板 vehicle、action→treatment 映射、剂量/时间、重复、细胞系协变量、版本 hash；均未核实。
- **下一步唯一判别动作**：只取官方 NCI-ALMANAC 数据字典与一个 manifest（不拟合、不跑生成代码），核验上述字段并记录 hash；通过才进入常规试点，失败则停止并另寻公开 plate-level vehicle 数据，标记未验证。
以下只作交叉回应与纠错，不重做首评，也不声称新拟合或新测量。

**先撤回我上一轮的数据错误。** 我把 Fig3b 说成“三个发育时间点”是错的：它是 3 个 labeled sample 随时间的 3D force 历史，1404 个 numeric tags 只是元数据，不是任务数或独立样本数。Fig5a/b 的 sample1–4 同标签只能支持“conditional same-export-row hypothesis”，不能说 run/culture 已配对；归一化和精确处理区间仍未认证。Fig7g 是 STORM pixel-density CDF，19/135 是论文层面的 synapse counts，不是独立培养或 firing 任务。若我此前引用“90% firing/20% vesicle”而审计文本未认证，应删除，不能当已核验事实。我的“joint 必须超过单独增益”“world=0”“C4 old=direct solver/new=不同 world solver”也都错误，下面明确纠正。

1. **AGFR 数学：同意，但新颖性未成立。** 固定 M 时，令 \(a=r_1 y_{\max}g\)，则  
\[
\dot R=r_0+(a-r_0-qu)R-aR^2
\]
是普通标量 Riccati/自催化储备方程；Fraction 审计通过。这是构造性重写，不是普适等价定理。额外可检验内容只能是两条约束的组合：再充填率依赖“当前已实现功能”而非仅 washout 时间或 M；输出又被 M 的阈值乘性门控。Stevens/Wesseling 1998 摘要已明确活动/胞内钙提高 refill、休息时松弛；Sakaba/Neher 2001 摘要已明确钙/钙调蛋白促进快速释放池补充。故“活动依赖补充”本身是既有先例，不能当新操作；只有“结构许可阈值 + 活动依赖 refill”的组合还可作为待证伪候选，目前没有已证明的新预测。  
关于 \(do(\text{activity clamp})\)：不能在保持 \(y=y_{\max}Rg(M)\) 的同时任意钳制 \(y\)。可操作定义应是对 refill 项中的独立活动信号 A 或 \(r_1\) 做干预，例如  
\[
\dot R=(r_0+r_1 A)(1-R)-quR,\quad y=y_{\max}Rg(M),
\]
或 \(do(r_1=\rho)\)，只改再充填、不改输出代数式。若 A 只是 y，则不存在独立钳制，只能观察到共变；不能把假设性干预说成已有数据支持。

2. **反方 D/G 反例：同意，应撤回强叙述。** 固定 F、\(k_a=1,k_i=0,D_{eq}=1,D(0)=.2\) 时，\(D(t)=1-.8e^{-t}\to1\)，说明该许可参数下是可逆补充，不是内在不可逆损伤。“不可逆对接损失”至多只能在特定 \(k_i>0\) 或 F 依赖参数区成立，需另行识别。G 方程在 \(R/R_0\le1\) 时正部强制为 0；若 \(G(0)=G_\infty=1,\eta=1\)，G 恒为 1，beta 不能积分低 R 缺口。因此“低力史/低储备补偿”的当前表述是反例所驳的，不应保留为已成立解释；加慢变量只是修正假说，不自动产生新颖性。

3. **离散 R 递推：同意反例，需修正边界条件。** \(k=2,C=1,R=.1,\text{loss}=0\) 给 \(1.9>C\)；\(k=.2,C=1,R=1,\text{loss}=2\) 给 \(-1\)。故缺参数/时间步约束时，“有界储备”保证失败。在协议给出的归一化 \(C=1\) 递推  
\[
R'=(1-k-\text{loss})R+kC
\]
中，\(k,\text{loss}\in[0,1]\) 足以保持 \([0,1]\)，因线性极值在端点；\(k+\text{loss}\le1\) 并非必要。若固定 C 不归一为 1，则需保留 C 因子，例如 \(0\le kC\le1,\ 0\le\text{loss}\le1\)；动态 C 另需转移解释，本审计未解决。

4. **来源审计：同意，不重复表头检查。** 五个文件 MD5/大小和 schema 已核验，再查同一批表头不是新进展。没有批准的 3D force→2D MEA 按 Sample 拼接；Fig5a/b 只有 4 行、一个共同药物序列的条件性配对可能，不支持跨日程、跨药物、反馈策略或后续改进任务。除非出现新的、可核查的主源——同一 run 的 force/firing/vesicle 原始时间序列、raw spike timestamps、精确处理区间和独立培养单位，或合法取得的 2026 CAF 全文/traces——否则应停止当前配置；四行回顾性 pilot 太窄，不能做方便拟合。

5. **归因与 C4：我明确纠错。** world、agent、inheritance、joint 应分别检验；joint 改善**不需要**正交互或超加和，主效应、组合 vs 单模块、交互项分别报告，有意义的可加组合不能排除。未测记 NOT_TESTED，证据不足记 NOT_ESTABLISHED，不记测得 0。我此前“joint 必须超过单独增益”以及“world=0”的写法撤回；mechanism 首评中“只有交互项改善才叫 joint”、skeptic 首评中“联合需超过最大值”也过强，均应修正。继承 vs restart 独立于 C4。C4 是固定同一目标 solver 起点、同反馈/数据/预算，比较同一 improver 在元任务学习前后两个检查点；不能 old=direct solver、new=不同 world 或不同 improver。我此前那类 C4 构造撤回。

6. **结论。** 最值得保留的是 Joy et al. 2023 的来源契约及“功能恢复≠结构恢复”这一待证伪问题；AGFR 的 \(r_1>0\) 只能作为嵌套模型假设，不是已验证核心。最强反驳是：无同一 run 的 force–firing–vesicle 原始轨迹，无 raw spike traces/run culture 映射，4 个 MEA 样本共享一个处理序列，普通储备池、直接药物/时间效应、off-target/黏附混杂均可解释。与 mechanism 的未决分歧是 \(do(\text{activity clamp})\) 是否可独立实现、组合是否真有增量；与 skeptic 的未决分歧主要是四行条件性 pilot 是否值得做，我和 skeptic 都不主张晋级。最廉价下一判别不是再查五表，而是认证一个新的同 run 原始资产；若认证不了，当前配置 STOP。本包不需要新 API/计算许可；无湿实验能力是实际限制，不虚构新源或已完成测量。
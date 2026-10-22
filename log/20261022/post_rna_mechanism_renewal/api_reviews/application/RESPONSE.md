## 独立首评：一个最小候选——“端点对齐的对比程序传输 + 决策翻转查询”（EACT-DQ）

我先自由探索，再按证据约束筛选。结论：只提一个主候选，且明确标为“机制假说/未拟合”，不是生物结果。

### 1. 自由探索与筛选

可行方向有几类：  
A. 用绝对分子谱预测功能端点；B. 通用“前向世界模型 + 逆向设计 + 闭环反馈”；C. 亚细胞空间扰动；D. CAF 细胞因子状态转换；E. 足细胞 CRISPR 功能筛选。  

筛选理由：A 被“上下文几何压缩会丢失 context-specific differential response”的线索削弱，且历史直接模型很强；B 与 LabCompass 一类工作过近，不能作为新机制核心；C 的 oracle 给精确 target counts，功能端点不是独立 efficacy；D 的 RNA 与功能共培养不能静默拼接，供体数小；E 有原始筛选和代码，但缺完整设计、功能菜单和 supplemental joins。因此这些都不能直接拟合。

我选一个最小但可证伪的操作：**不建模绝对表型，只建模同一实验 bundle 内的“处理—对照”对比；用少量端点对齐程序分解对比；只有当一次查询可能把当前决策 top-k 集合翻转到超过车辆重复噪声时，才做实验。** 名称暂定 EACT-DQ。

### 2. 主候选：EACT-DQ

**真实任务。** 给定上下文 \(c\)（供体/细胞状态/批次）和有限干预菜单 \(A\)（药物、细胞因子、浓度、时间），每轮在预算内选一批实验 \(B\) 运行，输出要推进到功能验证的 top-k 干预。药物发现决策是“下一批做什么、推进谁”，不是重建整个转录组。

**可观测数据。** 每个 bundle 至少要有：同一板/同一供体的 vehicle 臂；处理臂的分子读数 \(y\) 和/或功能端点 \(z\)；动作元数据（剂量、时间）；供体/板/批次；成本。只使用 bundle 内对比：

\[
\delta_{c,a}=\phi(y_{c,a})-\phi(y_{c,0}),\qquad
r_{c,a}=g(z_{c,a})-g(z_{c,0}).
\]

**生物假说 H（可证伪）。** 与功能相关的扰动差异主要落在少量“端点对齐程序”上；上下文差异主要是程序门控 \(\theta_{c,k}\)，动作差异主要是共享加载 \(\phi_{a,k}\)。若新动作的程序加载落在已测动作凸包内，可外推；若落在凸包外，必须查询。

\[
\delta_{c,a}\approx \sum_k \theta_{c,k}\phi_{a,k}u_k+\varepsilon,
\qquad
r_{c,a}\approx \sum_k \theta_{c,k}\phi_{a,k}\beta_k+\eta.
\]

决策分数：

\[
s(c,a)=\sum_k \theta_{c,k}\phi_{a,k}\beta_k.
\]

拟合用 bundle 内 pairwise ranking，而不是绝对谱回归：

\[
L=\sum_{c,a,a'}\max\{0,1-\operatorname{sign}(r_{c,a}-r_{c,a'})(s_{c,a}-s_{c,a'})\}+\lambda R.
\]

**反馈菜单。** 每轮可选择：  
1. vehicle 重复；2. 候选动作的分子对比；3. 候选动作的功能端点；4. 剂量/时间扩展；5. no-op/弃权。成本必须在 bundle 中显式给出，不能事后编造。

**查询规则。** 对候选批次 \(B\)，用后验样本计算当前 top-k 集合翻转概率 \(p_{\text{flip}}(B)\)；用 vehicle 重复 bootstrap 得到纯噪声下的翻转率 \(p_{\text{noise}}(B)\)。查询分数：

\[
q(B)=\frac{p_{\text{flip}}(B)-p_{\text{noise}}(B)}{\operatorname{cost}(B)}.
\]

若 \(\max_B q(B)\le 0\)，停止或弃权；否则运行最大者。这样阈值由观测噪声定义，不设任意临床效用 margin。

伪代码：

```text
输入：whole bundles, 有限菜单 A, 成本 cost, 预算
初始化 θ, φ, β
for round t:
   用所有匹配 vehicle 的 bundle 内对比拟合 θ, φ, β
   抽样后验
   for a in A:
       s_samples(c,a) = Σ_k θ_c,k φ_a,k β_k
   top = topK(mean s)
   for feasible batch B:
       p_flip = P_post(top set changes after B)
       p_noise = vehicle-bootstrap flip rate
       q(B) = (p_flip - p_noise) / cost(B)
   if max q <= 0: abstain/stop
   run B；只把匹配 vehicle 的对比加入更新
```

### 3. 数据与阻止拟合的缺口

**LabCompass 线索。** 论文元数据可认证，仓库 README/tree 可读；但 README 只有 synthetic example，未见实验数据 DOI/menu；全文 JATS 多次 429，paper-to-repo 链接未认证。若作者释放实验 bundle，它最接近本任务：有连续细胞因子/小分子菜单、功能目标、 successive updates。但拟合至少缺：每孔 vehicle、剂量/时间/成本、供体/板/批次、原始 flow gating、精确 target composition、动作到处理的映射。缺这些就不能拟合。

**CAF 细胞因子线索。** 作者 XML 有 RNA 和功能共培养，但小供体数、RNA 与功能数据不能静默拼成完整干预—反应表；缺 matched action menu 和 bundle 标识，不能拟合。

**足细胞 CRISPR 线索。** HRA018288 和代码明确，但缺完整设计、supplemental joins 和功能端点菜单，不能作为状态/功能多任务菜单拟合。

**可核查替代主源线索（未核实）。** 若不用 LabCompass，可查 NCI-ALMANAC 一类整盘药物组合 viability bundle；它可测“仅功能对比 + 查询”的 agent 简化版，但不能测含 \(\delta\) 的世界模型，故不替代主候选。此处未核实，不当作已知数据。

### 4. 最强普通解释、决定性廉价测试与失败规则

**最强普通解释。** 一个同信息的直接对比模型，加同样的主动查询和同等数据/反馈/计算，可能完全匹配；程序分解可能只是正则化。历史直接、无查询、混合方法很强，但这不证明生物结构无用，只要求同信息比较。

**决定性廉价测试。** 在一个有 whole bundle、匹配 vehicle、有限动作菜单和功能端点的公开数据上做回顾性自适应查询：按动作留出和按供体留出，训练/查询/评估分离。等预算比较 EACT-DQ 与直接绝对模型、直接对比模型、无查询低秩、通用不确定性主动学习、等预算随机、混合/堆叠。有用增益在见结果前定义为：决策 regret 的下降超过 vehicle 重复 bootstrap 的 95 分位噪声，且置信区间排除 0；不设任意临床 margin，不预设样本量。若晋升为框架，再补既定六强比较器族和同信息 world-free control。

**失败规则。** 若 EACT-DQ 相对直接对比或通用主动查询无增益；若增益在移除程序新颖性信号后消失；若增益来自更多查询、泄漏或不等预算；若 top-k 推进集合不优于等预算随机/直接模型；或若程序加载不能预测留出动作的功能排序，则拒绝该机制。若没有合格 whole-bundle 数据，则本候选不进入拟合。

**声明边界。** 世界 claim：上述程序门控假说，仅 speculative，未证实。Agent claim：决策翻转查询在等预算下降低 regret，可测。继承求解器/策略 claim：本轮不声称。联合 claim：须世界与 agent 同时过检验后才可谈。C4 claim：不声称；若以后做，必须用同一 start 的 old/new improver 和 transfer vs restart 度量。
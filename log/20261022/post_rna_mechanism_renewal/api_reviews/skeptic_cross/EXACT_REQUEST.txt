你是先前的 skeptic 角色。下面是你和另外两名角色的真实首评原文及root已执行的反例检查。请认真交叉质疑，并明确修正你自己的错误。


--- INDEPENDENT constructive ---
**证据边界**：以下为机制设计，不是已执行结果。证据包只提供CAF作者XML、小样本功能实验和数据库入口；我没有查证释放数据中是否存在匹配功能表。历史RNA pilot只否定其具体配置，不普遍否定状态机制；RSI文献占据的是通用可编辑改进器，不是本候选。

## 一、自由探索后的筛选

我考虑过三个方向。第一，以SubcellPert的亚细胞位置为结构约束，预测“位置条件化的分子计数”；但证据包明确其oracle给的是精确靶计数，不是独立功能终点，作为药物功能预测主候选缺关键join。第二，以足细胞氧化损伤CRISPR构造“抗氧化缓冲容量—阈值”模型；生物上合理，但现有静态筛选缺时间分辨恢复轨迹，无法把缓冲容量与功能阈值分开。第三，以CAF细胞因子状态—T细胞功能为对象，检验“状态历史依赖的滞回”机制。它有真实功能终点、细胞因子扰动和患者来源小样本；缺的是预处理历史/洗脱/同供体重复。这个缺口可用廉价实验直接检验，且失败规则清楚。因此选第三，且只选一个主候选。

## 二、主候选：CAF细胞因子历史依赖的免疫抑制滞回状态机制

**生物假说**：CAF在IFNγ/TGFβ等细胞因子作用下不是瞬时跟随当前浓度，而是沿一个免疫抑制状态变量\(s\in[0,1]\)移动；该状态具有阈值和滞回。相同最终细胞因子组合，从不同预处理历史到达时，CAF的分泌/表面程序及对T细胞迁移、激活的功能可能不同。若为真，联合免疫治疗的“顺序”而不只是“终浓度”会影响CAF功能；若为假，普通瞬时剂量—响应加供体异质性即可解释。

这不是从证据包推出CAF已存在滞回，而是可证伪的结构假说。证据包只记录apCAF/mCAF、IFNγ 20 ng/ml和TGFβ 10 ng/ml、T细胞迁移/激活coculture、n=3/4等作者条件；不能把这些小样本结果当作滞回证据。

**最小方程**。令\(c_t=(I_t,T_t)\)为标准化IFNγ/TGFβ浓度，\(s_t\)为免疫抑制状态：
\[
u(c)=\sigma\!\left(\beta_0+\beta_T\log(1+T_t/T_0)-\beta_I\log(1+I_t/I_0)\right)
\]
\[
\dot s=\kappa\,[u(c)-s]+\lambda\,s(1-s)(s-\theta)
\]
\[
y_{\text{mig}}=a s+\gamma^\top x+b_{\text{donor}}+\varepsilon,\quad
\operatorname{logit}P(y_{\text{act}}=1)=a' s+\gamma'^\top x+b'_{\text{donor}}
\]
其中\(\kappa>0\)是转换速率，\(\theta\in(0,1)\)是开关阈值，\(\lambda\ge0\)是滞回强度；\(x\)是供体/标志物协变量。关键嵌套关系是\(\lambda=0\)时退化为普通瞬时剂量—响应模型。洗脱期令\(c=0\)，若\(\kappa\)小且\(\lambda>0\)，状态可保留，形成“历史记忆”；若\(\lambda=0\)或\(\kappa\)大，洗脱后历史迅速消失。

**更新机制**。不是重训黑箱，而是对具有生物含义的\((\kappa,\lambda,\theta,\beta,a,b)\)做分层贝叶斯更新，供体为随机效应；先验约束\(\lambda\ge0,\theta\in(0,1)\)。新数据到来时，若后验把\(\lambda\)压到0，模型自动退回普通静态模型——这是机制允许失败的内置结构。主动实验选择用期望信息增益：
\[
c^\*=\arg\max_c\left[H(y\mid c,\mathcal D)-E_{\omega\mid\mathcal D}H(y\mid c,\omega,\mathcal D)\right]
\]
其中\(\omega\)为参数。优先选择能区分“历史敏感”和“瞬时响应”的预处理—洗脱—再刺激条件，而不是只重复已知剂量。

伪代码：
```text
输入：已有静态CAF数据D0；候选预处理/洗脱/终刺激条件C
1 用分层贝叶斯拟合两个嵌套模型：
   静态模型：lambda=0
   滞回模型：lambda>=0
2 对每个c in C，近似计算EIG(c)，选最大者做实验
3 测得功能y（迁移连续值、激活二分类），更新后验
4 在未参与拟合的留出供体上比较：
   预测MAE / Brier / log predictive density
   以及“历史方向”符号准确率
5 若滞回模型不优于静态模型，或lambda后验集中到0：
   停止该机制，不把失败归因于“样本不足”而继续加码
```

## 三、可用数据与缺失join

可用的是CAF作者XML：doi:10.1038/s41392-026-02965-1，PMC13680625，记录患者来源apCAF/mCAF、IFNγ/TGFβ处理、T细胞迁移/激活coculture、n=3/4，以及HRA011931/HRA008021等入口。但证据包明确：细胞因子扰动RNA与功能coculture不能静默拼成完整干预—响应表；未检查到匹配功能菜单。因此现有数据只能支持“现象可行性/参数先验”，不足以单独检验滞回。

缺失join包括：同一供体的预处理历史、洗脱时间、再刺激后功能重复；细胞因子浓度时间序列；供体协变量；以及功能读出与技术重复的噪声估计。若这些能从补充表或申请数据中获得，则先做回顾性可行性；若不能，则需在冻结协议后做最小前瞻实验。本回答不授权新生物研究。

## 四、最强普通解释

最强竞争解释不是“没有生物学”，而是：瞬时剂量—响应 + 供体随机效应 + 细胞因子受体饱和 + 洗脱残留 + 普通带滞后特征的回归。尤其普通模型若使用相同历史信息，也能表示滞回；因此不能以“可表示”反驳。本候选要赢的是有限数据下的预测/更新增益和阈值结构带来的可解释外推。若普通静态模型或普通滞后特征回归在留出供体上同样预测功能，则滞回结构没有贡献。

## 五、决定性廉价实验与失败规则

**实验**（需后续冻结协议授权）：在已有患者来源CAF供体上，做同供体配对的三条历史到达同一终刺激：A=IFNγ预处理→洗脱→IFNγ+TGFβ；B=TGFβ预处理→洗脱→同一终刺激；C=无预处理→同一终刺激。测T细胞迁移和激活。关键是终刺激相同，只变历史。若A/B/C功能无差异，或差异小于技术重复噪声，滞回现象失败。

**预测失败规则**：在留出供体上，滞回模型相对静态嵌套模型的连续功能MAE、二分类Brier/log predictive density没有改善，且“历史导致功能偏移方向”的符号准确率置信区间包含0.5，则作为预测机制失败。若现象存在但滞回模型不能预测留出供体，也只算现象线索，不算可用机制。

**更新失败规则**：主动EIG选择的实验相对随机选择的同预算条件，没有更快降低\(\lambda\)后验熵或没有提高留出预测，则更新规则失败；世界假说可另行检验，但不能声称更新机制有效。

有用增益在揭盲前预注册为：留出供体预测误差差值区间排除0，方向准确率区间下限高于0.5；不设任意临床效用margin。若区间宽，只报不确定，不报成功。

## 六、主张边界

本候选只主张一个世界模型结构：CAF功能状态可能具有细胞因子历史依赖的阈值/滞回；并给出贝叶斯更新和主动选点。它不主张通用逆设计、不主张RSI继承、不主张joint/C4加速，也不与LabCompass的生成式培养参数搜索混同。SubcellPert可未来作为亚细胞辅助协变量，但不是本检验必需；Huang等关于上下文特异差异响应易坍缩的摘要支持不要直接迁移全转录组，但不能替代本实验。若上述廉价检验失败，应明确放弃该机制，而不是用更大模型或更多历史阴性掩盖。

--- INDEPENDENT skeptic ---
## 1. 自由探索与筛选

我先看三个方向。  
(i) 基于“可恢复分辨率”做**上下文残差运输**：把扰动响应分解为共享响应 + 上下文特异残差，只在可测几何分辨率足够时启用残差。它直接命中“压缩后上下文特异差异响应塌缩”的发现，但证据包只确认摘要，全文、数据与代码未验证，最廉价判别实验缺少可执行资产。  
(ii) 用 CAF 的 apCAF/mCAF 功能共培养做**状态—功能校准运输**：生物学最贴近药效，但供体 n=3/4，且细胞因子 RNA 扰动与功能共培养不能静默拼接，缺匹配功能菜单。  
(iii) 用 SubcellPert 做**无 oracle 的共享亚细胞运输**。证据包给了 14 个成像数据集、13.88m 细胞、3.65b RNA 分子，且明确指出 Oracle 提供精确目标 counts、Joint 同时预测 counts 与定位；这留下一个具体、可证伪的操作问题。故只保留 (iii) 为主候选；若数据 schema 不含扰动标签或分子级位置，则没有可信候选。

## 2. 主候选：一致亚细胞运输（CST，推测性）

**生物假说 W**：扰动通过一个共享的亚细胞运输算子同时改变分子丰度与空间分布；counts 与定位是同一潜在算子的两个读出，而非两个独立任务。此假说是待检验的，不是证据包结论。

**操作**：对扰动 \(p\)、细胞/上下文 \(i\)、空间格 \(b\)，设扰动嵌入 \(e_p=E[p]\)，上下文嵌入 \(z_i\)，参考空间密度 \(q_i(b)\)：

\[
T_i(b,b')=\mathrm{softmax}_{b'}\left(-C_{b,b'}/\tau+A e_p+B z_i\right)
\]
\[
\pi_i=T_i q_i,\quad s_i=S e_p+U z_i,\quad r_i=\mathrm{softmax}(\log \pi_i+s_i)
\]
\[
\hat N_i=\mathrm{softplus}(v^\top[e_p;z_i]),\quad \hat n_i=\hat N_i r_i
\]

其中 \(T_i\) 是运输计划，\(\pi_i\) 是运输后的空间密度，\(s_i\) 是稀疏源汇项，\(\hat N_i\) 是总分子数。位置似然用 \(\pi_i\)。损失：

\[
L=\mathrm{CE}(n_i,\hat n_i)+\lambda_x\mathrm{NLL}(x_i\mid \pi_i)
+\lambda_s\|s_i\|_1+\lambda_e\|e_p\|^2
\]

关键不是“多任务”，而是 counts 与定位共享同一个 \(T_i\)；源汇项只允许有限偏离，并受稀疏惩罚。训练和评估必须按扰动留出，不能按细胞随机拆分。

**药物发现用途**：给定化合物/扰动，输出“丰度效应 + 空间重分布”双读数；优先排序两者一致的扰动，过滤只在 count 头上像阳性、但空间上不成立的候选，减少后续成像验证批次。它不是疗效声明，只是靶点参与和空间表型的优先级工具。

## 3. 等价性与表达力边界

我不主张 CST 与直接模型代数不等价。任何直接多任务模型加同样辅助损失都可逼近它；可检验的只是**有限数据/更新优势**。若同信息、同参数量、同训练预算、同辅助损失的直接模型追平 CST，则 CST 降级为普通正则化，不构成机制贡献。不能把“万能预测器可表示”当反驳，也不能把“约束更漂亮”当证明。

**最强普通对照**：  
1. 直接多任务：分别用 \(f_n(e_p,z_i)\)、\(f_x(e_p,z_i)\) 预测 counts 与位置，同参数、同辅助损失、同早停。  
2. 共享嵌入但分离头：有 \(e_p\)，无 \(T_i\) 运输约束；检验增益是否只来自共享表示。  
3. Oracle 精确目标 counts 上界与经典 Gaussian transport；排除“靠 oracle 泄漏”。  
4. 同信息世界无关控制：在扰动间置换 \(e_p\)，或跨细胞打乱空间标签但保留边际；若增益仍在，说明是泄漏/正则化。  
5. 若后续加主动选样，必须加随机/等预算混合搜索对照。  
6. 推广为框架前，证据包所列六个强对照家族须全部预注册；本阶段不宣称已满足。

## 4. 最廉价判别实验与失败规则

选**一个最小且含明确扰动标签的 SubcellPert 数据集**，只做回顾性实验；不做新生物学研究。确认 schema 后再下载。缺失 join 包括：扰动标签与细胞/分子级位置是否可对齐、是否有 vehicle/control 或可用上下文估计 \(q_i\)、实验 bundle 与成本是否明确。证据包称 schema/实验反馈 bundle 尚未 qualified，且未下载数据；这些不确认则不执行。

伪代码：

```text
for each leave-one-perturbation-out split:
  fit M_direct, M_shared, M_CST with same data/compute/early-stop
  eval count CE/MAE; localization centroid + radial metrics
  eval top-k perturbation ranking at fixed assay capacity k
  permute e_p across perturbations -> M_CST_perm
  report paired Δ vs max(controls), bootstrap over perturbations
```

**预注册有用增益**：在固定 k 个可验证扰动预算下，CST 在 count top-k 召回非劣的前提下，减少需要二次空间验证的假阳性批次；k 和“非劣界”由实际成像/测序容量与分辨率给定，不设临床效用阈值。联合判据要求 count 与 localization 的配对下界同时为正；只赢一个指标不算联合机制。

**失败规则**：直接多任务或“共享嵌入分离头”追平 → 拒绝结构假说；只在 oracle-count 设置赢 → 拒绝；增益在置换/打乱控制下消失 → 判为泄漏或正则化；schema 无法对齐 → 撤回候选；换一个独立数据集无同向增益 → 缩小 claim。若通过，才进入主动选样；主动增益若被随机/等预算混合搜索追平，也拒绝主动组件。

## 5. 主张分层

- **W（世界）**：存在扰动共享的亚细胞运输算子，耦合丰度与定位；这是可证伪假说。  
- **A（agent）**：CST 的共享运输约束在扰动留出下带来有限数据优势；只有对照通过才成立。  
- **I（继承求解器/策略）**：主候选不继承完整求解器；只可能继承 \(e_p\) 先验或运输参数，须做 transfer vs restart。  
- **J（联合）**：只有 counts 与 localization 同时超过最强直接对照，才称联合机制；单指标增益归普通多任务。  
- **C4**：若后续把它包装成可继承改进器，必须用同一 start 的 old/new improver 比较“继承后继续改进”与“重启后继续改进”；不预设超可加，也不要求无限加速。当前不主张 C4。

**会改变判断的证据**：同信息直接对照追平、增益仅存在于 oracle 或合成示例、置换控制下增益消失、schema 缺少扰动/位置对齐、独立数据集不复现、或 C4 同 start 测试无增益。反过来，若在扰动留出、同预算、无 oracle 条件下，CST 稳定同时改善 count 与定位，并能减少固定预算下的空间验证假阳性，则值得升级为带成本约束的主动查询框架。

--- INDEPENDENT application ---
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

--- ROOT_CROSS_QUESTIONS.md ---
# Questions after independent proposals and deterministic audits

All three independent responses were hash-sealed before this exchange. Each cross context receives all exact first responses, CHEAP_AUDIT_PROTOCOL.md, CHEAP_AUDIT_RESULT.json and this note. Please address the other roles' actual text, identify agreements and disagreements, correct your own errors, and select the best next evidence-producing action. Do not treat consensus as evidence or execute generated code. A precise repaired hypothesis is allowed; repairing an equation is not automatically novelty. Do not require positive data before proposing a hypothesis. About2500 Chinese characters each.

## Root's checked criticisms

CAF proposal: your lambda=0 model is first-order relaxation, not instantaneous static response. At common u=.5,kappa=1,t=1 it retains history difference exp(-1). Also lambda>0 is not sufficient for bistability; lambda1,kappa1 is strictly decreasing, while lambda5 has two stable outer equilibria. How distinguish slow relaxation, true equilibrium hysteresis, cytokine carryover, donor differences and composition shifts with available observations? n=3/4 functional experiments have no authenticated history/washout paired menu here. A wet-lab suggestion is legitimate, but no wet-lab access exists in this coding environment. Statistical significance is not an application-based useful-gain threshold, nor does posterior lambda at zero alone establish model invalidity. Does the current configuration warrant source qualification only, or mathematical/biological implementation?

Spatial proposal: with normalized r, sum(N*r)=N. Your abundance N head is independent of T at fixed features; a shared embedding still induces statistical coupling, so the audit does NOT deny all sharing, but the formula does not establish transport-mediated changes in total gene counts. Gene index and mass orientation are underspecified. A scalar shared across destination bins cancels from softmax; vector logits can fix that. How predict truly held-out perturbations using an unseen learned table E[p] without chemical/target descriptors? More importantly your failure rule says gain disappearing under label/spatial permutation indicates leakage. Correct biological signal should often disappear under permutation. Please correct this logic, explain valid controls, and separate model-training contribution from an actual agent. Counts+localization is not the user's world+agent joint benefit. C4 old/new improver from common start is distinct from inheritance vs restart. Would repairing these equations simply produce standard shared-embedding/unbalanced-OT multi-task prediction? Exact close predecessor still needed.

Decision-flip proposal: exact enumerated counterexamples show positive flip/cost but negative net value, and greater flip can rank a much less valuable query first. p_noise does not fix missing effect magnitude or treatment-vs-control noise differences. Treat the rule as a heuristic unless justified by a measured utility model; replacing it with knowledge gradient/EVSI is ordinary Bayesian design. Contrast low-rank endpoint alignment is closely related to standard supervised factorization/PLS; identify a precise additional difference or retain it as a conventional baseline. Convex-hull membership alone does not guarantee functional transport without the response assumptions. Your registered success suggestions based on vehicle noise/CI alone do not authenticate actual application value. Also NCI-ALMANAC can support a static action-conditioned functional world if correctly scoped; absent RNA does not automatically exclude a world-model study. Do not fabricate separate queryable assay bundles not released in data.

## Added primary evidence, not in first prompts

Author full XML for Lorch et al., “Latent causal diffusions for single-cell perturbation modeling”, PNAS, doi10.1073/pnas.2602630123, PMC13663777 (2026-10-08), retained with HTTP200, SHA3121d00e54c5c0a5bb13a5ef1dcd79087efff8d450393e5610bf5439d52f36ef. It models stationary noisy RNA, predicts unseen perturbation combinations, and linearizes learned drifts with CLIPR A=-VL+ (regularized form -VL^T(LL^T+lambda I)^-1), under explicit linear/rank assumptions. Author text distinguishes DE from direct effects; acknowledges multiple trajectories can share snapshots, perturbation diversity/assumptions matter, and weakly spanned shrinkage is not absence of regulation. All assessed perturbation datasets single-time-point; future multimodality/bistability mentioned. This is close prior for generic causal/dynamical coupling; it does not rule out new biological structure. We have not reproduced results or downloaded its data. Do not misread stationary inference as unrestricted identifiability.

Podocyte full text further states zero genes meet FDR<.05 in either screen; primary hits use nominal P<.05 and abs(log2FC)>=1. Five claimed replicates per condition are not many independent task populations. This does not prove null biology, but candidate-hit overlap is exploratory, not independently validated therapeutic targets.

## Desired outcome

Choose at most one priority from the three exact proposals or a clearly delimited repair. Record supportive evidence, strongest objection, disagreement, necessary module, missing source/data join, and one next discriminating action. If none is implementable, propose a checkable alternative primary asset/search target that addresses the missing task structure; mark unverified. We seek a credible new contribution with actual drug-discovery relevance, not an endless list of renamed standard algorithms. A conventional pilot may be useful if it resolves a specific new question and is explicitly labeled conventional; no biological fits or API-reported performance may be invented.


--- CHEAP_AUDIT_PROTOCOL.md ---
# Frozen discriminating mathematical audits

2026-10-22. Independent first responses are sealed in INDEPENDENT_RESPONSE_SEAL.json. Before implementing any biological model, run three small, deterministic audits of stated operations. These are counterexamples/necessary-condition checks, not biological simulations, benchmark wins, experiments on hidden assays, or universal mechanism impossibility proofs. No historical thresholds are changed. No fit or biological data conversion occurs.

1. CAF: evaluate the proposal's lambda=0 ODE analytically at kappa=1,u=.5,t=1 from s0=0 and1. Compare the same-current-input histories. For theta=.5 derive f'(s)=-kappa+lambda(-3s²+3s-.5). On[0,1] its maximum is -kappa+lambda/4. Therefore kappa=1,lambda=1 is strictly decreasing/uniquely equilibrated despite lambda>0. At lambda=5,u=.5 exhibit the three equilibria and their stability. Purpose: distinguish finite relaxation memory from bistable hysteresis; do not infer whether CAF biology has either.

2. Shared transport: grant the most favorable dimensionally consistent mass-preserving implementation (row-vector q times row-stochastic T, rather than the ambiguous written Tq). Use two distinct row-stochastic matrices and nonuniform spatial source-sink terms. With r=softmax(log(pi)+s), n=N*r, sum(n)=N independent of T and s at fixed abundance head. Show changed location but unchanged total. Separately show destination-independent scalar conditioning cancels from softmax, explicitly conditional on that scalar interpretation; vector logits need not cancel. Do not claim no statistical coupling via shared embeddings/training or no valid future gene-specific unbalanced model.

3. Decision flip: exact finite-state Bayesian query oracle, with perfect outcomes and deterministic zero vehicle noise. Incumbent reward .6; candidate is .61/.59 with probability .5/.5, assay cost .1 in reward units. Positive flip probability but net value .005-.1<0. For allocation, incumbent0, two prior-mean0 candidates: B=.001 with p=.9 else -.009; C=1 with p=.1 else -1/9. Equal cost .01; flip heuristic prefers B but expected improvement prefers C. Enumerate and compare exact rational expected utility. This disproves decision-optimality/cost-worth guarantees of the proposed rule, not a potential empirical heuristic advantage. Costs here are illustrative counterexample parameters, not authenticated biological assay costs or new utility thresholds.

Run assertions against these preregistered identities and retain JSON numbers and code hash. Actual reviewers will receive the exact sealed first opinions, these results and primary-source additions, then respond to one another. Their agreement cannot substitute for the checks or establish novelty. Subsequent biological fitting remains gated on qualified data and a distinct frozen study.


--- CHEAP_AUDIT_RESULT.json ---
{
  "status": "PASS",
  "checks": {
    "lambda0_has_finite_history_memory": true,
    "lambda1_strictly_decreasing_no_bistability": true,
    "lambda5_three_equilibria": true,
    "lambda5_outer_stable_centre_unstable": true,
    "transport_locations_change": true,
    "normalized_count_total_head_unchanged": true,
    "only_destination_constant_condition_cancels": true,
    "positive_flip_can_have_negative_net_value": true,
    "flip_ranking_can_reverse_value_ranking": true
  },
  "code_sha256": "c19d9ea162ec7eadc2b2429bffc8d231b8bc3aa4acca40dd1664ef2ef42db8df",
  "caf": {
    "lambda0_states": [
      0.31606027941427883,
      0.6839397205857212
    ],
    "history_difference": 0.36787944117144233,
    "lambda1_max_drift_derivative": -0.75,
    "lambda5_equilibria": [
      0.27639320225002106,
      0.5,
      0.7236067977499789
    ],
    "lambda5_derivatives": [
      -0.49999999999999956,
      0.25,
      -0.49999999999999956
    ]
  },
  "transport": {
    "pi": [
      [
        0.2,
        0.3,
        0.5
      ],
      [
        0.41,
        0.36000000000000004,
        0.22999999999999998
      ]
    ],
    "spatial_bin_counts": [
      [
        24.6,
        36.89999999999999,
        61.5
      ],
      [
        88.87511966281339,
        3.885218041921097,
        30.2396622952655
      ]
    ],
    "total_counts": [
      123.0,
      122.99999999999999
    ],
    "total_head": 123
  },
  "decision": {
    "harmful_query": {
      "prior": {
        "exact": "3/5",
        "value": 0.6
      },
      "flip": {
        "exact": "1/2",
        "value": 0.5
      },
      "evsi": {
        "exact": "1/200",
        "value": 0.005
      },
      "cost": {
        "exact": "1/10",
        "value": 0.1
      },
      "net": {
        "exact": "-19/200",
        "value": -0.095
      },
      "flip_score": {
        "exact": "5",
        "value": 5.0
      }
    },
    "candidate_B": {
      "prior": {
        "exact": "0",
        "value": 0.0
      },
      "flip": {
        "exact": "9/10",
        "value": 0.9
      },
      "evsi": {
        "exact": "9/10000",
        "value": 0.0009
      },
      "cost": {
        "exact": "1/100",
        "value": 0.01
      },
      "net": {
        "exact": "-91/10000",
        "value": -0.0091
      },
      "flip_score": {
        "exact": "90",
        "value": 90.0
      }
    },
    "candidate_C": {
      "prior": {
        "exact": "0",
        "value": 0.0
      },
      "flip": {
        "exact": "1/10",
        "value": 0.1
      },
      "evsi": {
        "exact": "1/10",
        "value": 0.1
      },
      "cost": {
        "exact": "1/100",
        "value": 0.01
      },
      "net": {
        "exact": "9/100",
        "value": 0.09
      },
      "flip_score": {
        "exact": "10",
        "value": 10.0
      }
    }
  },
  "biological_fits": 0,
  "biological_values_read": 0,
  "reserve_values_read": 0
}
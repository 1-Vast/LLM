**独立首评（无其他角色加权）**  
结论先行：当前资产**不值得直接作为“新核心机制”投入拟合或新实验**；值得继续的只有一次低成本的**数据资格审计**。若必须推荐一个公共一手资产，我推荐 **Joy et al. 2023 / Zenodo 8385319**，而不是 CAF 2026 或 GSE229742。唯一可提的机制是“张力门控的备用池—易释放池转换”，但它目前只是可证伪假说，且普通两池/时间-PKPD 解释尚未排除。

### 1. 唯一候选机制：张力门控备用池，而非一般递归
**主源**：Joy et al., “Synapses without tension fail to fire in an in vitro network of hippocampal neurons”, PNAS, doi:10.1073/pnas.2311995120；PMC10756289；作者链接的 Zenodo 8385319。该文的全文 XML 和 Zenodo 元数据已取得；五个小型工作簿的公开 MD5/大小匹配，但本包只核验了文件、表头和 ZIP/表结构，**未把表内数值当作已提取标量**。  
作者报告的定性现象是：Y27632/blebbistatin 使 3D 神经元力下降，washout 后力恢复；MEA  firing 在 24–48 h 恢复，而囊泡聚集未完全恢复；文中给出约 90% firing 对 20% 囊泡下降的描述，并明确带 off-target/adhesion caveat。作者自己的局部 reserve/readily releasable pool 解释**不是我们的新颖性**。

**可检验机制**：设 \(T_t\) 为实测或可推断的张力，\(C_t\) 为囊泡聚集/备用池代理，\(R_t\) 为易释放池，\(F_t\) 为 firing。核心结构不是一般 latent recurrence，而是：**张力只门控 \(C\to R\) 的补充速率，不直接改释放概率**；washout 只让 \(T_t\) 慢弛豫，\(R_t\) 受有界备用池约束。最小操作可写为  
\[
R_{t+1}=R_t+k(T_t)(C_t-R_t)-\rho u_tR_t,\quad
T_{t+1}=T_t+\frac{T_{\rm ext}(t)-T_t}{\tau_T},
\]
\[
k(T)=k_{\min}+\frac{k_{\max}-k_{\min}}{1+e^{-(T-T_{50})/s}},\quad
F_t=g(R_t).
\]
关键可观测判别量是 recovery gap：  
\[
D_t=F\text{-recovery}_t-C\text{-recovery}_t.
\]
机制预测 washout 早期 \(D_t>0\)，即 firing 可先于囊泡聚集恢复；若张力恢复慢，则 \(D_t\) 缩小或延迟。普通解释是 use-dependent synaptic depression + reserve pool + actomyosin 对健康/黏附的影响；张力也可能只是损伤/黏附标志，而非因果门控。

**药物发现应用**：不是宣称疾病疗效，而是用于 actomyosin/ROCK/NMII 类 CNS 候选的**washout/re-dosing 功能安全决策**：判断“等到 firing 恢复”是否足够，还是需要等到囊泡聚集恢复；若张力门控成立，短 washout 可能恢复功能但留下结构/储备缺口。该应用价值目前仅是待验证假设。

### 2. 证据筛选：为什么只到这里
CAF 2026（doi:10.64898/2026.09.19.752881）只有作者元数据/摘要已认证，全文访问失败（OpenAlex PDF/Grobid 401，未建 key/账号），无 CAF traces、任务菜单或成本；不能从摘要造定量数据。GSE229742 是 CAF05 在不同刚度下的 RNA（3 重复），无与 2026 力学/FRAP 或 2023 神经元功能的配对，不能当 action-conditioned functional world。2021 方法、2025 protocol、2024 YAP 摘要均不足以构成可执行任务/反馈。  
Joy 资产相对最好：全文 XML + 明确 Zenodo 链接 + 小工作簿文件校验。但关键缺陷是**没有已核验的同一 run 的 force–firing–vesicle 时间序列**。Fig3d 只有一个 force history，且处理区间映射 UNVERIFIED；Fig3b 是三个发育时间点，不是 1404 个任务；Fig5a/b 有相同 sample1–4 行标签和 before/after 1 h bleb/24 h/48 h 列，可能是配对端点，但**精确共享 raw run 身份与归一化 UNVERIFIED**；四个样本一个共同处理序列不构成跨药或 later-task  population；Fig6h 行匿名，不能当独立任务；Fig7g 是 STORM 像素 CDF（19 control/135 treated synapses），不是 firing 轨迹，且未下载，不能按文件大小造任务。  
历史 scoped negatives 也要保留：TG-GATEs rho0 DNA MAE .02731534 输给普通 refit .01895104；AZ paid-reference transport .07766765 输给 full direct .06620680；STACK 有 3.50% real gain 但未过注册有用阈值；简单继承动力学曾恰好匹配 mixture/search。任何新 world 必须赢过强 same-data refit/CL/AL/mixture/equal-budget search，而不是只赢旧基线。

### 3. 最廉价判别步骤（无拟合、无新 assay）
先做一次**来源资格审计**：用已下载的五个工作簿和 Joy 全文 XML，逐行重建“条件—样本/run—归一化—时间点”，只回答两个问题：  
1. 是否存在**同一培养/run** 的 force 与 MEA firing 时间序列，且 washout 时刻可重建？  
2. Fig5a/b 的列是否真是同一 MEA run 的配对端点，而不是同一处理序列下的多个电极/时间点？  
若答案是否，或只能把 3D force 与 2D MEA 按 “Sample1” 硬配，则 **STOP**，不进入拟合。若答案为是，再申请小 pilot 授权；本包不授权 fitting 或新实验。

**任务/反馈契约（仅审计版）**：任务单位必须是独立培养/制备/run，带药物、浓度、起止、washout、测量时刻；反馈是该 run 的 spike/burst rate 或 recovery class，并附 provenance 标志（是否同 run、是否归一化、是否独立）。时间点、电极、像素、行号均不得计为独立任务。当前 Joy 数据最多支持“候选端点表”，尚不满足 action-conditioned world 契约。

### 4. 成功/停止条件
**资格审计 GO**：至少一个关键 washout 对比有同一 run 的 \(T_t\) 与 \(F_t\)（最好有 \(C_t\)）时间序列，处理区间可重建，且至少两个独立培养/run 支持该对比；否则 STOP。  
**机制 GO（需另行授权）**：在 run-level held-out 上，门控转换模型相对普通两池/时间-PKPD，在相同信息、相同数据、同数据重拟合/CL/AL/mixture/equal-budget 搜索后，仍降低决策损失；增益须能换算为减少的独立 washout/MEA 实验成本或避免的错误 schedule，不能只用统计显著性。  
**证伪/STOP**：\(D_t\le 0\)；或 firing recovery 被 time-since-washout + baseline firing + \(C_t\) 完全解释；或张力项在 held-out 上无增量；或力仅反映黏附/健康混杂；或只能 in-sample 拟合。  
**C4 另计**：旧/新 improver 必须 common start、等预算；继承/restart 不能替代 C4。当前不能声称 C4，旧配置 STOP 保留，TG-GATEs later14/AZ413reserve 不打开。

### 5. world / agent / 继承 / 联合 / C4 归因
- **world**：只有在同一信息集、同一 run-level holdout 下，张力门控备用池赢过普通两池/时间-PKPD 且经强 refit 对照，才归因给世界结构；否则 world=0。  
- **agent**：只有允许选择下一个 washout 时点/条件，且成本敏感策略比随机/简单网格降低决策损失时才归因；现有四个样本/电极/时间点不是独立 query tasks。  
- **继承**：只有旧参数/结构继承相对从零重训有 held-out 增益才归因；历史上“简单继承恰好匹配 mixture/search”是强警告。  
- **联合**：必须是 world×agent 的 2×2 factorial，joint 超出单独增益；counts+location 不是 world+agent joint。  
- **C4**：只能是 old/new improver common-start、等预算的 RSI 比较；不是 inheritance/restart。当前资产不能支持 C4 归因。

**正式建议**：推荐 **source-only 继续 Joy/Zenodo 8385319 的资格审计**；若审计不过，停止该方向。若必须给一个机制，我只把“张力门控备用池”列为待证伪候选，不把它当已验证新核心。
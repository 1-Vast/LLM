**候选1｜动作依赖的“未来查询成本”状态（可证伪，phenotype-only）**

(1) 药物实验：用E. faecalis V583主实验的day2/4/6/8 collateral profile，预测“下一次IC50实测是否需要新查询”，并在固定预算下决定测哪个challenge drug。功能应用是降低确认药敏的实测次数。

(2) 最小操作：state s_t=(当日实际转移浓度d_t、可见生长孔、last-IC50向量、已查询集合Q_t)。定义查询成本c_t=1[challenge未在Q_t]；预测目标为IC50_{t+1}的均值和c_t。策略：argmax_d E[IC50改善|s_t,d]−λ·E[c_t|s_t,d]。仅用已测行，Q_t按真实查询顺序构造；λ由预算扫描。

(3) 实质差异：ordinary dynamic MDP与last-IC50都不含“未查询药需额外成本”这一状态；AL不含动作依赖的d_t。精确归约风险：若Q_t与d_t独立且成本恒为1，则退化为普通多输出回归+固定成本MDP；若成本只依赖t，则退化为普通AL。

(4) 需要：主实验5药×4lineage×4timepoint的完整IC50表、每日实际浓度与转移记录、challenge drug名单、查询顺序。未认证缺口：S1Data行数/缺失/schema未读；clone与population身份未join；20population CRO→DOX实验不能混入主实验。

(5) 最快杀死：在已测行上，用same-information direct multioutput预测c_t的AUC≤0.5，或加入c_t后策略收益相对λ=0无提升。

(6) 可证伪预测：world：c_t可由d_t与Q_t预测（AUC>0.6）；agent：含c_t的策略在等预算下命中数高于普通MDP；继承：把c_t规则写入后继程序，m1在新lineage上首次查询数低于m0；联合：world+agent联合优于各自单独；improver m1胜m0：在留出lineage上m1的查询次数下降且IC50命中不降。

**候选2｜“挑战前置条件”的时序反事实（可证伪，仅限CRO→DOX 20population）**

(1) 药物实验：CRO适应14天中，判断“第k天把样本转入DOX挑战”比第k+1天更优的实测设计；功能应用是定时第二药切换窗口。

(2) 最小操作：对每个population，记录day k的CRO母培养OD与DOX dose–response（IC50、AUC）。定义前置条件量g_k=IC50_DOX(k)−IC50_DOX(k−1)。假设g_k在k*处符号翻转；只用k≤k*的数据拟合翻转点，预测k*+1的IC50。公式：ĥ=argmin_h Σ_{k≤h}(IC50_k−f(k;θ))²，f为分段线性。

(3) 实质差异：原作dynamic MDP用day2/4/6/8的collateral profile做逆时序规划；本候选只用CRO→DOX的每日功能挑战，且不假设future profile已知。精确归约：若g_k单调且无翻转，则退化为普通refit分段线性，无新贡献。

(4) 需要：20population每日CRO母培养OD、DOX dose–response原始OD、IC50/AUC拟合单位、technical vs biological replicate、sampled branch与母培养的exact join。未认证缺口：Zenodo manifest未取；post-challenge continuation是否存在未知；不能把20population与主实验4replicate混算。

(5) 最快杀死：在20population上，g_k无符号翻转（翻转点估计置信区间覆盖全程），或分段线性相对普通refit无样本外IC50改善。

(6) 可证伪预测：world：g_k存在可估计翻转点（bootstrap CI不含端点）；agent：按ĥ选择切换日，DOX IC50低于固定day选择；继承：ĥ规则迁移到新population，m1的切换日误差低于m0；联合：world+agent联合优于固定日程；improver m1胜m0：m1在留出population上IC50降幅大于m0且查询次数不增。

两候选均为条件性假设；当前只有source lead，无WM/Agent/继承/RSI性能证据。若S1Data schema不支持Q_t或每日DOX原始OD，则相应候选降为普通应用，应报none。
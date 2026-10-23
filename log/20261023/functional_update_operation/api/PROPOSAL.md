NONE。无可自证区别的更新操作。16line已把panel-context restricted（linear/RBF）与full比较：MSE仅降3.47/3.59%，14/16同向，未过预注册5%门；top10 regret full .08565劣于geneprior .08521。故“按基因先验/QC/panel模块限制传播”的公式会退化为已测restricted kernel ridge/conditional EB，不能换名重启。

唯一可能形态：反馈残差 \(r_s=y_s-\hat y_s\)，令 \(N(q)\) 仅由预注册panel/QC/基因先验决定，\(\hat y_q^+=\hat y_q+\sum_{s\in N(q)}w_{qs}r_s,\; w=K(q,S)(K(S,S)+R)^{-1}\)。可继承对象为 \(N,K,R\)。但它就是强ordinary \(K(q)=Cov(e_q,r_S|q)[Cov(r_S|q)+R]^{-1}\) 的受限版；取RBF/panel邻域即restricted kernel ridge，取union support即CL/union refit。失败反例：q与s同panel但不同功能模块，\(Cov(e_q,r_s|q)=0\)，传播把s的line/batch特异误差注入q；或模块内正负残差混合，同向投影保留偏差。

当前缺失的具体可观测关系是独立line/batch留出中的配对“反馈残差—未测query误差条件方向协方差”：\(Cov(e_q,r_s|q,panel,QC,base)\) 显著非零，且geneprior/QC不能解释；现有只有聚合MSE/regret，没有该误差迁移矩阵，不能定位“一条反馈应纠正哪些未测干预/状态”。

最小合成双向检验（同信息同成本）：固定support数、query数、R、计算。支持例令 \(e_q=+0.6r_s+\epsilon\)，G1应较G0降MSE≥5%；推翻例令 \(e_q=-0.6r_s+\epsilon\) 或由异模块残差生成，G1应由前反馈关闭传播、不优于G0；若仍传播即失败。两例同时过才算非ordinary。需新独立真实功能应用数据：未参与16line的新line/batch，含真实Chronos或功能扰动标签，预注册q/S划分与5%门；分开U1/U0（真实反馈后模型适应 vs 不更新）与G1/G0（同base/history/budget的受限传播编辑器 vs 强ordinary条件EB/union refit）的后代功能效用，仅G1-G0过门才升级，否则STOP。不得把16line当确认。
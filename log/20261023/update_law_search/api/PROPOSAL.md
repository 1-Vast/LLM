NONE（作为新核心）。没有可证伪且非归约的额外更新操作；不声称性能、创新或RSI。

公式归约（4行）：
1. 普通低秩补全 \(\hat r_i=M_\Theta(u_i,v_i)\)；single-RNA 仅定义候选边先验 \(G=\{(u,v):s(x_u,x_v)\ge\tau\}\)。
2. 任何拟议受限反馈更新可写成同信息 refit：
\[
(\tilde\Theta,\hat\beta)=\arg\min_{\Theta,\beta}\sum_{i\in F}\ell\!\left(r_i;M_\Theta(u_i,v_i)+\beta^\top z_i\right)+\lambda R(\Theta,\beta),\quad z_i=(\phi(u_i),\phi(v_i),\hat r_i).
\]
3. 若只选边 \(S\subset G\)，等价于上式加 \(L_0\)/候选图约束；若用局部秩一，则
\[
J'^{-1}=J^{-1}-\frac{J^{-1}e_i v^\top J^{-1}}{1+v^\top J^{-1}e_i},
\]
即 IFT+Sherman–Morrison，无新估计器。
4. 单反馈只给 \(r\approx a^\top\delta\theta\)，沿 \(\ker(a^\top)\) 不可辨识；单轴相同、组合不同的 mixed-curvature 反例足以否定“单轴轨迹/Jacobian自动识别组合”。

最近普通操作如何复制：把相同候选边、相同 single-RNA 特征、相同反馈与调参预算交给 ordinary union refit/direct 即可复制选边；新增限制“先验候选图+不重估主效应”尚未形成可辨识目标，故无实质新增。法定输入：Norman 103 single/control RNA 与 3,160 source 功能 pairs 可做 source-only 探索；1,051 条已暴露 dev pairs 必须披露且不得当未触碰评估。SCHEMATIC 当前 score 经每 anchor 全 panel 回归/标准化，原始 counts 未取得，不可当合法稀疏反馈；不得使用未取得的 paired RNA。继承规则：普通低秩补全加 single-RNA 候选先验。未来 HYPOTHESIS：仅当存在“反馈符号一致性阈值的二值选边规则”且不重估主效应时，或许省样本；当前未定义。

最小反证：固定 G，用同一小反馈比较选边与 \(M_\Theta+\beta^\top z\) 的 ordinary refit；若同成本下 refit 不差，则停止。成功条件：仅在预注册未暴露 source pairs 上，相对最强同信息 refit/direct 在固定反馈成本下功能MSE与固定预算排名同时改善；否则停止。
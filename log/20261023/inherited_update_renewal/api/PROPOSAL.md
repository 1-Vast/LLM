提出一个操作：**控制零空间—同前向功能坐标共线更新约束**。不新增模块，只限制新任务反馈更新可行集。

设任务 \(t\) 基线虚拟细胞为 \(f_{\theta_t^0}\)。控制输入 \(X_t^C=\{x_{t,i}^C\}_{i=1}^4\)，药物反馈 \( (x_{t,j},y_{t,j}) \)（每药1点，共5点），锚点集 \(X\) 取同一前向坐标下的控制点与静态endpoint图节点。历史任务 \(h\) 有更新前后 \(\theta_h^0,\theta_h^{\rm post}\)。定义历史功能增量
\[
g_h(X)=f_{\theta_h^{\rm post}}(X)-f_{\theta_h^0}(X).
\]
当前雅可比 \(J_C=\partial f_{\theta_t^0}(X_t^C)/\partial\theta\)，\(J_X=\partial f_{\theta_t^0}(X)/\partial\theta\)。继承方向唯一由
\[
s_t=\arg\min_{s:\,J_Cs=0}\sum_h\|g_h(X)-J_Xs\|_2^2+\epsilon\|s\|_2^2
\]
给出，\(\epsilon\) 仅数值稳定，不是置信半径。新任务只估一个标量：
\[
\theta_t^{\rm post}=\theta_t^0+\alpha_t s_t,\quad
\alpha_t=\arg\min_\alpha\sum_j\big(f_{\theta_t^0+\alpha s_t}(x_{t,j})-y_{t,j}\big)^2+\lambda_R\alpha^2,
\]
\(\lambda_R\) 由历史留一任务选，不碰新任务留出。若需同边非线性重拟合，则对每个历史 \(h\) 在 \(X\) 上迭代求 \(g_h=f_{\theta_h^{\rm post}}-f_{\theta_h^0}\) 的相同前向坐标残差；不比较参数坐标增量。继承对象是 \(s_t\)，不是参数delta、药名或亲和核。

针对的可重复错误：4个无抑制剂controls加每药1反馈可被普通affine/直接refit张满，把控制批次差或噪声误归因到边。信息条件：controls确为未处理、历史contexts中控制残差低、且静态endpoint图显示药物差主要落在 \(J_C\) 零空间。此时比same-info direct/union refit省反馈，因为不学方向仅估1幅度；比calibration鲁棒，因为先限方向而非事后缩放；比metaupdate/equal-budget search省搜索，因为只在历史功能坐标对齐后的一维曲线内估计。其成立性为 **HYPOTHESIS**：历史功能增量在相同前向坐标重拟合后，到控制零空间的最小二乘方向跨context稳定且一维足够。

最小合成反例：\(f_\theta(x)=\theta^\top x\)，\(p=6\)，4 controls使 \(J_C\) 零空间为 \(\mathrm{span}(e_5,e_6)\)。真实 \(s_0=e_5+2e_6\)，药物反馈 \(a_F=e_5+e_6\)，\(y=3\)。普通same-info最小范数direct LS解 \(\delta_{\rm LS}=1.5(e_5+e_6)\)；留出 \(x=e_6\) 的真实预测2，direct为1.5，误差0.5。本约束继承 \(s_0\)，估 \(\alpha=1\)，误差0。强常规对手为direct LS、参数坐标union refit、calibration、低秩metaupdate、等预算随机搜索；若历史参数重参数化使直接平均 \(\delta_h\) 得 \(1.5(e_5+e_6)\)，本操作因在 \(X\) 上重拟合 \(g_h\) 仍
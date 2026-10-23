1. 唯一更新器：对干预 \(i\)，冻结当前状态编辑器 \(E\) 与功能头 \(h\)，令 \(x_i^0=E(i)\)、\(f_i^0=h(x_i^0)\)、\(r_i=y_i-f_i^0\)（\(y_i\) 为真实功能）。动作 \(a_i\) 进入 GRN 的受体活性门取 \(\alpha_i=1+\delta_i\)，只乘到 \(a_i\) 的已知外向作用；\(p_i=\partial h(E(i);\alpha_i)/\partial\alpha_i|_{\alpha=1}\)。更新
\[
\delta_i=\mathrm{clip}\!\left(\frac{p_i r_i}{\|p_i\|^2+\tau_i},-b_i,b_i\right),\quad \tau_i=\frac{\sigma_i^2}{n_i},\quad b_i=\sqrt{\frac{2\sigma_i^2\log(1/\varepsilon)}{n_i}},
\]
预测 \(f_i^1=h(E(i);1+\delta_i)\)，而 \(x_i^1=x_i^0\)。即功能反馈只修正功能预测，不借功能终点改写 RNA 状态。

2. 跨任务继承只传 \((\delta_i,s_i^2)\)，\(s_i^2=\sigma_i^2/(n_i\|p_i\|^2+\tau_i)\)。新任务 \(j\) 先用先验 \(\delta_j\sim N(\delta_i,s_i^2+\kappa)\)，再用其自身 \(y_j\) 按上式更新；\(\kappa\) 由源任务留一折估计，不另设网络。每个动作仅有 1 个可继承标量，反馈成本随 \(n_i\) 线性。

3. 同信息强 direct/ordinary union refit 会解
\[
\min_{E,h}\sum_i\|x_i-E(i)\|^2+\lambda\sum_i\|y_i-h(E(i))\|^2,
\]
让功能反馈同时进入 \(E,h\)；即使再拟合一个 \(\alpha\)，也不能保证 \(x_i^1=x_i^0\)，且新任务须重估全部参数。只有当它额外施加“冻结 \(E,h\)、仅单标量 \(\alpha\)、样本数界 \(b_i\)”时，才与本式逐点等价；因此可检验增益来自该限制，而非回归名字。

4. 最小反例：\(a=1\)，\(h(s;\alpha)=\alpha s\)，\(E(a)=0.9\)，真实 \(y=1.2\)。则 \(p=0.9,r=0.3,\delta=0.333\)，得 \(f^1=1.2,x^1=0.9\)；ordinary refit 可令 \(E=1.2\) 拟合 \(y\) 却改状态。等价检验：若 \(p=0\)，或把 ordinary refit 限制为仅 \(\alpha\) 且冻结 \(E,h\)，两者相同。

5. 真实有界实验（HYPOTHESIS：Norman K562 现有单/双扰动功能表含实际 fitness/growth 或增殖终点，且可与状态配对）：固定 \(E_0\)=常规 RNA 条件补全，用 20 个单扰动功能反馈估 \(\alpha\) 后冻结；测试 20 个留出双扰动功能，比较 no-update、本更新器、同反馈 ordinary union refit。成功：留出功能 MSE 较 no-update 降 \(\ge10\%\)，且较 ordinary refit 降 \(\ge5\%\) 或同功能下状态 MSE 更低；状态 MSE 升 \(\le1\%\)。STOP：功能降 \(<5\%\)、ordinary refit 不差（差异 CI 含 0）、状态 MSE 升 \(>2\%\)，或有效 \(n<10\)。

6. 分离继承与编辑器改善：预注册 \(2\times2\)：编辑器 \(E_0/E_1\) × 更新器 off/on。继承收益用 \(E_0\) 折拟合的 \(\delta\) 原样搬到 \(E_1\)/新折，比较 \((E_0,U)-(E_0,0)\) 与 \((E_1,U_{\rm transfer})-(E_1,0)\)；编辑器改善比较 \((E_1,U_0)-(E_0,U_0)\) 及 \((E_1,U_{\rm transfer})-(E_0,U_{\rm transfer})\)，其中 \(U_0\) 为不更新。若 \(E_1\) 提升只在重拟合 ordinary 或重估 \(\delta\) 后出现，则判为编辑器改善，不算继承。

7. 若不允许“冻结 \(E,h\)、单标量、样本数界”这一具体限制，则没有超出普通 union refit 的新操作，应判 NONE；若允许，则只按上式实测，不预设性能。
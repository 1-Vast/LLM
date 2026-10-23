**唯一候选：边差符号门控更新（Edge-Sign Gated Update, ESG）**。若下述最小证伪触发失败条件，则结论为 **NO_CANDIDATE**，不再给第二个规则或调参版本。

### 1. 合法观察与功能任务
- 合法观察：真实反馈批次 \(B=\{(s_i,d_i,y_i)\}\) 中已测的细胞状态 \(s_i\)、药物/剂量 \(d_i\)、标量功能响应 \(y_i\)。更新只使用 \(B\) 内已测样本；缺失药物-状态组合不估计、不填反事实、不预测未测绝对 count。
- 可观测边：仅由 \(B\) 内已测对构成  
  \[
  E_B=\{(i,j): d_i=d_j,s_i\ne s_j\ \text{或}\ s_i=s_j,d_i\ne d_j\}.
  \]
- 功能任务：世界模型 \(f_\theta(s,d)\) 输出功能响应排序分数，用于给下一批候选药物-状态实验排序；评价只用留出已测响应对的 pairwise/Kendall 排序。
- 数据合同：假设每个 study 内有足够上述可观测边，且可做 leave-one-study-out 回放。该合同尚未认证；下载数据本身不算创新。

### 2. 公式与伪代码
模型分解为 \(f_\theta(s,d)=b_\psi(s)+g_\phi(s,d)\)，冻结 \(\psi\)，只更新药物效应模块 \(\phi\)。固定预注册方向基 \(V\)，继承历史白名单 \(V_h\subseteq V\)。  
残差与边差：
\[
r_i=y_i-f_\theta(s_i,d_i),\quad \rho_{ij}=r_i-r_j.
\]
方向 \(v\in V\) 的边敏感度：
\[
a_{ij,v}=v^\top\frac{\partial[g_\phi(s_i,d_i)-g_\phi(s_j,d_j)]}{\partial\phi}.
\]
门控统计：
\[
m_v=\sum_{e\in E_B}1[|a_{e,v}|>\epsilon],\quad
k_v=\sum_{e\in E_B}1[\operatorname{sign}(\rho_e)=\operatorname{sign}(a_{e,v})],
\]
\[
p_v=\Pr[\operatorname{Bin}(m_v,1/2)\ge k_v].
\]
接受集合与更新：
\[
A=\{v\in V_h: m_v\ge m_{\min},\ k_v/m_v\ge 0.5+\delta,\ p_v\le \alpha/|V_h|\},
\]
\[
\phi\leftarrow \phi+\eta\sum_{v\in A}\operatorname{sign}\Big(\sum_{e\in E_B}\operatorname{sign}(\rho_e)a_{e,v}\Big)v.
\]

```text
输入: fθ, 固定V, 继承Vh, 冻结超参(α,δ,mmin,ε,η); 反馈B
E = {(i,j) in B×B: (d_i=d_j,s_i≠s_j) 或 (s_i=s_j,d_i
**唯一候选：边差符号门控更新（Edge-Sign Gated Update, ESG）**。若最小证伪触发失败条件，则结论为 **NO_CANDIDATE**，不再给第二个规则或调参版本。

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
E = {(i,j) in B×B: (d_i=d_j,s_i≠s_j) 或 (s_i=s_j,d_i≠d_j)}
r_i = y_i - fθ(s_i,d_i)
for v in Vh:
    m_v = 0; k_v = 0; S_v = 0
    for (i,j) in E:
        a = v^T ∂[gφ(s_i,d_i)-gφ(s_j,d_j)]/∂φ
        if |a| > ε:
            m_v += 1
            if sign(r_i-r_j) == sign(a): k_v += 1
            S_v += sign(r_i-r_j) * a
    p_v = BinomTail(m_v, k_v)
    if m_v >= mmin and k_v/m_v >= 0.5+δ and p_v <= α/|Vh|:
        A.append(v); s_v = sign(S_v)
φ ← φ + η * Σ_{v in A} s_v * v
输出: φ, A
```

### 3. 真正不同的操作与最接近普通对手
最接近普通对手：**对同一 \(g_\phi\) 做普通残差梯度下降 / 普通 sign-SGD**，即  
\[
\phi\leftarrow\phi-\eta\nabla_\phi\sum_i \ell(y_i,f_\theta(s_i,d_i)).
\]
ESG 的不同操作是：**不直接用样本残差梯度，而用“已测边差残差”与“方向基上的边差敏感度”的符号一致性做二项门控，只更新通过门控的方向，且步长只取符号**。相同信息（同一 \(B\)、同一 \(f_\theta\)、同一方向基 \(V\)）、相同表示（同一 \(g_\phi\)）、相同目标（排序/功能响应）与相同预算下，普通残差梯度会把“状态主效应未校准造成的残差”混入药物效应更新；ESG 用同药或同状态的可观测边差消去可加状态项，并用二项检验控制“方向敏感度与边差残差同号”是否超过随机。因此不是把普通梯度换个名字，而是改变了更新所用的统计量与选择操作。

### 4. 最小证伪与失败即 STOP
最小证伪：在已认证的 leave-one-study-out 回放中，固定同一 \(f_\theta\)、同一 \(V_h\)、同一更新预算（同方向数/同样本数/同计算量），比较 ESG 与普通残差梯度及 sign-SGD 的留出 pairwise/Kendall 排序。  
- 若 ESG 相对普通对手的留出排序提升没有超过预注册最小效应，或提升只出现在同 study 内、排除同 study 后消失，则 STOP。  
- 若 \(A\) 中方向在留出 study 上的符号一致率不超过 0.5，或门控接受的方向数与随机门控无差异，则 STOP。  
- 若 ESG 仅靠更多更新步/更多方向/更多标签获胜，则 STOP。  
触发任一条件即 **NO_CANDIDATE**。

### 5. 何种证据让参数/程序继承有用
需要看到：在留出 study 上，ESG 产生的接受方向集合 \(A\) 与符号 \(s_v\) 在后续独立批次中仍能预测边差残差符号，且把 \(V_h\) 继承到新 study 时，冷启动前若干批的排序优于不继承 \(V_h\) 的同预算普通更新；同时该收益不能由“模型整体更好”解释，即固定 \(f_\theta\) 的普通对手在同预算下不获得同等收益。若只有整体 MSE 更好而无方向集合/符号的可迁移预测证据，则继承无额外价值。
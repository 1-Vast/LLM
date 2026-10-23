**结论先行**：按你给定的证据与约束，我目前**不认为有合格的新机制**。最接近可试且可立即证伪的候选是“**组内秩势反馈更新（Within-Group Rank-Potential, WGRP）**”。它只加一个运算：在固定基础分数上，用反馈学习一个低维、按化学分组归一化的组内秩势，再做收缩更新。它很可能被普通“把组内秩作为特征的logistic/rank calibration”表达；因此下面把它当作待证伪候选，不称为新核心，更不宣称已成功。

## 1 应用与边界
只用于HCT116已执行的600 paired条件与现有化学分组外折；基础分数固定为已公平比较的chem logistic或RBF rawchem，不新增6h/24h表示，不重做晚期规则，不扩24h。标签仍只是作者Efficacy注释；剂量、功能测定时点、阈值未知，不能称前瞻固定剂量功能预测。不读取/猜测A375或另外3背景。CDK12文化组成与S4IC50不混入本检验。缺失证据：E的蛋白值与mask未拆分、E逐折不稳定、组内秩可迁移性未验证。

## 2 唯一新增运算
输入：样本\(i\)的固定基础分数\(s_i\)、化学分组\(g_i\)、组内样本数\(n_g\)、反馈标签\(y_i\)。  
组内秩：
\[
r_i=\frac{\mathrm{rank}_{g_i}(s_i)-1}{\max(n_{g_i}-1,1)},\quad z_i=r_i-\tfrac12 .
\]
唯一更新：
\[
s'_i=s_i+\lambda\,h_\theta(z_i),\quad h_\theta(z)=a z+b z^3,\ \theta=(a,b).
\]
\(\lambda\in[0,\lambda_{\max}]\)为全局收缩。除该秩势项外不改变任何输入、模型或损失。

关键假设：AP增益主要来自同一化学分组内的阳性-阴性排序；组间排序由基础分数可靠提供；在34阳性下只学2维\(\theta\)与1维\(\lambda\)方差可接受。反馈更新用组内配对损失：
\[
L(\theta)=\sum_g\sum_{\substack{i,j\in g\\y_i=1,y_j=0}}
\log\!\left(1+\exp[-(s'_i-s'_j)/\tau]\right)+\eta(a^2+b^2).
\]
\(\lambda\)只由内层留一化学分组AP增量选择，不用外层折标签。

可执行伪代码：
```text
U_t=(θ_t,λ_t)  # 可继承更新规则，初始 θ=0, λ=0
for 外层化学分组折 k:
  D_tr = 已见组反馈; D_te = 留出组
  固定基础分数 s（同人口）
  在 D_tr 上按 L(θ) 求 θ_tilde
  内层留一已见组选 λ_tilde：
    λ_tilde = argmax_λ median_innerAP(λ,θ_tilde)
  Δ = median_innerAP(λ_tilde,θ_tilde) - median_innerAP(λ_t,θ_t)
  if Δ>δ and 内层至少4/5组同号:
      θ_{t+1}=θ_tilde
      λ_{t+1}=clip(λ_t + η*Δ, 0, λ_max)
  else:
      θ_{t+1}=θ_t; λ_{t+1}=λ_t   # 不继承无一致增益的更新
  对 D_te 输出 s'_i=s_i+λ_{t+1}h_{θ_{t+1}}(z_i)
```
可继承对象仅是\((\theta,\lambda)\)、秩定义\(z\)、\(\tau,\eta\)和“同号才继承”的更新规则；不是基础模型权重。

## 3 世界模型为何可能优于同信息直接预测
不要求绝对表达优势，只要求有限样本/计算优势：直接联合模型要在34阳性上同时拟合组间与组内排序；WGRP把可更新部分压到3个参数，降低方差。计算上只对固定分数重排，不重训大模型。外推上组内秩按\(n_g\)归一，可迁移到新化学分组。但这些只是假设，必须被普通替代击败才算数。

## 4 最强普通替代
在同一折、同一输入、同一正则下，训练：
\[
p_i=\sigma(\beta_0+\beta_1 s_i+\beta_2 z_i+\beta_3 z_i^3+\beta_4\log n_{g_i}),
\]
以及RBF核版本加入\(z_i\)；另跑全局isotonic/quantile rank calibration。若WGRP不能稳定超过“含\(z_i,z_i^3\)的logistic/RBF”，则它只是普通秩特征校准，判不合格。

## 5 两个最小反例/等价检查
**反例A（组间效应）**：合成\(y_i\sim\mathrm{Bern}(\sigma(\alpha s_i+\beta_{g_i}))\)，组内秩与\(y\)条件独立。预期WGRP无增益或负增益；若仍赢，查泄漏。  
**反例B（线性秩势可表）**：合成\(y_i=\mathbf{1}(s_i+c z_i+\epsilon_i>0)\)。预期含\(z_i\)的普通logistic恢复到与WGRP等价；若WGRP显著更优，查是否用了额外信息、非线性替代未覆盖或折间泄漏。  
预期区分：真实数据上WGRP相对“最强普通替代”的增益应显著小于其相对无更新\(G_0\)的增益；否则更可能是普通替代设定不公。

## 6 可继承对象与U/G分离
共同起点：\(G_0\)=固定chem logistic（或RBF rawchem），\(U_0\)=无更新。  
- \(U_{\rm new}\)=WGRP组内秩势规则；\(U_{\rm old}\)=全局isotonic/rank calibration。  
- \(G_{\rm new}\)=允许基础预测器用反馈做普通微调；\(G_{\rm old}\)=冻结基础预测器。  
必须做2×2：\(U_{\rm new}G_{\rm old}\)、\(U_{\rm new}G_{\rm new}\)、\(U_{\rm old}G_{\rm old}\)、\(U_{\rm old}G_{\rm new}\)，共同起点相同。保存\((\theta,\lambda)\)不自动叫RSI；只有当序列反馈中\(U_{\rm new}\)比\(U_{\rm old}\)更快或更稳地改进\(G\)，才称可继承更新规则。验证“改进策略本身是否更会改进”时，记录每轮\(\Delta AP\)，比较两规则对下一轮\(\Delta AP\)的符号/幅度预测，而不是保存参数本身。

## 7 一手来源
我没有检索工具，不能假装查证2025–2026一手来源。上述运算对应的近邻是learning-to-rank、isotonic/quantile calibration、conditional neural processes等普通方法；不给出未核验的准确标识。

## 8 成功与停止门
**成功门**：固定HCT116 5化学分组外折、同人口、同基础分数；WGRP相对“含\(z_i,z_i^3\)的最强普通替代”主AP中位增益\(\ge0.015\)，至少4/5折同号，bootstrap 95%CI>0；且第二轮反馈后\(U_{\rm new}\)对\(\Delta AP\)的同号预测优于\(U_{\rm old}\)。  
**停止门**：\(\le2/5\)折同号，或中位增益\(<0.01\)，或相对普通替代CI跨0；则永久停止WGRP，不重命名、不用E蛋白值/mask拆分或24h结果救场。未过门前不得称生物学性能或实验成功。
**候选（唯一 operation）：功能正交残差更新器 FORU**

1. \(r_i=g_\theta(s_i,x_i)\)，\(\theta\) 为 predictor 参数，episode 内冻结。  
2. \(f_i=f(s_i)\in\mathbb R^m,\ c_i=c(s_i)\in\mathbb R^p\) 为预先注册的固定功能读出与组成轴。  
3. \(e_i=y_i-r_i\)。  
4. \(\psi_H=\arg\min_\psi \sum_i e_i^2\|f_i-\psi c_i\|_2^2+\lambda_\psi\|\psi\|_F^2\)，\(\psi\) 为 editor 参数。  
5. \(\tilde f_i=f_i-\psi_H c_i\)。  
6. \(\phi_H=\arg\min_\phi \sum_i (e_i-\phi^\top(\tilde f_i\odot x_i))^2+\lambda_\phi\|\phi\|_2^2\)，\(\phi\) 为 updater 参数。  
7. \(\hat y_\star=g_\theta(s_\star,x_\star)+\phi_H^\top(\tilde f_{\psi_H}(s_\star)\odot x_\star)\)。  

**最接近常规方法**：带特征残差头的 ridge/WLS；若 \(\psi_H\) 固定，则严格等价于固定 feature 线性 function head 或普通 WLS。具体差异是反馈残差平方 \(e_i^2\) 只用于编辑“功能读出—组成轴”投影，再冻结 \(\theta\) 拟合 updater；普通 union refit 不会用历史反馈改变未来特征坐标。若允许普通两阶段加权回归并给同样 \(\tilde f\)，单任务内很可能可复制；因此可辩护贡献只能来自跨任务继承的 \(\phi_H\) 与独立 editor 检验，而不是残差头本身。

**最小数学失败见证**：令 \(m=p=1\)，\(f_i=c_i=x_i=1\)，历史反馈 \(e=1\)。则 \(\psi_H=1\)，\(\tilde f=0\)，\(\phi_H=0\)，FORU 不更新；普通 WLS 可拟合斜率 1。若真实未来响应由 \(f\) 驱动且 \(f\) 与组成不可分，FORU 必然失败。这给出可证伪条件，而非事后找阈值。

**合法真实功能实验**：用 BeatAML exposed RNA/AUC，但不用旧 lowrank 分支。预先固定 \(f\) 为外部注册的通路/基因集功能打分，\(c\) 为暴露 RNA 的固定组成主成分或管家轴；反馈为 AUC 残差。按药物分组留出未来药物任务，样本也分组以避免泄漏；同一基础强 direct predictor \(\theta_0\)、同一反馈预算和顺序 \(H\)，比较无更新、普通 union refit、持续学习、AL+refit、简单混合、等总成本程序搜索与 FORU。主要看留出药物 AUC 的 MSE/排序。若不存在可预先注册且不依赖 AUC 的 \(f,c\)，或药物分组不足，则现有数据无法测试该 law；不得重开 Norman73 残差身份循环。

**继承与 editor 独立检验**：固定同一 \(\theta_0\) 和同一 \(H\)，训练得 \(\phi_H,\psi_H\)。新 episode 时重置临时预测器为 \(\theta_0\) 并清空缓存，只保留 \(\phi_H\)（及可选 \(\psi_H\)），比较保留与重置 \(\phi_H\) 的未来任务表现；同 predictor、同 history 下差异即 updater 继承。再固定 \(\phi\) 的拟合算法与预算，只替换 editor：反馈加权 \(\psi_H\) 对固定投影/随机投影，比较其产生的 \(\phi_H\) 在新任务上的继承收益；若固定投影不差，则 editor 无独立贡献。  
**等价风险**：单任务、固定 \(\psi\)、或把 \(\tilde f\odot x\) 直接交给普通 WLS 时，本候选会被严格复制；只有“反馈驱动 editor + 跨任务可继承 updater”的联合检验能区分。
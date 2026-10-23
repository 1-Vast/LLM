(1) 操作（≤8行）

- 记方案 \(a=(seq,t_0,t_1)\)，历史 \(H_g=\{(a_i,y_i)\}_{i<g}\)。普通对手：全量重拟合 ridge/1NN/mean。
- 提出 **U：按“时长归一化剂量暴露”加权的局部重拟合**，权重
  \(w_i=\exp[-\lambda\,d(a,a_q)]\cdot \rho^{\,g-g_i}\)，\(d\) 用 seq 的 Jaccard + \(|t_1-t_0|\) 的归一化差；\(\lambda,\rho\) 由 G0 内留一方案确定，**不接触 query 标签**。
- 预测器 F 仍用同一 ridge/1NN 形式，仅样本权重变；即 \(F_w\)。
- 关键非平凡点：权重乘一个 **可加性残差校正** \(\hat y=\hat y_w+\beta\,(\bar y_{g}-\bar y_{g-1})\)，\(\beta\) 由 G0 内“伪新一代”交叉验证估，用于吸收批次/代际整体平移；这是普通 weighted refit 没有的项。
- U 的更新规则：每代只更新 \(\beta\) 与 \(\rho\)，\(\lambda\) 冻结；不重选 window/mixture。
- G 策略：以“跨代残差均值漂移是否显著偏离 0”作为是否启用 \(\beta\) 的开关（预注册阈值）。
- 明确：F=加权 ridge/1NN；U=权重+漂移项更新；G=开关规则。若 \(\beta\equiv0\) 则退化为常规 weighted refit，须诚实标注。

(2) 修什么、为何普通对手未必相同

- 可观测错误：FAC 累计重拟合改善但 OLA 变差，提示“更多历史≠更好”，可能是代际整体平移与方案覆盖变化耦合。普通 union/refit 会把旧代标签等权并入，无法区分“覆盖增加”与“整体平移”；普通 recency/shrinkage 只调遗忘速率，不显式估计可加漂移。\(\beta\) 项直接估计代际均值平移，理论上可在 OLA 型退化中抵消平移而不丢弃旧覆盖。但若退化主因是 coverage/covariate shift 而非可加平移，本方法无效——这是可证伪点。若仅 \(\rho\) 加权，则等价于常规 recency weighted refit，不算新机制。

(3) 最小数据/控制

- 需要：每代方案的 seq、原始 \(t_0,t_1\) 代码、CV endpoint、代编号；G0 内可做留一方案估 \(\lambda,\rho,\beta\)。
- 当前缺失：中途状态、独立 patientID、真实小时、cellcount；单 control 只能约束部分测量变换，不能当 ground truth。无同皿轨迹，故不能识别全潜状态，本方法也不要求。

(4) 可手算反例/可证伪实验

- 反例：两代各 2 方案，G0 标签 {1,1}，G1 标签 {10,10}，query 与 G1 同 seq。等权 refit 预测≈5.5；\(\beta\) 估得 +9 后预测≈10。若真实 query=5.5（漂移是覆盖假象），则 \(\beta\) 项被证伪。
- 实验：在 FAC/OLA 上预注册 \(\beta\) 开关，比较 \(F_w\) vs \(F_w+\beta\) vs 等权 refit/recency，同信息同预算。

(5) 继承测试

- U 共同起点：固定 G0 同一 scaler、同一 \(\lambda\) 初值，比较“继承 U”与“每代从 G0 重拟合”在同 query 上的 MAE/MSE。
- G 同 U 同历史等预算：比较“开关规则 G”与“固定启用/固定关闭 \(\beta\)”及等预算随机开关，看后代效用是否超等预算 search。当前无完整多代任务库，可先在 FAC gen2/3、OLA gen2 上做单步继承测试，不声称多代 RSI。

(6) 成功与停止

- 成功：在预注册 query 上，\(F_w+\beta\) 相对等权 refit 与 recency 的 MAE 降低且两独立审计通过；OLA 退化被逆转或至少不劣于冻结 mean；继承 U 优于重拟合。
- 停止：若 \(\beta\) 开关在 G0 伪代 CV 中不显著、或 OLA 上 \(\beta\) 估计与真实平移符号不符、或收益可由普通 weighted refit 完全解释，则停止并标注为常规方法。
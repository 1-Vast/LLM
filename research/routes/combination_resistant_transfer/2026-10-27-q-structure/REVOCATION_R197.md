# R197 协议作废与重跑要求（REVOCATION，2026-10-27）

依据：独立挑战 [challenge_R197.md](challenge_R197.md)（task-30，i003-challenger）判决 **revise（≤5 必改）**；Lead 认可。**生效：PROTOCOL_R197 v1 下已产生或将要产生的任何 `r197.json`/verdict 均作废，不得解释/采纳；需 AMENDMENT-002 重跑并通过独立挑战（task-34）后才可解释。** `r197.py`/PROTOCOL 保留为已执行记录；本轮 runner 若在收到本通知前已出结果，需按 AMENDMENT 重跑。

## 1. 撤回理由（挑战核心）

1. **主问题 vs 主模型错位（FAIL）**：AMENDMENT-R197-001 因 B2（Q 低秩）在 H197a/b（整 cell-pair / condition-pair 留出）不可辨识，把主对比改成 **B3−B0**；但 B3 是 tissue/单药/通路交互的**特征回归**（`r197.py` 相关段），不含任何从 Q 矩阵学的低秩因子。B2 只在 H197c（随机条目，次设计）可辨识。→ "present" 只能支持"**预购元数据+单药特征在冷细胞对可预测 Q**"，**不能**支持 BRIEF 的"Q 低秩/背景依赖结构可复用"；"absent" 也不能关闭低秩结构研究。
2. **特征-端点构造重叠 + B0 冷细胞基线弱（FAIL）**：B1/B3 的 `LIBRARY_EMAX/AUC` 单药特征是 `SYNERGY_DELTA_EMAX`（观测−期望 Emax）期望项的输入 → 增益可来自**机械重构**而非结构；H197a 测试 cell-pair 在训练中无观测 ⇒ B0 列效应=0、B0≈μ+行均值，而 B3 带 tissue/单药细胞信息 → Δ=B3−B0 混淆"细胞级信息"与"结构增量"；present 只做 B3≥B1/B4 点比较，不要求 Δ vs B1 的 CI>0。
3. **δ_min=0.05 operational 理由不成立（WEAK）**：理由（噪声 0.109、秩方差<0.3%、低于此无决策价值）只是"很小"的改写；"与 A1 δ_min_latent=0.10 观测层折半一致"隐含 rel=0.25，而 Q2 可靠性 0.868（本身未认证）；按 0.868 折半应 ≈0.093。需可审计定义（决策/效用或按 A0 R_split reliability 的 latent→observed 换算并冻结）。
4. **A0 依赖感知范围过宽（WEAK）**：只到 cell/condition 节点级，不保留键/barcode 级复用；graph-aware 置换交换性未论证；R_split 0.50 沿用 q2 未认证口径且只测条件主效应。
5. **措辞/谱系/预算/确定性（WEAK）**：`no_stable_increment` 的"停止该资源条件规律研究"过宽、present 名称需限定、A0 与 B 判定无耦合；需补"不是新算子"、≤20 min 预算/缓存/降级与墙钟、输入 SHA、type-I 20 次精度的处理写死。

## 2. 判定登记

- **R197 v1：`inconclusive/design_invalid（主问题未被可辨识地检验）`**；不得写"Q 无可复用结构/条件规律不存在/反馈无用"；也不得写"条件结构可预测"。
- 低秩结构问题保持**未检验**；`no_stable_increment` 只能表示"该主设计下无增量"，且必须在 v2 中重新定义其停止范围。
- 与 C174 的更正一致：1.43% 仅加性主效应份额；不得据此关闭低秩研究。

## 3. 重跑要求（AMENDMENT-002，二选一，必须预注册）

- **方案 P（改命题，推荐若无法辨识 B2）**：主命题改为"**预购细胞/药物特征对冷细胞对 Q 的增量**"；verdict 改名（如 `feature_increment_present/absent`），明确不检验低秩结构；必须做**特征块消融**（B0→+metadata→+mono→+interaction）并报 Δ(B3−B1) 的 CI 下界>0；披露特征-端点构造重叠；禁止把 mono 可解释增量写成"条件结构"。
- **方案 Q（保留 BRIEF 问题）**：预注册 **B2 可辨识**的主设计（H197c 随机条目为主，或用 side-information 的 cell embedding 使整行预测可识别）；必须在设计体检中证明可辨识性、零分布/type-I/MDE 先于判定；不得把 B3 冒充低秩。
- 共同要求：δ_min operational 化（决策/效用定义或 reliability-adjusted 并冻结，不得用 0.868 或旧 CI 倒推）；A0 依赖降级为节点级 + 键/barcode 敏感性 + 置换交换性限制 + R_split 覆盖/阈值声明 + A0→B 解释继承规则；措辞模板（不写可迁移/反馈有用/机制/新算法；阴性≠结构不存在；停止范围限定）；"不是新算子"谱系声明；≤20 min 预算/缓存/实际墙钟；输入/脚本 SHA；type-I 模拟次数与精度处理写死；设计体检先于最终打分；两次逐字节相同。

重跑产物：`AMENDMENT_R197.md`、`r197_v2.py/json/rows.csv`、`report_r197_v2.md`、`record_r197_v2.md`、`usage_r197_v2.json`；跑完需 task-34 挑战通过后才可解释。原始 PROTOCOL_R197.md/r197.py（及任何 v1 产物）保留。

## 4. 影响

- 仅针对 R197 v1 的可解释性；不改变 R194-A2 原始测量、不改变 A1/A3 结论、不启动反馈/Agent/acquisition。
- R196 撤回（C176）与 R197 作废（C177）共同表明：本项目对"唯一正结果/条件结构"的审计级确认仍未完成，必须先把推断单位与可辨识性对齐。

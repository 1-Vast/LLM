# report_M2 —— R204-M2-P1 预注册设计报告（任务驱动主动辨识群体功能算子；不运行效果）

2026-10-28。对象：R204-M2（D1/M2 首选主线）。依据：`2026-10-28-deep-coupling-redesign/`（report/BRIEF/evidence_notes）、R203-P1 链、ERRATA C197/C199/C201/C203、N1 v0.4（仅作受控测试床参考）。
**状态：预注册设计草案；未运行效果比较、未声称增益；机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；0 wells（合成 compute-only）。**

## 0. 交付物

- 问题定义：[PROBLEM_M2.md](PROBLEM_M2.md)（`4AF84EE0…`）
- 执行设计：[DESIGN_M2.md](DESIGN_M2.md)（`DAFdcbb3…`）
- 形式化/算术：[formalism_M2.py](formalism_M2.py)（`54B227E9…`）→ [formalism_M2.json](formalism_M2.json)（`107DB450…`）
- pilot 计时：[timing_M2_pilot.json](timing_M2_pilot.json)（telemetry；末次 `79AB9FC9…`）
- 记录/用量：[record_M2.md](record_M2.md)、[usage_M2.json](usage_M2.json)

## 1. 形式化（冻结）

- X=培养物状态（含历史与绝对数量）；φ 为可观测小函数族（p 固定、基固定）；**闭合声明** `E[φ(X_Δ)|X_0=x,a]=K_a φ(x)` 为待检验假设，不是恒等式。
- 固定随机分配 π 的群体矩 `V_i=Σ_a π_i(a)K_a U_i`；**按已记录状态分配的正确估计** `V_i=Σ_a K_a E[1{A=a}φ(X_0)|i]`；**禁止**边际 π×均值捷径（设计算术 bias 范数 **0.2651**，非零）；动作标签完整使用；π 是 cohort 间分配、非细胞自由给药、非联用。
- 任务驱动闭环：从独立功能 f_g 拟合合法动作条件后继 → 依功能目标选起始条件/给药/时点 → 真实新矩检验闭合 → 闭合：K 乘积/已测功能重组；失败：报告哪一作用/时程不可复用。**函数选择/增补/有限样本误差控制仍为开放算法问题，不声称已解决。**

## 2. 可辨识性/非闭合（设计算术，非真实证据）

| 检查 | 结果 |
|---|---|
| 同 U、pure+mix 分配 | assignment design rank **3/3**（A=3）→ `K_a U` 全部可辨识；仅 mixture 时只有组合可辨识 |
| full K_a（每动作纯分配 + U 张成） | design rank **48/48**（A=3,p=4）→ full K 可辨识；条件=每动作 ≥p 组纯分配且 rank(U_a)=p |
| mixed assignments only（U 变化） | rank **40/48**，nullity 8 → 仅部分方向可辨识；不识别所有 K |
| 无支持动作 | positivity 违反 → K_a 不可辨识 |
| gauge | φ 基变换 `K_a→M K_a M^{-1}`、基/符号对称（非可辨识内容） |
| 闭合正例 | φ=(1,x)、x'=0.7x+0.2+ε → 闭合残差 **2.7e-15**（闭合） |
| 非闭合反例 | φ=(1,x,x²)、x'=x+0.7+0.8x²+ε → `E[x'²]` 含 x³/x⁴，闭合残差 **3.7577**（不闭合） |
| 正交设计示例 | 同 U：pure (1,0)/(0,1) 分离 K_a U；.5/.5 只给平均；不同 mix 可分离二者但**不能识别所有 K、不保证混合优于纯药** |

## 3. 与 KoopCell/DisKO/受控 EDMD 的边界（写死）

- **固定 φ 线性闭合由受控弱 EDMD/系统辨识+最优输入设计直接覆盖，必须作等价强基线**；同预算复制/超过 → **撤主算法主张**（`no_increment`/`rename_edmd`）。
- KoopCell/DisKO（未配对群体学习）、TD-JEPA/后继特征（转移/目标复用）、BATCHIE（模型后验+反馈+批量选择）**已覆盖部分，不声称新**。
- **拟研究交叉点仅是**：破坏性群体测量下由功能任务主动选择实际干预辨识可复用作用；若等预算无独立功能决策增量 → 撤主创新主张。
- 生物兼容：起终姐妹制备可交换；不伪配同细胞轨迹；计数保留；策略反馈需策略加权闭合；新药无输入特征/反馈无自动迁移保证。

## 4. 受控测试床与三阶段最小验证（预注册，不运行）

- **Stage 1 合成真值**：隐藏状态 d=4、A=3、φ 维 p=5、cohorts=200、timepoints=3；三例（线性闭合 positive control、非线性非闭合 negative control、部分支持不可辨识 negative control）；检查可辨识性/闭合/随机化可交换性；**只报检查结论，不报增益**。pilot 设计算术 **0.00303 s/rep**（stage1 投影 0.1 s）。
- **Stage 2**：合格多时间功能数据（同培养物/背景/批次可交换；剂量/时间/function readout；记录 π/动作；独立培养/板重复；计数保留）上**相同固定反馈**比较学习：候选 vs full-history retrain/hierarchical GP/KoopCell/DisKO 适配/TD-JEPA 后继特征适配/state-space PKPD；同信息/同预算/同调参；先留出程序再背景；新功能所有方法同标定。
- **Stage 3**：固定更新器比较取证：候选主动干预选择 vs random/GP/最优输入设计/BATCHIE 适配；最后完整闭环（计培养物/板/对照/失败/重复/标定/计算/调参）。
- **数据现状**：真实多时间功能/数据字典/正交功能数值**当前未取得**（C203）→ 真实阶段 `data_unavailable`，不得以合成/RNA 替代；也不得由导出缺失推断"只能新湿实验"。

## 5. 主端点/δ/功效/停止

- **Primary**：独立功能下的实际决策效用/后悔（per endpoint 分别规划）；δ=**0.05 normalized**；先检 `headroom=U_max−U0`（<δ→`unreachable_gate`；近满分→另立 budget-to-target，不换端点）。
- **功效**：配对独立单位；`MDE80=2.801585·SD/√n_ind`、`n_req=ceil((2.801585·SD/δ)²)`；cluster 按独立培养/背景/任务；**6,282 仅 Fisher-z 参考、非通用门**；RNA/预测校准/算子误差为 secondary，**不能替代**主端点。
- **等预算强基线**：受控弱 EDMD/工具变量系统辨识+最优输入设计（等价强基线）、KoopCell/DisKO 适配、TD-JEPA/后继特征适配、state-space/PKPD、hierarchical GP、full-history retrain。
- **停止/撤主张**：标准方法同预算复制/超过 → 撤主算法主张；闭合/随机化/测量合同失败 → stop；仅 RNA 收益无独立功能决策 → 撤主创新主张；成本超冻结上限 → stop；CI 无法排除无收益 → inconclusive；跨任务失败 → 限当前任务。
- **失败类别**：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`；`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 6. 预算/边界

- 合成阶段 compute-only、**0 wells**；Stage1 caps wall≤600 s/CPU≤2 h/内存≤8 GB；Stage2/3 计划 ≤1800 s；真实阶段另列资源/预算。
- 机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；**效果执行须另立独立挑战+Lead 批准**；本报告未运行效果、未声称增益。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2.md` | `4AF84EE09E2155F2E3801B32DADD02015501CABD3B26BD6A191284CBE98DEAAA` |
| `DESIGN_M2.md` | `DAFDCBB3E852659487E4B6BD6177D0061934EE58E6479277BD87E1236A3E12BD` |
| `formalism_M2.py` | `54B227E9CDAA2660A6B42AA02825BB7264F385E595D1E76123CE22647BF34C65` |
| `formalism_M2.json` | `107DB450BD90537B627C116851AC80050B8ABC31B3AE6D3B3F204ACB7072E92C` |
| `timing_M2_pilot.json` | telemetry（末次 `79AB9FC9…`） |
| report/record/usage | 见 `usage_M2.json` |

**确定性**：`formalism_M2.json` 两跑逐字节一致（`107DB450…`；wall 0.1 s）；JSON 键排序/无时间戳；计时只在 timing 文件。

## 8. 建议

1. **提交 M2 预注册设计做独立挑战**（重点：形式化/记录态估计/bias 禁止捷径；可辨识条件与 mixed 40/48 不识别全部 K；非闭合反例；与受控 EDMD 的等价基线边界；三阶段/固定反馈/固定更新器；primary/δ/headroom/MDE；数据需求/失败类别/预算/边界）。
2. 挑战通过后由 Lead 决定是否批准 **Stage 1 合成实现**（仅合成机制账、compute-only、0 wells；不批效果/真实决策/药理）；真实阶段需先取得合格多时间功能数据（当前 data_unavailable）。
3. **不做**：效果比较/增益声称、代码晋升、旧判定修改、恢复停止实验。

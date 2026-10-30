# record_M2.md —— R204-M2-P1 预注册设计记录（形式化/算术/计时；不运行效果）

角色：独立设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-143（R204-M2-P1）· 日期 2026-10-28
只写 `research/2026-10-28-m2-operator-prereg/` 与 `tmp/`；**未改 R204/N1/A/B/D 产物**；**未运行效果比较/未声称增益**；机制账 only；0 wells（合成 compute-only）。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 形式化（X/φ/闭合/群体矩/记录态估计/π 语义/动作标签/π 非联用） | ✅ PROBLEM §1：`V_i=Σπ_i(a)K_aU_i`；记录态 `V_i=Σ K_aE[1{A=a}φ(X0)\|i]`；禁止边际捷径（设计算术 bias 0.2651 非零）；π=cohort 间分配、非细胞自由给药/非联用；动作标签完整 |
| ② 任务驱动主动辨识（功能目标选起始/给药/时点；新矩检验闭合；闭合→K 乘积/功能重组；失败→报不可复用作用/时程；函数选择/增补/误差控制仍开放） | ✅ PROBLEM §2/DESIGN：闭环写死；明确函数选择/增补/有限样本误差控制**仍是待发展算法问题**，不声称已解决 |
| ③ KoopCell/DisKO/受控 EDMD 边界（固定 φ 线性闭合=等价强基线；同预算复制→撤主主张） | ✅ PROBLEM §3：固定 φ 线性闭合=受控 EDMD/系统辨识+最优输入设计直接覆盖；KoopCell/DisKO/TD-JEPA/BATCHIE 已覆盖部分不可声称新；交叉点仅为破坏性群体测量下任务驱动主动干预辨识 |
| ④ 受控真值测试床（隐藏状态/转移/非线性/非闭合反例；已知 K_a；可辨识性/非闭合/随机化可交换性；正交设计示例；不识别所有 K/不保证混合优于纯药） | ✅ PROBLEM §4/DESIGN §1：d=4/A=3/p=5/cohorts=200/t=3；三例；可辨识 rank 3/3、48/48、mixed 40/48；闭合 2.7e-15 vs 非闭合 3.7577；正交设计示例写死限制 |
| ⑤ 三阶段最小验证（受控真值→多时间功能固定反馈比较学习→固定更新器比较取证→完整闭环；先留出程序再背景；新功能同标定） | ✅ DESIGN §2/§3：三阶段+完整闭环；先程序后背景；新功能所有方法同标定；只换已观测权重=有限任务重组，不是零样本迁移 |
| ⑥ 主端点/δ/功效（独立功能决策效用/后悔；按端点规划；不用 6,282 通用门；先查天花板；δ/CI 写死；次端点=预测校准/算子误差/RNA 误差） | ✅ PROBLEM §6：primary=独立功能决策效用/后悔；δ=.05 normalized；headroom 先检；配对公式；6,282 仅 Fisher-z 参考；RNA/预测/算子误差为 secondary 不可替代 |
| ⑦ 等预算强基线/停止（EDMD+最优输入设计、KoopCell/DisKO、TD-JEPA、PKPD、层级 GP、全重训；同预算复制→撤） | ✅ PROBLEM §7/DESIGN §4：基线清单；同信息/同预算/同调参；标准方法复制→`no_increment`/`rename_edmd`；闭合/随机化/测量/仅 RNA 收益→撤/停 |
| ⑧ 失败类别/预算/数据需求/边界 | ✅ PROBLEM §8：失败类别完整；合成 compute-only 0 wells、Stage1 caps 600 s/2 h/8 GB；真实阶段数据需求列明且当前 `data_unavailable`；不称生物学/机制/迁移/决策收益/新颖性；不晋升代码/不改旧判定/不恢复停止实验 |
| 输出 report/record/usage+计时；标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~11:28 | 读 task-143 并 claim；读 R204 report/BRIEF/evidence、ERRATA、R203 链、N1 v0.4、AZ x2/x3 |
| ~11:31 | 写 `formalism_M2.py`（形式化、可辨识/Kronecker 设计、记录态估计 bias、闭合反例、随机化合同、测试床+pilot 计时、端点/基线/停止树） |
| ~11:33 | 修两处 Kronecker 行切片 bug（full-K 与 pilot）、Gp 8→24；重跑成功：same-U rank 3/3、fullK 48/48、mixed 40/48、bias .2651、closed 2.7e-15、nonclosed 3.7577、pilot 0.00303 s/rep |
| ~11:35 | 写 PROBLEM/DESIGN；`formalism_M2.json` 两跑逐字节一致（`107DB450…`） |
| ~11:39 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **只做设计/算术/计时**：formalism_M2.py 仅形式化常量、可辨识性 design rank 算术、记录态估计偏差 MC、闭合/非闭合反例解析算术、随机化合同、测试床规格、pilot 设计算术计时（构建矩设计并解小回归仅用于计时）；**不运行方法比较、不计算功能决策端点、不声称增益**。
2. **可辨识性结果**（设计算术，非真实证据）：same-U pure+mix rank 3/3 → `K_a U` 可辨识；full K 需每动作 ≥p 纯分配且 U 张成（例 rank 48/48）；mixed assignments rank 40/48（nullity 8，仅部分方向）；无支持动作不可辨识。
3. **记录态估计**：naive `π·Eφ` 偏差范数 0.2651（非零），确认必须用 `Σ K_a E[1{A=a}φ(X0)|i]`。
4. **闭合反例**：φ=(1,x) 线性系统闭合残差 2.7e-15；φ=(1,x,x²) 含 x³/x⁴ 项的非线性系统残差 3.7577（不闭合）；合成算术，不外推真实生物。
5. **与冻结实验关系**：N1 v0.4 仅作受控测试床参考，不并入 M2 主张；R204/N1/A/B/D 未改；AZ 数据字典/功能数值当前未取得 → 真实阶段 `data_unavailable`，不得以导出缺失推断"只能新湿实验"。
6. **确定性**：`formalism_M2.json` 两跑逐字节一致；JSON 键排序/无时间戳；pilot 计时只在 `timing_M2_pilot.json`。

## 3. 关键结果

- 形式化/估计式/π 语义/动作标签已冻结；任务驱动闭环与开放算法问题明确。
- 可辨识：same-U 3/3；full-K 48/48（条件）；mixed 40/48；无支持动作不可辨识；gauge `M K_a M^{-1}`。
- 估计偏差：naive 0.2651；闭合：2.7e-15；非闭合：3.7577。
- 基线：受控弱 EDMD+最优输入设计（等价强基线）、KoopCell/DisKO、TD-JEPA/后继特征、PKPD、层级 GP、全重训；同预算复制→撤主算法主张。
- 端点：独立功能决策效用/后悔；δ=.05；headroom/MDE 先检；6,282 仅 Fisher-z。
- 预算：合成 compute-only 0 wells；Stage1 600 s/2 h/8 GB；pilot 0.00303 s/rep（stage1 0.1 s/2 0.4 s/3 1.5 s）。
- 失败类别：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2.md` | `4AF84EE09E2155F2E3801B32DADD02015501CABD3B26BD6A191284CBE98DEAAA` |
| `DESIGN_M2.md` | `DAFDCBB3E852659487E4B6BD6177D0061934EE58E6479277BD87E1236A3E12BD` |
| `formalism_M2.py` | `54B227E9CDAA2660A6B42AA02825BB7264F385E595D1E76123CE22647BF34C65` |
| `formalism_M2.json` | `107DB450BD90537B627C116851AC80050B8ABC31B3AE6D3B3F204ACB7072E92C` |
| `timing_M2_pilot.json` | telemetry（末次 `79AB9FC9…`） |
| report/record/usage | 见 `usage_M2.json` |

## 5. 缺口与下一步

- **未运行任何效果比较/未声称增益**；所有数字为设计算术/合成计时。
- 执行前需：独立挑战 + Lead 批准；Stage 1 合成实现（仅机制账、compute-only、0 wells）；真实阶段需先取得合格多时间功能资源（当前 data_unavailable）。
- 机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；不恢复停止实验。

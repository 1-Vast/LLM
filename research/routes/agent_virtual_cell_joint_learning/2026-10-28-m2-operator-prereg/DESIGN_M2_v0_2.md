# DESIGN_M2_v0_2 —— R204-M2.1 执行设计（p=5 冻结；预注册草案；不运行效果）

2026-10-28。修正 v0.1（[DESIGN_M2.md](DESIGN_M2.md) `DAFDCBB3…`，保留不改）。依据：M2-C1 挑战（p=5 vs p=4 冲突）、[PROBLEM_M2_v0_2.md](PROBLEM_M2_v0_2.md)、`formalism_M2_v0_2.json`、`stage1_schema_v0_2.json`、`timing_M2_pilot_v0_2.json`、R204 BRIEF/report、R203-P1 链。
**状态：预注册设计草案 v0.2；未运行效果比较/未声称增益；机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；0 wells（合成 compute-only）。Stage 1 执行须另立挑战+Lead 批准。**

## 0. M2-C1 落实

| 必改 | v0.2 落实 |
|---|---|
| ① 冻结唯一 p | **p=5**（与 testbed 一致；理由见 PROBLEM §0）；全文无 p=4 数字残留 |
| ② 重算算术/代码/JSON/schema | `formalism_M2_v0_2.py`：**full K 参数 75/75 可辨识**（30 pure 组、10/动作、U 张成 R^5）；**mixed rank 75/nullity 0**（构造性满秩；条件性，不声称任意混合识别全部 K）；**same-U rank 3/3**；**U 长度 5**；无支持动作不可辨识；gauge 不变；`stage1_schema_v0_2.json` 写死 p/A/full K rank/mixed rank/nullity/param dim/U 长度/pure groups |
| ③ 文档/SHA/pilot | PROBLEM/DESIGN/report/record 更新数字/SHA；Stage1 pilot 用最终 v0.2 代码重跑（**0.00228 s/rep**；stage1 0.1 s、stage2 0.3 s、stage3 1.1 s）；两跑逐字节一致；JSON 无 telemetry |
| ④ 其余不变 | 形式化/记录态估计/EDMD 等价边界/三阶段/主端点/δ/headroom/MDE/6,282 边界/等预算基线/停止/数据/失败类别/边界保持 |

## 1. Stage 1：受控真值测试床（p=5）

- **系统**：隐藏状态 d=4（含历史）；A=3；**φ 维 p=5**；cohorts=200；timepoints=3；三例：
  ① 线性闭合（positive control，已知 K_a）；② 非线性非闭合（negative control，闭合必须失败；设计算术残差 **3.7577**）；③ 部分支持/不可辨识（negative control：某动作无支持 → K_a 不可辨识）。
- **可辨识检查**：same-U pure+mix → assignment design rank **3/3**（K_aU 可辨识）；full K 参数 **A·p²=75**，需每动作 ≥p=5 纯分配且 U_i 张成 R^5（30 pure 组）→ **rank 75/75**；mixed assignments（20 组、U 变化）→ **rank 75/nullity 0**（构造性；条件依赖设计支撑，不推广）；gauge `M K_a M^{-1}`；无支持动作不可辨识。
- **闭合检验**：真实新矩拟合 K_a 并算闭合残差/不确定性（bootstrap/CI，阈值预注册）；失败→`design_invalid: closure`；**只报检查结论、不报增益**。
- **随机化/可交换性**：π 先于结果、支持/平衡表、记录态估计式；失败→`design_invalid: randomization`。
- **正交设计示例**（仅算术）：同 U pure vs soft mixes 分离 K_aU；不识别所有 K、不保证混合优于纯药组。
- **预算**：合成 compute-only、0 wells；caps **600 s/2 h/8 GB**；pilot 0.00228 s/rep（stage1 投影 0.1 s）。

## 2. Stage 2/3（不运行；Stage 1 通过后另立预注册）

- **Stage 2**：合格多时间功能数据（同培养物/背景/批次可交换；剂量/时间/function readout；记录 π/动作；独立培养/板重复；计数保留）；**相同固定反馈**比较候选 vs full-history retrain / hierarchical GP / KoopCell-DisKO 适配 / TD-JEPA 后继特征适配 / state-space PKPD；同信息/预算/调参；先留出程序再背景；新功能所有方法同标定；只换已观测权重=有限任务重组。
- **Stage 3**：固定更新器比较取证：候选主动干预选择 vs random/GP/最优输入设计/BATCHIE 适配；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参。
- 数据现状：真实多时间功能/数据字典/正交功能数值未取得（C203）→ `data_unavailable`；不得以合成/RNA 替代。

## 3. 端点/功效/停止（不变）

- Primary=独立功能决策效用/后悔；δ=**.05 normalized**；headroom=U_max−U0 先检（<δ→unreachable_gate；近满分→另立 budget-to-target）；配对 MDE80=2.801585·SD/√n_eff；cluster 按培养物/背景/任务；**6,282 仅 Fisher-z、非通用门**；RNA/预测/算子误差仅 secondary。
- 等预算基线：受控弱 EDMD/工具变量系统辨识+最优输入设计（等价强基线）、KoopCell/DisKO、TD-JEPA/后继特征、state-space/PKPD、hierarchical GP、full-history retrain；同信息/预算/调参。
- 停止/失败：标准方法复制→撤主算法；闭合/随机化/测量失败→stop；仅 RNA 收益→撤主创新；成本超限→stop；CI 无法排除→inconclusive；失败类别见 PROBLEM §7；失败只写 `design_invalid`。

## 4. 预算/边界

合成 compute-only、0 wells；Stage1 caps 600 s/2 h/8 GB；Stage2/3 计划 ≤1800 s；真实阶段单列资源。机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**Stage 1 执行须另立挑战+Lead 批准**；不批 Stage 2/3 执行。

## 5. 批准清单

1. 唯一 **p=5** 与 testbed/算术/代码/JSON/schema 一致；full K **75/75**、mixed rank **75/nullity 0**（条件性）、same-U **3/3**、U 长度 5、pure groups 30、无支持动作不可辨识、gauge 不变。
2. 非闭合反例（2.7e-15/3.7577）保留；正交设计/随机化合同保留。
3. 形式化/记录态估计/EDMD 等价边界/三阶段/主端点/δ/headroom/MDE/6,282/等预算/停止/数据/失败类别/边界不变。
4. Stage1 只做受控真值/可辨识检查、不报增益；caps 600 s/2 h/8 GB/0 wells；两跑/schema/失败类别；Stage 1 后 Stage 2/3 另立预注册+独立挑战+Lead 批准。

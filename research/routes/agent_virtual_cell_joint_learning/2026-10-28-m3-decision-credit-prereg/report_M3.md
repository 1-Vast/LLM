# report_M3.md —— R204-M3-P1 决策反馈信用分数（DR/TMLE 支撑）预注册报告（**不运行效果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 `2026-10-28-deep-coupling-redesign/{report.md,BRIEF_R204.md}`、ERRATA C197/C199/C201/C207、R203 decision/power、M1 v0.2、M2 v0.2、N1 `report_n1_effect.md`。**状态：预注册完成；未运行效果比较、未拟合真实/响应数据、未声称增益；机制账 only、compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛。**

## 0. 判定（一屏）

- **M3 预注册草案完成；形式化/算术自洽检查全部 PASS（`all_checks_pass=true`）。**
- 冻结：一步 DR/重要性校正、`H=π/b`、`δ=E[H(Y−mθ)]`、策略值 `Eπm+δ`、score-tilt 更新 `logit m_{θ,ε}=logit m + ΣεH`、概率/权重截断、评价独立要求。
- **未证明新意**：这是标准 DR/重要性校正重述；**不据名称声称创新**；一步线性退化（π=b→H=1）为加权残差 → 保留等价、撤主创新。
- **M3 只作为支撑研究**：只更新功能均值 ≠ 细胞动力学兼容更新；不宣称序贯 DR/TMLE（无完整序贯历史/propensity/删失）。
- 三阶段/强基线/失败类别/停止/预算/数据需求已冻结；**未运行 Stage1/2/3 效果**；真实数据当前 `data_unavailable`（C203/C205）。

## 1. 一步形式化（冻结）

- `h` 已知背景/历史；`Y∈[0,1]` 独立功能读数；`b(a|h)` 已知随机分配概率；`π_k(a|h)` 冻结候选策略；`mθ(h,a)` 功能均值。
- `H_k(h,a)=π_k(a|h)/b(a|h)`；`δ_k=E_{h,a∼b}[H_k(Y−mθ)]`；`V_k=E_h[Σ_aπ_k mθ]+δ_k`。
- **DR 正确性条件**：b>0 覆盖 π 支持；**评价样本独立于 mθ 拟合与 π_k 选择**（否则 `leakage`）；mθ 可错仍有双稳健性（标准结果，不称新）。
- 更新：`logit m_{θ,ε}=logit mθ+Σ_k ε_k H_k`；在独立反馈上拟合 ε 使分数趋零；**预定截断**；共线/分离/无支持时不保证有限唯一解，只报告 `nonidentifiable`/`inconclusive`。
- **只更新功能均值头**；没有建立细胞状态/轨迹核兼容性，不能把功能头校准称为细胞规律改变。

## 2. 形式化算术结果（仅自洽检查；无效果）

| 检查 | 结果 |
|---|---|
| DR 恒等（m_true 与 m_wrong，两策略） | max abs gap **0.0 ≤1e-12**（PASS） |
| 零支持反例 | H 未定义、policy value 未识别；检出 `identified=false`（PASS） |
| 截断偏差 | cap=20 时 1 个权重被截断（max raw H=167），有界估计 bias **−0.026407185629**（检出；截断≠精确） |
| score-tilt 简单例 | ε root **−0.562633036711**；score at root **≈0≤1e-10**（PASS） |
| 共线 H | rank **1<2** → ε 非唯一（检出） |
| 分配二阶项 | π1：noise **0.6675**、full **0.8125**、bias² **0.145**；π2：0.24406/0.28479/0.04073；full≥noise（PASS） |
| 基线退化 | π=b→H=1，max abs(H−1)=0（加权残差退化；保留等价） |
| 规划算术（仅示例） | n_units=300、deff=2.2、n_eff=136.36、conservative SD=.20 → MDE80 **0.047982685≤.05**；n_req_cluster **278≤300**；6,282.10（δ=.05）/1,572.78（δ=.10）**仅 Fisher-z** |
| 形式化两跑 | `formalism_M3.json` 逐字节一致 SHA **`2256BDA2F2D9862C6F025557BA3FC6E850ED3D6EFD1C90E72244D7804F78AA48`** |
| pilot timing | 10 rep 算术平均 **0.000174 s/rep**、wall **0.00174 s**；caps 1800 s/2 h/8 GB PASS；0 wells |

> 以上仅为**形式化/算术自洽**；不比较方法、不报告效果/增益；截断/零支持/共线是有意构造的诊断反例。

## 3. 共享分数/实验分配（待验证）

- 同一组 H/δ 也用于设计下一批 b；冻结 m 时单个策略的二阶项：
  `Σ_h p(h)Σ_a π_k(a|h)^2[Var(Y|h,a)+(E[Y|h,a]−mθ)^2]/b(a|h)`。
- 错设时 `(E−mθ)^2` 非零且未知；**不能只按 Var 分配**；须用估计/保守上界，并在执行预注册中冻结 b_min/截断/最坏情况目标。
- 分配候选：shared-score vs random vs GP/uncertainty vs decision AL vs DR+MLE optimal；同更新器/同成本/同信息；未运行。
- **不声称分配优越性**：标准 DR 最优设计/批量 AL/GP 采集直接重叠。

## 4. 标准基线边界（同信息/同预算）

必须比较：普通全历史重训；重要性加权；DR/TMLE targeting；value-aware model learning；层级/GP；BATCHIE 适配；最优实验设计/决策 AL。共同合同：同特征/知识/反馈/调参≤20 configs/计算 caps 1800s/2h/8GB/初始数据/随机化记录；同 b 支持/成本/查询。
**一步线性退化**：π=b 或线性 m 时 score-tilt=加权残差 → 保留等价、撤主创新。
**序贯**：无完整序贯历史/propensity/删失，不称序贯 DR/TMLE。
**功能 vs 细胞**：功能均值更新≠细胞动力学兼容更新。

## 5. 三阶段最小验证（预注册；未运行）

1. **Stage 1 已知真值**：DR 恒等/双稳健、截断、零/低支持、错设、共线/分离、分配二阶项；只做检查性诊断，不报效果/增益。当前形式化算术已通过（非 Stage1 执行）。
2. **Stage 2 固定更新器比较分配**：shared-score/random/GP/决策 AL/DR+MLE；同反馈预算/特征/调参；只测分配；基线复制→`no_increment`；当前不运行。
3. **Stage 3 固定反馈比较学习 + 闭环**：candidate vs 全历史重训/IW/DR/TMLE；主端点=独立功能决策效用/后悔，δ=.05 normalized；headroom/MDE/cluster；6,282 仅 Fisher-z；次端点预测校准/DR 分数/RNA；最后计培养/板/对照/失败/重复/校准/计算/调参成本；当前不运行、真实数据 `data_unavailable`（C203/C205）。

## 6. 失败/停止/预算/数据

- **失败类别**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **停止**：标准 DR/TMLE+最优分配等预算复制/超过→撤主算法；极端权重/零支持→未识别；评价样本复用选策略→leakage；超 caps→stop；CI 不能排除无实用收益→inconclusive；功能头校准不得升级为细胞规律。
- **预算**：合成 compute-only 0 wells；caps **1800 s/2 h/8 GB**；本预注册不运行效果/湿实验。
- **数据需求**：独立功能读数（apoptosis/caspase/viability/regrowth 等）、随机化/倾向记录、独立培养/板/背景/任务、剂量/时间/readout、评价与策略选择分离、计数保留；当前 AZ 数据字典/功能 numeric 缺失（C203/C205）→ `data_unavailable`；不得用合成/RNA/预测替代独立功能决策。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `formalism_M3.py` | `F578180A10CDF8A055379BFC53FC9A1004C4D9F6118DD7EFEBEA82546E853EBC` |
| `formalism_M3.json` | `2256BDA2F2D9862C6F025557BA3FC6E850ED3D6EFD1C90E72244D7804F78AA48` |
| `timing_M3_pilot.json` | `3C133C69A71EBD33C720263617D38C0F7FC664A085AD6574129752C5674FAD47` |
| `schema_M3.json` | `10A8814B0867F778D313DAA8DCFB90FAE5C27E51A33C8B7D86A9BE9E9EB071A7` |
| `PROBLEM_M3.md` / `DESIGN_M3.md` / `report_M3.md` / `record_M3.md` / `usage_M3.json` | 见各文件/SHA 表 |

## 8. 建议（仅建议）

- 预注册形式化/基线边界/三阶段/失败/预算可提交**独立挑战**；通过后是否执行 Stage1 由 Lead 另行批准（须另立执行预注册）。
- **不建议**直接运行效果或把 M3 称为主创新；先由独立挑战检查 DR 强基线等价、支持/倾向/泄漏合同与数据门；当前无真实数据条件（`data_unavailable`）。
- N1 `no_increment` 仅其 own primary，**不作 M3 证据**；M2/M1 机制账不混同。

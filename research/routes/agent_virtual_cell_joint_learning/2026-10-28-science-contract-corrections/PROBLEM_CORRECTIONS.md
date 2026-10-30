# PROBLEM_CORRECTIONS：科学合同与实现纠正

2026-10-28。用户要求：先纠正科学合同与实现，不要继续围绕字段/SHA 反复审批。本目录为集中修正与关键数学核查（deterministic；不运行旧配置、不训练模型、不读真实数据）。

## 范围
1. **比较合同**：六个比较统一为 `D_j = R_candidate − R_baseline_j`（含 candidate vs standard）；统一 Holm；改善方向 D<0；单侧下尾检验。检查强改进/无改进/变差三种确定性算例，确认成功门可真正通过。
2. **headroom**：regret 下界为 0，故批次最大可能改善 = 基线 regret（不是 1−regret）。M3 Stage3 保存批次推断基线 regret 0.0203 < δ=0.05 → 该批次增益门不可达。
3. **概率权重**：按 `w` 采样就用实际行为概率 `H=π2/w`（若背景改变用联合密度比）；先通过有限环境 DR 恒等检查。
4. **learner 合同**：必须落实真实损失（NLL）、更新方程（logit fluctuation ε）、优化器（L-BFGS）与收敛条件（score 残差/grad）；任意线性 score 修正不等于预注册 logit targeting，sigmoid 变换不等于 TMLE。
5. **等价去重**：检查相同策略、单调重标、正仿射重参数化；若候选被标准方法解析覆盖，登记等价并停止相应增量主张，不靠重复运行制造差异。

## 产物
- `contract.py`：修正后的比较/headroom/DR/等价/learner 合同函数。
- `test_contract.py`：12 个确定性单测（全部通过）。
- `run_corrections.py` / `corrections_result.json`：保存数据的审计重算（不改冻结输出）。
- `NEXT_EXPERIMENT.md`：下一项有区分力实验与停止条件。
- 相关 errata：`2026-10-28-m3-stage3-run/ERRATA_M3_STAGE3.md`、`2026-10-28-m1-stage2-fail-diag/ERRATA_C217.md`。

## 边界
不重跑旧配置、不改冻结阈值/输出、不晋升代码；旧失败与原始 verdict 保留；本目录只是合同/数学核查，不是新科研效果。

# NEXT_EXPERIMENT：M3-S3b 修正后的固定反馈 learner 比较（尚未执行）

## 目的
在**高 regret 环境**与**真实 learner 合同**下，检验"candidate 的 logit-fluctuation 更新"是否相对**解析等价的 standard DR/TMLE 估计器**有可检出增益；若候选被标准方法覆盖，则登记等价并停止增量主张。

## 与已执行 Stage3 的区别（必须写清）
1. 比较族：`D_j=R_candidate−R_baseline_j` 六个，含 candidate vs standard；统一 Holm；D<0；单侧下尾。
2. headroom：执行前先算基线 regret；**要求 mean baseline regret ≥ 2δ = 0.10**（本批 0.0203 不满足，故不重跑旧配置）。
3. 概率：反馈按实际 `w` 采样，DR/IW 用 `w` 作分母；有限环境 DR 恒等残差 <1e-10 才可进入比较。
4. learner：candidate 拟合 logit fluctuation ε（真实 NLL、L-BFGS、score 残差 <1e-6）；standard 使用**同一 m 估计但无 ε 更新**的解析 DR/TMLE 形式；两者差异仅来自 learned fluctuation，不来自类名/缩放。
5. 等价去重：先做策略/单调/仿射等价审计；任何被解析覆盖的臂删除或并入 standard，不重复计数。
6. 分离：generator truth / training feedback / validation / final evaluator 隔离；raw R 与 paired D 分开保存；CI 按独立重复，不用规划 MDE。

## 预注册要点
- 环境：H=3/A=3/Y binary；π2 target；w 行为；μ 设计使 baseline regret≈0.14–0.20（>2δ）；R 独立重复 ≥20；cluster=replicate。
- 主端点：candidate vs standard（六比较族一员）；δ=.05；成功门 mean D≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05。
- 次端点：其余 5 个基线（去重后）；预测校准/score 残差仅 secondary。
- caps：1800s/2h/8GB/0 wells；两跑逐字节；失败类别含 precision_insufficient/equivalence/leakage/no_increment。
- 停止条件：① headroom<δ → 不运行；② 等价审计显示 candidate≡standard → 登记等价、停止增量主张；③ CI 无法排除 0 或无法排除 −δ → inconclusive；④ 标准方法等预算复制/超过 → no_increment/撤；⑤ 超 caps → compute_budget_exceeded；⑥ 任何失败不改变旧判定。

## 预期区分点
- 若 candidate 的真实 ε 更新能在同一 m/同一反馈上降低 regret 超过 standard，且 CI 排除 0 与 −δ → 有区分力证据（仍仅合成机制账）。
- 若等价 → 明确"该设计下无可继承增量"，避免继续以字段/运行次数充研究进展。

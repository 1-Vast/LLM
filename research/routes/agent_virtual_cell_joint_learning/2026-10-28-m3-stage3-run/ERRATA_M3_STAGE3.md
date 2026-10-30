# ERRATA：M3 Stage3 冻结输出保留；比较解释标为不成立（追加纠正）

2026-10-28。依据用户纠正说明与 `2026-10-28-science-contract-corrections/corrections_result.json` 的确定性重算。**原始 `m3_stage3.json`、verdict `no_increment`、per-arm 输出、SHA 全部保留、不修改。**

## 1. 主比较 Holm 映射错误
原实现先用每个 arm 的 `R_arm−R_standard` p 值做六基线 Holm，candidate 不在这张映射里；再对 candidate 取默认 1.0 → 主比较 p 恒为 1，成功门实现上不可满足。正确族应为六个 `D_j=R_candidate−R_baseline_j`（含 standard），统一 Holm。

## 2. 单侧检验方向错误
原 `one_sided_p` 用上尾 `0.5*erfc(t/√2)`；改善方向 D<0 应用下尾（t.cdf）。已用保存的逐重复 D 重算：六比较 mean D 为 +0.01/+0.01/0.00/0.00/+0.01/+0.01，单侧下尾 p≈0.828（0 差为 1.0），Holm 后仍 1.0；没有变成正面，但原检验映射必须纠正。该重算为审计，不冒充原冻结分析。

## 3. headroom 定义相反
原 `headroom=1−mean(R_standard)=0.9797`；regret 下界 0，故本批最大可能改善 = mean(R_standard)=0.0203（由保存值与源码反推；raw baseline R 未持久化）。本批即使 candidate 零 regret 也只能 mean D≥−0.0203，**不可能满足冻结 mean D≤−0.05** → 该批次增益门不可达；停止扩大此配置，不降 δ/不换 seed/不换环境救结果。

## 4. 实际采样概率 w，权重仍除旧 b
反馈实际按 `a~w(a|h)` 生成，learner 却用 `H=π2/b_old`。正确应为 `H=π2/w`（背景改变时用联合密度比）。有限环境恒等检查：目标值 0.455；用旧 b 的 DR=0.38436007（偏差 −0.07063993）；用实际 w 的 DR=0.455（恒等残差 0；`corrections_result.json` 中构造检查 gap 0.0）。注意这检查的是概率合同，不是 learner 的修复后效应。

## 5. learner 标签与预注册算子不一致；多个臂重复
实际 candidate=`0.5+0.5*score`，无 ε 拟合；标 TMLE 的 arm=`sigmoid(2*score)`，未解目标 score/NLL；standard/full-history 直接为经验均值；IW 在每格 H 固定时退化为同一均值；value-aware 为正仿射、argmax 相同；candidate 与 sigmoid arm 是同一 score 的单调变换。**这些不能包装成六种独立强算法验证**；正确做法是写清更新/损失/参数/停止条件、检查等价并去重。

## 6. SHA 含义收窄
policy SHA 仅 hash 固定名字，不能证明概率表/采样器相同；数据 SHA 不证明 propensity 正确或无泄漏。今后应 hash 实际概率表/支持合同与各 arm 实际消费输入/权重；按 replicate 保存流映射，不能把 replicate0 SHA 放在聚合记录后宣称全部核验。

## 处理决定
- 冻结输出保留；**"所宣称 M3/TMLE 合格算法比较"的解释标为不成立**；不新增算法失败/成功结论。
- 停止扩大该配置，先解决等价与目标合同，不自动重跑。
- 下一项实验见 `2026-10-28-science-contract-corrections/NEXT_EXPERIMENT.md`（M3-S3b，headroom≥2δ、真实 ε 拟合、去重、实际 w）。

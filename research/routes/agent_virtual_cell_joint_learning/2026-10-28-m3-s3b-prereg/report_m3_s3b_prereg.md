# report_m3_s3b_prereg —— R204-M3-S3b 修正合同高 regret 固定反馈 learner 比较预注册报告（先 headroom；不运行候选）

2026-10-28。对象：R204-M3-S3b 预注册。依据：M3 Stage3 `no_increment`（C218）+ C220/C221 合同纠正、NEXT_EXPERIMENT、M3 Stage1/C209、Stage2/C213、M3 v0.2、R204 BRIEF/report。
**状态：预注册草案；仅设计期 headroom（合成、机制账）；未训练/未运行候选、未报效果、未读真实数据；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_M3_S3B.md](PROBLEM_M3_S3B.md)（`869690F9…`）
- 执行设计：[DESIGN_M3_S3B.md](DESIGN_M3_S3B.md)（`79E1E109…`）
- headroom 设计：[headroom_design_m3_s3b.py](headroom_design_m3_s3b.py)（`68EF6698…`）→ [headroom_design_m3_s3b.json](headroom_design_m3_s3b.json)（`77F113FF…`）
- schema：[schema_m3_s3b.json](schema_m3_s3b.json)（`29747B9C…`）
- 记录/用量：[record_m3_s3b_prereg.md](record_m3_s3b_prereg.md)、[usage_m3_s3b_prereg.json](usage_m3_s3b_prereg.json)

## 1. 分离/纠正（写死）

- M3 Stage3 **`no_increment` 冻结保留**；C220 原“合格 M3/TMLE 比较”解释**不成立**；S3b 是**新预注册**，不是重跑旧 Stage3；旧判定/阈值/输出不改；一步投影仍撤（C208）。
- 仅合成机制账；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码。

## 2. 高 regret 环境/headroom（先于候选）

- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b 沿用 Stage2；m_wrong=.5；C_H=20；b_min=1e-6；**π2' 对角 .82、非对角 .09**；Q 公式；`w=Q/ΣQ`；反馈按实际 w；`H=π2'/w`；**H_max=18.9178<20，无 clipping**；support/positivity 检查通过。
- 设计期 headroom（R=20 seeds 20262201–20；300 feedback；300 eval；known truth）：

| baseline | mean | 95% CI(t₁₉) |
|---|---|---|
| P_empirical_mean | **.14841667** | **[.10382916,.19300417]** |
| P_standard_DR_TMLE（same m，analytic DR no ε） | **.14841667** | **[.10382916,.19300417]** |

- 均≥2δ=.10 → **executable**；**未重设环境**；headroom 设计期实测、不用候选结果反选；若未来<.10→重设/冻结或 unreachable_gate；不降 δ/不换 seed/环境。
- **DR 恒等**：m=μ、H=π2/w 时 correction expectation=0；**exact gap=0.0<1e-10**；H 用实际 w、不用旧 b；H_max<C_H 无 clipping。

## 3. Learner 合同

- **Candidate**：per-cell weighted Bernoulli NLL（offset logit(m_hat)、weights H=π2/w）拟合真实 logit-fluctuation ε；**L-BFGS**；score residual `<1e-6`；收敛；`m_ε=σ(logit m_hat+ε)`。
- **Standard**：same m、analytic DR/TMLE、**no ε**；`V_std=m_hat+H·mean(Y−m_hat)`。
- **禁止** `0.5+0.5*score`、`sigmoid(2*score)`、无 NLL/优化器的 sigmoid、用缩放/λ/类名制造差异；不得用旧 b 作 H 分母。
- 分离：truth/feedback/validation/final evaluator 隔离；raw R 与 paired D 分存。

## 4. 六比较/等价/统计

- Family=6 planned：primary candidate vs **P_standard_DR_TMLE**；secondary P_empirical_mean、P_importance_weighting、P_full_history_retrain、P_DR_targeting、P_value_aware。
- `D=regret_cand−regret_base<0`；δ=.05；**Holm family=6、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；CI R=20 cluster=replicate t(df=19)；不用 planning MDE 当功效；不换端点。
- **等价审计**：candidate vs 各 baseline 策略/单调/正仿射/解析覆盖→equivalence、合并等价类、停止增量；候选≡standard→no_increment；不得用实现差异制造独立成功；等价类预注册（full-history≡empirical、DR-targeting≡standard、value-aware 仿射）。

## 5. 执行/seeds/caps/schema/失败/停止

- seeds（20262200+）：env 20262200；headroom 20262201–20；feedback 20262221–40；evaluation 20262241–60；arms **20262261+20a+r**（a=0..6,r=0..19）；forbidden ranges 见 JSON；**overlap=[]、unique=true**。
- 两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独；caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **13 失败类别**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。
- **停止**：headroom<.10→重设/冻结或 unreachable_gate；等价→no_increment；DR gap≥1e-10→design_invalid: propensity/calibration；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务不训练/不运行候选。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3B.md` | `869690F912D92DDDBE8EB8372AA16E489F36610B9B7F8638AD40F4586AB8BF5E` |
| `DESIGN_M3_S3B.md` | `79E1E10971F09461E36531A3F46B8BAF88583B4C47448DB6C7B24CB13ACC0E9B` |
| `headroom_design_m3_s3b.py` | `68EF66988ABBC3E068C1BCCA230BB09C045FCE7019465F927468FA89436C829B` |
| `headroom_design_m3_s3b.json` | `77F113FF61649A5A5978B4EE3CA23673005CF9BDAA11E7B57D6AF6CCDE72DC12` |
| `schema_m3_s3b.json` | `29747B9C5E455B5E9738393938462B43FDD52289D82E5495DC1ED2501760D317` |
| report/record/usage | 见 `usage_m3_s3b_prereg.json` |

**确定性**：`headroom_design_m3_s3b.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈0.1 s 仅 usage/报告。

## 7. 建议

1. **建议提交独立挑战**：重点分离/纠正（Stage3 no_increment 保留、C220 解释不成立、S3b 非重跑）、高 regret 环境/headroom 值、DR identity gap 0.0/H=π2/w 无旧 b、learner 合同（真实 ε NLL/L-BFGS/score<1e-6；standard no ε；禁假变换）、六比较/Holm/δ/raw-paired/CI、等价审计、seeds/两跑/caps/schema/13 失败/停止。
2. 挑战通过 + Lead 批准后才可执行 **M3-S3b 候选 learner 比较**（执行时才训练/拟合；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练/运行候选/效果/代码晋升/旧判定修改；不把 Stage3 旧配置当 S3b；不把 no_increment 改写为通过。

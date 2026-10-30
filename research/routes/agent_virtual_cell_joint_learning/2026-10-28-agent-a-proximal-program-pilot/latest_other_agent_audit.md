# 最新另一 Agent 产物只读核对

审计快照：2026-10-28 15:23:30 +08:00。依据本 episode 的 `BRIEF.md`；只读指定研究产物，并用 maestro 环境重算保存 JSON/CSV 的计数、算术与 SHA。不重跑训练/模拟，不联网，不访问测试服务器，不读 sealed/凭据，不改对方文件。审计者 effective model / effort 均为 **unknown**，不声称 Terra 身份。

## 1. 实际文件状态先行

本次并非依据目录名判断成功或失败。完整文件名、字节数、mtime、SHA 见同目录 `latest_other_agent_audit_counts.json → inventory`。

| 实际目录 | 最终快照所见 | 状态 |
|---|---|---|
| `research/2026-10-28-m1-stage2-rerun/` | 9 文件：report、record、checks CSV、result JSON、diagnostics JSON、脚本、schema、timing、usage | 有保存的合成诊断结果；不是空目录或仅计划 |
| `research/2026-10-28-m1-stage2-fail-diag/` | 6 文件：PROTOCOL、脚本、JSON、report、record、usage | 有一次诊断设计及自报两跑的结果；审计开始只见前 3 件，15:20–15:21 又出现报告/记录/usage，因此采用最终快照 |
| `research/2026-10-28-m3-stage3-exec-prereg/` | 最终快照共 32 文件：已读 v0.1/v0.2 的 18 件，另在审计中新增 v0_3/v0_4 的 14 件 | **已审 v0_2 仅执行设计，没有 Stage3 学习效果结果**；其独立 challenge 为 revise；新增版本未审 |

审计过程中另见 v0_3/v0_4 文件。按父 Agent 的收口指令，不无限追踪后续版本；这些只纳入文件状态/哈希清单，未读取内容。以下 M3 判断**专指 v0_2**，不用于声称 v0_3/v0_4 仍有相同缺口，也不认证新版本状态。

关键实算 SHA：

| 文件 | SHA256 |
|---|---|
| M1 `m1_stage2_rerun.json` | `B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107` |
| diag `diag_m1_s2.py` | `DC9AD39CCC25C2EAD95F0F33A6178CD53E38AC62BB39A002C71936C49695EEF8` |
| diag `diag_m1_s2.json` | `6FBD101677728945F0721713391DEBA5F2747DC7F652F1EF4E0FAB0DBD2FBB54` |
| M3 `exec_plan_m3_s3_v0_2.json` | `7E51CBA589A0EFBCF6972763614C94F937EA55F1EDB22164E59EF3B6B2827D02` |

diag JSON 本身只绑定 C216 输入 SHA，未内嵌执行源码/协议 SHA。最终 `usage_diag_m1_s2.json → artifacts_sha256` 补记源码/协议/结果/报告 SHA，四项与当前实算全匹配。当前可见 mtime：源码 15:16:05、JSON 15:20:00、usage 15:21:03，**本快照没有源码晚于 JSON 的现象**；mtime 与事后 usage 仍不能独立证明实际执行版本。两跑一致由 usage 记录，本审计没有另行运行诊断，不能称为独立复现。

## 2. M1 重跑：可以采用的结果与范围

只读重算确认：H1 **0/16**，JSON pass 标记和 CSV 数值一致；H2 **5/5 收敛**，保存的最大边缘误差 `9.9e-9 ≤ 1e-8`；H3 `0.0134035243 ≤ .05`。结果判定保持 **`design_invalid: projection`**，不是 qualification pass。M1 保存的 12 文件链与当前文件 SHA 全匹配。

当前重跑脚本 `run_m1_stage2_rerun.py:110–123` 确实使用冻结 `.5/.1/.1` 参数尺度；训练/评价由不同 seed 生成。原无效运行没有因本次诊断恢复证据资格。

必须区分三层：

1. **冻结门槛失败是事实。** 当前拟合与采样管线未通过注册的 H1 指标。
2. **H1 不能认证条件校准。** `hist_tv`（283–293 行）只接收 `y_true,y_cand`，把所有行/动作的 Y 混合进 256 格直方图；`run_h1`（297–315 行）每评价行仅抽一个候选 Y。输入维度 d 是 8–64，但该指标不保留 X/A 分组。把同一组候选 Y 在行间置换会保留 H1 数值，却可能破坏 X/A 条件对应。故 H1 有条件关系盲点；即使通过，也不能推出 `P(Y|X,A)` 已校准。
3. **它也不是完整的药理/决策效果失败。** 当前数据为冻结合成 GMM，未比较独立功能决策收益或真实数据迁移。失败不足以推断生物机制不存在。

H3 的代码（476–518 行）是 small-case 下按指数奖励积分后归一化的动作分布 TV；不是高维条件密度 exact oracle。H2 证明当前数值配置的 Sinkhorn 边缘收敛。保存的 G1/G2/G4/G5/G6 标签包含结构声明/外部两跑记录，不能把标签统一当作本审计重新实验验证。

另一个未分离因素：C-MDN 的 NLL 是未截断高斯混合，采样后 `clamp` 到 box（212–264 行）；生成器则是按截断质量重加权的截断混合（152–174 行）。clipping 与 truncation 是不同分布，这可影响拟合/边界误差，但现有结果未量化其贡献；不能自行宣布这就是主因。

## 3. 失败诊断：保存数字可取，16/16 不可达归因不可采用

对同一保存 JSON 的重算结果：

| 保存指标 | 满足格数 |
|---|---:|
| floor MC q95 ≥ 容差 | 16/16 |
| 直接条件 oracle 两样本均值 > 容差 | 13/16 |
| 直接条件 oracle 两样本 q95 ≥ 容差 | **15/16** |
| 直接条件 oracle 两样本 q05 > 容差 | **12/16** |
| C-MDN TV > 直接 oracle 均值 | 16/16 |
| C-MDN TV > 直接 oracle q95 | **13/16** |

这些是同一参数种子、同一固定评价样本上的诊断，不是 16 个独立生成器复现实验。同一 d 的 oracle/floor 摘要在四个训练 N 行中复用，实际只有 4 组 oracle 摘要。

**发现 1：分位数概率方向错误，且混用了两种 q95。**

- `report_diag_m1_s2.md:45` 写“floor q95 ≥ 容差（oracle 完美模型在单格通过概率 ≤5%）”。这不成立：容差低于 q95 只说明其不是覆盖 95% 抽样结果的宽容差，不能推出通过概率 ≤5%；对应低通过概率应检查下侧分位数或直接失败频率。
- 同报告第 8 行称“16/16 oracle 真值两样本 q95 ≥ 容差”，实际直接 oracle 为 **15/16**。反例 `(d=64,N=512)`：直接 oracle q95=`.17724609375 < .18`，而 floor MC q95=`.1923828125 > .18`。报告将 floor 结论代入了直接 oracle。
- q05>tol 的 12/16 支持“这 12 格在该诊断样本下，即使 oracle 也很难稳定过关”的受限判断；不证明任何格数学上不可达，更不能概括其余 4 格为 ≤5% 通过率。JSON 没保存每次 oracle TV，不能从摘要恢复精确失败频率及其区间。

**发现 2：当前源码的 p_pop 采样并非协议所述每行 256 次独立 mixture 抽样。**

`diag_m1_s2.py:112–130` 在每行只生成一个 component (`u0=rng.random(n)`)，然后固定该 component 抽 `m_per_row` 个 Y。m=256 时，这 256 个 Y 共享分量；增加到 256 只减少分量内噪声，没有同等减少混合分量选择噪声。因此其 524,288 样本不能按“每行完整条件混合的独立重复”理解。直接 oracle m=1 路径没有这个批量采样问题。后续把固定 X/A 的非同分布行样本近似成 pooled multinomial 也另加了近似，不能把该 MC 的 q95 当作精确可达下界。

当前源码与最终 usage 自报源码 hash 一致，所以上述是**当前交付版本的可定位风险**；本审计没有执行级快照证明，避免断言未知历史版本如何运行。

**发现 3：不能将所有误差都归于估计器。**

C-MDN 在 13/16 格超过直接 oracle 的 q95，16/16 超过其均值，提示当前拟合/采样管线还有额外差异。它不是正式独立拟合检验，不能据此给条件校准误差或其原因下定论；同样也不能被“floor 不可达主导”标签抹掉。

非冻结 hidden256/epochs400 敏感性 6 格中 **1 改善、5 变差**，中位 ΔTV `+.07592773435`；只能说本次联合容量/训练时长改动未普遍改善。保真核验 d8/N512 的 `Δ=-.0068359375` 超过预设 `.005` caveat，另一个 d64/N4096 为 `+.001953125`。不能据此宣布容量原则上无用，或把其结果当冻结主证据。

**建议父 Agent 可采用的表述：**“M1 corrected rerun 未过冻结 H1；直接 oracle 诊断提示多数格存在明显有限样本门槛问题，同时拟合/采样额外差异仍在。当前诊断的分位数解释、floor 构造与原因排序不足以支持‘16/16 不可达、容差为主因’；保持原判定，归因未决。”

## 4. M3 v0_2：只设计，已有修订缺口

当前 plan/代码确有 7 个纯 learner arm、相同 allocation policy 字符串、primary 为 candidate vs `A_standard_DR_TMLE`、Holm family=6，未列 optimal-allocation arm。35 个冻结输入 hash 与当前文件全匹配。原 learner×allocation 复合比较矛盾在 arm 定义层面已修正。

但这些不能升级为效果或完成执行资格：

- `exec_plan_m3_s3_v0_2.py:334` 将 `all_arms_same_feedback_stream=True` 写成常量；它没有生成反馈流后逐臂比对。schema `arm_fields` 缺 `feedback_stream_sha`、`evaluation_stream_sha`，各 arm 也没有字段。报告/design 宣称已落实与实际 schema 不一致；已有 `challenge_M3_S3_EXEC_v0_2.md` 判 **revise**，本审计同意该可定位缺口。
- plan `schema_file` 仍指 `schema_m3_s3_exec.json`，而本版文件为 `schema_m3_s3_exec_v0_2.json`；`stop_boundaries` 仍残留“standard DR/TMLE + optimal allocation”旧文字。这是同步问题，不构成已经运行了不同 allocation 的证据。
- MDE `.04798268` 的保存算术复算一致，但采用假定 SD=.20、deff=2.2、未校正的 Z 常数。它不是对实际 R=10 cluster 与 Holm family=6 检验的实测功效保证；执行前须明确 cluster/多重性推断和功效假设。
- `status=preregistration_only_not_executed`、`stage3.status=planned_not_run`。没有 Stage3 训练/决策收益/真实数据效果，现阶段只可记设计进展。

本审计不追踪 M3 后续新版本，也不代替其审批。必要后续是补足可执行流记录/检查与最终实现 pilot、freeze 与挑战；不因当前设计算术通过就预告效果。

## 5. 本审计交付和采用边界

新增文件均位于本 episode：本报告、`audit_latest_other_agent.py`、`latest_other_agent_audit_counts.json`。运行命令：

```powershell
& 'D:\anaconda\envs\maestro\python.exe' 'D:\MAESTRO\research\2026-10-28-agent-a-proximal-program-pilot\audit_latest_other_agent.py'
```

退出码 0。只重算已保存数字/哈希，未 import 对方实验脚本。JSON 给出完整输入快照。父 Agent 应核验后采用本报告结论；本报告不是新的方法效果、生物机制或总体研究目标达成证据。

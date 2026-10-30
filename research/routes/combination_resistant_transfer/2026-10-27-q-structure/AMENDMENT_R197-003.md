# AMENDMENT_R197-003 —— R197 v2 结果解释前的预注册补写（2026-10-27，**最终 verdict 落盘之前**）

> 依据：`challenge_R197_v2.md`（i003 结果前预审）§2 两项必改 + Lead 三条消息（type-I CP 上界规则、Δ_primary 配对 bootstrap、wall>20 min ⇒ verdict 必须 `inconclusive`）。补写**不重跑主统计、不改主设计/门槛/δ_min/B 模型**；只改 type-I 设计体检的认证规则与推断口径的书面写死，并在最终 verdict 前落盘。写入本文件时 v2 全量正式结果尚未产生（此前只有一次 `--quick` 调试进程在写 JSON 时因 ndarray 序列化失败，留下的 `r197_v2.json` 是**无效残片**，将被正式运行覆盖；无任何可解释的 v2 verdict）。

## 1. type-I 认证规则（替换 AMENDMENT_R197-002 §4.4/§4.5 的对应条）

- **设计体检项（写死）**：H197c 主规则（放宽规则：`pooled Δ_primary ≥ δ_min` 且配对 cluster-bootstrap CI 下界>0；容量对照/置换-p 合取项省略 ⇒ 上界）的零数据模拟 type-I 的 **Clopper–Pearson 95% 单侧上界必须 ≤ 0.10**；**点估计≤0.05 不再单独作为通过依据**。
- **预注册扩充日程**（按顺序，不跳档）：初始 **n=20**；若 CP95 上界>0.10 → 追加 10 次（n=30）；仍>0.10 → 追加 10（n=40）；仍>0.10 → 追加 20（n=60）；**n=60 时仍>0.10 → 设计体检 FAIL → `inconclusive`**。每档均报告累计 `n、失败数、点估计、CP95 上界`。计算：`CP95 upper = Beta^{-1}(0.95; k+1, n-k)`（k=失败数；k=n 时记 1.0）。
- 零数据生成、放松规则定义、seed 推导（`20261110 + 累计档位偏移`）保持不变；追加模拟使用预先写死的分档 seed（第 1 档 20261110，第 2 档 20261310，第 3 档 20261410，第 4 档 20261510），不因结果挑 seed。
- 若按新规则 n=30 即满足（预计 0/30 → CP95 上界≈0.0945≤0.10），以该档为准；不得为让结果通过而越过档位。

## 2. Δ_primary 的配对 cluster bootstrap（写死）

- H197c 主对比 `Δ_primary = Spearman(B2) − Spearman(B0)` 的 cluster bootstrap 必须**配对**：每个 bootstrap replicate 只抽一次节点 multiplicity（细胞节点 + condition-pair 行节点），把同一组多重性复制后的**同一测试条目集合**同时用于 B2 与 B0 的预测，分别算 Spearman 后取差；**不得**为两个模型独立重抽。
- 两模型使用**同一 OOF 折分配、同一测试条目集合、同一观测值**；bootstrap 仅改变重采样权重/多重性，不改变折结构；`Δ_boot` 的 2.5/97.5 百分位为 CI，`MDE80=2.802·SD_boot`。
- 该配对口径同样用于 `beyond_prepurchased_features` 的 `Δ(B2−BMono)` CI 与置换零分布（同一测试条目/同一预测）。
- 实现断言（写进代码与 JSON）：bootstrap 函数内对 B2 与 B0 使用同一 `idx`/权重数组；JSON 记录 `paired_cluster_bootstrap: true`。

## 3. OOF 拼接尺度的披露与副指标（不改主判定）

- 主指标保持预注册的**全局 OOF Spearman**（5 折模型预测拼接后计算）；但 v1/v2 的折模型截距/尺度可能不同，拼接全局排序会混入折间尺度差。**新增副指标（只披露，不进主 verdict）**：
  - 每折 Spearman 的折均值 `per_fold_spearman_mean` 与折间 SD（B0/B2 及各模型）；
  - 主对比的折均值差 `Δ_foldmean = mean_f Spearman_f(B2) − mean_f Spearman_f(B0)` 及其按折的简单 percentile 敏感性（仅描述）；
  - 折内标准化敏感性：每折把预测与观测在该折内 z 标准化后再拼接算 Spearman（只报告）。
- 若全局 OOF 与折均值口径的 Δ 符号/量级明显不一致，报告必须并列说明（不据此改判）。

## 4. 预算规则（Lead 指令，写死）

- AMENDMENT_R197-002 §6 的「单命令 ≤20 min」是**设计门**而非建议：**若正式全量运行的实际 wall-clock > 20 min（1200 s），最终 verdict 必须为 `inconclusive`**（原因 `runtime_budget_exceeded`），**不得**把超时改写为"deviation 放行"、不得在超时后重跑挑选结果；即使 B2 指标好看也不得判 `low_rank_structure_present`。
- 记录：`usage_r197_v2.json` 与 `r197_v2.json` 写 `wall_seconds_total`、`cpu_time_seconds_total`（`time.process_time`）、`budget_seconds=1200`、`budget_exceeded` 布尔；`record_r197_v2.md` 记录实际 wall/CPU 与分步缓存路径。
- 工程性分步缓存（不改变统计/设计）：A0 完成后写 `tmp/r197_v2_stage_A0.json`；B 主+次设计完成后写 `tmp/r197_v2_stage_B.json`；最终写正式产物。缓存仅用于防止单进程失败时丢结果与审计墙钟，不参与任何选择。

## 5. 其它结果前小项（写入报告/记录检查清单，不改判定）

- H197a/b 的 B3 特征增量与 `feature_increment_*_descriptive` 标签只作描述，不进主 verdict；报告必须同时给 `Δ(B3−BMono)`（单药块贡献）。
- `beyond_prepurchased_features` 的 `Δ(B2−BMono)` 仍作**限定词**（非主判定门槛），其 CI 与主 CI 同口径。
- A0 V5 键级只敏感性、不入判据；barcode 级未覆盖与噪声标定仅 1.43% 观测的限制必须在报告写明。
- `rel_entry`/δ_min 依赖 A0 share_noise（老 Q2 噪声估计的对象限制），报告须带此限制；δ_min 不得写成"决策效用阈值"。

## 6. 影响面

- 不改变：H197c 主设计、B2 主模型、H197a/b 次设计、δ_min 定义（0.0734 量级，A0 冻结）、B0–B4 模型、MDE 公式、置换零分布、覆盖/可辨识性门槛。
- 改变：type-I 设计体检的认证规则（CP95 上界≤0.10 + 预注册扩充），以及 Δ 推断的配对口径写死（实现本已配对，现写入预注册）；新增 OOF 尺度副指标；新增 wall>20 min ⇒ inconclusive 后果。

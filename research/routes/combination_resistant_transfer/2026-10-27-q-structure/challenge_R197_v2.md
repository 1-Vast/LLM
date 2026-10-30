# R197 v2 独立挑战（task-34）—— 第一部分：**结果前预审**（2026-10-27）

> 状态：**结果前预审（pre-result review）**。R197v2（AMENDMENT-R197-002）正在运行、结果尚未解释。本文只对 [AMENDMENT_R197.md](AMENDMENT_R197.md) 是否**预先写死** challenge_R197 的 5 条必改做核对；**不是结果审**。结果出来后（T34 正式挑战）在本文追加"§5 结果审"再出最终 verdict。
> 依据：[challenge_R197.md](challenge_R197.md)（v1 挑战，revise，5 必改）、[AMENDMENT_R197.md](AMENDMENT_R197.md)、[REVOCATION_R197.md](REVOCATION_R197.md)、v1 `PROTOCOL_R197.md`（v1 无结果）。只读；未改 AMENDMENT/结果/其它目录；未运行效果。

## 0. 预审结论（一句话）

**5 条必改中 4 条已预注册、1 条部分（type-I 精确性）；另有 2 个应在本轮结果解释前写死的预注册小项（Δ 的配对重采样口径、type-I 的 CP 上界规则）。建议 runner/Lead 在解释前补一段 AMENDMENT-003（不改已跑统计量，只补判定/口径）；否则 T34 只能判"部分预注册"。**

- 已预注册：① 方案 Q（主设计 H197c 随机条目 + 主模型 B2 可辨识；H197a/b 降次描述；措辞限定）；② 特征-端点构造重叠披露 + 块消融 + `beyond_prepurchased_features`（含 Δ(B2−BMono) CI）；③ δ_min operational（0.10·sqrt(rel_entry)，A0 先于 B 断言，R_split/0.05 敏感性，禁 q2 0.868/旧 CI）；④ A0 依赖降级（节点级）+ 键级 V5 + 置换交换性限制 + R_split 覆盖 + A0 状态继承规则；⑤ 措辞/谱系/预算/SHA/种子/降级顺序/预注册文本更正。
- 部分：type-I 只有 20 次 + "点估计>0.05 追加 20" 的规则，但 1/20=0.05 不会触发追加，Clopper–Pearson 上界在 0/20 时仍≈0.139、1/20 时≈0.216——**不能认证 type-I≤0.10**；需预注册"CP 95% 上界≤0.10（或追加模拟至满足，否则 design check 失败）"。
- 小项（建议同批补）：主对比 Δ=Spearman(B2)−Spearman(B0) 的 cluster bootstrap 必须**配对**（同一节点 multiplicity 同时用于两个模型）；OOF Spearman 跨 5 折模型拼接的尺度问题未声明（v1 遗留；应预注册"每折 Spearman 均值"为副指标或 fold 内标准化敏感性，避免全局 pooled 由折间尺度驱动）。
- 需补 AMENDMENT：**是**（type-I CP 规则 + Δ 配对口径；可选 OOF 口径）。可用短 addendum；不要求重跑主统计，但 type-I 若按新规则不达标需预注册后果（`inconclusive`/design check 失败），不得事后放宽。

## 1. 5 条必改逐条对照

| 必改（challenge_R197 §3） | AMENDMENT 落点 | 状态 |
|---|---|---|
| 1. 主问题/主模型对齐：二选一（改命题为预购特征增量 / 预注册 B2 可辨识主设计）；no_stable_increment 不关闭低秩研究 | §0：**选方案 Q**——主设计=H197c（随机留出 20% 观测条目，5 折），主模型=**B2（加性+低秩 ALS，无元数据/单药特征）**、主对比 Δ=Spearman(B2)−B0；H197a/b 降次描述且明写"不检验低秩结构"；主问题可回答范围写死（不冷迁移/不反馈/不选药）；verdict 改 `low_rank_structure_present` / `no_stable_low_rank_increment`；H197a/b 有 `feature_increment_*_descriptive` 标签且不得关闭低秩研究（§4.7/§4.8） | **已预注册** |
| 2. 披露单药特征与 ΔEMAX 期望项构造重叠；块消融/Δ(B3−B1) CI；增强基线 | §4.1：P 块构造重叠披露写死、块消融 B0→BM→BMono→B3、含 P 的模型增量不得解释为条件结构；主模型 B2 不用 P/M/X；§4.7 `beyond_prepurchased_features` 要求 Δ(B2−BMono) CI 下界>0 且 B2 点≥max(BM,BMono,B3,B4)，否则 present 词降级；§4.4 另报 Δ(B2−BM)、Δ(B2−BMono)、Δ(B2−B3) | **已预注册（主口径）**；小项：Δ(B3−BMono) 的 CI 未单独预注册（建议标描述性即可，不影响主 verdict） |
| 3. δ_min operational 化 | §4.6：δ_min=0.10·sqrt(rel_entry)，rel_entry=1−share_noise_clipped（A0 重校准，先于 B 打分并冻结，运行时断言）；锚=R193-A1 latent 0.10；先验预期 share_noise≈0.46⇒δ_min≈0.073；敏感性 0.10·sqrt(R_split) 与旧 0.05 只报告；禁 q2 0.868/旧 CI 反推；不可计算→inconclusive | **已预注册** |
| 4. A0 依赖降级 + 键/barcode 级敏感性 | §3：V1–V4 限定"节点级依赖感知"写死；新增 **V5 键级 bootstrap**（4,686 使用键，B=1,000，seed 20261112，权重=4 键 multiplicity 积，仅敏感性）；barcode 级仍未覆盖（噪声标定 1.43%）披露；置换交换性限制写死；R_split 增加纳入/丢弃/Jaccard 报告且 0.50 只作"条件主效应可靠性"；A0 状态→B 解释继承规则写死 | **已预注册** |
| 5. 措辞/谱系/预算/SHA/type-I/冻结 | §4.8 允许/禁止句式；§7 不是新算子、不启动反馈/Agent、只写本目录；§6 缓存/降级/墙钟；§2 SHA（含运行前更正附录：q2.json `94C5CD9B…`、PROTOCOL_R197 `36EF1873…`）；§5 种子全列；§4.4/§4.5 type-I 规则（20 次 + 点>0.05 追加 20、合并>0.05 fail、报 CP 上界） | **部分（type-I 精确性不足，见 §2-①；其余 ✓）** |

## 2. 结果解释前必须补写的预注册项（要求 runner/Lead 在**看 v2 结果之前**补 AMENDMENT-003）

### ① type-I 的 CP 上界规则（最重要）
- §4.4/§4.5 现在的规则：H197c 主规则 20 次零数据模拟；"点估计 >0.05 → 追加 20；合并 >0.05 即设计体检失败"；同时报 Clopper–Pearson 95% 上界。问题：**1/20 = 0.05 不触发追加**（条件是 >0.05），于是 1/20 会以"点估计 0.05 ≤0.05"通过 B-D4，而 CP 95% 上界≈**0.216**；0/20 的 CP 上界≈**0.139**——两者都**不能认证 type-I≤0.10**（我的必改 5 明确要求 type-I 精度规则）。
- 要求（预先写死）：把"**CP 95% 上界 ≤0.10**"作为 type-I 设计体检的一部分；若不满足，追加模拟（20→40→…，追加次数预注册上限）直到满足；若到上限仍 >0.10 → `inconclusive`（design check 失败）。或等价地预注册最小 sims（如 40 次全 0 失败 / 47 次≤1）并固定；不得用"点估计≤0.05"代替。
- 同时写死 type-I 的拒绝定义（放宽规则省略哪些合取项）与零数据生成（整体置换 92,039 Q 值）不变——这部分已写 ✓。

### ② Δ_primary 的配对 cluster bootstrap 口径
- §4.4 写"H197c 双向按细胞+condition-pair 节点重采样、条目按重采样单元的多重性复制"，但未写**同一重采样是否同时用于 B2 与 B0**；Δ 是两个模型在同一测试条目上的 Spearman 差，必须**配对**重采样（同一次节点 multiplicity 同时重算两个模型的 Spearman），否则 Δ 的 CI/MDE 会偏大/不一致。要求在 AMENDMENT 写"paired cluster bootstrap（同一 resample 计算两模型）"，并写死两模型使用同一测试条目集合/同一 OOF 折。
- 附：H197c 的 OOF Spearman 是把 5 个折模型预测拼接后全局计算（v1 遗留）；不同折模型的截距/尺度差可能驱动全局排序；建议预注册"每折 Spearman 均值"为副指标（或折内标准化 pooled 为敏感性），主指标保持 OOF Spearman但报告该口径；不要求改主判定，除非 Lead 认为必须（这是口径披露，不是新门槛）。

### 结果前小项（写入 record/report 检查清单，不必改 AMENDMENT）
- H197a/b 的 B3 特征增量与 `feature_increment_*_descriptive` 标签只能描述，不得进入主 verdict；报告必须同时给 Δ(B3−BMono)（单药块贡献）的描述性数字。
- `beyond_prepurchased_features` 的 `Δ(B2−BMono)` CI 的 bootstrap 口径要与主 CI 一致（配对、同节点）。
- A0 V5 键级只敏感性、不入判据；barcode 级未覆盖需在报告写明。
- 预算：AMENDMENT §6 单命令 ≤20 min；Lead 通报 CPU ~16 min，**须在 record 记 wall-clock 与 CPU-time**；若 wall >20 min → 按 §6 降级顺序/`inconclusive: runtime budget`，不能事后放宽。
- δ_min 的 `rel_entry` 依赖 A0 的 share_noise（老 Q2 噪声估计只覆盖 1.43% 观测）；报告须带该限制，且不得把 δ_min 当"决策效用阈值"（§4.6 已写）。

## 3. 结果出来后（T34 正式结果审）必须核对的清单（预登记）

1. **A0**：修正式/未加权 sanity/dyadic 10.33/V1–V5/图感知置换/R_split（含覆盖与 Jaccard）；A0 status；`rel_entry` 与 δ_min 的数值/顺序断言（A0 日志先于 B 打分）。
2. **B-D1–D6**：覆盖（≥10,000 测试条目/每折≥1,000）、可辨识性（每行/列训练≥20、测试≥5、100%）、无泄漏断言、置换零分布 |mean|≤0.02、type-I（按 §2-① 新规则）、MDE80≤δ_min、确定性与 SHA 双跑。
3. **主结果**：Δ_primary=Spearman(B2)−Spearman(B0)、配对 cluster CI、置换 p、每折 Spearman、OOF R²；`beyond_prepurchased_features` 的 Δ(B2−BMono) CI 与 B2 vs BM/BMono/B3/B4 点比较；rank 选择结果（r 分布）。
4. **次设计**：H197a/b 的 Δ(B3−B0)、Δ(B3−BMono) 及 CI（描述性），并确认未进入主 verdict；B2 退化证明。
5. **措辞**：报告逐字引用 §4.8 模板；不得写"可迁移条件规律/反馈有用/机制/新算子/共同学习成立"；阴性不得写"Q 没有低秩/条件结构"或关闭其他表示/留出；δ_min/结果不事后调。
6. **偏离**：`record_r197_v2.md` 的偏离清单（尤其 rank 选择代理、预算降级、V5 实测 4,686 键、SHA 更正）；产物 SHA/双跑一致。

## 4. 声明

- 本文是**结果前预审**；未运行效果、未改 AMENDMENT/结果/其它目录；不构成 T34 最终 verdict。
- **是否需 runner 在结果解释前补 AMENDMENT：需要（2 项：type-I CP 上界规则、Δ 配对 bootstrap 口径；OOF 口径为建议披露）**。补写不改变已跑主统计量；但 type-I 若按新规则不达标，须预先写死后果（inconclusive/design check 失败）。
- 待 v2 结果出：在本文追加 §5 结果审（按 §3 清单）后给最终 verdict（proceed/revise/stop）。

**预审一句话：AMENDMENT_R197 已把 5 条必改的 4 条写死（方案 Q/H197c 主设计+B2 主模型、构造重叠披露+块消融+beyond_prepurchased_features、δ_min operational、A0 节点级+键级 V5+继承规则），措辞/谱系/预算/SHA 也都补了；但 type-I 仍以 20 次点估计+点>0.05 才追加（CP 上界可能 >0.10，无法认证），且 Δ_primary 未写死配对重采样——这两项需在结果解释前补 AMENDMENT-003，否则 T34 只能判"部分预注册 / inconclusive（type-I 未认证）"。**

---

## 5. 结果审（T34，2026-10-27，v2 已落盘后）

> 依据：`AMENDMENT_R197.md`（002，SHA `E1CB303B…`）、`AMENDMENT_R197-003.md`（003，SHA `973A95BB…`）、`AMENDMENT_R197-004.md`（004，SHA `73AC438B…`）、`r197_v2.py`（`B0C997B0…`）、`r197_v2.json`（`B0DBE798…`）、`r197_v2_rows.csv`（`D19B51B8…`）、`report_r197_v2.md`（`A99B0E3C…`）、`record_r197_v2.md`、`usage_r197_v2.json`（`E0D43803…`）、`tmp/_r197_v2_run*.json/log`。只读复核；未运行效果/模拟、未改 R197v2 产物。

### 5.0 结果审判决：**PASS（结果可解释；附 2 条记录级更正；不重跑、不改变 verdict）**

**可解释边界（写死）**：R197 v2 **只能**写"按预注册规则（002+003），因 **B-D3 可辨识性**与 **B-D5 MDE80>δ_min** 两项设计体检失败，verdict=`inconclusive`（未决）"；主结果（B2 OOF Spearman 0.7206/R²=0.603 vs B0 0.2073、Δ=+0.5133、配对 CI [+0.4458,+0.5756]、置换 p=0.001、Δ(B2−BMono)=+0.4208）**只是未认证的描述性数字**，不得写成"Q 低秩结构可预测/成立"；**B-D3 的失败含协议缺陷**（见 §5.2），但**本版不得改判**；B-D5 独立失败 → verdict 保持 inconclusive；A0 状态 `q2_inference_not_robust_under_dependence`；旧 0.868 可靠性/`condition_structure_present` 未获认证；1.43% 只保留"加性 condition 主效应份额"；不得写结构不存在、不得写可迁移条件规律/反馈有用/机制/新算法/共同学习成立/决策收益。

### 5.1 verdict 机械应用（PASS）

| 设计体检 | 预注册门槛（002） | 实测 | 判定 |
|---|---|---|---|
| B-D1 覆盖 | ≥10,000 测试条目；每折≥1,000；有限预测≥0.99 | 92,039；18,407–18,408；1.0 | PASS |
| B-D2 无泄漏 | 0 个折训练/测试相交 | 0 | PASS |
| **B-D3 可辨识性** | 每行/列训练≥20 且测试≥5（100%） | 行 min 56、100% ✓；**列 min 3、训练≥20 比例 94.91%、测试≥5 比例 91.38%**（5.09%/8.62% 列失败；JSON `identifiability_checks`） | **FAIL** |
| B-D3 B2 非退化 | U/V 非零 100% | U 非零行 100%、V 非零列 100%（JSON 1.0） | PASS（但见 §5.2） |
| B-D4 置换零/type-I | \|mean\|≤0.02；CP95 上界≤0.10 | 7.92e-05；**0.09503385（0/30）** | PASS |
| **B-D5 MDE80** | ≤δ_min=0.07339553 | **0.0941995**（SE=0.03362364） | **FAIL** |
| B-D6 SHA/确定性 | 输入/脚本 SHA；双跑一致 | 见 §5.3 | PASS |
| 预算门（003 §4） | wall≤1,200 s | **最终 run3/run4：564.5/525.4 s**（run1 669.5、run2≈631.7） | PASS（报告数字需更正，见 §5.5） |

**verdict=`inconclusive`**（`B_v2.judgment.verdict`），因为 B-D3/B-D5 两项预注册体检失败；**没有**因 Δ 点估计 +0.5133、CI 下界 +0.4458、p=0.001 而改判（report §0/§5 明写"仅报告，不认证"）；B-D3/B-D5 门槛来自 AMENDMENT-002，003/004 **未改任何门槛**（003 只加 type-I CP 规则/配对口径/wall 门；004 只改 telemetry 存放）；未事后扩 rank 网格（r=5 触上限记为 limitation）✓。

### 5.2 特别裁定：B-D3 是**协议缺陷**（limitation + 下一版预注册修订项；本版不改判）

- **裁定**：B-D3 把"**每列/每行的逐列样本量**"当作"**低秩因子可辨识性**"的判据，二者不是一回事。H197c 是随机条目留出：所有行/列在训练中都有观测（行 min 56、列 min 3；密度 26.8%），B2 的加性+低秩因子由全部行/列联合估计，且 B2 非退化检查（U/V 全部非零）**100% 通过**；失败来自 Q 矩阵边缘稀疏列（min 列观测 6；8.6% 列测试<5、5.1% 列训练<20）不满足"每列≥20/≥5"的覆盖式门槛。**该门槛是覆盖/样本量检查，不是可辨识性检查**：满足逐列≥20 不保证 UV^T 唯一（符号/尺度/旋转、rank 选择、多解），反之稀疏边缘列也不必然使整体因子不可估（因子可跨行/列借用强度）。
- **本版后果（写死）**：这是**协议设计缺陷/limitation**，不是 B2 不可辨识的证据，也**不能**据此把 verdict 改判或放宽门槛。verdict 保持 `inconclusive`；且 **B-D5（MDE80=0.0942>δ_min=0.0734）独立失败**——即使未来把 B-D3 换成正确的可辨识性检查，本版仍不能判 present。主结果只作描述性。
- **下一版预注册修订项（本版不执行）**：把"可辨识性"拆成：(i) **覆盖/稀疏检查**：报告行/列训练/测试分位数、稀疏边缘列的显式口径（全部列 vs 排除稀疏列的敏感性，两者都预注册）；(ii) **因子可辨识性检查**：B2 的 U/V 非退化（已 100%）、奇异值/条件数、符号/尺度不变性、rank 选择跨折稳定性；(iii) **mask 模拟**：按真实 Q 缺失图案/折掩码生成/遮挡条目，拟合 B2 并检验低秩成分/rank 的恢复（若失败则 failure 记在可辨识性而非稀疏样本量）；(iv) 以上在下一版运行前冻结，不得回写本版 verdict。
- 报告 §3.2/§5.3 已写"该检查把稀疏列逐列样本量与低秩因子可辨识性混在一起"（[report_r197_v2.md:109](report_r197_v2.md#L109)），方向正确；建议升格为"协议缺陷 + 下一版修订项"并写入 limitations（见 §5.5-①）。

### 5.3 数字、SHA、确定性（PASS，已独立核对）

- **SHA 全部一致**（我独立重算）：`r197_v2.py B0C997B0…`、`r197_v2.json B0DBE798…`、`r197_v2_rows.csv D19B51B8…`、`report A99B0E3C…`、`usage E0D43803…`；AMENDMENT-002 `E1CB303B…`、003 `973A95BB…`、004 `73AC438B…` 与 record §7 一致。
- **确定性**：tmp 快照 `_r197_v2_run1.json`=`F1636BE9…`(37,777 B)、`run2`=`C8991110…`(38,017 B)、`run3`=`B0DBE798…`(38,377 B)；**最终 `r197_v2.json` SHA = run3 快照 SHA**，`r197_v2_rows.csv` 在 run1–run3/最终均 `D19B51B8…`，run4 log 存在且最终产物于 19:11:47 写盘 → **run3/run4 逐字节一致**成立（run2 是 AMENDMENT-004 之前代码，JSON 与最终不同——报告"run2/run3"表述错误，见 §5.5-②）。
- **主数字与 Lead 通报一致**：B2 OOF Spearman **0.72060055**、R² **0.60291772**、B0 **0.20726992**；Δ_primary **0.51333063**、配对 CI **[0.44580795, 0.5756033]**、SE 0.03362364、MDE80 **0.0941995**、置换 p **0.000999**；Δ(B2−BMono) **0.42075039** CI [0.35477388,0.49222762]；feature ablation BM 0.0856/BMono 0.2999/B3 0.3190；次设计 H197a/b 的 Δ(B3−B0)/Δ(B3−BMono) 与报告/JSON 一致；δ_min **0.07339553**（0.10·√rel_entry，rel_entry 0.53869034）、type-I **0.09503385（0/30）**、E5–E8 均 PASS；B-D6=TRUE。
- **A0**：status **`q2_inference_not_robust_under_dependence`**；V4 CI [0.00018017,0.00175226]；R_split Spearman–Brown **median −0.70499245**（20 splits，raw r −0.2606；CI 全负）；旧 R=0.86786259 **未认证**；公式 R=0.2822 [0.1605,0.6502]；V5 键级仅敏感；1.43% 只作加性 condition 主效应份额的噪声标定对象——report §2/§4 措辞正确。

### 5.4 预注册性（003/004）、type-I CP、配对 bootstrap（PASS，附 1 条时间性说明）

- **003 预注册有效**：mtime 18:27:26，早于正式 run1 启动 18:28:30；其前只有无效 `--quick` 调试残片（无可用 v2 verdict），003 明确"补写不重跑主统计、不改主设计/门槛/δ_min"；内容正是我预审要求的 type-I CP 上界≤0.10（分档 20→30→40→60、失败档预注册）、Δ 配对 cluster bootstrap、OOF 尺度副指标、wall>1200 s ⇒ inconclusive。最终按 003 规则在 n=30 达 **0/30、CP95=1−0.05^(1/30)=0.09503≤0.10**，停止扩充——机械一致，未见越档/挑 seed。
- **配对 bootstrap**：JSON `paired_cluster_bootstrap: true`；主 CI/Δ(B2−BMono) 均由同一 cluster bootstrap（`boot_delta` 对两模型同一重采样）计算，两模型同一 OOF/测试条目/观测；报告与 JSON 一致 ✓。
- **004 预注册性（限定说明）**：004（telemetry 与确定性解耦，只把 wall/CPU 移出核心 JSON、不改统计量/门槛/判定）mtime **18:51:57**，晚于 run1/run2（18:39:47/18:51:36）**结果已存在**、早于 run3/run4（18:52:29/19:02:59）和最终 verdict；它不改变任何科学内容，但严格说**不是"结果前"预注册，而是"结果后、最终 verdict 前"的产物流水线修订**；报告/usage 应如此标注（现称"最终 verdict 前"可接受，但"pre-registered"易被读成结果前；建议改称"post-result telemetry amendment"）。不影响 verdict。
- **未改门槛**：B-D3/B-D5 门槛、δ_min、模型、主设计均保持 002 冻结值；003/004 未改；无 test 调参（attestation `no_test_tuning`）。

### 5.5 记录级更正（2 条；正式引用/入库前改，不重跑、不改 verdict）

① **B-D3 limitation 的写法**：report §3.2/§5.3 已说"混在一起"，但未明确"**协议缺陷/下一版预注册修订项**"；建议按 §5.2 重写为 limitation（含下一版分开 coverage/identifiability/mask 模拟的具体条目），并明确"B-D3 FAIL 不能解释为 B2 不可辨识；B-D5 独立失败使 verdict 仍 inconclusive"。
② **报告 telemetry/determinism 表述与 record/usage 不一致**：
   - report §0/§3.2/§6 写 wall=669.5/631.7–669.5 s（run1/run2，AMENDMENT-004 前），record §7/usage 最终为 **run3 564.5 s、run4 525.4 s**；预算门均 PASS（<1200），但报告应改用最终 run3/run4 或显式标注两组数字。
   - report §6 第一颗写"正式全量运行两次（run2/run3，同一代码）逐字节一致"，但 §6 SHA 行又说 run3=run4；实际 tmp 快照 run2 JSON=`C8991110…` ≠ run3/final `B0DBE798…`（run2 在 004/code patch 前），**确定性对是 run3/run4**；应改。
   - 建议 report/record 同时写明：run1/2 为 004 前运行（统计量相同、JSON 字段不同），run3/4 为 004 后确定性对；预算门按 run3/4 报告。
**其余**：v1 无有效结果/不引用 ✓；C177 状态 ✓；A0→B 继承 ✓；1.43% 边界 ✓；无越界措辞 ✓；rank 网格上限 5 的 limitation 已写 ✓。

### 5.6 可解释边界（最终，供 Lead/登记）

- **允许**："R197 v2 在预注册 002+003 下 verdict=`inconclusive`：B-D3 可辨识性（逐列样本量式检查，且该检查含协议缺陷）与 B-D5 MDE80=0.0942>δ_min=0.0734 两项设计体检失败；主结果 B2 OOF Spearman 0.7206（R²=0.603）vs B0 0.2073、Δ=+0.5133 CI [+0.4458,+0.5756]、p=0.001、Δ(B2−BMono)=+0.4208 仅为未认证描述性数字；B-D3 缺陷与下一版修订项已登记；A0 status=`q2_inference_not_robust_under_dependence`，旧 0.868/condition_structure_present 未获认证；1.43% 仅加性 condition 主效应份额。"
- **禁止**：`low_rank_structure_present`/低秩结构可预测/成立；结构不存在/无增量；在 v2 上放宽或重判 B-D3/B-D5；用 Δ CI/p 或 B2 vs B0 数字作已认证结论；引用 0.868 可靠性或旧 condition_structure_present；写 1.43% 是可迁移规律总量；写条件规律可迁移/反馈有用/机制/新算法/共同学习成立/A1-A2-A3 复活/决策/临床/外部复现；不得把 B-D3 协议缺陷当作"改判理由"或"结构存在的证据"。

**§5 结果审一句话：R197 v2 的 `inconclusive` 被 002+003 机械正确应用（B-D3、B-D5 两项体检失败；Δ CI/p 好看但不认证；B-D3 的逐列样本量门槛**确为协议缺陷**——记录为 limitation/下一版分离 coverage、U/V 非退化、mask 模拟的预注册修订项，本版不改判；B-D5 独立失败使 verdict 对 B-D3 修复也稳健）；SHA/确定性、A0 状态与 1.43% 措辞、type-I CP（0/30=0.0950）与配对 bootstrap 均核验通过——判 PASS（可解释，主结果仅描述性）；仅需 2 条记录级更正（B-D3 limitation 写法、报告 wall/run2-vs-run3 的 telemetry 表述），不重跑、不改 verdict。**

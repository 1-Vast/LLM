# R200-D5 报告：早期状态→晚期响应的时间预测边界（资格 + 设计）

2026-10-27 ｜ 执行：cellstate-lit（task-88） ｜ 状态：**完成资格与设计；不运行效果、不拟合预测、不读表达/响应**。
交付：`PROTOCOL_D5.md`（DRAFT）、`d5.py`（metadata-only 资格/切分设计）、`d5.json`（机器可读）、本文、`record_d5.md`、`usage_d5.json`。
背景：`research/2026-10-27-innovation-round-r200/BRIEF.md`（R200 纪律）；`direction-mechanism-expansion/{report.md:35,50,57; mechanisms_v3.md; latest_evidence.md:39}`；旧 A3v2（`2026-10-27-innovation-scouting/dynamic_route/`）**仅背景**，不复用其未认证部分。

## 0. 结论

1. **D5 的分子代理分支：`qualified_with_conditions`。** 本地 Mix-seq 可做 **6h→24h 晚期分子（RNA）** 的群体层开发预测：285 键 / 115 细胞系；合法药物（时间匹配 control + 每键 ≥20 QC-normal 细胞）细胞系 **BRD3379 95 / Bortezomib 22 / Idasanutlin 24 / Trametinib 24**；Trametinib 5 时点（3/6/12/24/48h + 时间匹配 DMSO，24 线）为 **探索**（严格匹配后各对比仅 15–19 线）。
2. **功能分支：`not_qualified`（`data_unavailable`）。** 本地资产**无任何晚期功能终点**（viability/apoptosis/再生长/存活），也**无同一细胞**的早–晚配对（破坏性快照；obs index 全唯一）。**RNA 代理 ≠ 功能终点。**
3. **时间轴严格性：`unverified`。** 无 batch/plate/run/曝光列；6h channel 全缺失、24h 部分缺失且与 6h 不重叠；hashed 臂每个 (treatment,time) 仅 1 个样本标签（无重复样本）。**不能把 6h/24h 差异直接当绝对时间效应/同板同批配对。**
4. **不建议本轮运行效果。** 预运行 MDE 上界已显示 V1 的 Bortezomib/Idasanutlin/Trametinib（n=22–24）与 V2（n=15–19）**很可能在 G3 判 `evaluation_cannot_distinguish`**（需跨模型误差相关 0.985–0.991，见 §3.3）。门的意义是阻止"比均值好一点点"被写成增量，而不是预测阴性。
5. **建议：提交独立挑战（是）。** 挑战通过前不运行；功能/决策主张需新测量（§5）。A3 v1/v2 未被修改。

## 1. 资源资格逐项（metadata-only；数字见 `d5.json` / `d5.py`）

### 1.1 早期时点与晚期终点是否同时存在且同一细胞/干预

| 项 | 结果 | 判定 |
|---|---|---|
| 早期 RNA（6h） | 33,072 细胞；4 药+control | ✅ 可支撑分子预测 |
| 早期形态/成像 | 无 imaging/morphology 列/`obsm` | ❌ 缺失 |
| 晚期分子 RNA（24h） | 101,610 细胞 | ✅ 可支撑（分子代理） |
| 晚期功能（viability/凋亡/再生长/存活） | obs/var 无功能列；`obsm/layers/uns` 空 | ❌ **缺失 → 功能分支 not_qualified** |
| 同一细胞（6h 与 24h 同细胞） | obs index 182,875 全唯一；无 lineage/cell_id 列 | ❌ **破坏性快照，非同细胞** |
| 同一干预同键 | 285 键同名 perturbation 在 6h/24h | ✅ 键级匹配 |
| 时间匹配 control | control 在 6h/24h 各 115 键 | ✅ 存在（载体身份另见 1.2） |

### 1.2 暴露 / 剂量 / 批次 / 独立培养

| 项 | 观测 | 判定 |
|---|---|---|
| 暴露时长/起始同步 | 无 exposure/duration 列；`time` 只是收割标签 | **缺失/未认证** |
| 剂量 | 每 6/24 药臂单值：BRD3379 0.0、Bortezomib 2.5、Idasanutlin 2.5、Trametinib 0.1、control 0.0 µM；**BRD3379=0.0 与处理矛盾**；hashed 臂（含 DMSO 标签）dose=0.1 | **需清洗/未认证** |
| batch/plate/run/donor | 无任何批次/板列 | **缺失** |
| channel | 6h 全缺失；24h 63,754/101,610 缺失；6h 与 24h 无共同 channel | **不能作同批代理** |
| 重复/独立培养 | 无 replicate/donor/passage 列；hashed 臂每条件 1 个样本标签 | **无重复样本** |

### 1.3 时间轴严格性（同板同批）

- 无 plate/batch/run 列；6h channel 全缺失、24h 部分有且不重叠 → **同板同批配对不可认证**。
- hashed 多时间臂"每个 (treatment,time) 一个 hash 标签"符合 multiplex 设计意图，但**无 run ID 可核**，不能据此认证同批。
- 混合时间标签 48,193 细胞（Trametinib 20,028 + CRISPR 28,165）；Tram 臂 per-cell 时间/处理可从 `hash_assignment` 恢复（single-tag 17,553），CRISPR 不用于 D5。
- **判定：`time_axis_unverified`；禁止绝对时间过程/同板同批/同细胞轨迹主张。**

### 1.4 缺失与重复

- V1：285 键 / 115 系；≥10 normal 键 **282/285**；前药每键 ≥20 normal：BRD3379 97、Bortezomib 22、Idasanutlin 24、Trametinib 24、control 112；**药物键+时间匹配 control 均 ≥20 → 95/22/24/24 系**。
- V2：20,028 → 17,553 single-tag（13,713 normal）；24 系；严格匹配后各对比 **n=15–19**（<20 → exploratory）。
- QC：normal 155,164/182,875（84.85%）；无样本重复。

### 1.5 功能结局：**RNA 代理 ≠ 功能终点**

- 本地 h5ad 无功能终点；候选择资源（PRISM / Tahoe / kinetic_horizon / GDSC / BeatAML）**均不是同一 Mix-seq 细胞×干预×时间点的晚期功能读数**（只作文件名/大小级盘点，未读内容）。
- 本地缺失不等于原始公共研究没有其它输出；本资格只针对本地 scPerturb h5ad。
- **功能/决策主张当前停止。**

## 2. 资格判定

| 分支 | 判定 |
|---|---|
| 早期 RNA → 晚期 RNA（同键、非同细胞；6h→24h；V1 4 药） | **qualified_with_conditions**（开发层） |
| 早期 RNA → 晚期 RNA（V2 Tram 5 时点；两早时点增量） | **qualified_with_conditions（exploratory only）** |
| 早期 RNA → 晚期功能 | **not_qualified**（`data_unavailable`） |
| 同板同批/暴露/独立培养认证 | **not_qualified/unverified**（`time_axis_unverified`） |
| **整体 D5** | **qualified_with_conditions（仅分子代理开发层；不进入候选/L2）** |

**conditions（写死）**：① 只做 6h→24h RNA→RNA 开发与 V2 探索；② 无功能终点，RNA 代理不是存活/再生长；③ 无同细胞早–晚配对；④ 无 batch/曝光/同板认证；⑤ 无样本重复/独立培养；⑥ 不得做绝对时间过程/轨迹/机制/迁移/决策收益/新颖性主张。

## 3. 严格时间预测设计（DRAFT；详见 `PROTOCOL_D5.md`）

### 3.1 问题与比较器

- **H-D5-1（V1，confirmatory-development）**：6h early state → 24h molecular effect，预测跨细胞系排序是否优于 static（无时间）与均值；主统计量 `mean_d [ρ(early6h)−ρ(static)]`（4 药等权）。
- **H-D5-2（V2，exploratory）**：**6h+12h vs 6h**（目标 24h/48h）的信息增量；capacity control（同维随机/第二时点打乱）不得复现增量；n=15–19<20 → 只描述。
- **H-D5-3（描述）**：`gap = ρ_oracle − ρ_early`；gap ≤ MDE80 → 精度内足够；gap > MDE80 且 Δ≥δ_min → 有信息但不足。
- **强基线**：mean、static、cell identity、线性 ridge、充分调参树/GBM（R200 BRIEF 基线要求）、GP、单早时点、两早时点；oracle 只作上界。
- **零模型**：均值、cell-shuffle、drug-shuffle（V1）、time-shuffle（V2）、capacity control（V2）、future-leak sentinel（阳性对照）、static-capacity。

### 3.2 切分与泄漏防护（写死）

- 单元 = 细胞系；V1 leave-cell-line-out 5 折（排序后 `index%5`）；内层按细胞系分组；标准化/PCA/基因集/λ 只在训练折。
- **目标时间/未来时间绝不入输入**；**V1 禁止"两快照拼接"臂**（C3 类只在 V2 且输入严格早于目标）；V2 目标 24h 输入只能来自 3/6/12h，目标 48h 输入只能来自 3/6/12/24h（3h 无更早输入，不作目标）。
- 折/种子（20261027）/清单 SHA 已冻结（`d5.json:split_design`，manifest `c258f5b0…`）。
- 同批/同板未认证 → 只作群体开发预测，不作时间效应解释。

### 3.3 判定门（冻结；先测后比）

- **δ_min = 0.10**（Δ Spearman；运营定义：n=15–95 时约对应 top-5 名单 1–2 位置稳定改变；不得事后改）。
- **G0 资格**：V1 每药 ≥20 线（95/22/24/24 通过）；V2 每对比 ≥20（15–19 → exploratory_only）。
- **G1 split-half 可靠性** `rho_sb ≥ δ_min+MDE80`；**G2 room** `≥max(δ_min,MDE80)`；**G3 MDE80** `≤δ_min`；**G4 主效应**（V1，点≥δ_min 且 CI>0）；**G5 泄漏审计**一票否决。
- **预运行 MDE 上界（冻结）**：`2.802·sqrt(2/(n−1))` → V1 n=95/22/24/24 = **0.409/0.865/0.826/0.826**；V2 n=15–19 = **0.93–1.06**。达到 δ_min=0.10 所需跨模型误差相关：V1 **0.940/0.987/0.985/0.985**；V2 **0.989–0.991**。→ **V1 的 24 线级与 V2 很可能 G3 失败**（判 `evaluation_cannot_distinguish`；不写阴性）。
- **判定语义**：G1–G3 失败 → `evaluation_cannot_distinguish`；G0 → `data_unavailable`；G5 → `design_invalid`；G4 失败 → `no_increment`；全过 → `development_increment_present`（只表达层开发）。V2 只 `exploratory_only`。

### 3.4 指标

- 主：within-drug 跨细胞系 Spearman（V1 4 药等权平均）；V2 配对 Δρ。
- 副：MAE/RMSE（标准化效应）、基因级 Spearman、top-k 恢复、校准；决策选择描述性指标**不称决策收益**。
- 充分性 gap 描述；room/MDE 先于主效果报告。

## 4. 失败类别与停止条件（摘要；全文见协议 §9）

`data_unavailable`（功能/资格）、`design_invalid`（泄漏/时间顺序/折）、`evaluation_cannot_distinguish`（G1–G3）、`no_increment`（G4 早期≈static）、`exploratory_only`（V2）、`time_axis_unverified`（同板/曝光/同细胞）、`functional_route_not_qualified`、`identifiability_unsupported`（轨迹）。
停止：任一门失败即停；不换端点/阈值/切分；不补造中间时点；不把 L1 升级 L2/候选；阴性不写不存在。

## 5. 缺口（不回避）

1. **无匹配晚期功能读数** → 功能/决策分支 `not_qualified`；需同细胞×同药×同剂量×6/24/48h 的 viability+凋亡/再生长、时间匹配 vehicle、≥3 复孔 × ≥2 独立培养。
2. **无同细胞早–晚配对**（破坏性快照）→ 不能做个体轨迹；需 lineage/live imaging 或多时点配对读出。
3. **无 batch/plate/run/exposure/重复** → `time_axis_unverified`；不能作绝对时间效应/同板同批/独立培养主张；需补元数据或新实验。
4. **V2 严格 n=15–19 <20** → 只 exploratory；两早时点增量不能出确认性判定。
5. **预运行 MDE 上界高** → V1 的 24 线级药与 V2 很可能不可分辨；这本身是设计结论，不应用"换指标"制造可分辨。
6. **不声称新颖性/机制/迁移/决策收益/真实轨迹**；A3v2 仅背景、不复用未认证部分。

## 6. 结论与建议

- **D5 可作为"另问"L1 开发资产保留**：仅限 6h→24h 晚期分子（V1 4 药，95/22/24/24 线）与 Trametinib 5 时点探索（V2，15–19 线）。
- **本轮不运行效果**（任务要求；且预运行上界提示高失败风险）。
- **建议提交独立挑战（是）**：审资格条件、L1 门、切分/泄漏防护、基线、失败类别/停止条件；挑战通过后才可另立任务运行。
- **不进入候选冻结、不进入 L2 决策层、不重开 R196v2/R197v2**；功能/决策主张等新测量。

## 7. 确定性/边界/SHA

- `d5.py` 两次运行 `d5.json` 逐字节一致：`d5.py` SHA `1422cb547c1f27cc7eaa04e97cc9a53fb28583646c9dff52b303cadf4dd2dce1`；`d5.json` SHA `823307432aedde95b7fa484224b7fff9aa01c1f827d0f962982e9a2862229624`（54,249 B）；折清单 SHA `c258f5b0467d992e823e3999133bb20a453a84ab2478d1434f4f60ce62df78b3`；种子 20261027。
- 输入：h5ad SHA `94a72400…`（1,459,410,830 B）；metadata-only：**未读 `X` 值/obsm/layers，未读响应，未拟合预测，未联网**。
- 未改其它目录/INDEX/git；只写 `d5_temporal/` 与 `tmp/`。旧 A3 文件未改（本任务未触碰）。

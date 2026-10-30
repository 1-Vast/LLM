# R200-D5 记录（record_d5）

2026-10-27 ｜ 执行：cellstate-lit（task-88） ｜ 工作目录：`D:\MAESTRO`。
对象：R200 方向 5「早期状态对晚期响应的时间预测边界」——本地时间分辨资源 metadata-only 资格 + 严格时间切分设计。**本轮不运行效果、不拟合预测、不读表达矩阵或响应数值。**

## 0. 纪律与范围

- 只写 `research/2026-10-27-direction-mechanism-expansion/d5_temporal/`（`PROTOCOL_D5.md`、`d5.py`、`d5.json`、`report_d5.md`、`record_d5.md`、`usage_d5.json`）与 `tmp/`；**未改其它目录/INDEX/git/A3 文件**。
- 禁止项执行：未训练模型、未拟合任何预测器、未运行效果/相关性统计、未读 h5ad `X` 数值/obsm/layers、未读任何响应或功能矩阵、未联网。
- 所有数据类数字来自 `d5.py` 对 h5ad **obs/var 元数据**的计数；其它本地资源只做**文件名/字节数**级盘点（未读内容）。

## 1. 读过什么

| 输入 | 用途 | 证据状态 |
|---|---|---|
| `research/2026-10-27-innovation-round-r200/BRIEF.md` | R200 纪律/任务边界（D5=设计/资格，独立挑战后才可运行） | 已读 |
| `research/2026-10-27-direction-mechanism-expansion/report.md`（D5 行 :35/:50/:57） | D5 方向定义、最小判别与停止条件 | 已读 |
| `.../mechanisms_v3.md` | 机制候选边界（D5 不属于 M1–M4 机制验证） | 已读 |
| `.../latest_evidence.md:39`（Q5 行） | D5 当前入口与数字（95/22/24/24、V2 15 线、L2 blocked） | 已读 |
| `research/2026-10-27-innovation-round-r199/BRIEF.md` | R199 纪律/资格门背景 | 已读 |
| `research/2026-10-27-conditional-shift/ERRATA_A3.md` | R195/A3 的 `not_qualified` 范围限制（不关闭较窄问题） | 已读 |
| `research/2026-10-27-innovation-scouting/dynamic_route/{a3_inspect.py,a3_meta.json,qualification.md,spec.md,protocol_draft_v2.md,REVISION_A3.md,challenge_A3.md,cadence_evidence.md}` | **旧 A3v2 仅背景**；D5 资格独立复算；不复用未认证部分 | 已读/哈希 |
| `data/external/mixseq_scperturb/mcfarland_2020.h5ad` **obs/var 元数据** | D5 资格：早期/晚期、同细胞、暴露/剂量/批次、时间轴、缺失/重复、合格单元 | metadata-only |
| 本地数据目录（mixseq/tahoe/kinetic_horizon/PRISM/GDSC/BeatAML 等） | 功能终点候选**文件级盘点**（路径/字节/文件数；不读内容） | metadata-only |
| `data/INVENTORY.md` | MIX-seq/Tahoe 资产类型（molecular/pseudobulk/relative-survival derived；模型预测非新测量） | 已读 |

**未读**：h5ad 表达值；PRISM/Tahoe/GDSC/kinetic_horizon 的任何响应/功能矩阵内容；其它研究目录的 effect 结果。

## 2. 做了什么

### 2.1 `d5.py`（metadata-only；确定性）

- 读取 h5ad `obs/var` 元数据与 `X` 形状；检查列存在性（功能/形态/同细胞链接/暴露/批次/重复）。
- 复算：精确 6h/24h 键（285）、115 细胞系、per-drug 键数、每键 QC-normal 细胞数、≥10/≥20 门槛；per-drug 合法（药物键+时间匹配 control 均 ≥20）细胞系 = **95/22/24/24**；control 112 线。
- 复算 hashed Trametinib 5 时点臂：分类 `hash_assignment`（single 17,553 / combo 2,339 / missing 136；normal 13,713）；24 线；每个 (treatment,time) 恰 1 个样本标签（**无重复样本**）；严格匹配后 V2 对比 n=15–19（<20 → exploratory）。
- 检查"同一细胞"：obs index 182,875 全唯一 → 无 barcode 同时出现于 6h/24h；无 lineage/cell_id 列。
- 检查"同一干预"：285 键同名 perturbation 在 6h/24h（键级匹配，非同细胞）；control 时间匹配存在（6h/24h 各 115 键）。
- 检查暴露/剂量/批次：无 exposure/duration 列；无 batch/plate/run/donor；6h channel 全缺失、24h 部分缺失；剂量单值且 BRD3379=0.0 矛盾；hashed 臂 dose=0.1（含 DMSO 标签，字段冲突）。
- 检查功能终点：h5ad 无任何功能列/层；本地候选资源仅作文件级盘点，无同一 Mix-seq 细胞×干预×时间的晚期功能读数。
- 生成冻结的折清单（V1 per-drug 5 折；V2 每对比 5 折；种子 20261027；manifest SHA）与预运行 MDE 上界/所需 r_err。
- 输出 `d5.json`（54,249 B；sort_keys、无时间戳；两次运行逐字节一致）。

**未做**：任何模型拟合/预测/相关性/效应计算；任何表达值读取；network。

### 2.2 设计（`PROTOCOL_D5.md`，DRAFT）

- 明确 V1（confirmatory-development，6h→24h 分子；4 药）与 V2（exploratory，Tram 5 时点；两早时点增量）。
- 强基线（mean/static/identity/ridge/tree-GBM/GP/单早/两早/oracle）、切分（细胞系分组 LOO；V2 目标固定、输入严格更早）、泄漏防护（G5）、零模型（cell/drug/time shuffle、capacity、future-leak sentinel）。
- 冻结令：δ_min=0.10；G1 split-half、G2 room、G3 MDE80、G4 主效应、G5 泄漏审计；失败类别/停止条件；数据规格（若升级功能/绝对时间）。
- 明确：功能分支 `not_qualified`（无匹配晚期功能）；时间轴 `unverified`；D5 不进入候选/L2、不重开 R196v2/R197v2、不声称新颖性/机制/迁移/决策收益。

## 3. 关键结果（全部 metadata-only）

| 项 | 结果 |
|---|---|
| h5ad | 182,875 细胞 × 32,738 基因；obs/var 元数据；无功能/形态/链接/曝光/批次/重复列；`obsm/layers/uns` 空 |
| 早期/晚期 RNA | 6h 33,072 细胞；24h 101,610 细胞 |
| 晚期功能 | **无**（功能分支 not_qualified；RNA 代理≠功能） |
| 同细胞早–晚 | **无**（obs index 全唯一；破坏性快照） |
| V1 键/细胞系 | 285 键/115 系；≥10 normal 282/285；drug+control ≥20 的合法线 95/22/24/24（BRD3379/Bortezomib/Idasanutlin/Trametinib） |
| V2 hashed 5 时点 | 17,553 single-tag（13,713 normal）；24 线；每条件 1 样本标签（无重复）；严格匹配后 n=15–19（<20 → exploratory） |
| 暴露/剂量/批次 | 无 exposure/批次；剂量单值且 BRD3379=0.0 矛盾；channel 6h 全缺失、24h 部分缺失 |
| 时间轴严格性 | **unverified**（同板/同批不可认证） |
| 预运行 MDE 上界 | V1 n=95/22/24/24 → 0.409/0.865/0.826/0.826；V2 n=15–19 → 0.93–1.06；所需 r_err 0.940/0.987/0.985/0.985、0.989–0.991 |
| 判定 | 分子分支 qualified_with_conditions；功能分支 not_qualified；整体 D5 qualified_with_conditions（仅分子代理开发层） |

## 4. 验证

```text
d5.py 最终连续两次运行，d5.json 逐字节一致：
  d5.json SHA256 823307432aedde95b7fa484224b7fff9aa01c1f827d0f962982e9a2862229624 (54,249 B)
  d5.py   SHA256 1422cb547c1f27cc7eaa04e97cc9a53fb28583646c9dff52b303cadf4dd2dce1 (36,857 B)
split manifest SHA256 c258f5b0467d992e823e3999133bb20a453a84ab2478d1434f4f60ce62df78b3
json.load(d5.json) OK；未读表达/响应；未拟合；未联网
```

**无**任何效果/预测计算；以上仅为元数据计数、文件哈希与确定性检查。

## 5. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_D5.md`（新，DRAFT） | 21,542 | `3923fe7d31904d3629d191677793f3d6a9c36cb4f3e66314ca955834623711a7` |
| `report_d5.md`（新） | 11,989 | `c94e0f9f8ac5e6a6f3bb635eeacdfbf688ab2bdf403c6eff0190029cccf561e0` |
| `d5.py`（新） | 36,857 | `1422cb547c1f27cc7eaa04e97cc9a53fb28583646c9dff52b303cadf4dd2dce1` |
| `d5.json`（新） | 54,249 | `823307432aedde95b7fa484224b7fff9aa01c1f827d0f962982e9a2862229624` |
| `record_d5.md`（本文件） | — | 不自我内嵌（见 `usage_d5.json`） |
| `usage_d5.json`（新） | — | 见文件 |

**未改**：A3v1/v2 全部文件、`2026-10-27-innovation-round-*`、`direction-mechanism-expansion/{report.md,mechanisms_v3.md,latest_evidence.md,...}`、`INDEX/SYNTHESIS/git`、`src/`。

## 6. 决定与理由

1. **整体判 `qualified_with_conditions` 而非 `not_qualified`**：D5 的可执行版本（6h→24h **分子**）有合法键、控制与足够细胞数（95/22/24/24）；但功能分支与时间轴严格性都不合格，因此条件写死并禁止功能/绝对时间/轨迹主张。
2. **V2 只 exploratory**：严格匹配后 n=15–19<20，不能出确认性判定；两早时点增量只作描述。
3. **不建议本轮运行**：预运行 MDE 上界大（24 线级需跨模型 r_err≈0.985–0.987 才可能 ≤δ_min），很可能 `evaluation_cannot_distinguish`；先独立挑战，避免"高成本低判别"运行。
4. **不复用 A3 未认证部分**：D5 的键数/合格线/功能缺失/时间轴均由 `d5.py` 独立复算；A3 仅作背景引用（其自身 L2 也被功能/批次阻塞）。
5. **保留"阴性≠不存在"与模板**：失败只写 `evaluation_cannot_distinguish`/`no_increment`/`data_unavailable`；不写"动态信息不存在"；不声称新颖性/机制/迁移/决策收益/真实轨迹。

## 7. 限制 / 未完成

- 未运行 L1（任务禁止；且预运行上界提示高失败风险）；所有门是"冻结后运行"的规则。
- 功能终点、同细胞配对、batch/exposure/独立培养均缺；需新测量（协议 §10）。
- V2 n<20 → exploratory；不能作跨药推断（单药 Trametinib）。
- 本地资源只做文件级盘点；不声称原始公共研究其它输出不存在。
- 设计尚未经独立挑战；R200 BRIEF 要求挑战通过后才可运行。

## 8. 下一执行者从哪里开始

1. 读 `PROTOCOL_D5.md`（§2 资格、§3 假设、§6 切分/泄漏、§8 判定门、§10 数据规格）与 `report_d5.md`（结论/缺口）。
2. **提交独立挑战**（建议：是）：审资格判定、L1 门/MDE、切分/泄漏防护、强基线、失败类别/停止条件；挑战通过前**不运行**。
3. 若挑战通过并获准运行：另立任务，按 `d5.py` 冻结的折清单/门运行（仍只分子层；不改 δ_min/切分）；先报 G1–G3，再报 G4。
4. **功能/决策/轨迹主张停止**：等 `PROTOCOL_D5.md` §10 的数据；不换名重启；不重开 R196v2/R197v2。

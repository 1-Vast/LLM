# R200-D5.1 修订协议：早期状态→晚期响应（PROTOCOL_D5_v0.2，DRAFT）

2026-10-27 ｜ 执行：cellstate-lit（task-96） ｜ 状态：**DRAFT（按 challenge_D5.md 的 revise/5 必改修订；仍未运行效果）**。
上游：`challenge_D5.md`（endpoint-auditor：`revise`，5 必改；当前 `approve_to_lead_exec = false`）；v0.1：`PROTOCOL_D5.md` / `d5.py` / `d5.json` / `report_d5.md` / `record_d5.md` / `usage_d5.json`（**冻结不改**，本文件取代其 primary/门/表述）。
本轮只做**文档/资格/设计修订**：不运行效果、不拟合预测、不读表达或响应矩阵；不声称新颖性/机制/迁移/决策收益。
机器可读修订结果：`d5_v0_2.json`（`d5_revision.py` 生成；两次运行逐字节一致）。

---

## 0. 相对 v0.1 的必改（挑战 5 条）

| # | 挑战必改 | v0.2 状态 |
|---|---|---|
| 1 | **BRD3379 = 0.0 µM 不能算 V1 第四药** | **已改**：V1 primary 仅 **3 个 active drugs**（Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24）；BRD3379 仅作 **zero-dose/vehicle-like control（secondary/descriptive）**；**撤回"4 drugs n≥20 confirmatory"** |
| 2 | V2 `paired_n=2` 字段错误 | **已改**：配对细胞系数 target24h E1/E2=**15**；target48h E1/E2=**16**、E2/E3=**15**；以 paired line sets 为准；v0.1 bug 已在 JSON 记录 |
| 3 | G0 加 active dose/处理身份门 | **已改**：**G0a 覆盖门 + G0b active-dose/identity 门**；3 active drugs 为 **metadata-level conditional pass**；BRD3379/control **fail**，BRD3379 排除出 primary |
| 4 | 更新 4 药表述/MDE/primary 并重算 SHA | **已改**：MDE 表仅 Bortezomib 0.865 / Idasanutlin 0.826 / Trametinib 0.826；v0.2 新文件 + SHA 记录；v0.1 文件不改 |
| 5 | 执行协议前细节清单 | **已补**：§11 E1–E12（加载/QC/pseudobulk/200 gene panel/fold loader/paired sets/零模型+未来哨兵/B1–B8 调参/两跑 schema/measured MDE 预认证/失败模板/G5 断言）；**本轮不运行** |

---

## 1. 范围与问题（不变）

- **D5 问题**：一个早期表达快照何时足够预测晚期响应？额外早期时点增加什么信息？失效域在哪？
- **可执行版本（仅分子代理）**：
  - **V1（confirmatory-development，3 active drugs）**：6h → 24h 晚期 **RNA** 效应；Bortezomib/Idasanutlin/Trametinib；n=22/24/24 合法细胞系。
  - **V2（exploratory only）**：Trametinib 5 时点（3/6/12/24/48h + DMSO）；比较"单早期快照 vs 两早期快照"的信息增量（目标 24h/48h；输入严格更早）；各对比 n=15–19<20 → 无判定权。
- **功能分支**：`not_qualified`（data_unavailable；无晚期功能终点）。
- **排除**：晚期功能/轨迹/同细胞配对/绝对时间过程/机制/迁移/决策收益/新颖性；A3v2 仅背景；不重开 R196v2/R197v2。
- **BRD3379**：**不是 active drug**；只是 zero-dose/vehicle-like control（0.0 µM、无 ChEMBL 注释）；**不进入任何 V1 primary 均值**；只在 secondary/描述中出现并强制标注。

---

## 2. 资格（v0.2 修订版；数字见 `d5_v0_2.json`）

### 2.1 Active-dose / treatment-identity 门（挑战必改-1/3）

| arm | dose | unit | ChEMBL | active-dose/identity check | 角色 |
|---|---|---|---|---|---|
| **Bortezomib** | 2.5 | µM | CHEMBL325041 | **conditional pass（metadata-level）** | active primary |
| **Idasanutlin** | 2.5 | µM | CHEMBL2402737 | **conditional pass（metadata-level）** | active primary |
| **Trametinib** | 0.1 | µM | CHEMBL2103875 | **conditional pass（metadata-level）** | active primary |
| BRD3379 | **0.0** | µM | —（无） | **fail** | **zero-dose/vehicle-like control；secondary only；排除出 primary** |
| control | 0.0 | µM | —（无） | fail（reference） | 时间匹配参照 |

- **认证等级（必须写死）**：metadata-level = `dose>0 + dose_unit + ChEMBL annotation`；**不是**独立剂量/化合物/vehicle identity 测定。**执行协议必须重新核验化合物 identity、实际剂量、vehicle** 后才能运行。
- **G0b 的结果**：3 active drugs = "conditional pass (metadata-level)"；BRD3379/control = fail；**BRD3379 未核前不 pass**（满足挑战要求）。
- **因此**：v0.1 的"BRD3379 95 线"数字仍保留为 **secondary/zero-dose control 的描述**，不再有 primary 权重。

### 2.2 V1 primary（3 active drugs；挑战必改-1/4）

- Active primary = **Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24**；各自使用自己的合法线集合（不同集合，**不是跨药配对**）。
- 主统计量 = **3 个 active drug 的 Δρ_d 等权平均**（每药 n 独立；报告 per-drug CI 与 drug-level range）。
- **BRD3379 不进入任何 primary 均值/CI/状态**；输出中强制标注 `BRD3379 zero-dose/vehicle-like control (not active)`。
- **MDE 预运行上界（active only）**：Bortezomib **0.865**（n=22）、Idasanutlin **0.826**（n=24）、Trametinib **0.826**（n=24）；达到 δ_min=0.10 所需跨模型误差相关 **0.987/0.985/0.985**。
- **v0.1 的 4 药 primary / "4 drugs n≥20 confirmatory" 已撤回**；v0.1 文件保留但不作运行依据。

### 2.3 V2 paired 修正（挑战必改-2）

| target | E1 | E2/E3 | n_E1 | n_E2 | n_E3 | **paired cell lines** |
|---|---|---|---|---|---|---|
| 24h | inputs 6h | E2 = 6h+12h | 18 | 15 | — | **15（E1∩E2）** |
| 48h | inputs 6h | E2 = 6h+12h；E3 = 6h+12h+24h | 19 | 16 | 15 | **16（E1∩E2）；15（E2∩E3）** |

- `paired_n` 语义 = **配对细胞系数量**（交集），不是 `len(dict)`；v0.1 的 `paired_n=2` 是字段 bug，已在 `d5_v0_2.json:v2_corrected.v0_1_bug` 记录旧值 [2,2,2] 与正确值 [15,16,15]。
- 配对线名单精确列表见 `d5_v0_2.json:v2_corrected.paired_line_sets`；**执行时只在这两个/三个集合的交集上计算 Δρ**，不得用全 n 当配对 n。
- **V2 仍 exploratory only**（n<20）；不作跨药推断。

### 2.4 其余资格（不变）

- 6h 33,072 细胞 / 24h 101,610 细胞；obs index 182,875 全唯一 → **无同细胞早–晚配对**（破坏性快照）。
- 285 键名称级共享；control 6h/24h 各 115 键（时间匹配对照；载体身份未认证）。
- **无晚期功能终点**：h5ad obs/var 无 viability/apoptosis/regrowth/IC50/response；`obsm/layers/uns` 空；**RNA 代理 ≠ 功能终点**。
- 无 exposure/duration、batch/plate/run/donor 列；6h channel 全缺失、24h 部分缺失；hashed 臂每 (treatment,time) 1 样本标签（**无重复样本**）→ **time_axis_unverified**。
- V1 键级覆盖：≥10 normal 282/285；active drugs 合法线 22/24/24；BRD3379 secondary 95 线仅作控制。
- V2：17,553 single-tag（13,713 normal）；24 线；严格匹配后 n=15–19。

### 2.5 判定（v0.2）

| 分支 | 判定 |
|---|---|
| V1 早期 RNA → 晚期 RNA（3 active drugs） | **qualified_with_conditions**（confirmatory-development，仅 3 active drugs） |
| V2 两早时点增量 | **qualified_with_conditions（exploratory only）** |
| 早期 RNA → 晚期功能 | **not_qualified（data_unavailable）** |
| 同板同批/暴露/独立培养 | **not_qualified/unverified（time_axis_unverified）** |
| BRD3379 | **zero-dose/vehicle-like control；secondary/descriptive only；不得进入 primary** |
| **整体 D5** | **qualified_with_conditions（仅 3 active drugs 的分子代理开发层；`approve_to_lead_exec=false`，需再挑战）** |

---

## 3. 可证伪假设（v0.2）

| 假设 | 内容 | 最小判别 | 反例/失败 |
|---|---|---|---|
| **H-D5-1**（V1，3 active drugs） | 6h 早期状态对 24h 晚期 RNA 效应的跨细胞系预测优于 static/mean | `mean_{d∈3 active} Δρ_d`；点≥δ_min 且 95% CI 下界>0；G0–G5 全过 | 早期≈static → `no_increment`；G1–G3 不过 → `evaluation_cannot_distinguish` |
| **H-D5-2**（V2 exploratory） | 增加一个更早快照（6h+12h vs 6h）提高对 24h/48h 晚期 RNA 的预测 | 配对 Δρ 仅在 **paired sets（15/16/16）** 上计算；capacity 对照不得复现 | 无增量/仅容量增量 → 单早时点足够；n<20 → 只描述 |
| **H-D5-3**（描述） | 单早快照充分性 gap = ρ_oracle−ρ_early | gap≤MDE80 → 精度内足够；gap>MDE80 且 Δ≥δ_min → 有信息但不足 | oracle 估不准/room<MDE → 不可分辨 |
| **H-D5-F**（功能） | 6h 预测 24h/48h 功能 | **本地不可检验** | `data_unavailable`；RNA 代理不能替代 |
| **H-BRD3379（secondary）** | BRD3379 作为 zero-dose/vehicle-like control 的晚期 RNA 轨迹（描述） | 仅描述；**不进 primary** | 不用于任何 confirmatory 判定 |

---

## 4. 数据、端点与单元（不变）

- **单元**：细胞系（不是 key/细胞/时间点）。V1 active 每药 n=22/24/24；V2 每对比 n=15–19，配对 n=15/16/15。
- **目标 y（晚期 RNA）**：QC-normal 细胞 pseudobulk logFC（相对时间匹配 control）；train-only 冻结 top-K=200 基因的 logFC 均值（K=200；train-only 选择）；向量版副端点。
- **早期特征**：V1 = 6h logFC（同 200 基因面板）；V2 = 严格更早时点 logFC 拼接。
- **静态特征**：DepMap/CCLE basal expression（与 h5ad symbol 交集）；训练折内标准化/PCA/ridge。
- **BRD3379 secondary**：仅作 zero-dose/vehicle-like control 的晚期 RNA 描述；**不得进入 200 gene panel 的 primary 训练目标**（可作为额外描述性目标，但必须标注并与 primary 完全分开）。
- **禁止**：目标时间/未来时间进入输入、特征选择、标准化、调参；V1 不设两快照臂。

---

## 5. 比较器（同信息、同调参预算）

| 代号 | 模型 | 说明 |
|---|---|---|
| B0 | mean | 每药/时间训练线均值（组内 ρ=0） |
| B1 | static | CCLE/未处理特征（无时间） |
| B2 | cell identity | 细胞系 one-hot（留出细胞系退化为均值；参考） |
| B3 | linear ridge | 早期状态 → 晚期效应 |
| B4 | tree/GBM | 充分调参（库/网格执行前冻结；R200 BRIEF 强基线） |
| B5 | GP | RBF/类别核 |
| B6 | simple time model | **仅 V2**：更早时点线性时间外推 |
| B7 | single early | 单早时点 |
| B8 | two early | 两早时点（V2） |
| Oracle | late state | 真实目标时点状态（room/上界；非候选） |
| Functional | — | 本地不可得（not_qualified） |

---

## 6. 切分、泄漏与零模型（不变）

- **V1**：外层 leave-cell-line-out 5 折（合法线排序后 `index%5`；同线不跨折）；内层训练折内按线分组；标准化/PCA/基因集/λ 只在训练折。
- **V2**：目标固定；输入严格更早；外层 leave-cell-line-out；内层训练折内按线分组；3h 无更早输入不作目标。
- **折清单**：`d5_v0_2.json:folds_v0_2`（V1 active drugs 的 manifest SHA `0056d69e…`；BRD3379 secondary 单独列；V2 各对比）；种子 20261027。
- **G5 泄漏规则**：目标/未来时间绝不入输入；V1 禁两快照；折按细胞系；测试线不进预处理；代码级断言 + 未来哨兵 + 独立复核。
- **零模型**（设计）：N0 mean、N1 cell-shuffle、N2 drug-shuffle（V1）、N3 time-shuffle（V2）、N4 capacity control（V2）、N5 future-leak sentinel（阳性对照）、N6 static-capacity。

---

## 7. 指标

- V1 主：每药 `Δρ_d = ρ(early6h_d) − ρ(static_d)`（留出线跨线 Spearman）；主统计量 = **3 active drugs 等权平均**；per-drug CI + drug-level range。
- V2 主（exploratory）：配对 `Δρ=ρ(E2)−ρ(E1)`（仅 paired sets 15/16；target48h 另 E2/E3 15）；capacity 对照。
- 副：MAE/RMSE、基因级 Spearman、top-k、校准；决策选择描述性指标**不称决策收益**。
- 充分性 gap 描述；BRD3379 secondary 单独报告并标注 control 身份。

---

## 8. 判定门（v0.2 冻结）

- **δ_min = 0.10**（Δ Spearman；运营定义不变；不依赖未读表达值；不得事后改）。
- **G0a 覆盖**：每个 active primary drug ≥20 合法线（实际 22/24/24 → pass）。
- **G0b active-dose/identity**：dose>0 + dose_unit + ChEMBL annotation（metadata-level）；3 active drugs = **conditional pass（execution re-verification required）**；BRD3379/control = fail；**BRD3379 排除出 primary**。
- **G1 split-half 可靠性**：`rho_sb ≥ δ_min + MDE80`。
- **G2 room**：`room = ρ_oracle − ρ_static ≥ max(δ_min, MDE80)`。
- **G3 MDE80**：配对 Δ 的细胞系 cluster bootstrap（1,000 次，种子 20261027）；`MDE80 ≤ δ_min`。
  **预运行上界（active only）**：`2.802·sqrt(2/(n−1))` → Bortezomib **0.865**、Idasanutlin **0.826**、Trametinib **0.826**；所需 r_err **0.987/0.985/0.985**；V2 n=15–19 → 0.93–1.06 / r_err 0.989–0.991。→ **若无高度误差相关，V1 与 V2 很可能 G3 失败判 `evaluation_cannot_distinguish`**（不写阴性）。
- **G4 主效应**：3 active drugs 等权平均 Δ ≥ δ_min 且 95% CI 下界>0。
- **G5 泄漏审计**：§6 全过；否则 `design_invalid`。
- **语义**：G1–G3 任一失败 → `evaluation_cannot_distinguish`；G0a/G0b 失败 → `data_unavailable`/`active_dose_identity_unverified`；G5 → `design_invalid`；G4 失败 → `no_increment`；全过 → `development_increment_present`（仅表达层开发）。V2 只 `exploratory_only`。

---

## 9. 失败类别与停止条件（v0.2）

`data_unavailable` / `active_dose_identity_unverified` / `design_invalid` / `evaluation_cannot_distinguish` / `no_increment` / `exploratory_only` / `time_axis_unverified` / `functional_route_not_qualified` / `identifiability_unsupported`。
停止：任一门失败即停；不换端点/阈值/切分；不补造中间时点；不把 L1 升级 L2/候选；阴性不写不存在；**BRD3379 不得被用作 active drug 复活 4 药 primary**。

---

## 10. 若升级功能/绝对时间所需数据（不变）

同 v0.1 §10：匹配晚期功能（viability+凋亡/再生长；时间匹配 vehicle；≥3 复孔 × ≥2 独立培养）；暴露/时间轴/批次；重复；若轨迹需同细胞/谱系链接；决策层需动作/效用/δ_min/MDE。

---

## 11. 执行协议前细节清单（挑战必改-5；本轮只列，不执行）

| id | 内容 |
|---|---|
| **E1 数据加载** | h5ad obs/表达（执行时用 anndata 读 `X`，本轮不读）；QC=`cell_quality=="normal"`；pseudobulk per (drug,line,time)=mean；对照：V1=time-matched `perturbation=control`，V2=DMSO hash label；logFC=log2((pseudo+1)/(ctrl+1))；记录每条件细胞数；禁止按表达再做选择 |
| **E2 200 gene panel** | 每 drug/target/fold 只用**训练线**的 mean |logFC| 取 top-K=200；冻结 gene list SHA；测试线不进 panel；向量端点=同 200 基因 |
| **E3 fold loader/assert** | 加载 `d5_v0_2.json:folds_v0_2`；断言每药折恰好划分其合法线、同线不跨折、规则 `index%5`、种子/版本正确、manifest SHA 复算一致 |
| **E4 V1 paired sets** | V1 **不做跨药配对**：每 active drug 用自己合法线集合（22/24/24）；primary=3 drug-level Δρ 均值；报告 per-drug CI 与 drug-level range；BRD3379 不参与 |
| **E5 V2 paired sets** | 只在 paired sets 上算 Δρ：target24h E1/E2 n=15；target48h E1/E2 n=16、E2/E3 n=15；名单见 JSON；断言输入严格早于目标 |
| **E6 零模型/未来哨兵** | N0–N6（§6）；固定种子；置换次数 ≥200；N5 future-leak sentinel = 用目标时点特征替代早期特征，应接近 oracle；若不然则管道/指标失效（fail closed） |
| **E7 B1–B8 调参预算/网格** | 执行前冻结库/网格/候选数/内层折；每模型**相同调参预算**（同候选数 × 同内层折）；报告选中超参与预算计数；不得用测试折调参 |
| **E8 两跑/输出 schema** | 同种子跑两次；输出逐字节一致（无时间戳）；固定 schema：per contrast `{n, rho_early, rho_static, delta, CI, MDE80, room, reliability, gates, verdict}` + config/fold SHA + pseudobulk 数组 SHA |
| **E9 measured MDE 预认证** | G4 前先算 split-half 可靠性/room/measured MDE（cluster bootstrap 1,000 次，种子 20261027）；G1–G3 不过 → `evaluation_cannot_distinguish`，**不跑 G4**；记录实测值 |
| **E10 失败模板** | 记录 verdict_class、reason、失败门、实测值、**不声称什么**、所需数据；阴性≠不存在；禁止事后改门 |
| **E11 G5 代码断言** | 断言目标时间不在输入时间列表；V1 模型集不含两快照；折按细胞系；预处理只在训练折；无表达派生测试信息；未来哨兵；fail closed |
| **E12 本轮不运行** | 本轮无任何效果/预测/表达读取；执行需另立任务 + 独立挑战 |

---

## 12. 边界/A3/C/不做

- A3v2 `L1 feasible/L2 blocked` **仅背景**；D5 资格独立复算；不重用 A3 未认证部分。
- C176/C177/C179/C181/C186 仅背景；不重开 R196v2/R197v2；R195 ERRATA_A3 的范围限制保留。
- **不得声称**：新颖性、细胞状态机制、迁移、决策收益、真实轨迹、动态世界模型；BRD3379 不是 active drug；RNA 不是功能终点。
- 功能/决策需新测量；BRD3379/control 只作次级描述。

---

## 13. SHA / 确定性 / 再挑战

- v0.2 新产物：`d5_revision.py` **6a89039c7073782c71083d9095cc72172718ec374b84890e213788233057d199**（31,093 B）；`d5_v0_2.json` **d41ed20fc6a4545e2e8cada3b14702edd9c044093bfa4e1a018988358d207830**（32,951 B）；两次运行逐字节一致；V1 active primary fold manifest SHA **0056d69e4b6fbe515915008fd2f1a40213ea6a8837c7c673546bf76f901a52d2**。
- v0.1 六文件 + challenge_D5 的 SHA 作为输入登记在 `d5_v0_2.json:inputs_sha256`；**v0.1 文件未改**。
- **`approve_to_lead_exec = false`**；完成任务后建议**再提交独立挑战**（审 active-dose 排除、V2 paired、G0/G3、执行清单）；挑战通过后另立执行协议/任务，仍不运行效果直到批准。

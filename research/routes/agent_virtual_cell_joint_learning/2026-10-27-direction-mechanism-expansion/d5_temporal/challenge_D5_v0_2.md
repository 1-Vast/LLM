# R200-D5.1-C1 再挑战（challenge_D5_v0_2.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3/D5 同一独立挑战者；未参与 D5.1 修订）· 对象：`research/2026-10-27-direction-mechanism-expansion/d5_temporal/{PROTOCOL_D5_v0_2.md, d5_revision.py, d5_v0_2.json, report_d5_v0_2.md, record_d5_v0_2.md, usage_d5_v0_2.json}` + v0.1 历史。
方式：**只读复核**（文档/JSON/gates/E1–E12/差异/SHA；**不运行效果、不拟合预测、不读表达或响应矩阵**）；只写本文件与 `tmp/`。
完整性：protocol **`D1ABD7C6…`**；JSON **`D41ED20F…`**；report **`4B742A0D…`**；record **`BB4C5130…`**；usage **`910427F6…`**；`d5_revision.py` `6A89039C…`；V1 active manifest `0056d69E…`；v0.1 六文件 SHA 未变；均与磁盘实算一致。

## 0. 总判决

**reduce_to_descriptive（不建议 approve_to_lead_exec；不是直接 stop）。**
D5.1 的 5 条必改**主体已落实**：BRD3379 排除出 primary、3 active drugs 等权；BRD3379 标 zero-dose/vehicle-like control（secondary/descriptive）；V2 JSON 的 paired_n 已修为 **15/16/15**；G0b active-dose/identity 门（metadata-level conditional pass；BRD3379/control fail）；MDE 表 active only **0.865/0.826/0.826**；G3 高失败风险→evaluation_cannot_distinguish 诚实；E1–E12 已列。
**但当前不能批准为“confirmatory-development execution”**：
1. **协议 H-D5-2 仍有 typo**：`paired sets（15/16/16）`，与 §2.3/JSON/report/record/usage 的 **15/16/15** 不一致；这是 V2 配对语义的直接矛盾，必须修。
2. **G3 预运行上界 0.865/0.826/0.826 > δ_min=0.10**，达到 δ_min 所需跨模型误差相关 **0.987/0.985/0.985**；没有证据支持；执行 confirmatory H-D5-1 大概率只能记录 `evaluation_cannot_distinguish`。**不建议把 confirmatory 执行作为当前目标**。
3. **E1–E12 尚未达到可执行冻结度**：E6 零模型只写“≥200 permutations”（v0.1 冻结口径是 1,000，不能反向降）；E7 只说“执行前冻结库/网格”，没有具体 grid/trials；E1/E2/E3/E5/E8/E9/E11 较好，但 E6/E7 需补。若直接 approve，执行者会在运行前自由选择，违反预注册。

**建议路径：reduce_to_descriptive**——保留 **3 active drugs、V1 6h→24h 分子代理、V2 exploratory** 的**纯描述性**分析（per-drug Δρ/CI/MDE/room/reliability 全部报告，但不做 H-D5-1 confirmatory 检验、不设 G3/G4 通过/失败、不写 biology/decision）。若 Lead 要求的是 **confirmatory H-D5-1**，则应 **stop** 并记录所需测量规格（更多独立细胞系/配对误差验证/功能结局），不要用“执行一次记录不可分辨”替代资格。

**最致命 3 条**

1. **H-D5-2 typo 15/16/16**（protocol line96）vs **15/16/15**（§2.3/JSON `v2_corrected`/report/record/usage）。V2 配对 n 是任务 ① 的必改核心；这个不一致直接使执行协议自相矛盾。必须改为 15/16/15，并全文检索无残留。
2. **G3 上界 .865/.826/.826 > δ=.10；r_err .987/.985/.985**。confirmatory H-D5-1 在 22/24/24 线上几乎不可能达到 MDE≤.10；**不能 approve confirmatory**；只能 reduce 描述性或 stop。`evaluation_cannot_distinguish` 的诚实不等于值得执行。
3. **E6/E7 未冻结**：E6 写 “≥200 permutations” 但 v0.1 协议/零模型设计是 1,000；E7 只写“执行前冻结库/网格”，没有具体候选数/网格/内层折/预算计数。E1–E12 必须补成可执行、可审计、同预算的冻结清单，否则不能 approve。

## 1. 逐条确认

### ① 5 必改落实 —— **PASS 主体；typo FAIL**

- **BRD3379**：protocol §1/§2.1、JSON `active_drug_qualification`、report/record/usage 均把 BRD3379 标 **zero-dose/vehicle-like control、secondary/descriptive only、排除 primary**；V1 primary 为 **Bortezomib 22 / Idasanutlin 24 / Trametinib 24** 等权；**“4 drugs confirmatory” 已撤回**；MDE 表不含 0.409；**PASS**。
- **V2 paired**：JSON `v2_corrected` 正确 **15/16/15**；protocol §2.3、report/record/usage 正确；**但 protocol H-D5-2 line96 写 15/16/16** → **FAIL（typo）**。
- **G0b**：`dose>0 + dose_unit + ChEMBL annotation`（metadata-level）；3 药 conditional pass；BRD3379/control fail；执行前再核 compound/dose/vehicle；**PASS（带 metadata-level 局限）**。
- **MDE/4 药表述同步**：active only **0.865/0.826/0.826**、r_err **0.987/0.985/0.985**；v0.1 的 4 药 primary 已撤回；**PASS**。
- **SHA/两跑**：protocol `D1ABD7C6…`、JSON `D41ED20F…`、report `4B742A0D…`、record `BB4C5130…`、usage `910427F6…`；`d5_revision.py` 两次/连续运行 JSON 同 SHA；**PASS**。

### ② primary/MDE/G3 —— **PASS（诚实），但不支持 confirmatory**

- V1 primary = **3 active drugs 等权平均**；per-drug n 22/24/24；不跨药配对；**PASS**。
- MDE 上界 active only **0.865/0.826/0.826**；r_err **0.987/0.985/0.985**；G3 `MDE80≤δ_min`；预判 likely `evaluation_cannot_distinguish`；**PASS（诚实）**。
- **但**：pre-run upper **远大于** δ=.10；在 24 线上没有可行的 confirmatory power；**approve_to_lead_exec 应保持 false**；只能 reduce/stop。
- V2 n=15–19<20 → exploratory only；功能路由 not_qualified；time_axis_unverified；overall qwc 仅 3 药分子代理开发层；**PASS**。

### ③ E1–E12 —— **WEAK（部分可执行；E6/E7 不足）**

- E1 数据加载/QC/pseudobulk/control；E2 train-only 200 gene panel；E3 fold loader/assertions；E4 V1 不跨药配对；E5 V2 paired sets 15/16/15；E8 两跑/schema；E9 measured MDE precertification；E11 G5 断言；E12 本轮不运行——**基本具体**。
- **E6 不足**：只写“≥200 permutations”；v0.1 协议/零模型设计为 **N1/N2 1,000**；不能降低；应写 **1,000**（或给出预注册功效理由），并写清 N1/N2/N4/N5 的合法零、配对/聚类单位。
- **E7 不足**：只写“执行前冻结库/网格”，没有 **具体 library/网格/候选数/内层折/trials/compute cap**；同预算不可核查。必须给出具体 grid 或明确“执行前冻结清单 SHA”且包含候选数。
- **PASS 但有条件**：E1/E2/E3/E5/E8/E9/E11 可执行；E6/E7 必须补后才能 approve（若 reduce，仍应补为描述性执行清单）。

### ④ 是否值得执行 —— **建议 reduce_to_descriptive；若要求 confirmatory 则 stop**

- **(a) 授权一次 confirmatory 执行记录 evaluation_cannot_distinguish**：**不建议**。G3 预运行上界 .865/.826/.826 已说明在 22/24/24 线上几乎必然不可分辨；执行只得到“无法分辨”，成本/风险不值得，且容易被误读为“做过实验”。
- **(b) stop + 测量规格**：**若 Lead 要 confirmatory H-D5-1，选 stop**。所需：
  - **独立细胞系**：按 `2.802√(2/(n−1))≤.10`，每 active drug 约 **1,571 条独立细胞系**（或可认证的跨模型误差相关 **≥.987/.985**；未认证）；当前 22/24/24 远不足。
  - **配对/同细胞设计**：解决破坏性快照/同批/暴露；当前无。
  - **功能结局**：viability/凋亡/再生长，匹配同细胞×同药×同剂量×6/24/48h；当前无。
  - **batch/exposure/vehicle** 记录；当前无。
  - **V2** 15–19 线仍 exploratory；不能升级 confirmatory。
- **(c) reduce 为纯描述性**：**推荐**。保留 3 active drugs/V1 分子代理、V2 exploratory，报告 **per-drug Δρ、CI、MDE、room、reliability、per-fold**，但**不做 H-D5-1 confirmatory 检验**、不设 G3/G4 通过/失败、不写 `evaluation_cannot_distinguish` 为推断结论；不称 biology/迁移/决策/机制/功能；BRD3379 仍 secondary；V2 仅描述。这样保留 L1 开发资产而不伪装成 confirmatory。

### ⑤ 边界 —— **PASS**

- 仅分子代理开发层；功能/决策/轨迹/机制/迁移/新颖性不称；A3v2 仅背景；不重开 R196v2/R197v2；BRD3379 不复活 4 药 primary；RNA 代理≠功能；技术重复≠独立培养；time_axis_unverified；**PASS**。

## 2. 必改（≤5；reduce 前/若坚持 confirmatory 前）

1. **修 H-D5-2 typo**：protocol line96 `paired sets（15/16/16）` → **15/16/15**；全文检索无 “15/16/16”；与 JSON/report/record/usage 一致。
2. **E6 零模型固定为 1,000**：N1/N2 1,000（或给出预注册功效依据，不得用 200 反向降）；写清 N1/N2/N4/N5 合法零、聚类/配对单位、seed。
3. **E7 具体化**：B1–B8 的 library/网格/候选数/内层折/trials/compute cap 具体写死或给“执行前冻结清单 SHA”；同预算可核查；不得看结果调参。
4. **reduce 语义重写**：若选 reduce，H-D5-1 改为 **descriptive**（无 confirmatory/G3/G4 通过失败）；报告 per-drug Δρ/CI/MDE/room/reliability + fold；明确“不可推断 biology/迁移/决策/机制”；V2 exploratory；BRD3379 secondary。若坚持 confirmatory，**stop** 并记录 §3 测量规格。
5. **G0b 执行前再核**：3 active drugs 的 compound identity/dose/vehicle 必须实测/记录；G0b 失败→`active_dose_identity_unverified` 停止；BRD3379 不得回到 primary。

## 3. Lead 批准前条款/预算

**若 Lead 选 reduce_to_descriptive（推荐）**：
- 先修 1–3；将协议标记 `descriptive_only`，无 confirmatory H-D5-1、无 G3/G4 判定；只报告描述性统计与 MDE/CI。
- 执行预算：3 active drugs ×5 folds；B1/B3/B4/B5（或预先冻结的最小集）；每 arm 同调参 trials/inner CV/seed/compute cap；E1–E12 执行冻结版；**不运行效果本任务**。
- Lead 文本须写：仅 O'Neil 内部开发性描述；非 confirmatory；不称 biology/迁移/决策/机制/功能；G3 预运行 .865/.826/.826，描述性 CI 不用于推断；BRD3379 secondary；V2 exploratory。
- 若 Lead 选 **stop**：记录 §4 测量规格；不执行、不写阴性；D5 保留为 data/infrastructure 记录。

**若 Lead 坚持 confirmatory H-D5-1**：
- **stop**（不是 approve）；所需独立细胞系 ~1,571/药或认证 r_err≥.987/.985；配对/功能/batch 新测量；V2 不可升级；不得用一次 evaluation_cannot_distinguish 执行替代。

## 4. 复核证据与本轮边界

- 实际 SHA：protocol `D1ABD7C6…`、JSON `D41ED20F…`、report `4B742A0D…`、record `BB4C5130…`、usage `910427F6…`；`d5_revision.py` `6A89039C…`；V1 active manifest `0056D69E…`；v0.1 六文件 SHA 未变。
- 关键矛盾：protocol line96 “15/16/16” vs §2.3/JSON/report/record/usage **15/16/15**；E6 “≥200” vs v0.1 1,000；E7 无具体 grid；MDE active only .865/.826/.826；G3 high failure honest。
- **本轮未运行效果/未拟合/未读表达或响应矩阵**；只读文档/JSON/SHA；只写本文件与 `tmp/`。
- **reduce_to_descriptive**（推荐）；**approve_to_lead_exec=false**；若 Lead 要 confirmatory→stop；不称 biology/迁移/决策/机制/功能/新颖性；冻结≠资源足够/关系成立/Stage1/效果。

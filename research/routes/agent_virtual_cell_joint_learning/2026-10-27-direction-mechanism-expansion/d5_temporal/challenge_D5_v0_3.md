# R200-D5.2-C1 再挑战（challenge_D5_v0_3.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3/D5 同一独立挑战者；未参与 D5.2 修订）· 对象：`research/2026-10-27-direction-mechanism-expansion/d5_temporal/{PROTOCOL_D5_v0_3.md, d5_revision_v0_3.py, d5_v0_3.json, report_d5_v0_3.md, record_d5_v0_3.md, usage_d5_v0_3.json}` + v0.2 历史。
方式：**只读复核**（文档/JSON/E6/E7/描述性 schema/EX-G0b/SHA；**不运行效果、不拟合、不读表达或响应矩阵**）；只写本文件与 `tmp/`。
完整性（实算）：protocol **`E848A0BA…`**；code **`D66FBDBE…`**（27,070 B）；JSON **`97250A0B…`**（28,629 B）；report **`2C35780D…`**；record **`018F57E4…`**；usage **`1FB7C4A2…`**；v0.2 history `D1ABD7C6…`/`D41ED20F…` 未变。

## 0. 总判决

**revise（≤5；当前不可 approve_to_lead_exec_descriptive；不是 stop）。**
D5.2 的 5 条必改**主体已落实**：typo **15/16/15 全文 0 残留**；E6 N1/N2/N3/N4/N6 **1,000**；E7 冻结版本/网格/候选数/内层折/CPU cap；H-D5-1 **descriptive**、G3/G4 通过失败移除、`evaluation_cannot_distinguish` 不再作推断；描述性 schema 齐全；EX-G0b 执行前再核；BRD3379 secondary；V2 paired 15/16/15。**描述性执行路径本身可批准**，但当前有两类**可修的文档/预算自洽错误**，必须先修：
1. **protocol §12 与 report 的 SHA/size 仍是旧值**：`ff4c03…`（26,947 B）/`3508dada…`（28,575 B）；实际 code **`D66FBDBE…`（27,070 B）**、JSON **`97250A0B…`（28,629 B）**（record/usage/JSON 已是实际值）。这直接违反 task ①“SHA/两次运行一致”，冻结后会产生错误代码/JSON 引用。
2. **E7 拟合预算算术不一致**：tuned_models 只有 **6 个**（B1/B3/B4/B5/B7/B8），600 fits/model → **3,600 fits total**；不是 4,200。当前 protocol/JSON/report/usage 都写 **4,200**。必须改为 **3,600**，或追加一个**预注册**的第 7 个 tuned model 并写其 grid（不能看结果后决定）。

修完这两类（及同步 SHA）后，**建议 approve_to_lead_exec_descriptive**（仅描述性、非 confirmatory）。当前不批准执行。

**最致命 3 条**

1. **旧 SHA/size 残留**：protocol §12、report §SHA 写 `ff4c03eb…`/`3508dada…`（26,947/28,575），实际 `D66FBDBE…`/`97250A0B…`（27,070/28,629）；record/usage/JSON 正确。必须修 protocol/report（及任何引用）到实际值；否则“两次运行一致”的冻结链不成立。
2. **E7 total fits 4,200 与 6 个 tuned models 矛盾**：6×600=3,600；4,200 只有在 7 个 tuned model 时成立。当前 `tuned_models` 仅 6 个，4,200 无来源；必须改为 3,600，或预注册第 7 个模型+grid+预算；不能保留“4,200”作为预算。
3. **描述性执行仍不可直接启动**：上述 SHA 与预算错需先修；另 E7 CPU 120 min / 3,600 fits 的执行 wall 估算尚未给出，需在 Lead 批准前写预算测试/预检值（不运行效果）。

## 1. 逐条确认

### ① 5 必改落实 —— **PASS 主体；SHA/E7 为 FAIL**

- **typo**：v0.3 protocol/report/record/JSON/code 全文 **无 `15/16/16`**；V2 全部 **15/16/15**；v0.2 的 typo 定位在 `PROTOCOL_D5_v0_2.md:96` 冻结历史；**PASS**。
- **E6**：N1/N2/N3/N4/N6 = **1,000**；seed 20261027；合法零/同折同药同时间层/保留边缘/同调参预算；N5 future-leak sentinel 1/fold/arm；**PASS**。
- **E7**：库版本（sklearn 1.9.0/numpy 2.4.6/pandas 2.3.3/scipy 1.17.1）、内层 5 折、8 candidates×5 =40 fits/unit、15 units=600/tuned model、具体 ridge/HistGBM/GP grids、grid SHA `d2835e79…`；**PASS 主体**；**但 total 4,200 与 6 models 矛盾（见致命 2）**。
- **H-D5-1 descriptive**：明确“不检验时间预测是否成立；只描述可达精度与方向”；G3/G4 通过/失败移除；`evaluation_cannot_distinguish` 不再作推断；precision descriptor 语言；**PASS**。
- **描述性 schema**：per-drug `rho_early6h/rho_static/delta_rho/CI/mde80/room/reliability/per_fold/hyperparams`；summary；BRD3379 secondary；V2 fields；禁止 confirmatory/biology 等；**PASS**。
- **EX-G0b**：执行前实测/记录 compound identity/dose/vehicle/source/assay；失败→`active_dose_identity_unverified` STOP；BRD3379 永不回 primary；**PASS**。

### ② 描述性边界 —— **PASS**

- 核心声明“本分析不检验时间预测是否成立；只描述可达到的精度与方向”。
- 仅 per-drug Δρ/CI/MDE/room/reliability/per-fold + summary + BRD3379 secondary + V2 exploratory；MDE/room 仅 precision descriptor；禁止 confirmatory p 值/判定、biology/功能/迁移/决策/机制/新颖性/真实轨迹；**PASS**。

### ③ 数据/切分/配对 —— **PASS**

- V1 3 active drugs（Bortezomib 22 / Idasanutlin 24 / Trametinib 24）6h→24h 分子代理；leave-cell-line-out 5 折；内层按细胞系；**PASS**。
- V2 paired **15/16/15**；n<20 exploratory；输入严格更早；**PASS**。
- 功能 not_qualified；time_axis_unverified；RNA 代理≠功能；**PASS**。

### ④ E1–E12 / E7 可执行性 —— **WEAK（除 arithmetic/SHA 外大体可执行）**

- E1 h5ad 加载/QC/pseudobulk/control；E2 train-only 200 panel；E3 fold assert；E4 V1 无跨药；E5 V2 paired；E6 1,000；E8 两跑/schema；E9 描述性测量；E10 报告模板；E11 G5 断言；E12 不运行——**具体可执行**。
- **E7** 具体网格已给；**但 total fits 需纠正**；**CPU 120 min 与 3,600 fits 的 wall 预算**尚未给预检值；Lead 批准前需给 **预算测试/预检 wall**（不运行效果）。
- **E1–E12** 仍有一个可补细节：E2/E1 的 **pseudobulk 数组 SHA、gene panel SHA、fold manifest SHA** 需在执行 schema 中明确；目前 E8 提到 config/fold/pseudobulk SHA，足够；**PASS/可执行**。

### ⑤ 是否值得执行 —— **建议 approve 描述性（修完后），不是 stop**

- **confirmatory 不可行**：G3 上界 `.865/.826/.826` vs δ=.10；需 ~1,571 独立细胞系/药或认证 r_err≥.987/.985；**不 approve confirmatory**。
- **描述性执行有价值**：记录 3 active drugs 的 per-drug Δρ/CI/MDE/room/reliability、fold 方向、V2 exploratory；提供 L1 开发资产的经验描述；**不推断 biology/时间预测成立**。
- **成本可控**：3,600 fits（修正后）+ 1,000×零模型；CPU 120 min cap；若预算测试 pass，**值得做一次**。
- **不建议 stop**（除非 Lead 不再需要 L1 描述资产）；**不建议 confirmatory**。
- **最终建议**：修 SHA/E7 后 **approve_to_lead_exec_descriptive**；Lead 文本明确“descriptive_only、非 confirmatory、不可推断 biology/时间预测”。

## 2. 必改（≤5）

1. **修 SHA/size**：protocol §12、report §SHA 的 `ff4c03eb…`（26,947 B）/`3508dada…`（28,575 B）改为实际 `D66FBDBE…`（27,070 B）/`97250A0B…`（28,629 B）；全文检索无旧值；record/usage/JSON 已正确，保持。
2. **修 E7 total fits**：6 tuned models ×600 = **3,600**；将 protocol/JSON/report/usage 的 4,200 改为 3,600（或**预注册**第 7 个 tuned model + grid + 600 fits 后为 4,200；不得看结果决定）。同步 `tuning_E7.max_fits_total` 与 checklist E7。
3. **给 CPU/预算预检**：说明 3,600 fits + 1,000×零模型在 120 min cap 内的估算/预检 wall；若超 → `protocol_deviation` stop；不得放宽 cap。
4. **描述性执行冻结项**：E1–E12 执行版；EX-G0b 先核；两跑逐字节；schema（per-drug/CI/MDE/room/reliability/per-fold/BRD3379 secondary/V2 exploratory）；禁止 confirmatory/biology/function/migration/decision/mechanism；不写 `evaluation_cannot_distinguish` 推断。
5. **Lead 文本条件**：仅 approve **descriptive_only**；非 confirmatory；不称时间预测成立/biology；若 Lead 要 confirmatory → stop + 测量规格；BRD3379 永不回 primary；v0.1/v0.2 未改。

## 3. 若修完，Lead 批准文本（建议）

> **批准 D5.2 v0.3 进入一次纯描述性执行（descriptive_only；非 confirmatory）。**
> 冻结：protocol `E848A0BA…`（修后重算 SHA）；JSON `97250A0B…`（修后重算）；code `D66FBDBE…`；E6 1,000；E7 3,600 fits × CPU 120 min cap（或预注册第 7 模型后 4,200）；E1–E12；EX-G0b 先核；两跑/schema。
> 范围：3 active drugs（22/24/24）、V1 6h→24h RNA 分子代理、V2 exploratory（15/16/15）、BRD3379 secondary only；**不检验 H-D5-1、不设 G3/G4 通过失败、不写 evaluation_cannot_distinguish 推断**；只报 per-drug Δρ/CI/MDE/room/reliability/per-fold；不称 biology/功能/迁移/决策/机制/新颖性/真实轨迹；RNA 代理≠功能。
> 停止：EX-G0a/G0b 失败→stop；泄漏→design_invalid；超出预算→protocol_deviation；功能/时间轴边界不变；confirmatory 需求→stop+测量规格。
> 预算：3,600 fits（修正后）+ 零模型；CPU 120 min；执行前报预算预检与两跑确定性。

## 4. 复核证据与本轮边界

- 实际 SHA：protocol `E848A0BA…`、code `D66FBDBE…`（27,070 B）、JSON `97250A0B…`（28,629 B）、report `2C35780D…`、record `018F57E4…`、usage `1FB7C4A2…`；**protocol/report 内 ff4c/3508 为旧值**；`tuned_models` 6 个、`max_fits_total=4200` 矛盾。
- **本轮未运行效果/未拟合/未读表达或响应矩阵**；只读文档/JSON/SHA；只写本文件与 `tmp/`。
- **当前 revise；修完 1–3 后可 approve_to_lead_exec_descriptive；不 approve confirmatory；不 stop（描述性 L1 资产仍有价值）**。不称 biology/功能/迁移/决策/机制/新颖性；冻结≠资源足够/关系成立/Stage1/效果。

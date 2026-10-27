# R199-ON2-EX 报告：σ_e 标定 + MDE80 认证 + 确定性单插补敏感性（资格执行，非效果）

2026-10-27 · 角色：ON1/ON2 执行者（非提案者；不参与效果设计）· 任务：R199-ON2-EX（ON2 v2 冻结协议下的**唯一允许的资格执行**）· 依据：`PROTOCOL_ON2.md` v2.2 §3.2(b) σ_e 条款、§3.3(2) 单插补敏感性、§4/§5 判定与边界；`ERRATA_ON2_1.md`、`report_on2_1.md`、`record_on2_1.md` §10 冻结文本。
**本轮不运行效果/训练/更新器比较、不做迁移/决策分析、不称资源足够/关系成立/效果；只做噪声标定与单插补敏感性。**

## 0. 判定（一屏）

**σ_e 标定 + MDE80 认证：`calibration_passed`。**
- measured **σ̂_e = 0.1422665081**（well-level；complete-case cohort，all batches/all cells）；
- **SE_unit = 0.0251494031**；**MDE80 = 0.0287644381**；**n_eff = 6**；**δ_min_provisional = 0.10**；
- **MDE80 (0.0287644) ≤ 0.10** → 通过；未触发 `design_invalid: precision_insufficient`；
- 允许的下一步（仅此一句）：**"资格执行完成，可进入开发性描述分析（须另立协议+独立挑战）"**。
- **不**运行效果/更新器；**不**称资源足够/关系成立/效果/独立确认/迁移/决策收益/机制/新算法。

## 1. 冻结协议与输入

- 规范协议：`PROTOCOL_ON2.md` v2.2，SHA256 `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7`；`ERRATA_ON2_1.md` `3C6138DF…E7870B`；`report_on2_1.md` `C6CF6467…D569EE`；`record_on2_1.md` `789A0114…484694`；`on2.json`（v2.0 历史数据产物，门级数字有效）`AD7E6D13…81F7C8`。
- 组合工作簿：`data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`，SHA256 `A0E2E002…C14818`，368,832 行。
- 本轮只按冻结条款读 `viability1–4` 做 σ_e 标定与单插补敏感性；**不做效果/更新器/训练/迁移**；确定性：`calib.json` 键排序、无时间戳、`allow_nan=False`、输入/脚本 SHA 写入。

## 2. σ_e 标定（complete-case 主标定）

- **cohort**：complete-case 行（viability1–4 全非空；**all batches/all cells**；协议 §3.2(b)(1) 的 "complete-case 行（主）"）；rows_used **363,090**；rows_excluded_k1（全表）**78**（这些行不在 complete-case cohort 中；该计数为全表口径）。
- **成员/单元**：complete-case 成员上下文 **44,070**；合法 `(batch,cell,partner,role)` 上下文 **2,927**；可替换 Δ 单元 **442,996**。
- **固定索引分半（禁按值排序）**：重复列固定 `viability1, viability2, viability3, viability4`；k=4 → `{v1,v2}` vs `{v3,v4}`（2+2）；每行 half 均值、成员曲线半均值（16 行半均值之均值）、Δ 半值（两成员曲线半均值差，符号按归一名升序，前者减后者）。
- **估计量**：`σ̂_e² = Σ_units (Δ_h1 − Δ_h2)² / Σ_units denom`；complete-case 每单元 `denom = 2 members × 16 rows × (1/2+1/2) / 16² = 1/8`；sumsq = **1,120.7665523745**；sumden = **55,374.5**；σ̂_e² = 0.0202397，σ̂_e = **0.1422665081**。
- 结论文本：σ̂_e 是 **well-level 标准差**；不是效应估计；技术重复不当作独立 n（n_eff=6 held-out 细胞）。

## 3. MDE80 认证（冻结公式）

- `SE_unit = σ̂_e/√32 = 0.1422665081 / 5.6568542495 = 0.0251494031`
- `MDE80 = 2.8015852181 × SE_unit / √n_eff = 2.8015852181 × 0.0251494031 / √6 = 0.0287644381`
- `n_eff = 6`（每折 6 held-out 细胞，保守）；`δ_min_provisional = 0.10`
- **比较：0.0287644381 ≤ 0.10 → PASS（calibration_passed）**；MDE80 占 δ_min 的 **28.76%**；未触发 `design_invalid: precision_insufficient`，也未进入任何效果步骤。
- 说明：借用先验（0.041/0.058/0.109）只作期望、不是本次实测；本次 σ̂_e=0.1423 高于借用上界 0.109，但 MDE 仍远低于 δ_min，认证通过。

## 4. Scope 变体（透明性；gate 用 primary complete-case all batches）

| scope | rows | legal contexts | units | σ̂_e | SE_unit | MDE80 | ≤0.10 |
|---|---:|---:|---:|---:|---:|---:|---|
| complete-case all batches/all cells（**primary/gate**） | 363,090 | 2,927 | 442,996 | **0.1422665081** | **0.0251494031** | **0.0287644381** | PASS |
| complete-case batch1 all cells | 357,876 | 2,791 | 441,867 | 0.1422146472 | 0.0251402354 | 0.0287539525 | PASS |
| complete-case batch1 target 30 cells | 275,412 | 2,149 | 340,088 | 0.1384458171 | 0.0244739940 | 0.0279919441 | PASS |
| complete-case batch2 all cells（披露） | 5,214 | 136 | 1,129 | 0.1612883917 | 0.0285120289 | 0.0326104156 | PASS |

- 主分析设计为 batch1/target30；上述 scope 均 PASS，说明认证不依赖"全 batch 合并"的偶然性；gate 仍按协议 complete-case cohort 的 primary（all batches）报告；scope 仅透明性披露。

## 5. all-available 敏感性标定（rule A；仅敏感性）

- cohort：原始行 ≥1 非空技术重复且该行 **k≥2**；rows_used **368,754**；**k=1 的 78 行不参与标定并计数**。
- 成员上下文：**45,948 / 46,104 可用**（排除 **156** 个行内 <95% 的成员上下文；这与 v1.1 rule A 一致）；合法上下文 **3,101**；Δ 单元 **470,179**；**单位排除 = 473,906 − 470,179 = 3,727**。
- 固定索引分半：k=4→2+2、k=3→2+1、k=2→1+1；`denom = Σ_{两成员}Σ_{16行}(1/h1+1/h2)/16²`。
- 结果：sumsq **1,211.1961362423**；sumden **58,868.04296875**；σ̂_e = **0.1434390629**；SE_unit = **0.0253566835**；MDE80 = **0.0290015134 ≤ 0.10 → PASS**。
- **仅敏感性**，不替代主标定/gate，不作资格数。

## 6. 确定性行均值单插补敏感性（不是 MI）

- 方法：**单次确定性行均值单插补**；每行缺失重复值用该行非空重复均值补；**无随机抽样、无 m、无 seed、无 Rubin**；结构约束 batch/cell/partner/dose-row（不跨端点/不跨研究）；**不是多重插补**。
- 全表：rows **368,832**；Δ 单元 **473,906**；**Δ 均值 = 0.0059696378**（描述性；**不是效应估计、不是资格门**）。
- batch1 target：Δ 单元 **363,304**；Δ 均值 **0.0034618085**。
- 描述性并排（仅参考、不是效应比较）：complete-case 主 Δ 均值 **0.0062839576**（442,996 units）；all-available rule A Δ 均值 **0.0060780967**（470,179 units）；imputed Δ 均值 **0.0059696378**（473,906 units）。
- **单插补敏感性仅作描述性稳健性；不用于门级判定/效果推断**；|Δ 均值| 远小于 δ_min=0.10，但这**不**构成"资源足够/关系成立/效果"的证据。

## 7. 排除计数（冻结 schema 对照）

| 项 | 值 | 说明 |
|---|---:|---|
| rows_total | 368,832 | 全表 |
| rows_excluded_k1 | **78** | 全表 k=1 行；不参与标定 |
| complete-case rows_used | 363,090 | primary cohort |
| all-available rows_used | 368,754 | ≥2 repeats |
| complete-case units | 442,996 | primary units_used |
| all-available rule-A units | 470,179 | 敏感性 units |
| all-available no-exclusion units | 473,906 | 诊断基线 |
| all-available units excluded | **3,727** | 473,906−470,179 |
| complete-case member contexts | 44,070 | complete grids |
| all-available member contexts usable/excluded | 45,948 / **156** | rule A |
| members contexts dropped to <2 usable | **0** | 三 scope |

## 8. 确定性、SHA、wall/CPU

- `run_calib.py` SHA256 **`3786576B019D7B44E8C2572006BAD0BE5D507CFDC644CED7232A70C6594579D9`**（22,348 B）。
- `calib.json` SHA256 **`DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A`**（6,935 B）；两次独立运行**逐字节一致**（两次 calib SHA 相同）。
- `usage_calib.json` SHA256 **`77D24047F120974F15BE77FB8D9DA6F7DCC89C5F04AD6816733CADCD4AF0158B`**（713 B）。
- 两跑 wall/CPU：run1 **46.34 s / 43.83 s**；run2 **47.34 s / 45.22 s**；≤45 min 预算；CPU-only，无 GPU，无网络。
- 输入 SHA：工作簿 `A0E2E002…C14818`、协议 `7B34DB79…0B2BA7`、ERRATA `3C6138DF…E7870B`、report `C6CF6467…D569EE`、record `789A0114…484694`、on2.json `AD7E6D13…81F7C8`。
- `calib.json` 键排序、无时间戳、`allow_nan=False`，输入/脚本 SHA 写入；wall/CPU 只在 `usage_calib.json`。

## 9. 边界（随认证一起读）

- **只做资格执行（σ_e 标定 + MDE 认证 + 单插补敏感性），不运行效果/更新器/训练/迁移/决策分析。**
- 认证通过仅表示"可进入开发性描述分析（须另立协议 + 独立挑战）"；**不**表示资源足够、关系成立、Stage 1/效果、独立确认/迁移/决策收益/机制/新算法。
- 技术重复≠独立培养；n_eff=6 是保守 held-out 细胞数，未把 64 well 当独立样本；σ_e 与 Δ 为标定/描述性统计，不是效应估计。
- 缺失机制未知（不假设 MCAR/MAR）；batch3 全失、702 个 15 行 pair-cell；v1 `data_unavailable` 保留；AMENDMENT_ON1-001 不冻结；v1.1 仅敏感性。
- 下一步效果/开发性描述协议必须另立 **pre-registration + 独立挑战**，且不能绕过本认证。

## 10. 交付

- `exec_calibration/run_calib.py`、`calib.json`、`usage_calib.json`、本报告、`record_calib.md`。
- 未修改 `PROTOCOL_ON2.md`/`on2.py`/`on2.json`/`report_on2_1.md`/`record_on2_1.md`/ON1 产物/其它目录/INDEX/SYNTHESIS/git；只写本目录与 `tmp/`。

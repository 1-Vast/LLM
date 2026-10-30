# PASS LOG — 定向检索与本地核验（2026-10-27）

预算：2 个定向 pass（BRIEF §2）。本地已存文件阅读不计 pass。受限域名不重试超过 2 次。
核验员：lit-verifier（task-2）。当前消耗：**PASS 1（承接完成，未新增网络）＋ PASS 2（1 个新 pass，合并查询）**。

## PASS 1 — 2026-10-27 11:2x（线 A 原文事实 + 线 B 先例存在性，合并）
**状态：完成（本次任务内完成判读，无新增网络请求）。**
- 输入：`sources/queries/` 下既有 Europe PMC / OpenAlex 查询 JSON（A/B/C 系列共 30+ 条）、`sources/extracts/` 下 5 篇 arXiv 全文与 sentences、BATCHIE 全文、AL_guide_2025、ComboCat 全文/sentences、MOESM1/3/5/6/8/9/10 补充材料、`research/2026-10-27-oneil-transfer-qualification/combocat_dense_supp_data1.zip`（73,327,836 B，Supplementary Data 1）。
- 完成内容：
  1. 线 B 先例逐篇核对（本地全文，非摘要）：arXiv 2605.26093（GoBOED）、2602.05340（decision-focused sequential design）、2603.14094（robust BOED）、2605.04895（regime-conditioned BO）、2506.07805（R-IDeA 鲁棒 BOED under misspecification）；BATCHIE（PDBAL）、AL_guide_2025（α·S+(1−α)·σ）。
  2. 关键判读：decision-focused acquisition 已被 2605.26093/2602.05340 覆盖；乘积门控结构见 R-IDeA（门控变量=模型错设残差，非 MDE）；噪声/识别 SNR 条件见 2605.04895；BATCHIE 正文无 "SNR 惩罚"（候选 v1 表述需更正）。
  3. 线 A/ComboCat 原文事实：dense 模式 806 组合/290k 测量/同板 3 技术重复/每组合 1 板/端点字典；sparse 模式 10 对角实测+90 补全、仅 40 组合 dense 复筛验证；注释与身份问题（见下）。
- 产物：`evidence.md` §1–§3（F01–F30）。

## PASS 2 — 2026-10-27 12:4x（线 B 复核：MDE/可分辨性/功效 × acquisition 缺口）
**状态：完成。1 个新 pass（同一 pass 内合并 EPMC/OpenAlex 查询；arXiv API 不可达，见缺口 G1）。**
- 脚本与原始响应：`sources/queries/pass2_targeted_queries.py`、`pass2_followup_queries.py`；结果 `sources/queries/pass2_epmc_*.json`、`pass2_openalex_*.json`、汇总 `sources/queries/pass2_summary.json`。
- 查询与结果：
  - EPMC `P2-q3_power_acquisition_recent`（power analysis/"minimum detectable effect"/power-aware × acquisition function/BOED/batch AL，2023–2026）→ **hitCount=0**。
  - EPMC `P2-q2_decision_acq_noise`（decision-focused/goal-oriented/VOI × acquisition/design/AL × MDE/power/detectability/replication/sample size，2023–2026）→ hitCount=1，唯一命中为法医学文献综述工具（无关）。
  - EPMC `P2-q1_EVSI_sample_size`（VOI/EVSI/ENBS × sample size/power/cost × trial/decision/design）→ hitCount=477，EVSI/ENBS 成熟文献群（仅题录，未读全文）。
  - OpenAlex 标题摘要精确过滤：`P2-o4`（"decision-focused" ∧ "acquisition function"）→ **0**；`P2-o5`（"statistical power" ∧ "Bayesian experimental design"）→ **0**；`P2-o3`（"minimum detectable effect" ∧ "active learning"）→ 1（2026 农业害虫监测预算约束 AL，仅相邻）；`P2-o6`（"detectability" ∧ "active learning"）→ 1552（均为入侵/异常/欺诈"检测"任务，术语撞车，无关）。
  - arXiv API：2 次 read timeout + 1 次 HTTP 429（受限，不重试）→ 记录缺口。
- PASS 2 判读：**未发现**"以每动作实际重复数计算 MDE 并作为 acquisition 准入闸"的已发表工作（零命中只作检索结果，不写成不存在）；"decision-focused acquisition"本身的先例已在 PASS 1 覆盖。

## 本地核验补充（不计 pass）
- ComboCat Supplementary Data 1（REVISED）直读审计（openpyxl，只读）：`data` sheet 292,458 行、45 列、806 个 root_id（=combination:cell_line，数据字典原话）、每 root 重复集恰为 {1,2,3}（`replicate`，同板技术重复）；`cell_lines_summary` 36 行（Human 33/bacteria 2/fungus 1；14 lineage 水平，其中 1 行 organism/lineage 不一致）；`drugs_summary` 136 行、class 仅 5 水平；**804/806 root_id 为 32 位哈希，`drug1_name/drug2_name` 仅占位符 "drug1"/"drug2"，数字键摘要与 root_id 无 join key** ⇒ A2 留药切分所需药物身份/注释在发布文件内不可连接。审计记录：`sources/extracts/combocat_dense_supp_workbook_audit.txt`。
- MOESM8（sparse 模式化合物表）openpyxl 只读计数：135 行，CHEMBLID/Action_Class（5 水平）/Reported_Target（99 个不同值）。
- 结论写入 `evidence.md` F19–F30（ComboCat 事实/A2 门槛算术）。

## 未决缺口
- G1 arXiv API 不可达（本轮未取到 arXiv 侧 PASS 2 结果）；已本地覆盖 5 篇关键 arXiv 全文，但不能排除未下载先例。
- G2 EVSI/ENBS 仅题录级（477 命中未读全文）；若需精确差异边界需另读 2–3 篇全文。
- G3 BATCHIE 补充材料（PDBAL theory）未下载，"正文未见 SNR 惩罚"不能全称否证。
- G4 ComboCat 身份映射若作者另有分发渠道，需 A1 线取得后按 `evidence.md` F29/F30 重判 A2 门槛（当前判：A2 不运行，只记资格结论）。

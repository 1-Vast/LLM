# R202 轮记录：外部独立组合/功能资源定向征询（2026-10-28）

## 结论
总体 **`not_qualified`**；无 qualified/qualified_with_conditions；**建议停止外部征询**。找到了比本地更原始更大的外部组合数据（AZ/GDSC 2024 raw 3.9M wells；NCI-ALMANAC 3.7M 行），但都在**独立重复/独立培养（G4）**与**与 Jaaks A0 匹配键（G1）**上失败，且缺暴露时间/正交功能读数。

## 逐候选（原因码）
- AZ/GDSC 2024 raw wells：not_qualified（no_independent_replicate_or_culture/jaaks_overlap_insufficient/no_exposure_time/no_orthogonal_functional_readout）；3,915,245 well 行、754 细胞、84,055 (cell,pair) 单元、每单元 7×7 wells；与 Jaaks 8 有向对/68 A0 键、barcode 0 重叠；0 个 pair-cell ≥2 重复板/独立培养。唯一值得保留的"新关系开发"资源（241MB zip），但非独立重复/功能验证目标。
- NCI-ALMANAC：not_qualified（G4 fail）；3,686,475 行、61 细胞、305,081 pair-cell、2,866,683 keys 中仅 6,831=0.24% 跨板重复、精确 A0 键 0。
- DREAM 2015：access_restricted（Synapse 403，未绕过）。
- PanThera 2024：aggregated_only/no_combination_data（models 877MB >500MB）。
- SAFER 2024：reaggregated_lineage/data_unavailable（>500MB）。
- Dryad 类器官顺序给药 2025：access_restricted/jaaks_overlap_insufficient（401 bearer；仅方向3新协议候选）。
- HF ABX-CT-004：synthetic_benchmark。
- Novartis U2OS DRUG-seq：mono_only。
- 功能独立性资源：no_candidate_found（有界检索，不写不存在）。

## 可下载/受限
均≤500MB：NCI zip 85,966,226 B SHA 69367A8B…；AZ raw well zip 241,088,863 B SHA E8CB50F6…；受限/超限如实记录（receipts/download_manifest.json、access_status.json、search_log.json）。

## 所需测量（重开 A/B/D3 条件）
① 每 (cell, directed pair, dose) ≥2 独立培养/板（不同日/passage/flask；技术孔不算）；② 数字剂量+暴露时间/检测方法；③ 与 Jaaks ΔEMAX 同族端点或单药参照校准（不得 raw viability 直接混 ΔEMAX）；④ ≥1 正交功能读数（apoptosis/caspase/靶点参与/再生长/live imaging）；⑤ ≥500 A0 匹配键或另立"新关系"协议不声称复用 A0/Jaaks；⑥ 来源链/非重聚合 lineage。决策收益需 ≈6,282 独立细胞（δ=.05）。

## 边界
metadata-only；未训练/未拟合/未读响应做效应；未绕过登录/许可；不称新颖性/迁移/决策收益/机制；阴性写"未发现/不可得"不写不存在；不晋升代码。


## 修正（2026-10-28，R203-X1 / C202）
本记录中"0 个 pair-cell 有 ≥2 重复板/独立培养"是**导出键构造造成的假 0**：`scan_azeraw.py` 以 `lib1_drug`/`lib2_drug`（含 barcode）作 pair 身份，同 pair 跨 barcode 被拆开，`units_with_ge2_platforms=0` 不可作为作者未做重复的证据。**撤回该 fail 依据**；R202 总体 `not_qualified` 本轮不重做（G1 68<500、功能 numeric/协议字段缺口仍在），是否影响 Q1 需另立重评。AZ 2024 论文 Methods S15/S17 报告 72h+CellTiter-Glo 2.0、7 具名系技术三重复于 6 次实验、部分组合凋亡/PARP/caspase 验证；导出中 301 个 (line,pair) 恰 18 matrix 记录、161 个可归为 6 QC 日期×3 matrix，但**无显式实验/重复/处理日/passage/独立培养标签**；功能数值仅图/PDF（未取得数值表）。下一步先获取/清洗/映射（数据字典、功能数值），不先做新湿实验；技术三重复≠独立培养。详见 `research/2026-10-28-az-export-coverage/report_x2.md` 与 C202。

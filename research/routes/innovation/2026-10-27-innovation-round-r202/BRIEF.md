# R202 BRIEF：外部独立组合/功能资源定向征询与资格（2026-10-28）

## 背景（R201 收束后）
- R201 主line（Agent 反事实计划比较+虚拟细胞跨计划一致模型+反馈统一修订）已收敛：机制 A 因**零模型/σ 不可从 O'Neil 4×4 技术重复中独立校准**停止归档（C192/C194/C195）；双预算主 T1 仅合成计算证据且 H_B=`partial_decision_benefit`（C193）；D1 stop（C188/C189）、D3 design_invalid（C187）、D5 descriptive_only（C191）、ON3 no_increment（C190）。
- 所有可执行决定性实验均已按预注册规则收束；**剩余瓶颈=缺少独立测量/独立培养/重复结构/功能终点的组合资源**（A 线需独立 wells/plates/培养重复或合成 ground-truth；方向3 需真实顺序程序与功能数据；方向4/5 需材料数据；B 线 T3 需真实报价/湿预算）。
- 用户允许下载数据集与调用 API。本轮目标：**定向征询本地未收录的公开独立组合/功能资源**，先资格后（若合格）再设计，不重复已否定路线（DrugComb v1.4/1.5、PRISM/BeatAML/Mix-seq、O'Neil、Jaaks O/V、GCP2020、ALMANAC 空目录、VIS2024/Nyman2020/Hill2017/JUMP-CP/BATCHIE/GDSC2 等已审）。

## 本轮唯一任务（R202-Q1：外部资源定向征询+资格，不运行效果）
候选（逐一核，不预设）：
1) **AstraZeneca-Sanger DREAM 2015**（组合预测挑战；公开数据含 synergy/viability、多细胞系；需核重复/独立培养/剂量/端点/与 Jaaks 实体重叠）。
2) **NCI-ALMANAC**（NCI-60 组合；需核重复/独立培养、端点、剂量、与 Jaaks 重叠）。
3) **Novartis 组合公开集/其他 2024–2026 公开组合资源**（如 GDSC2 扩展、Community、PharmacoDB 汇总、DepMap 组合子集）。
4) **功能独立性资源**：同一细胞/干预的独立功能读数（apoptosis/caspase/靶点参与/再生长）公开集；若无可明确记录。
5) 其他检索到的 2024–2026 组合/顺序程序公开数据（含 Mix-seq 之外的时间序列/顺序）。

## 资格门槛（沿用并写死）
- 实体与 Jaaks 共享 **≥10 细胞/≥10 有向对/≥500 匹配键**（A0 复用门槛）、原始板孔与 Jaaks original/validation 不相交、**数字剂量+暴露时间**、**独立测量或独立培养**（不同日/passage/培养瓶；技术重复不算）、**≥1 正交功能读数**（若主张功能）、冻结聚合的组合 Δ 或功能 viability、**非重聚合 lineage**。
- 判 `qualified / qualified_with_conditions / not_qualified`（原因码）；不达标不得进入效果；**不得把同一 96 细胞换聚合当新数据**；不得把预测挑战表的已聚合分数当原始重复。
- 若需下载：记录 URL/大小/SHA；≤500 MB/文件；不读响应做效应统计（仅结构/元数据/空值计数）。

## 纪律
- metadata-only；先资格后设计；不运行效果/不拟合预测；不称新颖性/迁移/决策收益/机制；阴性写"未发现/不可得"，不写不存在；完成后由独立挑战复核，再决定是否重开 A/B/D 线。
- 只写 `research/2026-10-27-external-resource-hunt/` 或新目录与 tmp/；不晋升代码。

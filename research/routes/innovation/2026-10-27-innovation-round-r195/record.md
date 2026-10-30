# R195 轮次记录：条件级跨 screen 复验的资源资格审计 → `not_qualified`（分析 A 收口）

2026-10-27。角色：Lead（冻结/核验/综合）＋ 独立资源审计员（drugcomb-auditor，task-18）＋ 独立挑战者（i003-challenger，task-19，待 A3 完成后审）。本轮 **metadata-only**：未读响应数值、未估 Q、未训练模型。

## 0. 一句话结果

- **A3 `not_qualified`（`data_insufficient`）**：按冻结门槛 G1–G6 核查后，**没有**满足"≥2 个独立组合 screen、≥200 共享细胞、≥10,000 跨组匹配条件单元、噪声标定 ≥5%、组合协同端点"的可得资源。
- 主候选 DrugComb v1.5 full（本次下载 1.42 GB）：34 study/1,432,351 行；20 个合格 combo study（G1 过），但 **G2 共享细胞仅 41（<200）**、**G3 跨 study 匹配单元 4,179（<10,000）**；G3 另一读法（可行 Q 四元组上界 123,538）下 G3 过，但 **G2 仍 41≪200**，且 Q 结构集中在 9/5/6 个共享细胞上（比 A1 的 96 更少）→ 两种读法都 `not_qualified`。
- **分析 A 收口 = `condition_level_cross_screen_untestable`**：条件级共享份额仅 **1.43%**（C172），跨 screen 复验在可得资源上**不可检验**。这是"规格不满足/不可检验"的证据，**不是**"条件级结构不存在"的普遍结论。
- 下一轮（R196）转向**冻结结论（C130）的可靠性重估**：在审计要求下（药物分组内层调参、独立评估单元、细胞聚类 CI、MDE 先验）重跑"both-unseen 时注释替代身份"的增益，回答"项目唯一正结果在修正协议下是否仍成立"。

## 1. A3 门槛与结果

| 门槛 | 阈值 | 实测（DrugComb v1.5 full；本机其它候选） | 判定 |
|---|---|---|---|
| G1 独立测量组（不同 study/lab/publication，非同板 barcode 分半） | ≥2，每组 ≥100 combo blocks | **20** 个合格 combo study（Publication/AstraZeneca/NCATS Tripod） | PASS |
| G2 共享细胞系（组合测量，严格归一 + 碰撞报告） | ≥200 | **41**（最大单对 study 共享 13：ALMANAC×ASTRAZENECA） | **FAIL** |
| G3 跨组匹配条件单元（cell×无序药对，≥2 独立组） | ≥10,000 | **4,179**（4,158 在 2 study、21 在 3 study；仅 1,362 落在"≥2 共享细胞"study 对；Q 四元组上界 123,538 的另一读法下仍因 G2 失败） | **FAIL** |
| G4 噪声标定（组内重复） | ≥5% | 23.59% | PASS |
| G5 组合协同端点（Bliss/ZIP/ΔEMAX 类） | 存在 | 14 个响应/派生列存在（仅表头；未读值） | PASS |
| G6 与 Jaaks 重叠 | 报告 | 共享细胞 49 / 药物 52；匹配单元 103（实体）/615（药对） | 报告（"独立资源"表述须限定） |

- **DrugComb v1.4（本地全量）**：466,033 combo blocks / **112 细胞** / 380,418 单元；9.63% 单元有 ≥2 blocks（多为同 study 重复板）；100% block_id 可映射 v1.5 study，但仅 621 个重复单元跨 study → **112<200 结构性 G2 失败**，且无 study 列（G1 独立性不满足）。
- **本机其它**：PRISM primary/secondary 共享 568 细胞但**均为单药 log2 fold-change → G5 失败**；BeatAML 单药/患者样本 → G2/G5 失败；O'Neil 39 细胞/3 BatchID（同一研究 lab，批次≠独立 screen）→ G1+G2 失败；Jaaks 96 共享细胞（C171，非更大独立资源）；`gdsc2_fitted`/`batchie`/`nci_almanac` 本地目录为空 → `data_unavailable`（检索缺口，不写"不存在"；ALMANAC 60 细胞只能经 DrugComb 访问）。
- **实测文件 ≠ 发表 S1 表（必须披露）**：34 study/1,432,351 行（combo 739,964 + 单药 692,387）vs S1 表 37/1,469,182；缺 3 个纯单药 study（ELLINGER/GORDON/TOURET），若干 study block 数不同 → 门槛一律用实测文件。
- **下载**：仅 DrugComb v1.5 full（1,421,694,989 B，≤1.5 GB 预算；URL/MD5/SHA256 回执在 `a3_overlap/download_receipt_a3.json`）；raw dose-level（2.0 GB）超预算未下载 —— 剂量等价补验属新预算/新协议，不属 qualified_with_conditions。

## 2. 所需资源规格（下一资源门槛；解冻条件）

1. **≥2 个独立组合 screen/study**（不同 lab/publication/screen，非同日/同板 barcode 分半），每组 ≥100 combo blocks；
2. **≥200 个共享细胞系**（≥2 独立组均有组合测量，严格归一名 + 碰撞报告）；
3. **≥10,000 个跨组匹配条件单元**（cell×无序药对，且**剂量设计等价可验证**，或提供 raw dose-level 数据）；
4. **≥5% 匹配单元有组内重复**（可标定噪声）；
5. **校准的组合协同端点**（Bliss/ZIP/ΔEMAX 类）+ QC 元数据 + 非饱和证据，且 **condition×cell 交互不得主导**（A2 已测 48.5% 交互 / 46.1% 噪声）。

## 3. 核验与产物

- Lead 核对：A3 产物 SHA256 与报告一致（PROTOCOL_A3 `E7E6ED2D…`、a3.py `CDFEA4F1…`、a3.json `B466FE87…`；报告称两跑逐字节相同）；判定/门槛与 a3.json 一致；响应列仅表头存在性（12/14 响应列存在，未读值）。
- 产物（`research/2026-10-27-conditional-shift/`）：[PROTOCOL_A3.md](../2026-10-27-conditional-shift/PROTOCOL_A3.md)、[a3.py](../2026-10-27-conditional-shift/a3.py)、[a3.json](../2026-10-27-conditional-shift/a3.json)、[report_a3.md](../2026-10-27-conditional-shift/report_a3.md)、[record_a3.md](../2026-10-27-conditional-shift/record_a3.md)、[usage_a3.json](../2026-10-27-conditional-shift/usage_a3.json)、`a3_overlap/`（6 表 + 下载回执）。
- 边界：`not_qualified` 只在"已核查资源范围"内成立；不写"不存在"；不启动 B/C/acquisition；未晋升代码；总体目标未达成。


## 4. ERRATA（外部重审后，2026-10-27）

依据 `research/2026-10-27-cross-domain-directions/late_results_audit.md`：

1. **门槛范围**：G2≥200 共享细胞、G3≥10,000 匹配单元是「冻结的大规模跨 screen 设计」门槛，未从配对效用/正确依赖功效反推；**不能**推出「所有条件复验均不可检验」。较窄问题（固定条件/背景/细胞子集/单 study 内描述性一致性）可另定可测科学对比与真实决策后再推断所需独立支持，但不得偷换成原协议成功或用新切分伪造未暴露确认。
2. **独立 screen 证据**：study_name/publication 不同只定位数据出处，不自动证明无复用筛选/无重发布/独立培养；无序药对 summary 交集不满足 controlled_anchor 的同方向/数值剂量/端点等价；block 重复 ≠ 独立培养（G4 只是潜在测量机会）。
3. **「condition×cell 交互不得主导」不是普遍资源资格要求**：背景依赖规律恰可能位于 condition×cell 交互（秩 1 反例）；资源要求应改为「误差与目标信息可区分」，不得用 A2 的 48.5%/46.1% 分割当作排除资源理由。
4. 见 [ERRATA_A3.md](../2026-10-27-conditional-shift/ERRATA_A3.md)；C175 为更正入口。A3 的计数与「冻结大规模设计未准入」结论不变；A3 通过≠条件级结构存在/可迁移；不启动 B/C/acquisition。

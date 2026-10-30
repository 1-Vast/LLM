# record — R198-A1 关系冲突信号机制（设计/先例）过程记录

2026-10-27。角色：R198-A1 机制探索（**只做设计与先例；不运行效果、不训练、不读响应做效果**）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-innovation-scouting/conflict_signal/` 与 `tmp/`；未改 `PROTOCOL_*`、其它研究目录、INDEX、SYNTHESIS、git、源数据。

## 1. 范围与预算

- 范围：把用户 17:44 重审后的主线"少量功能反馈区分三类失败——(i) 数值需调整 / (ii) 共享关系适用条件失效（关系冲突）/ (iii) 表征遗漏关键状态——并用于未测药物选择"落成可证伪机制规格、机制候选、先例覆盖与 protocol 草案。
- 不在范围：任何效果实验/模型训练/拟合/响应值分析；不重跑 I003/可检出性门控/预测方差采样；不做机制/靶点/临床主张；不声称新颖性。
- 预算：本地阅读 + 有界检索（5 次 web_search 调用、15 条 query）+ 纯代数构造；无 GPU/湿实验/大数据下载。

## 2. 时间线与命令

| 时间 (≈UTC+8) | 动作 | 产物/结果 |
|---|---|---|
| 18:03–18:05 | 读 task-24，认领（rev1→2）；读 R193 BRIEF/相关目录列表 | task 认领完成 |
| 18:05–18:15 | 必读：`cross-domain-directions/report.md`（29 KB）、`directions_v2.md`、`evidence_notes.md`、`challenge.md`；`handoff-method-audit/report.md`；`SYNTHESIS.md`（C141/C154/C160/C167/C171/C172/C174 边界）；`conditional-shift/ERRATA_Q2.md`；`CLAIM_STATUS_AUDIT.md`（C174 定义） | 边界与最新状态吸收（只读） |
| 18:15–18:22 | 本地先例源盘点：`cross-domain-directions/challenge_sources/`（AlphaEdit v4 HTML、复现研究 v2 HTML、LOGICZSL PDF+txt）、`data/external/research_sources/20261023/functional_mechanism_frontier/`（alphaedit/replication/search/revision 等）、`lit/` | 复用已核原文；新增未复现声明 |
| 18:22–18:30 | 数据可用性盘点：Jaaks Original/Validation（R193-A0 `matching_qualified`）、DrugComb v1.4/v1.5（R190–R195 边界）、BeatAML（单药）、DepMap 19Q4/gdsc2_fitted/tahoe/sciplex3 等 | 写入 spec §6 可算性表 |
| 18:30–18:42 | 有界检索：5 次 `web_search`（15 条 query，原文见 §3）；`web_fetch` 对 aclanthology/arxiv/ar5iv 均返回"non-public IP"（同 SYNTHESIS C58），**新条目只能到索引/摘要级（R/A）** | `prior_art.md` §0 检索范围 |
| 18:42–18:58 | 写 `spec.md`：三类失败 operational 定义、四对照量正交化、确定性反例构造、M1/M2 机制、可算性表、P1–P7 可证伪预测、挑战接口 | spec.md（SHA 见 §5） |
| 18:58–19:06 | 写 `prior_art.md`：AlphaEdit/AlphaEdit+/LOGICZSL/Poke&Strike/PDTSyn/BATCHIE 逐条 + R 级相近先例 + 覆盖结论 + 新颖性边界 | prior_art.md |
| 19:06–19:12 | 写 `protocol_draft.md`：数据/反馈集、关系集施工、更新器与对照、δ_min/MDE 预注册流程、失败类别、停止条件、泄漏防护、最小实验 | protocol_draft.md |
| 19:12–19:15 | 写 `record.md`/`usage.json`；计算交付物/证据文件 SHA256 | 本目录 |

单命令耗时均 <1 min；无效果运行。

## 3. 有界检索记录（本轮新增，索引级；不声称穷尽）

5 次 `web_search` 调用，query 原文：

1. `knowledge editing protected relations conflicting new evidence constrained update drug response pharmacology`
2. `Poke and Strike task sensitivity parameter identification drug screening feedback`
3. `drug combination prediction model failure mode relational conflict versus representation missing context`
4. `AlphaEdit biomedical model editing drug discovery pharmacogenomics`
5. `model editing conflicting knowledge AlphaEdit ACL 2026 findings`
6. `detect misspecification versus parameter shift online feedback experiment design`
7. `drug combination transfer learning applicability condition violation detection`
8. `knowledge added drug response prediction constrained relation violation test`
9. `Poke and Strike learning task-informed exploration policies parameter identification abstract`
10. `logical constraints drug combination synergy prediction knowledge graph 2025 2026`
11. `model misspecification detection structural change versus parameter drift online learning feedback`
12. `context-specific drug combination effect inversion cell line prediction prior relation violated`
13. `knowledge editing drug response prediction biomedical knowledge graph conflicting evidence`
14. `concept drift taxonomy real drift virtual drift conditional change relation`
15. `active learning model selection misspecification detection number of experiments distinguish hypotheses`

命中（仅索引/摘要级）：AlphaEdit+（ACL 2026 Findings，冲突/不一致知识下的模型编辑）；Poke&Strike（arXiv:2509.00178，ar5iv 片段）；SynergyGraph（Sci. Rep. 2025，细胞系特异协同 + KG/超图）；"What Changed? Drift Detection with Real, Virtual, and Incomparable Diagnosis"（arXiv:2609.27865）；概念漂移综述（arXiv:2203.11070）；Lovell et al. 2011（PMLR，用最少实验区分假设）。**均未取全文**（web_fetch 失败），覆盖判定已按 R/A 级标注。

## 4. 观测与决定

### 观测

1. 既有边界：C141（只能排组合不能排细胞）、C154（主动学习在正确粒度上已测、无优势）、C160（细胞状态分支停在检定力，不是无信息）、C167（R192 `not_replicated` 未校准功效、不得当阴性）、C171（R193-A1 `inconclusive`、MDE80 0.2042 > δ_min 0.0893）、C172/C174（1.43% 仅加性条件主效应份额；加权矩/依赖单位/可靠性须重核）、R195（大规模跨 study 门槛未过、但不关闭较窄条件问题）。
2. 既有数据入口（不运行）：Jaaks Original/Validation 的 R193-A0 匹配四元组（6,223,367；controlled_anchor 92,039；96 细胞/98 有向药对）；DrugComb v1.4/v1.5（R190–R192 边界）；BeatAML 单药；DepMap/gdsc2 可作基线细胞特征；ComboCat unqualified；O'Neil 独立培养不足。
3. 先例覆盖（有界）：AlphaEdit/LOGICZSL/Poke&Strike/PDTSyn/BATCHIE 的**机制本身**均有先例（P 级）；但"关系冲突的分类证书 + 决策精度门控"用于**药理组合反馈**：本轮有界检索**未发现**直接应用；"三类失败区分"**未发现**先例。零命中不写"不存在"。
4. 三个可区分对照量（`R_abs`、`C_conf`、`L_lev`、`O_rep`）在确定性构造中可独立变化（spec §4 表）：残差大但 Q=0（i）；残差小但 Q=1 符号翻转（ii）；leverage 与 Q 独立。故"关系冲突"不是残差/距离/leverage 的改名——但是否在真实数据上独立**是要检验的假设**，不是已成立结论。
5. (iii) 在现有数据上**不可认证**：组合资源没有配套可测状态（时间/培养/处理中读数）；单细胞扰动资源端点不同。只可做诊断代理（`O_rep` + 全释放残差结构）。

### 决定

1. **三类失败采用可辨识性优先的写法**：先写"单批反馈不足时输出 `not_identifiable`"，再给最小可辨识设计；不给出一个在所有情形下自动分类的"冲突分数"。
2. **关系冲突判据必须三件套**：`C_conf`（nuisance-正交关系空间违约）+ `X_flip`（≥2 独立上下文的符号/排序翻转）+ `J_min`（最小释放集结构）；同时报告 `R_abs`/`L_lev` 作对照；任一单独量大不判 (ii)。
3. **机制候选 2 个**：M1 = 受保护关系更新 + 冲突证书（AlphaEdit 启发的约束更新；线性情形必须与投影核等价对照数值等同）；M2 = 决策精度门控的冲突消退（Poke&Strike 启发；仅在 Stage 2 采样比较，且无合法区分测量时必须拒绝购买/宣称）。
4. **协议分期**：先固定反馈比较更新器（Stage 1），出现可归因增量后才比较 acquisition（Stage 2）——遵循 cross-domain report §7 的顺序，避免更新器与采样一起换而无法归因。
5. **δ_min 不编造数值**：draft 只写定义流程（从任务成本/最小有用差异，看到效果前写死；不用旧 CI 下界倒推），并把 MDE/功效预检作为冻结前硬门；数值留待成本/效用冻结时确定。
6. **不声称新颖性**：所有机制成分有先例；组合是待检验的科学问题，不是已成立算法。报告了 AlphaEdit+ 与漂移诊断等近似先例（R 级）避免"没人做过"的误写。

## 5. 交付物与哈希（写入时）

| 文件 | SHA256 |
|---|---|
| `spec.md` | `488F719D5A6BD436612FD146A8DB4B068253D002C6B9FFF87EE771C9850599DD` |
| `prior_art.md` | `1753352C040BDFD39A15848B35CD2B83CB013DB2FBF3AD2BDD0B8CCFC8114193` |
| `protocol_draft.md` | `550E9AE14A8BC4663D3FC6CEAEC1CC3461DE61B0C537EABA4C18B6E5CDDF7FD6` |
| `record.md` / `usage.json` | 见写后快照（本文件自身与 usage 不嵌自身哈希） |

**只读证据文件 SHA256（本轮阅读快照）**

| 文件 | SHA256 |
|---|---|
| `research/2026-10-27-cross-domain-directions/report.md` | `B238CD848C2CFBB5987487415EB34D560EEE94387A6AB7FA73B50BFBCECED87B` |
| `.../directions_v2.md` | `CA81B5AE8E86BC057EB4E6C6C857455CDAFF012F544BDA5C52BD149AEF8A2A06` |
| `.../evidence_notes.md` | `22BD3EC8EE015BC817482B3E7D512659790C88A805FD3ECB82F63125713BD50A` |
| `.../challenge.md` | `DE558202051FAC1F6A3C517C5B17A7551C4594E73ECEAD379283F8FE2BE582F6` |
| `research/2026-10-27-handoff-method-audit/report.md` | `FCF876787B1E9D94D899D04BA0F7CB81B946D4253A0E781334128D5EC5A97F10` |
| `research/SYNTHESIS.md` | `4499C5EB620517E7F1A7599762FD0A1E8A11E6E5EF9468E1E84E3C4EA4B261E6` |
| `research/2026-10-27-conditional-shift/ERRATA_Q2.md` | `B8E0F3CDE76791A9156F954CBB77BD95FE12C38A83F31BF32816F700A6393348` |
| `research/CLAIM_STATUS_AUDIT.md` | `21147A07288F4C6676A7CCDE37926AE34429700F14C5652423D54ACE8CCC4F9D` |

本目录未生成代码/数据文件（本任务是设计/先例，不需要运行脚本）；无响应值被读取或写出。

## 6. 局限

- **未验证**：三类失败在真实数据中是否可区分、冲突证书是否有决策增量、M1/M2 是否优于强基线——全部是待检验预测（spec §7、protocol_draft §6），本轮无任何效果证据。
- **先例覆盖有界**：新增检索只能到索引/摘要级（web_fetch 不可用）；已核原文来自既有本地快照（AlphaEdit/LOGICZSL P 级；Poke&Strike/PDTSyn/BATCHIE 为上一轮 P 级笔记）。零命中≠不存在。
- **关系集尚未构造**：protocol_draft §2 的施工规则未执行（本轮不运行），关系数量/误差带/稳定性未知；这是冻结前必须完成的独立步骤。
- **(iii) 目前不可认证**：无配套可测状态；只给出所需最小新测量（spec §8），不预测其可得性。
- **δ_min 无数值**：成本/效用未冻结，draft 拒绝编造数值；Stage 1 若无法定义成本，只能报 MDE/区间，不判成功/失败。
- **数据边界**：Jaaks 剂量只到已发布设计列、screen/批次混淆、同组织为主（R193-A0）；DrugComb 外部确认受 study/端点/功效未校准限制（R192）；BeatAML 单药；ComboCat 排除。
- 报告中的确定性构造只是"对照量可独立变化"的算术例（不证明真实数据存在对应结构）；不涉及任何响应读数。

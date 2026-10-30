# 轮次记录 — R189 线 B：I003 先例定向核验与独立挑战（task-2 / task-3）

2026-10-27。角色：定向文献核验员（lit-verifier，task-2）＋ 独立挑战者（i003-challenger，task-3）；Lead 负责冻结候选、综合裁定与核验。本目录同时承载线 B 的检索源文件；线 A（ComboCat 资格审计）在 `../2026-10-27-combocat-resource-audit/`。

## 范围与预算

- 范围：回答两问——(1) 候选 `I003.v1`（可分辨性约束的决策聚焦证据选择）的最近先例覆盖与剩余差异；(2) ComboCat 原文中 A2 外部复现所需的事实（dense 设计/端点/重复/注释与身份可得性）。
- 预算（BRIEF §2）：2 个定向检索 pass；本地已存文件阅读不计；受限域名重试 ≤2 次；不算力型实验、不运行效果实验。
- 实际消耗：**PASS 1（承接完成，无新增网络）＋ PASS 2（1 个新 pass，EPMC/OpenAlex 合并查询；arXiv API 2 timeout+1 429 记缺口 G1）**。详见 [pass_log.md](pass_log.md)。

## 时间线

| 时间 (UTC+8) | 动作 | 产物 |
|---|---|---|
| 11:18–11:25 | 承接线 B 侦察：arXiv 5 篇、BATCHIE 全文、ComboCat 全文/sentences、MOESM 补充材料、EPMC/OpenAlex 查询落盘 | `sources/` |
| 11:16–11:18 | 候选 v1 冻结（`../2026-10-27-innovation-round-r189/CANDIDATE_I003_v1.md`）；检索预算写入 BRIEF | BRIEF/CANDIDATE |
| 12:20–12:36 | 独立挑战（只读审查；未运行效果实验） | `challenge_I003.md`（10 项判决、7 FAIL/2 WEAK/总判 stop） |
| 12:40–12:51 | 先例核验完成：35 条逐字引文回查（脚本 `sources/queries/verify_evidence_quotes.py`，0 miss） | `evidence.md`、`pass_log.md` |
| 12:51–13:10 | Lead 综合：谱系核验、引文抽查、候选撤回状态、轮次记录/索引/登记更新 | `../2026-10-27-innovation-round-r189/record.md` 等 |

## 观测与决定

1. **先例覆盖＝部分覆盖。** decision-focused acquisition 已由 GoBOED（arXiv 2605.26093，"fully decision-focused"）与决策聚焦序贯设计（arXiv 2602.05340，directional uncertainty 更早停止）直接实现；"acquisition × sigmoid 门控"乘积结构见 R-IDeA（arXiv 2506.07805；门控变量是模型错设残差 `|f̂−g|`，不是测量可分辨性/MDE）；噪声/识别 SNR 与预算 regime 见 arXiv 2605.04895；决策价值 vs 样本量/成本属成熟 EVSI/ENBS 家族（页目级）。**唯一未发现先例的物件**＝"以每动作实际重复数 r 与板内 σ 计算 MDE 作为 acquisition 准入闸"（PASS 2 零命中：EPMC power×acquisition=0；OpenAlex decision-focused∧acquisition=0、statistical power∧BOED=0）。零命中只作检索结果记录，不写成"不存在"。
2. **剩余差异均为构成/应用层**：R1 MDE 闸变量、R2 行级物理成本、R3 两药未见先验进 acquisition（本轮不可检验）、R4 top-k 边界带拒绝规则（GoBOED 的决策无关方向不敏感性已是理论近邻）。不足以支撑"新算法"主张；按 BRIEF §3 应收窄为**评估修正**或停线。
3. **候选表述更正**：候选 §4 称 BATCHIE 有"SNR 惩罚的 DBAL"，正文未检出该惩罚项（正文是 PDBAL：最小化后验样本间期望距离）；"undetectable"仅出现在 phase-I 孔失败的数据质量语境。补充材料未下载，只作正文级更正（缺口 G3）。
4. **ComboCat A2 事实**（供 A1 交叉核对，见 `evidence.md` F19–F30）：dense 模式 806 组合、>290,000 测量、每组合 3 个 10×10 矩阵重复＋单药/对照重复、**每块板只测 1 个组合 ⇒ cell×pair 单元共 806、无药对跨细胞系重复**；sparse 模式只实测对角 10 剂量对、其余 90 为模型补全（不得当实测）；端点 `raw_val`/`perc_cell_death`/`bliss_synergy`/`mean_syn`/`flagged_final`；**硬阻断**：804/806 root 为 32 位哈希、药名占位符、摘要表数字键无 join key ⇒ A2 门槛（两药未见 ≥800 + ≥12 注释水平）不可达。
5. **独立挑战**：10 项判决 FAIL 1/2/3/6/7/8/9、WEAK 4/5、总判 **stop**。决定性理由：候选沿用 R5 已停 I003.v1 编号与同一对象（主张 B，"不换名重提"）；主分数 S=VOI×D 在 r 固定时与纯决策价值秩等价（H2 即等价性证明）；MDE 的 r/σ 在本归档不可操作化；主对比（I003 vs 纯决策）预期零效应且 H3 不可证伪；与 C141/C154/C144 结构性冲突。
6. **Lead 裁定**：候选 **STOP/撤回**（`CANDIDATE_I003_v1.md` 加状态节，原文保留）；本轮不运行效果实验；唯一保留物＝"把无法分辨的对比整类判为不可作为证据→改变动作集与停止条件"，须新编号、重新登记、先解决 r/σ 与 R4 T307/T309 准入闸，且只能作评估修正。

## 局限

- 检索非穷尽：G1 arXiv API 不可达（PASS 2 未覆盖 arXiv 侧；已本地覆盖 5 篇关键全文，不能排除未下载先例）；G2 EVSI/ENBS 仅题录；G3 BATCHIE 补充材料未下载；G4 ComboCat 身份只查已下载发布物，"未找到映射"≠"映射不存在"。
- 挑战与核验为两名独立只读代理；其模型/有效设置未由运行时确认。引文抽查由 Lead 复核，未逐条复读全部 30 条 FACT 的上下文。
- 本记录不声称任何新颖性、收益或机制结论；未晋升代码。

## 交付物

- [evidence.md](evidence.md)（F01–F30，四节 FACT 清单）、[pass_log.md](pass_log.md)
- [challenge_I003.md](challenge_I003.md)（独立挑战，10 项判决）
- `sources/`：arXiv/EPMC/OpenAlex 一手全文与查询响应、ComboCat 补充材料、`sources/queries/verify_evidence_quotes.py`、`sources/extracts/combocat_dense_supp_workbook_audit.txt`
- 轮次综合：[../2026-10-27-innovation-round-r189/record.md](../2026-10-27-innovation-round-r189/record.md)；候选状态：[../2026-10-27-innovation-round-r189/CANDIDATE_I003_v1.md](../2026-10-27-innovation-round-r189/CANDIDATE_I003_v1.md)

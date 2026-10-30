# R200-D5-C1 独立挑战（challenge_D5.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3 同一独立挑战者；未参与 D5 起草）· 对象：`research/2026-10-27-direction-mechanism-expansion/d5_temporal/{PROTOCOL_D5.md, d5.py, d5.json, report_d5.md, record_d5.md, usage_d5.json}`。
方式：**只读复核**（文档/JSON/资格数字/折清单/门设计；**不运行效果、不拟合预测、不读表达或响应矩阵**）；只写本文件与 `tmp/`。
完整性：`d5.py` SHA `1422CB54…DD2DCE1`；`d5.json` SHA `82330743…C2229624`；`PROTOCOL_D5.md` SHA `3923FE7D…623711A7`；`report_d5.md` SHA `C94E0F9F…CCF561E0`；`record_d5.md` SHA `D15286BA…222B461`；`usage_d5.json` SHA `E360377C…8927614`；折清单 manifest `c258f5b0…df78b3`——均与记录一致。

## 0. 总判决

**revise（≤5 必改；当前不可 approve_to_lead_exec；不是 stop）。**
D5 的**大结构基本正确**：6h 33,072 / 24h 101,610 细胞；obs 全唯一、**无同细胞/lineage 配对**（破坏性快照）被正确承认；285 键名称级共享、control 时间匹配但载体未认证；**无功能终点** → 功能 not_qualified；无 exposure/dose/batch/独立培养/重复；V2 15–19<20；严格时间切分/未来时点禁入/V1 禁两快照/V2 早时点限制/fold SHA/零模型/G0–G5/MDE 预判/失败停止/边界/A3 仅背景均基本自洽；MDE 上界高、G3 高失败风险→evaluation_cannot_distinguish 的处理诚实。
**但资源资格与 primary 不能直接批准**：V1 的“4 药等权”包含 **BRD3379 0.0 µM**（protocol §2.3 自己承认“BRD3379=0.0 与处理臂矛盾”），其 95 条合法线占 primary 的极大权重；零剂量臂不能作为 active drug 进入 4 药等权平均。其次 V2 `paired_n=2` 与 `nested_paired_line_sets` 的 15/16 线不一致，H-D5-2 的配对 n 需写死。修完这两项（及相应 G0/primary/d5.json/report）后可再挑战/approve_to_lead_exec；本轮不建议直接运行。

**最致命 3 条**

1. **BRD3379=0.0 µM 被当作 V1 第四药**（protocol §2.3 line63 明确矛盾；`d5.json.v1_exact_6_24.per_drug.BRD3379` 95 线；`primary_contrasts.V1_...per_drug_n.BRD3379=95`）。零剂量不构成 active perturbation；若是 vehicle/control，则 V1 的 4 药等权平均混入对照，H-D5-1/G4/“4 drugs”状态全部失效。**必须排除 BRD3379 出 primary 或提供独立证据证明 0.0 是有效剂量并重做资格**；在修正前不能称 `qualified_with_conditions` 的 4 药 primary 已自洽。
2. **V2 配对 n 不一致**：`d5.json.primary_contrasts.V2_extra_early_snapshot.contrasts[*].paired_n=2`（target24h/target48h）与 `v2_hashed_arm.nested_paired_line_sets` 的 **15/16 配对线**、`n_E1/n_E2` 18/15、19/16 冲突。H-D5-2 的“paired Δρ”必须明确使用配对线集合（15/16 等），`paired_n=2` 至少是字段语义错误；否则执行时可能用错 n/错比较。
3. **资格判定必须加 active-dose/G0 条件**：当前 `G0_eligibility` 只检查“每药 ≥20 线”，不检查剂量/处理有效性；因此 BRD3379 0.0 仍 pass。需在 G0 增加“active dose/处理身份”门（或明确 BRD3379 为 control/排除），并更新 `overall_D5` 的 conditions/报告；否则“qualified_with_conditions”不保守。

## 1. 逐项判决

### ① 资源资格（PASS 主体；BRD3379 处 FAIL） 

- **6h/24h 细胞数**：33,072/101,610；**obs index 全 182,875 唯一** → 无 barcode 同细胞早–晚配对；无 lineage/cell_id；**破坏性快照**被正确承认；**PASS**。
- **285 键 perturbation 名称级共享**、115 细胞系；control 6h/24h 各 115 键；**时间匹配但载体/病毒身份未认证**；**PASS（有披露）**。
- **V1 合法线 95/22/24/24** 数字与 d5.json 一致；**但 BRD3379 0.0 剂量矛盾未解决** → **FAIL（见致命 1）**。
- **V2**：20,028 cells → 17,553 single-tag / 13,713 normal；24 线；每 (treatment,time) 1 sample label；严格匹配 n=15–19<20 → **exploratory_only**；**PASS**。
- **无功能终点**：h5ad 无 viability/apoptosis/regrowth/IC50/response 列，obsm/layers/uns 空；RNA 代理≠功能；**functional not_qualified/data_unavailable**；**PASS（保守）**。
- **无 exposure/duration、dose 清洗未完成、无 batch/plate/run/donor、6h channel 全缺失、无独立培养/重复**；**time_axis_unverified**；**PASS（正确披露）**。
- **判定整体**：molecular qwc、functional not_qualified、time_axis_unverified、overall qwc 的**结构自洽**；但 **BRD3379/4 药**使 “qwc” 的 primary 资格不保守 → **WEAK/FAIL**。

### ② 严格时间切分/防泄漏 —— **PASS（设计层）**

- **V1**：外层 leave-cell-line-out 5 折（合格线按名称排序，`fold=index%5`，同 cell line 同折）；内层训练折内按 cell line 分组；**未来时点绝不入输入**；**V1 禁止两快照拼接**（C3 only V2）；**PASS**。
- **V2**：目标 24h 只用 3/6/12h；目标 48h 只用 3/6/12/24h；3h 无更早输入不作目标；目标固定；leave-cell-line-out；**PASS**。
- **折清单 SHA** `c258f5b0…`；种子 20261027；manifest `d5.json` 有 V1/V2 每折线表；**PASS**。
- **零模型/泄漏哨兵**：N0 mean、N1 cell-shuffle、N2 drug-shuffle（V1）、N3 time-shuffle（V2）、N4 capacity、N5 future-leak sentinel、N6 static-capacity；**可实现/可执行**（设计层）；**PASS**。
- **未披露泄漏路径**：同板/同批/同细胞系重复**因无 batch/plate、obs 全唯一、cell-line holdout 被排除**；但 **no batch metadata** 仍是 `time_axis_unverified` 的已知限制，不构成未披露。**PASS（带条件）**。
- **V1 4 药**中的 BRD3379 不是时间切分泄漏，而是 **active-dose/资格**问题；见致命 1。

### ③ 假设/指标/判定门 —— **PASS 主体；V2 paired_n 需修**

- **H-D5-1/V1**：`Δρ_d=ρ(early6h)−ρ(static)`，4 药等权平均；主=within-drug cross-line Spearman；**主假设可证伪**（early≈static→no_increment；MDE/room/reliability不过→evaluation_cannot_distinguish）；**PASS**（除 4 药含 BRD3379）。
- **H-D5-2/V2**：`ρ(E2)−ρ(E1)`，capacity control 不得复现；n=15–19<20 → exploratory；**假设可证伪**；**但 `paired_n=2` 字段错误**，需修。
- **H-D5-3**：`gap=ρ_oracle−ρ_early`；gap≤MDE80→精度内足够；**描述性**；**PASS/WEAK**（MDE 高时“足够”语义弱，但不作 primary）。
- **H-D5-F**：功能不可检验→data_unavailable；**PASS**。
- **δ_min=0.10、G0–G5、split-half rho_sb、room、MDE80 upper**：V1 0.409/0.865/0.826/0.826；V2 0.93–1.06；**G3 预判高失败风险→evaluation_cannot_distinguish**；**honest**；**PASS**。
- **失败类别/停止**：data_unavailable/design_invalid/evaluation_cannot_distinguish/no_increment/exploratory_only/time_axis_unverified/functional_route_not_qualified/identifiability_unsupported；停止不换端点/阈值/切分、不补中间时点；**PASS**。
- **PASS 但需执行前写死**：V2 paired line sets 15/16（见致命 2）；G4 只 V1；V2 只描述。

### ④ 边界/A3 复用 —— **PASS**

- A3v2 `L1 feasible/L2 blocked` **仅背景**；D5 独立复算；未复用 A3 未认证的功能/批次/剂量/同批；**PASS**。
- 不重开 R196v2/R197v2；C176/C177/C179/C181/C186 仅背景；**PASS**。
- 不称新颖性/细胞状态机制/迁移/决策收益/真实轨迹；功能/决策等新测量；**PASS**。

## 2. 必改（≤5）

1. **解决 BRD3379 0.0 µM**（最高优先）：在 V1 primary 中**排除 BRD3379**，改为 **3 个 active drugs：Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24**；BRD3379 只能作为 **zero-dose/vehicle-like control/secondary**（需明确标签），不得进入 4 药等权平均。或者，若坚持 4 药，必须提供独立剂量/处理 identity 证据证明 0.0 是有效剂量，并重做资格/primary；当前不得称 4 药 self-consistent。同步更新 `G0`（每药 n≥20 的 active 检验）、`primary_contrasts`、`v1_exact_6_24`、`H-D5-1`、报告/记录/协议、MDE 表（去掉 0.409 的 BRD3379 或改标 control）。
2. **修正 V2 配对字段**：把 `paired_n=2` 改为**配对细胞系数量**（target24h E1/E2 **15**；target48h E1/E2 **16**、E2/E3 **15**；以 `nested_paired_line_sets` 为准），并在 H-D5-2/primary_contrasts 明确 **paired line sets**、E1/E2/E3 的 n；禁止把 `paired_n=2` 当线数。
3. **G0/资格加 active-dose 门**：G0 除每药≥20 线外，加“active dose/处理身份已核”条件；BRD3379 未核前不 pass；更新 `overall_D5` conditions 和 report §2/§3；整体可仍 qwc（3 active drugs）但不得写 4 药 primary。
4. **更新 d5.json/report/PROTOCOL_D5/record/usage 的 4 药表述与 MDE/primary**：若排除 BRD3379，V1 primary = mean over 3 active drugs；MDE upper 只列 Bortezomib/Idasanutlin/Trametinib（.865/.826/.826）；G3 预判仍 evaluation_cannot_distinguish；不得保留 “4 drugs n>=20” 的 confirmatory 状态。重算 d5.py/d5.json SHA 并记录。
5. **执行协议前补细节**（即使修完也需另立执行协议）：数据加载（h5ad obs/表达、QC/pseudobulk/control/200 gene panel）、折清单 loader/assertion、V1/V2 paired sets、零模型/未来哨兵实现、B1–B8 调参预算/网格、两跑确定性/输出 schema、measured MDE 预认证、失败类别报告模板、G5 代码断言；本轮不运行效果。

## 3. 若修完，可提交 Lead 的执行协议前检查（不是现在批准）

- **V1 3 药**：Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24；BRD3379 作 zero-dose/vehicle control（不参与 active primary）。
- **V2**：target24h E1/E2 paired **15**；target48h E1/E2 **16**、E2/E3 **15**；n<20 exploratory_only。
- **切分**：V1 5 折 cell-line holdout（`index%5`）；V2 target fixed/earlier inputs；fold manifest c258f5b0…；V1 禁两快照；future-time sentinel。
- **门**：δ_min=.10；G0 active n≥20；G1 rho_sb≥δ+MDE；G2 room≥max(δ,MDE)；G3 MDE≤δ；G4 mean Δ≥δ & CI lower>0；G5 no leak；V2 only exploratory；G3 高失败→evaluation_cannot_distinguish，不写阴性。
- **边界**：功能 not_qualified、time_axis_unverified；不称机制/迁移/决策收益/新颖性；A3 仅背景；不重开旧轮。

## 4. 复核证据与本轮边界

- 实际 SHA：d5.py `1422CB54…`、d5.json `82330743…`、protocol `3923FE7D…`、report `C94E0F9F…`、record `D15286BA…`、usage `E360377C…`；折清单 `c258f5b0…`；均与记录/协议一致。
- 关键矛盾证据：protocol §2.3 line63 **“BRD3379=0.0 与处理臂矛盾”**；d5.json `v1_exact_6_24.per_drug.BRD3379.n_eligible_lines=95`、`primary_contrasts.V1...per_drug_n.BRD3379=95`；`primary_contrasts.V2...paired_n=2` vs `nested_paired_line_sets` n=15/16。
- **本轮未运行效果、未拟合预测、未读表达/响应矩阵、未改 D5/A3 产物**；只读文档/JSON/SHA；只写本文件与 `tmp/`。
- **revise**：修完 1–4 后可再挑战/approve_to_lead_exec；当前不运行、不称 qwc 的 4 药 primary 自洽。冻结≠资源足够/关系成立/Stage1/效果；功能/决策/轨迹等新测量，RNA 代理不是功能终点。

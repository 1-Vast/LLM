# R200-D1 独立挑战（task-93）：独立信息审计 + 目标资格 + 预注册设计

2026-10-27。角色：独立挑战者（非提案者、未参与 D1、不训练/不拟合/不做效应或迁移统计；Q 值只用于精确恒等式核验）。对象：[PROTOCOL_D1.md](PROTOCOL_D1.md)、[d1.py](d1.py)、[d1.json](d1.json)、[report_d1.md](report_d1.md)、[record_d1.md](record_d1.md)、R200 BRIEF、R197v2、A0/q2/ERRATA、R196v2、independent-reassessment。**本轮不运行效果；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_to_lead_exec / approve_to_lead_design，也不是 stop）。**

信息分解（秩/冗余/H197c 可重建）与"0.7206 不能当闭包外证据"的审计是**强且可复核**的；但**目标资格表有一处明确的事实错误（O'Neil 被判为空目录）、T4 可及性结论被夸大**；设计草案又存在 **T3 主目标在自身 MDE 门下不可行 / T2/T1 目标层级未先验锁定 / "去闭包结构模型"未操作化** 三个问题。当前不能进入"最小实验"，修订后可重新提交（大概率只能把 T2 跨 screen 同键作为 primary，T3 降为探索/design_invalid，T4 仍无合格目标）。

最致命 3 条：
1. **目标资格表事实错误：O'Neil 不是空目录，T4 "本地不可得"结论过强**。D1 把 `O'Neil` 与 NCI-ALMANAC/VIS2024 等并列为"空目录 `data_unavailable`"（`d1.json E_target_eligibility` 的 files 字典里甚至没有 O'Neil 条目；report §4 表格同）。本地 `data/raw/oneil2026_qualification/` 有 **7 个文件、40.5 MB**（含 combination response workbook、single-agent workbook、figshare receipts），且 ON1/ON2/ON3 已把 O'Neil 作为组合 viability 资源做过资格/设计/执行；O'Neil 与 Jaaks 有 **9/39 共享细胞**（< D1 冻结的 ≥10 shared cells 阈值），且无 A0 匹配条件/ΔEMAX 同端点 → 它应判 `not_qualified`（`data_insufficient` / `no_operational_target`），**不是 `data_unavailable`**；T4（不同测量/培养）也不是"本地不存在组合资源"，而是"**没有满足 A0 复用门槛的不同测量/培养目标**"（O'Neil 是不同测量但 9<10 且无匹配键）。同时 `nyman2020` 在 d1.json 中记 `empty:false` 却无有效数据文件，分类不一致。目标资格/汇总（qualified=0/condition=1/not=7）与"所需测量规格"都需按这个事实重写。
2. **T3 主目标在自身 MDE 门下不可行，但设计仍写 T3→T2→T1 主推断优先级**：T3 = Validation-only 495 keys；D1 自己写"若 target units independent，MDE80≈2.802/√495≈0.126 > δ_min=0.05，clustered 更差，pre-register MDE gate"（`d1.json F.T3.planning_mde_note`、report §5）。按同一冻结门，**T3 应 `design_invalid: precision_insufficient`**，不能做 primary；T2（9,154 匹配键）未给 MDE，T1（18,782 键）只是同 screen 内部前驱；T4 无合格目标。**目标层级必须在看 target 响应前预注册为"资格+功效之后的选择"**（例如 T2 若 MDE≤0.05 则 T2 primary，T3 只作探索或直接 design_invalid，T1 只作内部前驱），不能保留"T3 优先、失败再换 T2"的次序（那是事后选择）。更重要的是：T2 是**同键跨 screen 复测**，只能检验"同平台/同端点的跨 screen 可复现性"，**不能检验"闭包外/新键结构"**；D1 不能把 T2 的成功写成"闭包外结构可迁移"。
3. **"去闭包结构模型"与"精确闭包重建基线"在 T1/T2/T3 上没有可执行定义**：PROTOCOL §6 只写"closure-excluded 结构模型（只用源侧信息预测目标的非闭包成分）vs 强基线"，没有定义（a）哪些特征块算源侧、（b）如何在训练中排除闭包方向（投影？只用非可重建条目？目标侧 grouped split？）、（c）T2 同键目标上"精确闭包重建"到底用 target training 还是 source Q、贡献是否 0、（d）T3 新键上精确闭包基线的定义（protocol 说 contribution 0，但 target 自身 Q 仍有 4 键闭包结构；grouped split 后需报告）。没有这些，主对比无法实现，也无法判断"闭包外"到底剩什么。

## 1. 逐条判决

| # | 项 | 判决 | 关键理由/证据 |
|---|---|---|---|
| ① | 信息分解（秩/冗余/H197c 100% 重建/C179） | **PASS（可复现性高）** | 我独立核对 `d1.json` 的算术链：K=4,686；rank=**3,005**；nullity=1,681=249（96 cells+156 conditions−3 components 的加性核）+1,432（超结构零空间）；冗余 89,034/92,039=**96.735%**；同行 0.93161595、同列 0.5073936、并集 0.9673508；2,000 条恒等式 `max|err|=0`；λmax=278.487、tol=2.8e-7、最小非零特征值 24（间隔清晰）；H197c 5 折每折 rank(train)=3,005、未用键 0、test 18,408/18,407、`recon_frac=1.0`、`max|err|=0`/`lsqr` 精确重建。SHA 与报告一致（protocol `E693496F…`、d1.py `E9737BF5…`、d1.json `F0DC308F…`），两次完整运行逐字节一致（record §3）。"0.7206 不能作为闭包外结构证据、C179 不变"是正确结论；**这不等于结构不存在**，报告 §2.2/§3 已写。 |
| ② | 共享原始响应/身份 | **PASS** | 每键被中位 64 条目使用（p95 233、max 239）、每块 run 板进入中位 420 条目（p95 852、max 857；按 key max 906）、每条目原始支撑中位 4 行/4 板（64.13% 恰 4 块不同板）；条目对共享 ≥1 键 **0.48%**（20,136,653/4,235,542,741）、共享 ≥1 板 **1.85%**（78,357,125/4,235,542,741；Bonferroni 界 [0,3.16%]）——与 d1.json B 一致；结论"闭包靠全局线性代数耦合而非条目成对共享"成立。229/229 条目同 anchor/同浓度、单端点、单 screen；A0 1.43%/3.94%/94.63% 只读引用并明确"Q 方差份额，不是预测信号" ✓。 |
| ③ | 目标资格 | **FAIL** | **O'Neil 被误判为空目录**（见 §2.1）；**T4 "本地不存在"过强**（O'Neil 是本地不同测量组合 viability 资源，但 9/39 共享细胞<10、无匹配条件/同端点 → 应 `data_insufficient`/`no_operational_target`，不是 `data_unavailable`）；`nyman2020` `empty:false` 但无数据文件，分类不一致；qualified=0/condition=1/not=7 的汇总与"所需测量规格"需按此修正。Validation `qualified_with_conditions` 的条件（独立 screen/板/run、barcode 不相交、96 共享细胞/98 有向对/6,223,367 四元组、同平台端点、9,154/9,649 匹配键、MDE 预注册）本身写得清楚 ✓；但"本地唯一独立操作性目标"的措辞要限定为**跨 screen 同平台/同端点复测**，不能读成独立测量/培养/lineage。其余候选（DrugComb data_insufficient、PRISM/BeatAML/GCP2020 no_operational_target、同资源重编码 same_resource_reencoding、表达资源 no_operational_target）基本正确 ✓。 |
| ④ | 设计草案 | **FAIL/WEAK** | T3 495 keys 的规划 MDE≈0.126>δ_min=0.05，按自身门应 `design_invalid`，但 protocol/report 仍把 **T3→T2→T1** 当主推断优先（§2.2）；T2/T1 未给 MDE，T1 只是同 screen 前驱；"closure-excluded structural model"未定义（§2.3）；精确闭包重建基线在 T2/T3 的定义不完整；closure gate（≤5%）方向正确（H197c 100% 就是反例）但需在目标特定 split 上预注册/预检；MDE=2.802×cluster-SD(Δ) 的 cluster 单位/Δ 定义需写死；等信息/等预算无计算 cap；零模型可设计但需实现细节。 |
| ⑤ | 边界/归因 | **WEAK** | 只写设计/资格、不称新颖性/机制/迁移/决策收益 ✓；R197v2 0.7206 只当待检验对象/C179 ✓；A0/R196v2/A3 状态引用基本正确 ✓；"阴性≠不存在" ✓。**但** report §0.6 把 Validation 称为"唯一独立操作性目标"、§7 说"真正卡点是独立测量/培养目标缺失"——前者把跨 screen 同平台写成"独立"，后者忽略 O'Neil 是本地不同测量资源（只是不满足 A0 阈值）；需限定措辞。 |
| ⑥ | 总判决 | **revise** | 见 §3–§4。 |

## 2. 三个关键问题细节

### 2.1 目标资格表：O'Neil 误判 + T4 结论过强（可核事实）

- 本地存在 `data/raw/oneil2026_qualification/`：7 个文件、40,543,740 B（combination response workbook 38.8 MB、single-agent workbook、figshare receipts 等）；ON1/ON2/ON3 已用该资源做资格/设计/执行。D1 的 `E_target_eligibility` 把 `O'Neil` 放在 "NCI-ALMANAC / O'Neil / VIS2024 / Nyman2020 / Hill2017 / JUMP-CP / BATCHIE / GDSC2" 组，files 字典**没有 O'Neil**，理由"no local files in these directories (empty or absent)"——这是**错误事实**。
- 正确分类：O'Neil 是**独立 screen/板/run、不同测量（combination viability，非 ΔEMAX）**的组合资源；与 Jaaks 共享 **9/39 细胞**（< D1 冻结的 ≥10 shared cells 门槛，见 Q0/ON1 的 9 个重叠细胞），且**没有 A0 匹配条件/同端点** → 应判 `not_qualified`（`data_insufficient` 或 `no_operational_target`），**不是 `data_unavailable`**；T4 的结论应改为"**没有满足 A0 复用门槛的不同测量/培养目标**（O'Neil 有资源但 9<10 且无匹配键）"，而不是"本地不存在组合资源"。
- `nyman2020` 在 d1.json 记 `empty:false`（有子目录无文件），与"empty or absent→data_unavailable"的叙述不一致；应统一为"无有效数据文件"并给 data_unavailable 或相应类别。
- 影响：目标资格表、qualified/condition/not 汇总、T4 的 `required_measurements_if_T4_needed`、"D1 真正卡点是独立测量/培养目标缺失"的结论都要按此修正；**不影响 Validation 是唯一 qualified_with_conditions 目标**这一结论，但理由/边界要准确。

### 2.2 T3 主目标不可行；T2/T1/T4 的目标层级必须预先锁定

- D1 自己写 T3（Validation-only 495 keys）"if target units were independent, MDE80≈2.802/√495≈0.126；clustered design will be worse — pre-register MDE gate"（`d1.json F.T3`）。按 D1 冻结的 `MDE80≤δ_min=0.05` 门，**T3 应 `design_invalid: precision_insufficient`**，不能作为 primary。
- 但 PROTOCOL §6/report §5 的主推断目标写 **T3（若有）→ T2 → T1**；这等于把"会被自己的 MDE 门拒掉的目标"排在 primary 位置，执行时只能事后换 T2（选择性）。必须**在看 target 响应前**写死目标选择规则：T2（9,154 匹配键）先算 MDE；若 T2 MDE≤0.05 → T2 primary；T3 只作探索（或直接 `design_invalid`）；T1 只作同 screen 内部前驱（不是独立目标）；T4 无合格目标 → `data_unavailable` 并写所需测量规格。任何"T3 优先、失败再换 T2"都不是预注册。
- 更根本：T2 是**同键跨 screen 复测**（Validation 是独立 screen/板/run，但同平台/同端点、96 共享细胞），能检验"跨 screen 同键可复现性"，**不能检验"新键/闭包外结构"**；T3 495 键 MDE 又不够；T4 无合格目标。因此 D1 当前**没有一个既有独立 target 又有功效去检验"闭包外/新键结构"**的设计；必须把结论收窄为"跨 screen 同键复现（T2）+ 内部前驱（T1）"，或明确 T3 只 exploratory、不称结构迁移。若 Lead 接受"最小实验只做 T2 跨 screen 复现"，需在协议里写死这个收窄，不能保留"T3→T2→T1"的主推断措辞。
- 另：T3 的 MDE 计算用 `2.802/√n` 是"单位方差/独立单元"的粗算，不是 Spearman Δ 的 MDE；T2/T1 也没有真 MDE。必须用目标侧 cluster-SD/配对 bootstrap 预估并写死（T3/T2/T1 各一列），不能只写一个 planning note。

### 2.3 "closure-excluded structure model" / 精确闭包重建基线不可执行

- PROTOCOL §6 只有一句"closure-excluded structure model（只用源侧信息预测目标的非闭包成分）"，没有定义：源侧特征块、目标侧训练/留出、如何排除闭包方向（投影到 A 的零空间？只在非可重建条目上训练？目标侧 grouped split？）、模型类/调参、与基线同预算的配置；这使主对比无法实现，也无法判定"闭包外"到底剩什么。
- **精确闭包重建基线**：protocol 说"在新键目标上贡献按定义为 0，必须显式报告"；但 T2 是同键重测，精确闭包重建应基于 target training 还是 source Q？T3 的新键目标自身仍有 4 键闭包结构（Q 的 derivation），在 grouped split 后 target training 是否能重建 test entries？需要写死定义并报告 target closure rate；否则基线不可比。
- **closure gate**：方向正确（H197c 100% 重建 ⇒ target 不可识别）；但需在目标特定 split（T2/T3 的 cell/key holdout）上预注册 `recon rate ≤5%` 的预检协议与失败处置（design_invalid/换结构切分），不能把 H197c 的 100% 直接套到 T2/T3 就假定 gate 会过。
- **MDE/δ**：D1 §6 写 `MDE80=2.802×SD_cluster_bootstrap(Δ)`，但 Δ 是 Spearman 差还是 mean-Δ？cluster 是 cell/plate/key？必须写死；T3 的 0.126 只是假设单位方差；T2/T1 需各自预估。
- **等信息/等预算**：只写"同特征块/同调参预算/同计算上限"，没有可核查 cap；树/矩阵补全/GP/直接响应预测的实现与调参预算需 code-level。
- **零模型**：目标内置换保 mask、源-目标映射置换、同维随机特征、同资源换端点负对照可设计，但需要实现细节与算力；"源-目标映射置换"可能破坏 drug/cell 匹配结构，需说明合法性。

## 3. 必改（≤5，最小实验前完成）

1. **修正目标资格表（可核事实）**：把 O'Neil 从"空目录/data_unavailable"改为**本地存在但 not_qualified**（共享细胞 9<10、无 A0 匹配条件/同端点；`data_insufficient`/`no_operational_target`）；修正 T4 表述为"无满足 A0 复用门槛的不同测量/培养目标（O'Neil 是不同测量资源但 9<10 且无匹配键）"；修正 `nyman2020` empty:false/无文件的归类；更新 qualified=0/condition=1/not 汇总与 required measurement specs。
2. **预注册目标层级/功效**：T3 495 keys 先按冻结 MDE 门判 `design_invalid: precision_insufficient`（或只 exploratory），不得 primary；T2 需给出 key-level/pair-level MDE 预定值（≤0.05 才可 primary）；T1 仅同 screen 前驱；T4 无合格目标。写死"资格+功效后选择、不得事后换目标"；并明确 T2 是**跨 screen 同键复现**，不能称"闭包外/新键结构"。
3. **操作化主对比/基线/闭包门**：定义 closure-excluded 模型的源侧特征、目标侧 split、闭包排除方式（投影/非可重建条目/结构 split）、模型类与调参预算；定义精确闭包重建在 T1/T2/T3 的训练集/贡献（含 T2 同键情形），并报告 target closure rate；写死 closure gate（≤5%）的预检、失败处置与换 split 规则。
4. **MDE/δ/rank/聚类/预算**：把 MDE 从"2.802×SD_cluster_bootstrap(Δ)"的模糊写法落到"Δ=Spearman 差、cluster=目标侧 cell/plate/key、配对 bootstrap"的公式；给 T1/T2/T3 各自 planning MDE（基于真实 cluster SD 或预注册的保守假设，不能用 2.802/√n 冒充 Spearman MDE）；设计门 MDE≤0.05 与失败类别；等信息/等预算加可核查 cap（配置数/CV/计算时间/内存）。
5. **边界与措辞/记录**：Validation 只能写"独立 screen/板/run、同平台/同端点、96 共享细胞的 cross-screen 复测；不是独立测量/培养/lineage 确认"；删"唯一独立操作性目标"的绝对措辞；T4/O'Neil 修正；R197v2 0.7206 仍只当 C179 待检验对象、不得写"结构成立/不存在"；A0 1.43%/3.94%/94.63% 只作 Q 方差份额；D1 报告/JSON/协议三处目标资格与 T4 表述保持一致。

## 4. 若后续允许进入最小实验，需补的预注册细节

- **目标选择规则**：T2（若 MDE≤0.05 且 closure gate≤5%）为 primary；T3 exploratory 或 design_invalid；T1 internal precursor；T4 无合格目标（data_unavailable）+ 所需测量规格；不得看结果换目标。
- **切分/closure gate**：T2/T3 的目标侧 cell/key/partner grouped split；预注册 target Q closure reconstruction test（H197c 的 A4 公式在本 target 的 split 上；recon rate≤5% 才可 primary）；失败→design_invalid/换结构 split（预先定义可换的 split 族，不按结果选）。
- **MDE/δ/CI**：δ_min=0.05（Kendall 近似）；MDE=2.802×SD_bootstrap(Δρ) 的公式、cluster 单位（cell/plate/key）、B、seed；T2/T3/T1 planning 值；MDE>δ→design_invalid；rank CI/null 不排除 0→evaluation_cannot_distinguish；no_increment 边界。
- **主模型/基线**：closure-excluded 结构模型的源侧特征块、闭包排除操作、模型类与超参网格；均值/加性/充分调参树（DrEval）/矩阵补全/GP/精确闭包重建/直接响应预测的实现与同预算训练；不得给主模型额外信息/预算。
- **零模型/负对照**：目标内置换（保 mask）、源-目标映射置换、同维随机特征、同资源换端点负对照（仅量化泄漏，不作目标）；各自实现与算力。
- **确定性/输出**：同脚本两跑逐字节一致；JSON 键排序/无时间戳/allow_nan=False；输出 schema（target/split/closure rate/MDE/Δρ/CI/null/失败类别）；输入/脚本/协议 SHA；预算测试（wall/CPU/内存）。
- **边界**：仅开发性；不称独立确认/迁移/决策收益/机制/新颖性；不把 T2 同键跨 screen 写成独立测量/培养；阴性≠结构不存在；R197v2 0.7206 只作待检验对象。

## 5. 声明

- **本轮不运行效果/不训练/不拟合/不做效应或迁移统计**：只读 D1 产物与 R197/A0/A3/Q0/ON1–ON3 记录；未执行 d1.py、未读 Validation/Original 响应值做效应；Q 值未用于任何相关/预测统计；rank/冗余/H197c 数字只做算术与产物一致性核对。
- **D1 产物未改**：仅写本文件与 `tmp/`；未改 PROTOCOL/d1.py/d1.json/report/record。
- **总判决：revise**；信息分解 **PASS**，目标资格 **FAIL（O'Neil/T4）**，设计草案 **FAIL/WEAK**；修正必改 1–5 后，若 Lead 接受"T2 跨 screen 同键复现"的收窄，可再提交 `approve_to_lead_design`（不是 exec）；若 Lead 要的是"新键/闭包外结构"的独立检验，则本地无合格目标/功效，应 `stop` 并写所需测量规格（T4 新测量）。

**一句话：D1 的秩/冗余/H197c 100% 可重建与"0.7206 不是闭包外证据"审计是强且可复核的（96.735% 冗余、3,005 独立值、5/5 折精确重建、SHA/双跑一致），但目标资格把本地存在的 O'Neil 误判为空目录、T4 结论过强，设计又把 MDE≈0.126>0.05 的 T3 495 键放在 primary 优先、而 T2 只是同键跨 screen 复现；且"去闭包结构模型"尚未操作化——判 revise：先修正目标资格/层级/MDE/模型定义，再谈最小实验；若坚持新键/独立测量问题，本地无合格目标，应 stop 写测量规格。**

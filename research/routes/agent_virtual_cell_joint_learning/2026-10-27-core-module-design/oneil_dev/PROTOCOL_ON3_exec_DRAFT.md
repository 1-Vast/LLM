# PROTOCOL_ON3_exec_DRAFT —— ON3 执行协议草案（ON3-READY；待 Lead 批准冻结）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。基于 `PROTOCOL_ON3_v0_2.md`（SHA `97FE124A…`）与 `challenge_ON3_v0_2.md`（**approve_to_lead**，4 项执行前必办）。**本文件是冻结前草案：未运行 ON3 效果/训练/更新器；只完成预算测试、参考实现、单测、两跑确定性、schema 校验与文档。** 冻结条件：同一挑战者复核 + Lead 批准；冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数。

## 0. 依据与状态

- 资格：ON2 v2.2 冻结（`PROTOCOL_ON2.md` `7B34DB79…`）；ON2-EX `calibration_passed`（σ̂_e=0.1422665081、SE_unit=0.0251494031、MDE80=0.0287644381、n_eff=6、δ_min=0.10）。
- 设计：ON3 v0.2（`97FE124A…`）、`on3_design_v0_2.md`（`4AB51CE5…`）；ON3-C1/v0.2 复核：`challenge_ON3.md`（`E440F79B…`）、`challenge_ON3_v0_2.md`（approve_to_lead）。
- 本草案已落实 4 项执行前必办：① B6 预算实测 + 语义冻结；② 参考实现 + **15 项单测**（含 B6 null 门、pure-cold、B5 TE）+ 两跑确定性 + schema 校验；③ context-ablation 移出二元门改描述性诊断；④ MAE/MDE 修复、B5 TE 措辞、纯冷细胞写入 protocol/schema/单测。

## 1. 执行设计（与 v0.2 一致、修正处标 ★）

- **数据**：complete-case **363,090/368,832=98.44%**；**主分析 batch1 357,876 行**；batch2 **仅披露**（5,214 行/1,129 单元/136 上下文；不进训练/指标/增量/敏感性）；batch3 全失（0/5,040）披露；30 非 Jaaks 目标细胞；5 折继承 ON2（6/6/6/6/6）。
- **端点**：viability 四重复均值；complete 4×4 网格 Δ 单元；角色分层；符号归一名升序；k=1 沿用 ON2 排除；不插值/不外推；**不与 Jaaks ΔEMAX 拼接**；主分析不插补；确定性行均值单插补仅敏感性（非 MI）。
- **掩码（冻结）**：整成员块掩码；M=8/38 药物（`dinaciclib, erlotinib, methotrexate, mitomycine, sn38, sorafenib, topotecan, vinorelbine`）；held-out 细胞中 `masked iff partner∈M or a∈M or a'∈M`；M 选择 key/seed/tie 与 v0.2 相同；**20% 是药物比例，实际掩码单元 46.39%**（持续披露）。
- **覆盖（冻结）**：target30 单元 340,088；掩码 **157,768**；非掩码 context 182,320；每 fold 掩码 **30,824–32,400**、掩码上下文 **368–372**、非掩码 35,680–37,338；每 held-out 细胞掩码 min **4,237**、非掩码 context min **4,749**；覆盖门 fold≥5,000 / cell≥500 / fold-context≥50 / cell-context≥500 全 PASS。
- **泄漏审计（★修正）**：
  - **9 项二元泄漏审计**（全部必须 PASS，否则 `design_invalid`）：① 掩码扰动（+1e6 预测不变）② 无 cell id 特征 ③ 仅 batch1 ④ 无 Jaaks/ΔEMAX ⑤ 无剂量插值 ⑥ 无 test 调参 ⑦ 掩码只由 key/seed 生成 ⑧ 单药值不进 primary ⑨ 折分配继承 ON2。
  - **model-free reconstruction audit（独立、必须 =0）**：DSU 端点不可同连通；**target30 0/157,768；per fold 0/30,824–32,400**（`on3_refimpl/reconstruction_audit.json`）；执行时逐 fold 复算断言 0。
  - **context-ablation（★移出二元门）**：独立描述性诊断 `Δρ_context = ρ(B4)−ρ(B4-ablated)`；**≤0 只改措辞（"未观察到 context 描述性增益"），不触发 design_invalid**。
- **比较器（冻结）**：**B4 vs B2 为唯一 primary**；B3/B5 secondary；B0/B1 层级参照；B5-shuf 删除；完整比较表、禁止选最佳。
- **指标（★MAE/MDE 修复）**：
  - rank 主指标 Spearman ρ；主比较 Δρ(B4−B2)；增量判定：Δρ ≥ `Δρ_min_rank=max(0.10, Q95_null(Δρ_null))`、bootstrap 单侧 95% 下界>0、B6 单侧 p≤0.05、≥4/5 folds 正；否则 `no_increment`。
  - **MDE80=0.0287644381 只用于 mean Δ 尺度**（设计门 prior：MDE80≤δ_min=0.10）；**不用于 MAE**；**删除 `|ΔMAE|<MDE80` 门**。MAE 只作描述性：报告 ΔMAE(B4−B2) 与按 held-out 细胞配对 bootstrap 95% CI；**不得**以 MDE80 判 MAE 精度。
  - rank 不可区分：观测 Δρ 落 B6 零分布 95% 内 → `evaluation_cannot_distinguish`。
- **B5（★措辞修复）**：`HistGradientBoostingRegressor(random_state=20261130)`；特征=**训练 cell 的 member-pair target-encoding（在训练细胞内 5 折交叉拟合；绝不使用掩码单元响应/被掩码值）**、partner、role、cell offset（非掩码 context）、context size；容量网格 {max_depth 2/3 × min_samples_leaf 50/200}、lr 0.05、max_iter 200；无 cell id；secondary capacity control。
- **纯冷细胞（★写入 protocol/schema/单测；v2 修复）**：`pure_cold_cell` sensitivity：held-out 细胞**全部单元**掩码、无 context；仅用训练结构预测；指标 ρ/MAE 与 B2 描述性对比；**不进 primary/increment**；schema 必需键 `pure_cold_cell`。**真正的单测：test_12（`test_12_pure_cold_path_uses_b2_only`：monkeypatch 禁用 `predict_b4` 后 `pure_cold_eval` 仍输出与手工 B2 相同的 ρ/MAE、签名无 c/U）+ test_12b（schema 缺 `pure_cold_cell` 即失败）**；`test_04` 是 mask perturbation、`test_05` 是 context-ablation（**不冒充 cold 单测**）；`selfcheck.py` 端到端也调用 pure cold，但**不作为 unit test**。
- **B2**：cell-blind partner×member-pair lookup + backoff（role×partner→global）；不使用 held-out context；强静态基线。

## 2. B6 预算与语义（冻结）

- **语义冻结（★）**：`refit_cu_only` —— 训练结构（μ、role/partner/member-pair 效应、pair 因子 V）**每 fold 只拟合一次**；**每次置换只重估 held-out 细胞的 c_cell/U_cell**（用置换后的非掩码 context），不重拟合训练结构、不重拟合 B4 的其他参数。**full_refit（每次重拟合训练结构）不使用**（预算不可行，见下）。
- **实测（`budget_test/budget_test.json`，synthetic shapes 与冻结设计一致；未读响应值）**：
  - `refit_cu_only` **冻结值 = 1,000 × 5 folds measured wall 306.722 s**（raw full-run 5,000 real permutations；约 5.1 min），≤45 min → **冻结 1,000 置换**；**早期 run_budget.py 的 308.086 s 仅 history/timing noise，不是 frozen/measured 冻结值**；
  - **raw evidence（v2 补，证明 5,000 次真实置换）**：`budget_test/run_b6_full_raw.py`（SHA `F81DCC09…`）实际运行 5 折 × 1,000 = **5,000 次 refit_cu_only 置换**，full-run wall **306.722 s**（≤2,700 s；总预算按 measured 计），stdout 见 `budget_test/b6_full_raw.log`（SHA `38A3B9F3…`），计数/逐折/计时见 `budget_test/b6_full_raw.json`（SHA `0ABE96F0…`，`total_real_permutations=5,000`、`total_perms_match=true`、per-fold 1,000）；语义断言：训练结构每 fold 拟合一次、每次置换只重估 c/U。
  - **`est_1000x5_refit_cu_only=693.34 s` 说明/撤回**：该值是 100-perm pilot（20/fold）的线性外推（17.069 s 含 3.558 s 一次性训练拟合；0.13511 s/perm），忽略了每 fold 只拟合一次与冷启动摊销；**已撤回/仅历史**，冻结预算采用 full measured **306.722 s**，不得引用 693.34。
  - `full_refit` 5 perms/fold 实测 26.02 s → 外推 1,000×5 ≈ **4,408.80 s（约 73.5 min）> 45 min** → **不采用**；
  - budget test 总 wall 351.35 s；**早期 `run_budget.py` 的 308.086 s 仅历史证据（同一实现，计时噪声），冻结值只用 raw full-run 306.722 s**。
- **B6 细节**：置换 held-out 细胞非掩码 context 跨细胞（保持 partner/role 分层）；1,000 次；seed=20261130；单侧上 95th；同时报告双侧 2.5–97.5；**null Δρ 定义 = ρ(B4_null)−ρ(B2)**（同一掩码单元/同一 B2 静态预测）；p = mean(null Δρ ≥ observed)。
- **null 校准门（二元，冻结）**：B4 null ρ 的 2.5–97.5 覆盖 0 且 mean|ρ_null| ≤ 0.05；否则 `design_invalid`（**已加入单测 test_11**，正/负例均验证）。
- **执行总预算（用 measured）**：B6 **306.722 s（raw full-run 实测）** + B4/B2 拟合与预测 <10 s + bootstrap（5,000×5 folds，预测固定；约 1–3 min）+ 两跑确定性 → 总 **<15 min**，≤45 min 留足余量；执行单命令实测将在 execution record 报告（不改变冻结预算/置换数）。

## 3. 参考实现、单测、两跑确定性、schema（`on3_refimpl/`）

| 文件 | 作用 | SHA256 |
|---|---|---|
| `refimpl.py` | 掩码/重建审计/B2/B4/B6/bootstrap/context-ablation/纯冷/schema/B5 TE | `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4` |
| `data_prep.py` | metadata/空值掩码 only：units + M + reconstruction 分母 | `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510` |
| `reconstruction_audit.json` | target30/per-fold 分母（0 可重建） | `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315` |
| `budget_test/run_b6_full_raw.py` | full 5,000-perm raw 预算证据脚本 | `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A` |
| `budget_test/b6_full_raw.json` | 5,000 perms 计数/逐折/计时 | `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A` |
| `budget_test/b6_full_raw.log` | raw stdout/进度日志 | `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D` |
| `budget_test/budget_test.json` | 预算汇总（frozen 306.722；含 raw evidence/693.34 撤回） | `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8` |
| `selfcheck.py` | 确定性端到端自检（synthetic） | `032F21492F79B4C0CFD7870C4464F7691A3104C97E00DFC828C22FED71A8BE48` |
| `selfcheck.json` | 自检输出（两跑逐字节一致） | `2B0537A101A00276F96C89A319EC41488C3853DDBB933DCF5ADFEE33B6335DBE` |
| `test_refimpl.py` | **15 项单测**（含 pure-cold、B5 TE） | `B36D1FCFDD31F1ED622455FF0610E1B4C50864B39A65641C315A9ED48B989A0F` |
| `test_results.txt` | 单测结果 | `8E17572B7C1C9EA3634870F4F7398A9EB847A35ABCF5E0B0CDF6EDA101D8030E` |

- **单测结果：Ran 15 tests — OK（3.19 s）**；覆盖：mask 确定性/掩码规则/reconstruction 目标分母与正控制/掩码扰动/context-ablation 跑通且非二元/schema/two-run 确定性/fold 继承/无 Jaaks 路径/无 test 调参+常数冻结/B6 null 校准门（正负例）/**pure-cold path（test_12：禁用 predict_b4 仍= B2、签名无 c/U）**/**schema 必含 pure_cold_cell（test_12b）**/**B5 TE 不用掩码响应（test_13：rare pair 用 global backoff、无 masked 参数）**。
- **两跑确定性**：`selfcheck.py` 两次运行输出 `selfcheck.json` **逐字节一致**（SHA `2B0537A1…`；两次文件副本同 SHA）。
- **schema**：`EXEC_REQUIRED_KEYS` 含 `pure_cold_cell`；缺失键检测通过；执行输出必须含全部键（见 §4）。
- **重建分母**：`reconstruction_audit.json`：target30 **0/157,768**；fold 0–4：31,767/30,824/30,876/32,400/31,901，各 **0 可重建**；均由 `data_prep.py` 以 metadata/空值掩码 only 计算（wall 40.03 s）。

## 4. 输出 JSON schema（冻结）

`task, protocol, inputs, mask{M,seed,rule,counts}, coverage{fold,cell}, results{folds×comparators×metrics}, primary{delta_rho,delta_rho_ci,delta_rho_min_rank,null_p,delta_mae,delta_mae_ci}, null{B6_distribution_summary,gate}, bootstrap{B,seed,percentiles}, context_ablation{diagnostic}, pure_cold_cell{rho,mae,n_units}, gates{data,design,leakage_binary_9,reconstruction}, verdict, failure_categories, attestation, determinism`。
- 无时间戳、键排序、`allow_nan=False`；输入/脚本 SHA 写入；执行脚本/输出 schema 冻结后不改。

## 5. 失败类别/停止/报告措辞（冻结）

- `data_unavailable` / `design_invalid`（数据/设计/9 项二元泄漏/reconstruction≠0/B6 null 门失败）/ `evaluation_cannot_distinguish`（rank 落 null 95% 内）/ `no_increment`（B4 vs B2 未达增量）。
- 停止：任一 gate FAIL 停并记录；**不换指标/切分/端点/掩码/比较器/seed/超参；不因结果重跑**。
- 阴性模板（冻结）："在本资源（O'Neil complete-case、batch1、30 目标细胞）与本设计（整成员块掩码、5 折细胞留出）下，未观察到 B4 相对 B2 的预注册描述性增量；这不等于结构不存在、不可迁移或没有决策价值。"
- 阳性模板（冻结）："在本资源/本设计下观察到 B4 相对 B2 的预注册描述性增量（Δρ=…，CI…，null p=…）；仅描述性，不构成迁移/决策收益/机制/独立确认证据。"
- **context-ablation 只写诊断**；纯冷细胞只写 sensitivity；两者都不改变 primary 判定。

## 6. 边界（执行时仍适用）

- 仅 O'Neil 内部开发性描述；不称迁移/外推、决策收益、机制、独立确认、更新器优势、资源足够、新颖性。
- 仅 viability（mu/muMax、X/X0 为派生，不作独立读数）；不与 Jaaks ΔEMAX 拼接；技术重复≠独立培养；3 BatchID 同 lab；batch2 仅披露；batch3 全失披露；702 个 15 行 pair-cell 排除；无暴露时间/assay 列；单药参照未用；缺失机制未知（不假设 MCAR/MAR）。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；执行仍不运行更新器/迁移/决策分析。

## 7. 冻结前检查单（Lead 批准时逐项）

- [x] B6 预算冻结值 = **306.722 s**（raw full-run 5,000 real permutations；308.086 s 仅早期 run_budget history/timing noise，不作冻结值）；`est_1000x5=693.34` 已撤回；full_refit 不可行 4,408.80 s 外推；
- [x] 参考实现 + **15 单测**（含 pure-cold/B5 TE/B6 null 门）+ 两跑确定性 + schema 校验；
- [x] reconstruction 分母 target30/per fold（0/157,768 与 0/30,824–32,400）；
- [x] context-ablation 移出二元门；9 项二元泄漏审计 + reconstruction 独立；
- [x] MAE/MDE 修复（删除 |ΔMAE|<MDE80）；B5 TE 措辞；纯冷细胞写入 schema/单测；
- [x] 执行 protocol/schema/预算/失败类别/措辞冻结；
- [ ] **同一挑战者复核本 exec DRAFT**（复核预算/单测/两跑/schema）；
- [ ] **Lead 批准并冻结**（冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数）。

## 8. 冻结文本候选（Lead 批准用；完整全链 SHA 见 `FREEZE_ON3_exec.md`）

> **ON3 执行协议：`design_frozen_qualified_with_conditions` 的 execution protocol（DRAFT → 待 Lead 批准冻结）。**
> **冻结值**：B6 `refit_cu_only` = **1,000 置换**；预算冻结值 = **306.722 s**（raw full-run 5,000 real permutations，≤2,700 s）；308.086 s 仅为早期 run_budget.py history/timing noise；`est_1000x5=693.34` 为 pilot 外推、**已撤回**；full_refit 不采用（外推 4,408.80 s）；执行总预算 measured **<15 min**。
> **规范文件链（最终 SHA；完整含 protocol/record/usage 本体的全链在 `FREEZE_ON3_exec.md`，其 SHA 由 Lead 批准文本引用）**：
> - `on3_refimpl/refimpl.py` `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4`
> - `on3_refimpl/test_refimpl.py` `B36D1FCFDD31F1ED622455FF0610E1B4C50864B39A65641C315A9ED48B989A0F`
> - `on3_refimpl/test_results.txt` `8E17572B7C1C9EA3634870F4F7398A9EB847A35ABCF5E0B0CDF6EDA101D8030E`（15/15 OK）
> - `on3_refimpl/selfcheck.py` `032F21492F79B4C0CFD7870C4464F7691A3104C97E00DFC828C22FED71A8BE48`
> - `on3_refimpl/selfcheck.json` `2B0537A101A00276F96C89A319EC41488C3853DDBB933DCF5ADFEE33B6335DBE`（两跑逐字节一致）
> - `on3_refimpl/reconstruction_audit.json` `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315`（target30 0/157,768；per fold 0/30,824–32,400）
> - `on3_refimpl/data_prep.py` `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510`
> - `budget_test/run_b6_full_raw.py` `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A`
> - `budget_test/b6_full_raw.json` `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A`（5,000 perms / 306.722 s）
> - `budget_test/b6_full_raw.log` `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D`
> - `budget_test/budget_test.json` `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8`（frozen 306.722）
> - `budget_test/run_budget.py` `5BCA9F93F0CB59512BAF0BED7276A486709C09035875FC8D648661DF844AB963`（早期历史脚本，非冻结值来源）
> **单测 15 项全 OK（3.19 s）**；两跑 selfcheck 逐字节一致；泄漏审计 9 项二元 + reconstruction=0；context-ablation 描述性诊断；MAE 不用 MDE80；B5 TE 不用掩码响应；纯冷细胞 sensitivity（test_12/12b）。
> 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；执行仅 O'Neil 内部开发性描述，不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**。

## 9. 版本

v0.2 exec DRAFT（ON3-READY.2），2026-10-27；配套 `on3_refimpl/`、`budget_test/`、`record_on3_ready.md`、`usage_on3_ready.json`；**未运行 ON3 效果/训练/更新器**；等待复核与 Lead 批准。

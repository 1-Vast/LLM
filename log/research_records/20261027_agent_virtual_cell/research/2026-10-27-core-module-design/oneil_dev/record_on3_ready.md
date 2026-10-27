# R199-ON3-READY.3 审计记录（record_on3_ready）

角色：ON1/ON2/ON2.2/ON3 执行者（非提案者，未参与挑战）。任务：**R199-ON3-READY**——完成 `challenge_ON3_v0_2.md`（approve_to_lead）的 4 项执行前必办 + execution protocol 草案；**未运行 ON3 效果/训练/更新器**（只运行预算测试、参考实现单测、两跑确定性、metadata/空值掩码预计算）；未改 v0.1/v0.2 文件与 ON1/ON2/ON2-EX 产物。

## 1. 依据（只读）

| 文件 | SHA256 |
|---|---|
| `challenge_ON3_v0_2.md`（approve_to_lead，4 项必办） | `DA7009644EB12C1C31BC350E52B80C510B9117485FE7624441A6D1F347A0760A` |
| `challenge_ON3_exec_confirm.md`（ON3-EXEC-C1，revise 3 必改） | `25F3F34077EC3A95DFEFE63D194A59027879FF17029317597ACFB4FF34E854EA` |
| `PROTOCOL_ON3_v0_2.md`（v0.2 DRAFT） | `97FE124A866F4B47BB2ACB04D8B4B5EBDFE4FCF9FB039B6EE8988E6A1F5F4FB9` |
| `on3_design_v0_2.md` | `4AB51CE57C6360DBB63EA8AA29E6F40D5492DBD30A6E71A6D0644BFC78C58BBA` |
| `PROTOCOL_ON2.md` v2.2 / `ERRATA_ON2_1.md` / `report_on2_1.md` / `record_on2_1.md` | `7B34DB79…` / `3C6138DF…` / `C6CF6467…` / `789A0114…` |
| `exec_calibration/calib.json`（ON2-EX 认证） | `DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A` |
| `on2.json` | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| 组合工作簿（仅元数据/空值掩码） | `A0E2E002DC06C34E8AEDF3206877A93BAB7E45190AD8BB8E70ED79FF24C14818` |

## 2. 4 项执行前必办的落实

### ① B6 预算测试 + 语义冻结
- **语义冻结**：`refit_cu_only` —— 训练结构（μ/role/partner/member-pair 效应 + pair 因子 V）**每 fold 只拟合一次**；**每次置换只重估 held-out 细胞 c_cell/U_cell**（用置换后的非掩码 context）；**不重拟合训练结构**。`full_refit` 语义**不采用**（预算不可行）。
- **实测**（`budget_test/budget_test.json`；synthetic shapes=冻结设计，未读响应值）：
  - `refit_cu_only` **冻结值 = 1,000×5 measured wall 306.722 s**（raw full-run 5,000 real permutations）；null Δρ mean 0.0001393、Q95 0.000917；→ **冻结 1,000 置换**；**早期 run_budget.py 的 308.086 s 仅 history/timing noise，不作冻结/measured 值**；
  - **raw full-run 证据（ON3-READY.2 补）**：`budget_test/run_b6_full_raw.py` 实际运行 **5 折×1,000 = 5,000 次真实置换**，wall **306.722 s**；`b6_full_raw.json`（`total_real_permutations=5000`、`total_perms_match=true`、per-fold 1,000、`budget_ok=true`）；`b6_full_raw.log` 含逐 100 perms 进度与 FINAL 行；与早期 308.086 s 属同一实现/计时噪声；
  - **`est_1000x5_refit_cu_only=693.34 s` 撤回**：pilot 线性外推（100 perms；含一次性拟合/冷缓存），忽略摊销；冻结预算采用 measured 306.722 s，693.34 仅历史、不得引用；
  - `full_refit` 5 perms/fold 实测 26.021 s → 外推 1,000×5 = **4,408.795 s（约 73.5 min）> 45 min**，不采用；
  - pilot（20/fold）17.069 s；budget test 总 wall **351.353 s**。
- **冻结后不得执行时缩减**；若未来执行环境变化导致超 45 min，只能回到冻结前重议并披露。

### ② 参考实现 + 15 项单测 + 两跑确定性 + schema 校验
- `on3_refimpl/refimpl.py`：mask 选择/规则、symbolic reconstruction（DSU）、B2、B4（ALS/ridge/context 估计）、metrics（Spearman/MAE/top-k 附录）、paired bootstrap、B6（两种语义）、context-ablation、pure cold、schema、null gate。
- `on3_refimpl/data_prep.py`：metadata/空值掩码 only 的 units + M + reconstruction 审计（wall **40.03 s**）。
- **重建分母（修复）**：`reconstruction_audit.json`：**target30 0/157,768**；fold 0–4 分别 **31,767 / 30,824 / 30,876 / 32,400 / 31,901，各 0 可重建**（不再用 all-batch 205,044 分母）。
- **单测：Ran 15 tests — OK（3.19 s）**（`test_results.txt`）：mask 确定性/掩码规则/reconstruction 目标分母+正控制/掩码扰动/context-ablation 跑通且非二元/schema/two-run 确定性/fold 继承/无 Jaaks 路径/无 test 调参+冻结常数/B6 null 校准门正负例/**pure-cold path（test_12：monkeypatch 禁用 predict_b4 仍= B2、签名无 c/U）**/**schema 必含 pure_cold_cell（test_12b）**/**B5 TE 不用掩码响应（test_13：rare pair 用 global backoff、无 masked 参数）**。
- **两跑确定性**：`selfcheck.py` 两次输出 `selfcheck.json` **逐字节一致**（SHA `2B0537A1…`；另存副本同 SHA）。
- **schema**：`EXEC_REQUIRED_KEYS` 新增 `pure_cold_cell`；缺失键检测通过。

### ③ context-ablation 分类修复
- **泄漏审计**：9 项**二元**（mask 扰动/无 cell id/仅 batch1/无 Jaaks·ΔEMAX/无剂量插值/无 test 调参/mask key/单药不进 primary/折继承）+ **model-free reconstruction 独立审计（必须=0，target30/per fold 分母）**。
- **context-ablation**：移出二元门；作为**独立描述性诊断** `Δρ_context = ρ(B4)−ρ(B4-ablated)`；≤0 只改措辞（"未观察到 context 描述性增益"），**不触发 design_invalid**。

### ④ MAE/MDE、B5 措辞、纯冷细胞
- **MAE/MDE**：**删除 `|ΔMAE|<MDE80` 门**；MDE80=0.0287644381 只用于 **mean Δ 尺度**（设计门 prior：MDE80≤δ_min=0.10）；MAE 只作描述性（ΔMAE + paired-by-cell bootstrap 95% CI），不得以 MDE80 判 MAE 精度。
- **B5 措辞**：改为"**训练 cell 的 member-pair target-encoding（训练细胞内 5 折交叉拟合；绝不使用掩码单元响应/被掩码值）**"；`random_state=20261130`、容量网格冻结。
- **纯冷细胞**：写入 execution protocol/schema/单测：`pure_cold_cell` sensitivity（held-out 细胞全部单元掩码、无 context；只作描述性，不进 primary/increment）；schema 必需键；`pure_cold_eval` 只调用 B2 静态预测（无 c/U）。

## 2A. ON3-READY.2：challenge_ON3_exec_confirm 3 必改闭合

1. **pure-cold 真正单测 + 虚假声明修复**：新增 `test_12_pure_cold_path_uses_b2_only`（monkeypatch 禁用 `predict_b4` 后 `pure_cold_eval` 仍输出与手工 B2 相同的 ρ/MAE；签名无 c/U）、`test_12b_schema_requires_pure_cold_cell`、`test_13_b5_te_uses_only_training_cells_no_masked_responses`；单测总数 **12→15，Ran 15 tests OK（3.19 s）**；`test_04`（mask perturbation）/`test_05`（context-ablation）不再被冒充为 cold 单测；protocol §1 声明已改为实际 test id。
2. **预算 raw evidence + 693.34 撤回**：新增 `budget_test/run_b6_full_raw.py` + `b6_full_raw.log` + `b6_full_raw.json`：`refit_cu_only` 实际执行 **5 折 × 1,000 = 5,000 次真实置换**（`total_perms_match=true`），full-run wall **306.722 s**（≤2,700 s）；逐 100 perms 进度/log、FINAL 行、逐折计时均在 raw 证据中；`budget_test.json` 增加 `budget_raw_evidence` 块（log/JSON/脚本路径+SHA、5,000 perms、逐折 wall）并把 `est_1000x5_refit_cu_only=693.34` 标为 **pilot 线性外推、已撤回/仅历史**；执行总预算改用 measured 306.722 s（<15 min）。
3. **全部 SHA 重算 + 冻结文本**：refimpl/test_refimpl/test_results/protocol/record/usage/budget 全部新 SHA（见 §4）；`selfcheck.json` 两跑仍逐字节一致（`2B0537A1…`，refimpl 变更未改变输出）；冻结文本候选见 §8（引用本次新 SHA）；旧 SHA 不得用于 Lead 批准。

## 3. Execution protocol 草案

- `PROTOCOL_ON3_exec_DRAFT.md`（v0.3，SHA `8B4B8FCC…`）：含最终预算/B6 语义与 1,000 置换/raw evidence/schema/15 单测/两跑/≤45 min/失败类别/阴性阳性模板/冻结后禁改项（mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数）+ §8 冻结文本候选。
- **执行总预算（用 measured）**：B6 **306.722 s（raw full-run）** + B4/B2 拟合/预测 <10 s + bootstrap（固定预测，约 1–3 min）+ 两跑确定性 → **<15 min**；执行时报告实测 wall（不改变冻结预算）。

## 4. 产出与 SHA

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON3_exec_DRAFT.md`（v0.3） | `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336` |
| `on3_refimpl/refimpl.py` | `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4` |
| `on3_refimpl/data_prep.py` | `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510` |
| `on3_refimpl/reconstruction_audit.json` | `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315` |
| `on3_refimpl/selfcheck.py` | `032F21492F79B4C0CFD7870C4464F7691A3104C97E00DFC828C22FED71A8BE48` |
| `on3_refimpl/selfcheck.json` | `2B0537A101A00276F96C89A319EC41488C3853DDBB933DCF5ADFEE33B6335DBE` |
| `on3_refimpl/test_refimpl.py`（15 单测） | `B36D1FCFDD31F1ED622455FF0610E1B4C50864B39A65641C315A9ED48B989A0F` |
| `on3_refimpl/test_results.txt` | `8E17572B7C1C9EA3634870F4F7398A9EB847A35ABCF5E0B0CDF6EDA101D8030E` |
| `budget_test/run_budget.py` | `5BCA9F93F0CB59512BAF0BED7276A486709C09035875FC8D648661DF844AB963` |
| `budget_test/budget_test.json`（frozen 306.722；raw evidence/693.34 撤回） | `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8` |
| `budget_test/run_b6_full_raw.py` | `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A` |
| `budget_test/b6_full_raw.json`（5,000 perms） | `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A` |
| `budget_test/b6_full_raw.log` | `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D` |
| `record_on3_ready.md` / `usage_on3_ready.json` / `FREEZE_ON3_exec.md` | 本记录 / 已写出 / 全链冻结文本（最终 SHA 见 FREEZE_ON3_exec.md 与 Lead 批准文本） |

- v0.1/v0.2 文件与 ON1/ON2/ON2-EX 冻结产物 SHA 未变（见 usage）。

## 5. 命令/时间

| 命令 | wall |
|---|---|
| `on3_refimpl/data_prep.py`（metadata/空值掩码 only） | **40.03 s** |
| `budget_test/run_budget.py`（synthetic shapes；未读响应值） | **351.35 s**（含 1,000×5 B6 308.09 s + full_refit pilot 26.02 s + pilot） |
| **`budget_test/run_b6_full_raw.py`（raw full 5,000 perms）** | **306.722 s**（≤2,700 s；逐 100 perms 进度/计时见 log） |
| `on3_refimpl/selfcheck.py` 两跑 | 两跑逐字节一致（`2B0537A1…`） |
| `python -m unittest -v test_refimpl` | **15 tests OK（3.19 s）** |

- 未运行 ON3 效果/训练/更新器/迁移/决策分析；未读响应值做统计（预算测试用 synthetic；data_prep 只用元数据/空值掩码）。

## 6. 剩余缺口/边界

1. **同一挑战者（endpoint-auditor）复核 ON3-READY.2 修订**（pure-cold 单测/15 tests、raw budget evidence/693.34 撤回、新 SHA）→ 若 PASS 可 **approve_freeze_exec**；Lead 批准并冻结；本轮**未**批准/冻结。
2. 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；执行时若发现实现偏差须停并重新预注册，不得事后调整。
3. 执行仍只写 O'Neil 内部开发性描述；不称迁移/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。
4. 限制不变：masked 46.4% 单元（20% 药物比例）、masked-member 选择影响结果、transductive context 非纯冷启动（纯冷细胞仅 sensitivity）、B4 小数据过拟合、context-ablation 若 0 只能写"未观察到 context 描述性增益"、缺失机制未知、batch3 全失、702 个 15 行 pair-cell、无暴露时间/assay、单药参照未用、技术重复≠独立培养。
5. 预算测试用 synthetic shapes；真实执行的 bootstrap/B4 拟合时间可能略有差异，但 B6 主消耗已 raw 实测 **306.722 s**，总预算余量充足；执行 record 报告实测 wall。

## 7. 明确不做

- 未运行 ON3 效果/训练/更新器比较/迁移/决策分析；未改 v0.1/v0.2、ON1/ON2/ON2-EX 产物；未声称新颖性；未把 exec DRAFT 当已冻结执行依据。

## 8. 冻结文本候选（ON3-READY.3；完整全链 SHA 见 `FREEZE_ON3_exec.md`）

> **ON3 执行协议：`design_frozen_qualified_with_conditions` 的 execution protocol（DRAFT → 待 Lead 批准冻结）。**
> **冻结值**：B6 `refit_cu_only` = **1,000 置换**；预算冻结值 = **306.722 s**（raw full-run 5,000 real permutations，≤2,700 s）；308.086 s 仅为早期 run_budget.py **history/timing noise**；`est_1000x5=693.34` 为 pilot 外推、**已撤回**；full_refit 不采用（外推 4,408.80 s）；执行总预算 measured **<15 min**。
> **规范文件链（最终 SHA；完整含 protocol/record/usage 本体的全链在 `FREEZE_ON3_exec.md`，其 SHA 由 Lead 批准文本引用）**：
> - `PROTOCOL_ON3_exec_DRAFT.md`（v0.3）`8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336`
> - `usage_on3_ready.json` `252E59D77DB5B6E414A679A2690217AACA35E04C3D3F645A053588F401441129`
> - `on3_refimpl/refimpl.py` `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4`
> - `on3_refimpl/test_refimpl.py` `B36D1FCFDD31F1ED622455FF0610E1B4C50864B39A65641C315A9ED48B989A0F`
> - `on3_refimpl/test_results.txt` `8E17572B7C1C9EA3634870F4F7398A9EB847A35ABCF5E0B0CDF6EDA101D8030E`（15/15 OK）
> - `on3_refimpl/selfcheck.py` `032F21492F79B4C0CFD7870C4464F7691A3104C97E00DFC828C22FED71A8BE48`
> - `on3_refimpl/selfcheck.json` `2B0537A101A00276F96C89A319EC41488C3853DDBB933DCF5ADFEE33B6335DBE`（两跑逐字节一致）
> - `on3_refimpl/reconstruction_audit.json` `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315`（target30 0/157,768；per fold 0/30,824–32,400）
> - `on3_refimpl/data_prep.py` `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510`
> - `budget_test/run_b6_full_raw.py` `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A`
> - `budget_test/b6_full_raw.json` `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A`
> - `budget_test/b6_full_raw.log` `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D`
> - `budget_test/budget_test.json` `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8`（frozen 306.722）
> - `budget_test/run_budget.py` `5BCA9F93F0CB59512BAF0BED7276A486709C09035875FC8D648661DF844AB963`（早期历史脚本，非冻结值来源）
> **本记录 record_on3_ready.md 的最终 SHA** 与 `usage_on3_ready.json`、`FREEZE_ON3_exec.md` 的 SHA 见 `FREEZE_ON3_exec.md`（该文件为完整全链冻结文本；Lead 批准文本引用其 SHA）。
> 单测 **15 项全 OK（3.19 s）**；两跑 selfcheck 逐字节一致；泄漏审计 9 项二元 + reconstruction=0；context-ablation 描述性诊断；MAE 不用 MDE80；B5 TE 不用掩码响应；纯冷细胞 sensitivity（test_12/12b）。
> 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；执行仅 O'Neil 内部开发性描述，不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**。

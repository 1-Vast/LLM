# FREEZE_ON3_exec —— ON3 execution protocol 冻结文本（全链 SHA；Lead 批准用）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。**本文件是 ON3 执行协议冻结文本的完整全链 SHA 记录**；作为 Lead 批准 `approve_freeze_exec` 的引用文本。**本文件不运行 ON3 效果/训练/更新器；其自身 SHA 见 Lead 批准文本（文件不能自引用）。**

## 0. 冻结声明

> **ON3 execution protocol 判定：`design_frozen_qualified_with_conditions` 的 execution protocol（DRAFT → 待 Lead 批准冻结；冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数）。**
> 依据：ON2 v2.2 冻结资格 + ON2-EX `calibration_passed`（σ̂_e=0.1422665081、SE_unit=0.0251494031、MDE80=0.0287644381、n_eff=6、δ_min=0.10）；ON3 v0.2 DRAFT + v0.1/v0.2/exec 复核链；**仅 O'Neil 内部开发性描述；不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结 ≠ 资源足够/关系成立/Stage 1/效果。**
> **冻结值**：B6 `refit_cu_only`，**1,000 置换**，预算冻结值 **306.722 s**（raw full-run 5,000 real permutations；≤2,700 s）；308.086 s 仅早期 `run_budget.py` history/timing noise；`est_1000x5=693.34` 为 pilot 外推、**已撤回**；full_refit 不采用（外推 4,408.80 s）；执行总预算 measured **<15 min**。
> **单测 15/15 OK（3.19 s）**；两跑 `selfcheck.json` **逐字节一致** `2B0537A1…`；泄漏审计 9 项二元 + reconstruction=0；context-ablation 描述性诊断；MAE 不用 MDE80；B5 TE 不用掩码响应；纯冷细胞 sensitivity（test_12/12b）。

## 1. 全链最终 SHA（冻结引用；本文件写入时的最终值）

| # | 文件 | SHA256 |
|---|---|---|
| 1 | `PROTOCOL_ON3_exec_DRAFT.md`（exec DRAFT v0.3） | `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336` |
| 2 | `record_on3_ready.md`（审计记录 + 冻结文本） | `92EC25CD64D8D0DF23EC84E6134E989CE50D7B2FCC62FC48219AA99451F1BBA3` |
| 3 | `usage_on3_ready.json` | `252E59D77DB5B6E414A679A2690217AACA35E04C3D3F645A053588F401441129` |
| 4 | `on3_refimpl/refimpl.py` | `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4` |
| 5 | `on3_refimpl/test_refimpl.py` | `B36D1FCFDD31F1ED622455FF0610E1B4C50864B39A65641C315A9ED48B989A0F` |
| 6 | `on3_refimpl/test_results.txt`（Ran 15 tests OK） | `8E17572B7C1C9EA3634870F4F7398A9EB847A35ABCF5E0B0CDF6EDA101D8030E` |
| 7 | `on3_refimpl/selfcheck.py` | `032F21492F79B4C0CFD7870C4464F7691A3104C97E00DFC828C22FED71A8BE48` |
| 8 | `on3_refimpl/selfcheck.json`（两跑同 SHA） | `2B0537A101A00276F96C89A319EC41488C3853DDBB933DCF5ADFEE33B6335DBE` |
| 9 | `on3_refimpl/reconstruction_audit.json`（target30 0/157,768；per fold 0） | `DC93D4FEA64217CB8F5C83EE9BB97A42AFEB3465ED3C41AEC780ECD769C37315` |
| 10 | `on3_refimpl/data_prep.py`（metadata/nullness only） | `7C11B0C57724DCD58785A303671E4F265C469EC5D30159D3649800164C74D510` |
| 11 | `budget_test/run_b6_full_raw.py`（full 5,000-perm raw 脚本） | `F81DCC09823726BC89AD14668FFCFD5D6E0ED63DB875A5BD83D98B4260D3325A` |
| 12 | `budget_test/b6_full_raw.json`（5,000 perms / 306.722 s） | `0ABE96F0F14D7AC5517C5CF24851E9E195B5EACC12D1CC04C9238AB36411803A` |
| 13 | `budget_test/b6_full_raw.log`（逐 100 perms 进度/FINAL） | `38A3B9F3BB26C651FEE01D612367AD2052F71177BD49F4963B4869B7202EDC7D` |
| 14 | `budget_test/budget_test.json`（frozen 306.722；raw evidence；693.34 撤回） | `4D08670FAED6809D1AA0765511F628B4B59F2F26DF6D552FAC5CDB45F542BBB8` |
| 15 | `budget_test/run_budget.py`（早期 run，历史；非冻结值来源） | `5BCA9F93F0CB59512BAF0BED7276A486709C09035875FC8D648661DF844AB963` |
| 16 | `challenge_ON3_exec_confirm.md`（ON3-EXEC-C1 revise） | `25F3F34077EC3A95DFEFE63D194A59027879FF17029317597ACFB4FF34E854EA` |
| 17 | `challenge_ON3_ready2_confirm.md`（READY.2-C1 revise） | `C0570C9E0BAF1D373EFCEF1D74C1F731F267E79093F65AF7E86A0FE9CDF4117B` |

> 注：#16/#17 为只读挑战输入（复核链）；其 SHA 由 `challenge_ON3_exec_confirm.md`/`challenge_ON3_ready2_confirm.md` 实际内容决定（见 §2 核对）。
> **本文件 `FREEZE_ON3_exec.md` 自身 SHA** 由 Lead 批准文本引用（文件不能自引用）；其计算见 §2。

## 2. 复现/核对命令（只读）

```powershell
cd D:\MAESTRO\research\2026-10-27-core-module-design\oneil_dev
Get-FileHash PROTOCOL_ON3_exec_DRAFT.md, record_on3_ready.md, usage_on3_ready.json, `
  on3_refimpl\refimpl.py, on3_refimpl\test_refimpl.py, on3_refimpl\test_results.txt, `
  on3_refimpl\selfcheck.py, on3_refimpl\selfcheck.json, on3_refimpl\reconstruction_audit.json, `
  on3_refimpl\data_prep.py, budget_test\run_b6_full_raw.py, budget_test\b6_full_raw.json, `
  budget_test\b6_full_raw.log, budget_test\budget_test.json, budget_test\run_budget.py, `
  challenge_ON3_exec_confirm.md, challenge_ON3_ready2_confirm.md, FREEZE_ON3_exec.md -Algorithm SHA256
```

- 两跑自检：`PYTHONHASHSEED=0 python -X utf8 on3_refimpl/selfcheck.py` 两次 → `selfcheck.json` 同 SHA `2B0537A1…`（已执行，见 `record_on3_ready.md`）。
- 预算 raw：`python -X utf8 budget_test/run_b6_full_raw.py` → 5,000 real permutations / 306.722 s（`b6_full_raw.log` FINAL 行）。
- 未运行 ON3 效果/训练/更新器；仅 O'Neil 内部开发性描述；执行仍须按冻结协议，不称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性。

## 3. 冻结后禁改项

- mask（M 列表/规则/seed）、fraction、超参、rank/λ、指标/差值规则、B6 置换数、B6 语义（refit_cu_only）、bootstrap B/seed/percentile、schema/单测、报告模板，全部冻结；执行若发现实现偏差须停并重新预注册，不得事后调整。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；执行 record 报告实际 wall/bootstrap。

## 4. 版本

v1.0 ON3-READY.3 冻结文本，2026-10-27；待 Lead 批准 `approve_freeze_exec`。

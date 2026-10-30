# record_M3_v0_2.md —— R204-M3.1 预注册审计记录（M3-C1 三必改；**不运行效果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R204-M3.1（按 M3-C1 revise 修 3 项；**未运行效果比较、未拟合真实/响应数据、未声称增益**）。**机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；M3 Stage1 执行须另立执行预注册+独立挑战+Lead 批准。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 12:24–12:26 | 读 task-160/M3-C1；复制 v0.2 文件；不改 v0.1 |
| 12:26–12:30 | 修 `formalism_M3_v0_2.py`：基线补 optimal/decision_AL、失败类别补 nonidentifiable/two_run_mismatch、Fisher-z round/ceil/非 gate；Stage2/3 arms 显式补全；新增 checks |
| 12:30–12:33 | 跑 v0.2 形式化：19 项 checks 全 PASS；两跑 `formalism_M3_v0_2.json` 逐字节一致 SHA `299E5B03…` |
| 12:33–12:38 | 写 PROBLEM/DESIGN/schema/report/record/usage v0.2；核对 SHA/timing；完成 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `2026-10-28-deep-coupling-redesign/report.md` | `609ADAB397371AE7493176C75F31DE40132A1C4D5402E9B97C302E10931B7E70` |
| `2026-10-28-deep-coupling-redesign/BRIEF_R204.md` | `1A200669E10B989272F74DD2FD7AC37938FEFA013B65751C7467094B82478EF1` |
| `2026-10-27-agent-cell-colearning/ERRATA_R201_R202.md` | `7CB756ACFFA9F9E37ECD9F26C7124FE2F87CF4BF8B1432A70B8847BAFFA9D227` |
| `2026-10-28-decision-power-scope/PROBLEM_DECISION.md` | `60C9D66FE1970A3AC8B25330DCB95760BA9C0FC65236E899166D971A6898A4A8` |
| `2026-10-28-decision-power-scope/power_scope.json` | `734B98B3B2D754A200419F125C6026423B77C4331F7A85706923C31BCC1474BC` |
| `2026-10-28-decision-power-scope/DECISION_R203_P1_SCOPE.md` | `2EDDC655D177D933B3A56F8432282CEB659E9B43AC3BD770220703B79230777C` |
| `2026-10-28-m2-operator-prereg/PROBLEM_M2_v0_2.md` | `25BC2663BC970D21857796E68428D91EA2E867D13AA371DAE817B7C08A94A4BF` |
| `2026-10-28-m2-operator-prereg/DESIGN_M2_v0_2.md` | `5891858E8647EA5C47549931B6D852C459795A12919798ED223F4C8F9C788255` |
| `2026-10-28-m1-executable-gen-prereg/PROBLEM_M1_v0_2.md` | `18A7FC9F3EE9AF21BBCC7DCD84DBF6F50654DDD92E342E6ABA613E938D2F9C9B` |
| `2026-10-28-m1-executable-gen-prereg/DESIGN_M1_v0_2.md` | `11FACB26A3D62E216B7699C1AB8F7473844EE385B526A966372902E4CE092705` |
| `2026-10-28-n1-effect-run/report_n1_effect.md` | `DB9C91F032FE059048BA66327F1DC5401EAD5A158B2FC91B4E506DF05513589A` |
| v0.1 M3 产物（保留不改） | `PROBLEM_M3.md` `EDC66222…`; `DESIGN_M3.md` `D839DACD…`; `formalism_M3.json` `2256BDA2…` |

## 3. 输出（本任务；只写 v0.2 新文件与 tmp/）

| 文件 | SHA256 |
|---|---|
| `formalism_M3_v0_2.py` | `3E709B8193AFA3814D821B46E9D541957B1864308D9DF98E2A60F118A25997B3` |
| `formalism_M3_v0_2.json`（两跑一致） | `299E5B03E916BFB0FA36C02FE8446EA6170FAD89E6DF4BC039A92B0E36DD7E39` |
| `timing_M3_pilot_v0_2.json` | `BA261FA71AE957D38CA76BB4EB6A43B1E1FC230F5290088469425A63A3963C36` |
| `schema_M3_v0_2.json` | 见文件 |
| `PROBLEM_M3_v0_2.md` / `DESIGN_M3_v0_2.md` / `report_M3_v0_2.md` / `record_M3_v0_2.md` / `usage_M3_v0_2.json` | 见 usage/SHA 表 |

## 4. M3-C1 三项落实（摘要）

1. **标准基线**：`standard_baselines.baselines_required` 增 `optimal_experimental_design`、`decision_AL`；`schema_M3_v0_2.json` 同步；Stage2 arms = shared-score/random/GP/**decision_AL**/**optimal_experimental_design**/DR+MLE；Stage3 arms = candidate/full-history/IW/DR/TMLE/**optimal_experimental_design**/**decision_AL**；同信息/反馈/调参≤20/caps/合法实验包；等预算复制/超过→`no_increment`/撤。
2. **失败类别**：`failure_categories` 增 `design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch`；Stage1 共线/分离/无有限解、两跑不一致路由至对应类别；失败只写类别、不报效果。
3. **Fisher-z**：6,282.1038/1,572.7759 标为仅 Fisher-z 连续规划参考；`non_integer=true`、`not_a_gate=true`、`not_paired_DR_formula=true`；schema/report 给 round=6282/1573、ceil=6283/1573；决策用 MDE80=.047982685、n_req278、headroom、cluster。

## 5. 形式化检查/两跑/预算

- **19 项 checks 全 PASS**（DR gap 0；零支持未识别；截断 bias −0.026407185629；ε root −0.562633036711；共线 rank1；分配 full≥noise；π=b 退化；最优设计/决策 AL 基线+Stage2/3 arms 检查；nonidentifiable/two_run_mismatch 失败类别检查；Fisher-z round/ceil/非 gate 检查）。
- 两跑 `formalism_M3_v0_2.json` 逐字节一致 SHA **`299E5B03…`**；timing 10 rep 平均 **0.000176 s/rep**、wall **0.00176 s**；caps 1800s/2h/8GB PASS；0 wells。
- **未运行**效果比较/训练/真实数据/湿实验；N1 `no_increment` 未作 M3 证据。

## 6. 边界/未做

- 支撑研究/机制账 only；不称药理/真实决策/迁移/机制/新颖性；一步公式非新意；不晋升代码；不改旧判定/门槛；不恢复停止实验；功能头校准不得称细胞规律改变。
- M3 Stage1 执行须另立执行预注册+独立挑战+Lead 批准；真实数据 `data_unavailable`（C203/C205）；不得合成/RNA 替代独立功能决策。

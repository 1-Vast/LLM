# record_n1_gates —— R203-N1-IMPL 实现+资格门审计记录（不报效果）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R203-N1-IMPL（按 Lead `DECISION_R203_N1_PREREG.md`，仅实现+资格门；不跑效果比较、不报 regret/top-k/selection accuracy；不读真实响应/A/B；0 wells）。**本记录只记录实现/资格门；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 10:51–10:53 | 读 `DECISION_R203_N1_PREREG.md`、PROBLEM/DESIGN/generator v0_4、V4_validation、timing pilot、P1 scope/power_scope、ERRATA R201/R202（C197/C199/C201）；核对冻结 SHA 一致 |
| 10:53–10:56 | 建 `2026-10-28-n1-implementation/`；写 `run_n1_gates.py`（只读导入冻结 generator；实现 V1–V4/G1–G7 的 gate 检查；不报效果） |
| 10:56–10:58 | 首跑 V2 FAIL（误把 KL 算成 state 间差异；冻结 transition 不依赖起始 s）；改为 action/history context vs baseline KL → PASS |
| 10:58–11:00 | 修正 G7 wall 计时混入结果 JSON 导致两跑不一致 → wall 移入 `timing_n1_gates.json`；两跑 `n1_gates.json` 逐字节一致 |
| 11:00–11:03 | 写 schema/report/record/usage；核对 SHA；完成 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `DECISION_R203_N1_PREREG.md` | `930F1567254095945C228532AB8D1576915AAD01AC8ACC06185D99B573C174AD` |
| `PROBLEM_N1_v0_4.md` | `5C513D9461FAEDBD3372463A4FDD1868C927EB48501BC0CDEB7643FF6FA0649A` |
| `DESIGN_N1_v0_4.md` | `94BAB8052EF4864BD745986326F4869D9054C2935794FEDAD8733733B57C029C` |
| `generator_n1_v0_4.py`（只读导入，未改） | `AA5D454A82366BF3B7FC9E7F67FAA3499098621FAD45B84804485550E6EDCC97` |
| `generator_n1_v0_4.json` | `35E41136E344AAF6C51A73B19418FF5CBEAD9460697BB8B1EE92F9E16D610263` |
| `V4_validation_v0_4.json` | `254BEBAB201AA8A0EA33AEA8A47BC7D37A99ADE1436319D159603061DC8E2ECF` |
| `timing_n1_pilot_v0_4.json` | `A4C7E0F675B0020B99A93CC022572B3E85F30A26E391493AF45FAA3C005586C7` |
| `DECISION_R203_P1_SCOPE.md` | `2EDDC655D177D933B3A56F8432282CEB659E9B43AC3BD770220703B79230777C` |
| `power_scope.json` | `734B98B3B2D754A200419F125C6026423B77C4331F7A85706923C31BCC1474BC` |
| `ERRATA_R201_R202.md`（C197/C199/C201 修正） | `7CB756ACFFA9F9E37ECD9F26C7124FE2F87CF4BF8B1432A70B8847BAFFA9D227` |

## 3. 输出（本任务；只写 `2026-10-28-n1-implementation/` 与 tmp/）

| 文件 | SHA256 |
|---|---|
| `run_n1_gates.py` | `D2AA831F26AE8882F2B5B60C4C3FB2ACCAEA327AA381A4F949D32D23B276D7B8` |
| `n1_gates.json`（两跑一致） | `529C1D2EE1E4B4039F4BBD10115C362EEE419D4BEF62A07FEC5A3C4046CBA0E0` |
| `n1_gates_rows.csv` | `78457E1F97B85D1D70918BFCE28AB0E79123225E5D9BD3589EACF951B587F6EB` |
| `timing_n1_gates.json` | `5A52E42F845A4127E2FB09E0DA9061FB591C83DE474E8C5286380CF17F7F75AC` |
| `schema_n1_gates.json` | 见文件 |
| `report_n1_gates.md` | 见 usage/复核方 |
| `record_n1_gates.md` | 本文件（SHA 见 usage/复核方） |
| `usage_n1_gates.json` | 最后写出（SHA 见复核方） |

## 4. 实现/门结果（摘要）

- **实现**：只读导入冻结 `generator_n1_v0_4.py`；S=3、state-specific β_s/γ_s、plan-pair 共享同轮 state、状态依赖 f/g/h、两套 GT、gauge 固定；B1–B6/M 七方法由冻结模块提供；未改 λ/特征/初始化/V4 spec。
- **V1 PASS**：Δ_f/σ_max 11.6554≥2；LRT power state 1.000。
- **V2 PASS**：action/history context vs baseline max KL 0.61703≥.10；β_s/γ_s design 非零（各 2 状态）；CI 由 G3 可辨识恢复覆盖。
- **V3 PASS**：E_h_max 0.50891≥.20；interaction LRT power 1.000。
- **V4 PASS（唯一 gate）**：独立 seed=20261062/n=200：mean 503.04246827、SE 64.42138097、CI [376.77888173,629.30605481]；dev 20261061 post-hoc/oracle 20261063 fallback **未运行/未替代**。
- **G1 PASS**：976/20000=.0488≤.05；Wilson upper .05187354≤.075。
- **G2 PASS**：powers 1.000/1.000/1.000。
- **G3 PASS**：143/600/140/3；recovery state corr .94317、interaction 1.0、transition TV 0.0。
- **G4 PASS**：无泄漏检查全过；B2 audit PASS；无 A/B。
- **G5 PASS**：两跑 `n1_gates.json` 逐字节一致 SHA `529C1D2E…`；wall 只在 timing。
- **G6 PASS**：schema required keys 完整。
- **G7 PASS**：真实最终实现 pilot（2 reps×20 units）：per-rep .0455s、projected main 20.48s、mem .04GB、B2 audit PASS；caps 1800s/2h/8GB/0 wells。
- 总 gate-only wall：run1 3.74s、run2 3.70s；无效果比较。

## 5. 边界/未做

- **仅机制账**（合成、compute-only、0 wells）；**未运行效果比较**、未报告 regret/top-k/selection accuracy/method differences；未读真实响应；未用 A/B 资源。
- 不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧门槛/判定；不恢复停止实验。
- N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本记录不批准/不运行效果。

# record_M3.md —— R204-M3-P1 预注册审计记录（**不运行效果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R204-M3-P1（按 R204 BRIEF 与用户报告 §3 M3 设计支撑研究预注册；**未运行效果比较、未拟合真实/响应数据、未声称增益**）。**机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；M3 执行须另立预注册+独立挑战+Lead 批准。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 12:20–12:22 | 读 task-157、deep-coupling report/BRIEF、ERRATA C197/C199/C201/C207、R203 decision/power、M1 v0.2、M2 v0.2、N1 report；核对边界 |
| 12:22–12:26 | 建 `2026-10-28-m3-decision-credit-prereg/`；写 `formalism_M3.py`（DR 恒等/截断/支持/score-tilt/分配/规划/基线退化检查） |
| 12:26–12:28 | 首跑形式化：零支持/截断示例构造有误（b 仍正、m_true 下截断无偏）→ 修正为零支持策略/错设 m；`all_checks_pass=true` |
| 12:28–12:32 | 两跑 `formalism_M3.json` 逐字节一致 SHA `2256BDA2…`；写 PROBLEM/DESIGN/schema/report/record/usage |
| 12:32–12:35 | 核对 SHA/timing；完成 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `2026-10-28-deep-coupling-redesign/report.md` | `609ADAB397371AE7493176C75F31DE40132A1C4D5402E9B97C302E10931B7E70` |
| `2026-10-28-deep-coupling-redesign/BRIEF_R204.md` | `1A200669E10B989272F74DD2FD7AC37938FEFA013B65751C7467094B82478EF1` |
| `2026-10-27-agent-cell-colearning/ERRATA_R201_R202.md`（C197/C199/C201/C207 引用） | `7CB756ACFFA9F9E37ECD9F26C7124FE2F87CF4BF8B1432A70B8847BAFFA9D227` |
| `2026-10-28-decision-power-scope/PROBLEM_DECISION.md` | `60C9D66FE1970A3AC8B25330DCB95760BA9C0FC65236E899166D971A6898A4A8` |
| `2026-10-28-decision-power-scope/power_scope.json` | `734B98B3B2D754A200419F125C6026423B77C4331F7A85706923C31BCC1474BC` |
| `2026-10-28-decision-power-scope/DECISION_R203_P1_SCOPE.md` | `2EDDC655D177D933B3A56F8432282CEB659E9B43AC3BD770220703B79230777C` |
| `2026-10-28-m2-operator-prereg/PROBLEM_M2_v0_2.md` | `25BC2663BC970D21857796E68428D91EA2E867D13AA371DAE817B7C08A94A4BF` |
| `2026-10-28-m2-operator-prereg/DESIGN_M2_v0_2.md` | `5891858E8647EA5C47549931B6D852C459795A12919798ED223F4C8F9C788255` |
| `2026-10-28-m1-executable-gen-prereg/PROBLEM_M1_v0_2.md` | `18A7FC9F3EE9AF21BBCC7DCD84DBF6F50654DDD92E342E6ABA613E938D2F9C9B` |
| `2026-10-28-m1-executable-gen-prereg/DESIGN_M1_v0_2.md` | `11FACB26A3D62E216B7699C1AB8F7473844EE385B526A966372902E4CE092705` |
| `2026-10-28-n1-effect-run/report_n1_effect.md` | `DB9C91F032FE059048BA66327F1DC5401EAD5A158B2FC91B4E506DF05513589A` |

## 3. 输出（本任务；只写新目录与 tmp/）

| 文件 | SHA256 |
|---|---|
| `formalism_M3.py` | `F578180A10CDF8A055379BFC53FC9A1004C4D9F6118DD7EFEBEA82546E853EBC` |
| `formalism_M3.json`（两跑一致） | `2256BDA2F2D9862C6F025557BA3FC6E850ED3D6EFD1C90E72244D7804F78AA48` |
| `timing_M3_pilot.json` | `3C133C69A71EBD33C720263617D38C0F7FC664A085AD6574129752C5674FAD47` |
| `schema_M3.json` | `10A8814B0867F778D313DAA8DCFB90FAE5C27E51A33C8B7D86A9BE9E9EB071A7` |
| `PROBLEM_M3.md` / `DESIGN_M3.md` / `report_M3.md` / `record_M3.md` / `usage_M3.json` | 见 usage/SHA 表 |

## 4. 完成内容/检查

- **一步 DR 形式化**：`H=π/b`、`δ=E[H(Y−mθ)]`、`V=Eπm+δ`；评价样本独立要求；不称新意。
- **score-tilt 更新**：`logit m_{θ,ε}=logit mθ+ΣεH`；截断/共线/分离/无支持非唯一性写入。
- **共享分数/分配二阶项**：`Σπ²[Var+(E−mθ)²]/b`；错设时不能只用 Var；b_min/支持/随机化记录约束。
- **标准基线边界**：全历史重训/IW/DR/TMLE/value-aware/层级-GP/BATCHIE/最优设计；同信息/同预算；π=b→H=1 加权残差退化→撤主创新；功能均值更新≠细胞动力学。
- **三阶段**：Stage1 已知真值检查；Stage2 固定更新器比较分配；Stage3 固定反馈比较学习+闭环；主端点 δ=.05/headroom/MDE/cluster；6,282 仅 Fisher-z；次端点校准/DR 分数/RNA。
- **失败/停止/预算/数据**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded、unreachable_gate、precision_insufficient、no_increment、inconclusive；caps 1800s/2h/8GB/0 wells；真实数据 `data_unavailable`（C203/C205）。
- **形式化自洽检查**：DR max gap **0.0**；截断偏差 **−0.026407185629**；支持未识别；score-tilt root **−0.562633036711**；共线 rank **1**；分配 full≥noise；MDE **0.047982685≤.05**、n_req **278**；`all_checks_pass=true`。
- **两跑** `formalism_M3.json` 逐字节一致 SHA `2256BDA2…`；timing 10 rep 平均 **0.000174 s/rep**、wall **0.00174 s**；caps PASS。
- **未运行**任何效果比较/训练/真实数据/湿实验；N1 `no_increment` 未作 M3 证据。

## 5. 边界/未做

- 仅支撑研究/机制账；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- M3 Stage1/2/3 执行须另立执行预注册 + 独立挑战 + Lead 批准；本任务不批准/不运行。
- 真实数据当前 `data_unavailable`（C203/C205）；不得用合成/RNA/预测替代独立功能决策。

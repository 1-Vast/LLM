# Lead 批准 AMEND-001 v0.3、冻结 ON3 execution protocol v1.1、授权执行一次（non-blind/peeked，附 peek 限制）

2026-10-27。依据：ON3-AMEND-001.2-C1 最终复核（task-84，endpoint-auditor）判 **approve_to_lead，无剩余必改**；peek 披露全覆盖、旧 QUICK 路径已修、FREEZE v1.1 全链一致、代码/测试/selfcheck 未变（15/15、两跑一致）。

## 批准对象（唯一有效 SHA）
- AMEND v0.3：`AMENDMENT_ON3_EXEC-001.md` SHA256 `37D4BA1176E352863548C6BFC9CBA3477F826DD37A04BEEAB2FF3DB68BCC4062`
- peek 规范：`PEEK_DISCLOSURE_ON3.md` SHA256 `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`
- v1.1 freeze：`FREEZE_ON3_exec_v1_1_DRAFT.md` SHA256 `14A6E1E3A5204A1C17423F0491DFDCF9A4951A9A93AC2011DA12C4C127F89C25`
- v1.1 protocol：`PROTOCOL_ON3_exec_v1_1_DRAFT.md` SHA256 `8C4B2D9BA1DF9A91CB3DFC0AF18BC677AF87A0ADB7075D03FC5CDCCF886EC7C4`
- updated report `9F2DC14E…`、record `2292C048…`、usage `38647AFF…`、record_amend `883E27E4…`、usage_amend `B2A6236B…`；refimpl `AD1C54D5…`、run `41D2BC2C…`、test `25B6E410…`、test_results `6282E395…`（15/15 OK 2.867s）、selfcheck `7F3EDA17…`/`3EB44C25…`
- 旧 `8B4B8FCC…`/`41BC637C…`/`F514347B…` = **invalid spec, no valid execution；不得用于批准或引用**。

## 唯一设计改动（成功标准未降）
null gate 对象 `ρ_null` → `Δρ_null=ρ(B4_null)−ρ(B2)`，输出字段 `p2_5_delta_rho`/`p97_5_delta_rho`/`mean_abs_delta_rho`；其余全部不变（数据/切分/mask M+seed 20261130/fraction/端点/B2/B4/B5/纯冷/B6 1,000×5 refit_cu_only/bootstrap 5,000/指标/差值规则/MDE80/δ_min/schema（除 gate 字段名）/两跑/实测 wall/<15 min/失败类别/禁改项）。

## peek（非盲）限制（写死）
实现方已见 `tmp/on3_exec_quick_debug.invalid.json`（`39868CE4…`）的 primary/results（Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、per-fold B0–B5、verdict=design_invalid）→ **v1.1 有效执行是 non-blind/peeked**：
- **不得称盲验/盲预注册确认/独立确认**；
- 结论仅写"O'Neil 内部、本设计下的开发性描述结果（non-blind/peeked），附 PEEK_DISCLOSURE_ON3.md 披露"；
- QUICK primary 未用于选择方向/指标/阈值/切分/mask/超参/比较器；QUICK invalid artifact 不得作为结果引用；
- 执行报告必须含 `peek_disclosure` 字段。

## 执行授权（一次）
- 按 v1.1 执行 **full B6 1,000×5 refit_cu_only、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap**；产出 `on3_exec.json`/`report_on3_exec.md`/`record_on3_exec.md`/`usage_on3_exec.json` + SHA。
- 不运行效果/更新器/迁移/决策分析；结果仅开发性描述；冻结≠资源足够/关系成立/Stage 1/效果。
- 发现实现偏差→停并重新预注册，不得执行时改协议；冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数。
- 阴性只能写"本资源/本设计下无描述性增量（non-blind/peeked）"；不得写结构不存在/迁移/决策收益。

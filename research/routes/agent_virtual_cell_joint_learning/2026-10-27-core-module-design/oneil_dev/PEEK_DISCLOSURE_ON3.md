# PEEK_DISCLOSURE_ON3 —— ON3 有效执行的 peek（非盲）披露规范文本

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。**本文件是 ON3 的规范 peek 披露文本**，供 AMEND-001 v0.3、PROTOCOL v1.1、FREEZE v1.1、report_on3、record_on3、usage_on3、record_on3_amend001、usage_on3_amend001 引用；**不执行 ON3、不新读原始响应值**。

## 1. peek 事实（写死）

1. **实现方已看到真实数据上的 QUICK result-shaped artifact**：`tmp/on3_exec_quick_debug.invalid.json`（原 `tmp/on3_exec_quick_debug.json`；SHA256 `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5`；配套 usage `.invalid.json` SHA `60DB423C22DA660FD43D5DEA4D5FBD857B9DD076D74B124C089D273150F9CC11`）。
2. 该 artifact 为 **QUICK=1, N_PERM=20, BOOT_B=100** 的**无效执行**（非冻结 full run：B6 1,000×5、bootstrap 5,000 未跑；无双跑），但含完整 schema 的 **primary/results**：
   - `delta_rho_mean = 0.0277068`；`delta_rho_ci95 = [0.01828, 0.03572]`；`positive_folds = 4`；`delta_rho_min_rank = 0.10`；
   - 每折 B0–B5 的 ρ/MAE/top-k；context-ablation/pure-cold；`verdict = design_invalid`；
   - `null.n_perm=20` 与 `gate.n_perm=100` 不一致（无效执行痕迹）。
3. **因此 ON3 的有效 v1.1 执行是 non-blind / peeked**：实现方在看到上述 primary/results 之后才进行 v1.1 冻结与执行。**不是盲验、不是盲预注册确认、不是独立确认**。

## 2. 解释限制（写死；适用于 v1.1 执行与任何结果报告）

1. **不得称盲验/盲预注册确认/独立确认**；不得写"预注册确认""独立验证""blind validation"等。
2. 结论只能写：**"O'Neil 内部、本设计下的开发性描述结果（non-blind/peeked），并附本 peek 披露"**；不得升级为迁移/外推/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。
3. **QUICK primary 未用于选择方向/指标/门槛**：null gate 修订的正当性仅来自同节已冻结 `Δρ_null` 定义 + null 预测含不变 `B2_static` 的代数必然性；QUICK 的 Δρ/CI/positive folds/B0–B5 等**未用于**选择指标、阈值、切分、mask、超参、比较器或方向。
4. 修复后仍可能 `no_increment`/`evaluation_cannot_distinguish`；QUICK Δρ=0.0277 < 0.10，即使按冻结增量规则也 likely `no_increment`，**不构成正结果**。
5. 执行报告（`report_on3.md`/`usage_on3.json`/`record_on3.md`）**必须包含 peek 披露字段/段落**（`peek_disclosure`），并写明 non-blind/peeked、QUICK invalid artifact 不得引用。
6. QUICK invalid artifact 已 quarantine（`.invalid.json`），**不得作为结果引用**；正式 `on3_exec.json` 不存在仅指 formal artifact 未生成，**不等于无 result-like artifact**。

## 3. 允许/禁止措辞（冻结）

- 允许："O'Neil 内部开发性描述；non-blind/peeked；结果附 peek 披露；QUICK invalid artifact 仅用于说明门规格缺陷、未用于选择。"
- 禁止："盲验""独立确认""预注册确认""独立验证""迁移""外推""决策收益""机制""更新器优势""资源足够""新颖性""结构成立/不存在"（阴性只能写"本资源/本设计下无描述性增量"）。

## 4. 引用位置

- `AMENDMENT_ON3_EXEC-001.md`（v0.3）§peek；
- `PROTOCOL_ON3_exec_v1_1_DRAFT.md` §peek 披露；
- `FREEZE_ON3_exec_v1_1_DRAFT.md` 冻结声明 + 全链表；
- `report_on3.md`/`record_on3.md`/`usage_on3.json` 的 `peek_disclosure`；
- `record_on3_amend001.md`/`usage_on3_amend001.json` 的 peek 字段；
- Lead 批准文本须含 peek 限制（引用本文件 SHA）。

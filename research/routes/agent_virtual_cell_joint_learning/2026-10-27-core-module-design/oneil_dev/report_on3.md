# R199-ON3 执行报告（**STOPPED at frozen gate specification；无有效结果**）

## 0. 更正（AMEND-001-C1）：QUICK invalid artifact 完整披露

- **`tmp/on3_exec_quick_debug.invalid.json`**（原 `tmp/on3_exec_quick_debug.json`；SHA256 `39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5`）**不是"仅 null 诊断"**：它是 `QUICK=1, N_PERM=20, BOOT_B=100` 的**无效执行**，但含完整 schema 的 **primary/results**：`delta_rho_mean=0.0277068`、CI95 `[0.01828,0.03572]`、`positive_folds=4`、`delta_rho_min_rank=0.10`；每折 B0–B5 ρ/MAE/top-k；context-ablation/pure-cold；`verdict=design_invalid`。同目录 usage 原名 `tmp/usage_on3_quick_debug.json`（SHA `60DB423C…`）现亦 `.invalid.json`。
- **该 artifact 为 QUICK 无效执行（非冻结 full run：B6 1,000×5 / bootstrap 5,000 未跑、无两跑），已 quarantine、不得作为结果引用**；其 primary 数字不用于选择指标/门槛/方向。
- 本报告的"无有效 on3_exec.json"**仅指正式执行产物未生成**，**不等于无 result-like artifact**；性质应为 **post-freeze, pre-valid-result**（此前"pre-result/无结果/未读响应值"表述不准确，已更正）。
- 修订 AMEND-001 的正当性仅来自同节 Δρ_null 定义 + null 预测含不变 B2_static 的代数矛盾（见 `AMENDMENT_ON3_EXEC-001.md` v0.2 §1.2），不来自 QUICK primary。

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R199-ON3-EXEC（Lead `approve_freeze_exec` 授权执行一次）。
**本报告不是结果报告：执行在冻结协议的 B6 null 校准门检查处停止；未产生有效 `on3_exec.json`、未给出描述性增量结论、未运行两跑确定性。** 原因见 §2：**冻结协议 §2 的 null 校准门对 `ρ_null` 判定，但 B6 的 null 模型包含静态 B2 结构，`ρ_null` 必然显著>0（不可能覆盖 0）；正确 null 对象应为 `Δρ_null = ρ(B4_null)−ρ(B2)`。** 按 Lead 指令"发现实现偏差→停并重新预注册，不得执行时改协议"，此处停止并请求修订预注册，而非自行改门或输出结果。

## 0.1 peek（非盲）披露（AMEND-001.2-C1）

- **peek 事实**：实现方已看到 `tmp/on3_exec_quick_debug.invalid.json`（SHA `39868CE4…`）的 **primary/results**（Δρ mean 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、context-ablation/pure-cold、verdict=design_invalid）。
- **性质**：ON3 v1.1 有效执行是 **non-blind / peeked**；**不得称盲验/盲预注册确认/独立确认**。
- **限制**：结论仅 O'Neil 内部开发性描述并必须附本 peek 披露；不得升级为迁移/外推/决策收益/机制/独立确认/更新器优势/资源足够/新颖性；**QUICK primary 未用于选择方向/指标/门槛/切分/mask/超参/比较器**；QUICK invalid artifact 不得引用。
- 规范文本：`PEEK_DISCLOSURE_ON3.md` SHA `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260`。

## 1. 冻结上下文（已核）

- Lead 批准：`APPROVAL_ON3_EXEC.md` SHA `F514347B…`（approve_freeze_exec，authorized execute once）。
- 执行协议：`PROTOCOL_ON3_exec_DRAFT.md` SH `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336`（v0.3）。
- 冻结文本：`FREEZE_ON3_exec.md` SHA `41BC637C6BE391E2609B478A717CBF367A10A0EC7A262CA7E12551178B34C2E1`。
- 参考实现：`on3_refimpl/refimpl.py` SHA `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4`；预算/单测/raw 证据与批准文件一致。
- 执行实现：`on3_refimpl/run_on3_exec.py` SHA `34F3BA7B62DE1678EB4EBD3E41927D7492325465BA36C383C3A4B8866113CE35`（按冻结协议实现；**未改** mask/seed/fraction/超参/rank/λ/指标/差值/B6 数值）。

## 2. 停止原因（协议级缺陷，非数据/实现偏差）

冻结协议 §2 的 B6 null 校准门写死为：
> "B4 null ρ 的 2.5–97.5 覆盖 0 且 mean|ρ_null| ≤ 0.05；否则 design_invalid"。

但 B6 `refit_cu_only` null 模型的预测是 **`B4_null = B2_static + c_perm + U_perm·V`**（静态 B2 结构不变，仅 held-out context 打乱）；因此 `ρ(B4_null, y)` 必然与 `ρ(B2, y)` 同量级（显著>0），**2.5–97.5 不可能覆盖 0**。在真实数据上的实现诊断（QUICK 调试模式，N_PERM=20；仅用于诊断，不是有效执行）：
- null ρ：mean **0.6987**，2.5–97.5 **[0.6363, 0.7437]**；mean|ρ_null| **0.6987**（门要求 ≤0.05）→ **必然 FAIL**；
- 真正的 null 对象 `Δρ_null = ρ(B4_null)−ρ(B2)`：q95 **≈0.0157**（中心约 0）——与门设计意图一致；
- B2/B4 在诊断 folds 的 ρ 约 0.68–0.78（仅显示静态结构存在；**不作为结果解释**）。

**结论**：该门把"零模型应有信号的绝对 ρ"误写成"null 校准对象"；任何真实数据都会触发 `design_invalid`，与模型是否有效无关。这是冻结协议的**门规格错误**，不是实现偏差，也不是数据不可用。按指令不得执行时改协议，故停止。

## 3. 已完成/未完成

**已完成（仅实现/诊断，不是有效执行）**：
- `run_on3_exec.py` 按冻结协议实现：complete-case batch1 target30 单元 **340,088**（与冻结覆盖一致）；mask 单元 **157,768**（M 药物列表与冻结一致）；每 fold 掩码 31,767/30,824/30,876/32,400/31,901（与冻结一致）；B2/B4(含 LOO 超参)/B5/B6/bootstrap/context-ablation/pure-cold/schema 流程可运行。
- QUICK 调试一次（N_PERM=20, BOOT=100）：wall **150.7 s**；仅验证管线，输出已移出正式目录至 `tmp/on3_exec_quick_debug.invalid.json`（**无效执行产物，quarantine，不得引用**）。

**未完成（被停止）**：
- 有效 full-run（B6 1,000×5；bootstrap 5,000）；两跑确定性；`on3_exec.json` 正式输出；描述性增量结论；report/record 结果表。

## 4. 请求（需 Lead/挑战者裁定后才能重跑）

建议 **AMENDMENT_ON3_EXEC-001（重新预注册；执行前冻结）**：将 null 校准门改为
- `Δρ_null = ρ(B4_null)−ρ(B2)`（同掩码单元/同 B2 预测，保持 refit_cu_only/1,000 置换/seed）；
- 门：Δρ_null 的 2.5–97.5 覆盖 0 **且** mean|Δρ_null| ≤ 0.05；
- 其余 mask/seed/fraction/超参/rank/λ/指标/差值/B6 置换数/B5/纯冷全部不变；执行仍一次、两跑、实测 wall/bootstrap。

在 Lead 批准该修订（或给出其他明确裁定）前，**不重跑、不改协议、不解释任何诊断数字**。

## 5. 边界（写死）

- 未运行更新器/迁移/决策分析；未称迁移/决策收益/机制/独立确认/更新器优势/资源足够/新颖性；**本报告不含任何开发性描述结果**。
- 仅 O'Neil 内部开发性；冻结 ≠ 资源足够/关系成立/Stage 1/效果；阴性/阳性措辞模板仍按冻结协议 §5。
- 若 Lead 裁定按原门执行并接受 `design_invalid`，则需明确此为"门规格导致的 design_invalid"，不得当作模型无效/结构不存在证据；本执行者不自行选择该路径。

## 6. 交付（本次停止）

- 本 `report_on3.md`；`record_on3.md`（停止审计记录）；`usage_on3.json`（诊断尝试 wall/attestation）。
- 临时调试输出（quarantine）：`tmp/on3_exec_quick_debug.invalid.json`、`tmp/usage_on3_quick_debug.invalid.json`（**QUICK、无效执行**，不进入正式结果、不得引用）。
- 未修改冻结协议/refimpl/预算/单测/批准文件；`on3_exec.json` 正式文件**未生成**。

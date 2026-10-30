# R199-ON3 执行审计记录（record_on3.md；**STOPPED at frozen gate specification**）

## 0. 更正（AMEND-001-C1）：QUICK invalid artifact 与状态

- `tmp/on3_exec_quick_debug.invalid.json`（原 `on3_exec_quick_debug.json`；SHA `39868CE4…`）是 `QUICK=1/N_PERM=20/BOOT=100` 的**无效执行**，但含**真实数据 result-shaped primary/results**（Δρ mean 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、每折 B0–B5 ρ/MAE/top-k、verdict=design_invalid）；**不得引用为结果**；正式 `on3_exec.json` 不存在 ≠ 无 artifact。
- 正确状态：**post-freeze, pre-valid-result**（不是"pre-result/无结果/未读响应值"）；QUICK artifact 已 quarantine（`.invalid.json`），不进正式结果路径；其 primary 数字未用于选择指标/门槛/方向。
- AMEND-001 修订依据仅来自同节 Δρ_null 定义/代数必性（v0.2 §1.2）；QUICK 不构成正结果（Δρ 0.0277<0.10，按冻结增量规则 likely `no_increment`）。

角色：ON1/ON2/ON2.2/ON3 执行者（非提案者，未参与挑战/批准）。任务：R199-ON3-EXEC（Lead `approve_freeze_exec` 授权执行一次）。**本记录记录：执行在冻结协议 B6 null 校准门处停止；未产生有效结果；未运行两跑；未改协议。**

## 0.1 peek（非盲）披露（AMEND-001.2-C1）

- 实现方已见 `tmp/on3_exec_quick_debug.invalid.json`（SHA `39868CE4…`）的 primary/results（Δρ 0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、verdict=design_invalid）→ ON3 v1.1 有效执行 **non-blind/peeked**。
- **不得称盲验/盲预注册确认/独立确认**；结论仅 O'Neil 内部开发性描述并附 peek 披露；QUICK primary 未用于选择指标/门槛/方向；QUICK invalid artifact 不得引用。
- 规范文本：`PEEK_DISCLOSURE_ON3.md` `B4CAD955…`；执行报告必须含 `peek_disclosure`。

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| ~21:49–21:50 | 读 `APPROVAL_ON3_EXEC.md`（批准/冻结文本）、`FREEZE_ON3_exec.md`、`PROTOCOL_ON3_exec_DRAFT.md` v0.3；确认冻结 SHA/预算/单测/raw 证据一致 |
| ~21:50–21:52 | 写 `on3_refimpl/run_on3_exec.py`（按冻结协议；未改 mask/seed/fraction/超参/rank/λ/指标/差值/B6=1,000）；修实现 bug（fold cell id 重置、B5 特征 cell offset/context size、bootstrap 存储、schema sanitizer） |
| ~21:52–21:55 | 读入 O'Neil 工作簿 → complete-case batch1 target30 单元 **340,088**；mask **157,768**；5 折覆盖与冻结一致（31,767/30,824/30,876/32,400/31,901） |
| ~21:55–21:57 | QUICK 调试运行（N_PERM=20/BOOT_B=100；**仅诊断**，非有效执行）：wall 150.7 s；流程跑通，但 null 门 FAIL |
| ~21:57–22:00 | 诊断冻结 §2 null 门语义：`ρ_null` mean 0.6987、2.5–97.5 [0.636,0.744]（不可能覆盖 0），而 `Δρ_null` q95≈0.0157；判定为**协议门规格错误**（应为 Δρ_null），按 Lead 指令停止、请求修订预注册；写 report/record/usage；调试产物移 tmp |
| — | **未运行 full-run（1,000×5）**；未生成正式 `on3_exec.json`；未做两跑确定性 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `APPROVAL_ON3_EXEC.md` | `F514347BA162A571D9FE9A9B7BC1B0012AAADCE46EA233778D6C6BC7A7866280` |
| `PROTOCOL_ON3_exec_DRAFT.md`（v0.3） | `8B4B8FCC4B8E2E1DF7DE00A4498AF5EAF52535A042E4F58F348D7D6EA3672336` |
| `FREEZE_ON3_exec.md` | `41BC637C6BE391E2609B478A717CBF367A10A0EC7A262CA7E12551178B34C2E1` |
| `on3_refimpl/refimpl.py` | `B5485B23F416175E69507397997F05C671C9248DD614361E7482D3C54D580FA4` |
| `on3_refimpl/run_on3_exec.py`（本次执行实现） | `34F3BA7B62DE1678EB4EBD3E41927D7492325465BA36C383C3A4B8866113CE35` |
| 组合工作簿 | `A0E2E002DC06C34E8AEDF3206877A93BAB7E45190AD8BB8E70ED79FF24C14818` |
| ON2 v2.2/ERRATA/report/record/on2.json/calib | `7B34DB79…` / `3C6138DF…` / `C6CF6467…` / `789A0114…` / `AD7E6D13…` / `DC2D29C1…` |

## 3. 停止依据（关键）

冻结协议 §2（v0.3）原文：
> "null 校准门（二元，冻结）：**B4 null ρ 的 2.5–97.5 覆盖 0 且 mean|ρ_null| ≤ 0.05**；否则 `design_invalid`。"

实现诊断（QUICK，仅诊断；**不得作为结果引用**）：B6 `refit_cu_only` null = `B2_static + c_perm + U_perm·V`，所以 `ρ(B4_null, y)` 与 `ρ(B2,y)` 同量级：
- `ρ_null` mean **0.6987**，2.5–97.5 **[0.6363, 0.7437]** → 不可能覆盖 0；mean|ρ_null|=**0.6987** >0.05 → 门必 FAIL；
- `Δρ_null = ρ(B4_null)−ρ(B2)`：q95 **≈0.0157**（中心≈0）。

→ 该门把"应含静态信号的绝对 ρ"当作 null 校准对象，**任何真实数据都会 `design_invalid`**；这是**冻结门规格错误**，不是实现偏差、不是数据不可用、也不是模型结果显示。按 Lead 指令"发现实现偏差→停并重新预注册，不得执行时改协议"，**停止**。

## 4. 决策

1. **不执行 full-run、不输出结果、不两跑**：在 Lead/挑战者裁定前不重跑、不改协议、不解释诊断数字。
2. **请求 AMENDMENT_ON3_EXEC-001**（执行前重新预注册并冻结）：null 门改为 `Δρ_null = ρ(B4_null)−ρ(B2)` 的 2.5–97.5 覆盖 0 且 mean|Δρ_null|≤0.05；其余 mask/seed/fraction/超参/rank/λ/指标/差值/B6=1,000/B5/纯冷全部不变；执行一次、两跑、实测 wall/bootstrap。
3. 若 Lead 裁定按原门执行并接受 `design_invalid`，须明确这**不是**模型无效/结构不存在/资源不足证据；本执行者不自行选择该路径。

## 5. 产出/边界

- 正式产出：本 `record_on3.md`、`report_on3.md`（STOP 报告）、`usage_on3.json`（诊断尝试 wall/attestation）。
- 调试产物（**无效执行，quarantine，不得引用**）：`tmp/on3_exec_quick_debug.invalid.json`、`tmp/usage_on3_quick_debug.invalid.json`（QUICK=1，N_PERM=20/BOOT=100）。
- **未生成**正式 `on3_exec.json`；未运行 ON3 有效执行；未运行更新器/迁移/决策分析；未称迁移/决策收益/机制/独立确认/更新器/资源足够/新颖性；冻结 ≠ 资源足够/关系成立/Stage 1/效果。
- 未修改冻结协议/refimpl/预算/单测/批准文件；只写 `oneil_dev/` 新增与 `tmp/`。

## 6. 明确不做

- 未把 QUICK 诊断当作执行结果；未在报告/消息中给出 B4 vs B2 的描述性增量结论；未改协议门/指标/差值/B6 数；未重跑追结果；未声称任何生物学/效果结论。

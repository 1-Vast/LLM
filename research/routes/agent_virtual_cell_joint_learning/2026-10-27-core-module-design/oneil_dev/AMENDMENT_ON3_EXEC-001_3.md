# AMENDMENT_ON3_EXEC-001.3（v1.2）—— ON3 执行溯源修复（provenance-only；不改变执行语义）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：Lead `DECISION_ON3_PROVENANCE.md`（SHA `6C2DFD55C89D2BE4989480307A7A538829E850627E784CB0F815EEE359EB00C3`；裁定 **Option B 严格修复**，不采用元数据豁免）。**本修订只改执行实现的输出 input 溯源字段/路径；执行语义/数据/切分/mask/超参/rank/λ/指标/差值规则/B6 1,000×5 refit_cu_only/bootstrap 5,000 一律不变。** 本文件起草与预检**未运行 ON3 有效执行**；重跑需按 v1.2 freeze 授权。

## 1. 缺陷（v1.1 执行溯源偏差）

- v1.1 执行（provisional）的 `on3_exec.json` 在 `protocol` 与 `inputs.protocol_on3_exec`/`inputs.freeze_on3_exec` 中写入**旧 invalid spec**：`PROTOCOL_ON3_exec_DRAFT.md` `8B4B8FCC…` / `FREEZE_ON3_exec.md` `41BC637C…`，而非 Lead 批准的 v1.1 `8C4B2D9B…`/`14A6E1E3…`。
- 批准文本明文规定旧 `8B4B8FCC…`/`41BC637C…`/`F514347B…` **invalid spec，不得引用/不得用于批准**；因此正式证据链不得携带这些 SHA。
- 执行语义未受影响（数据/切分/mask/B4/B6/指标/阈值/两跑均按 v1.1），但**严格修复要求重跑一次**并产出 v1.2 正式链。
- **provisional 结果保持 quarantine、不得引用/登记**（见 §5）。

## 2. 唯一改动（精确代码 diff）

文件：`on3_refimpl/run_on3_exec.py`（v1.1 `41D2BC2C…` → v1.2 `B3A5569EC852AE6FD1B5D879336E44EC3F1F5F55D2BB420DF9D7EED41CEC8E39`）。
精确 diff：`tmp/on3_amend001_3_code.diff` SHA `EF43ACDE57EB3DB574F2142CE9904E7F8D19651E3DAF9154486A795A13F0CCBA`。

**Before（v1.1）：**
```python
'protocol_on3_exec': {'path_rel': '.../PROTOCOL_ON3_exec_DRAFT.md',
                      'sha256': sha_file(os.path.join(ONEIL, 'PROTOCOL_ON3_exec_DRAFT.md'))},
'freeze_on3_exec': {'path_rel': '.../FREEZE_ON3_exec.md',
                    'sha256': sha_file(os.path.join(ONEIL, 'FREEZE_ON3_exec.md'))},
...
'protocol': {'file': 'PROTOCOL_ON3_exec_DRAFT.md', 'sha256': inputs['protocol_on3_exec']['sha256'],
             'freeze_file': 'FREEZE_ON3_exec.md', 'freeze_sha256': inputs['freeze_on3_exec']['sha256']},
```
**After（v1.2）：**
```python
'protocol_on3_exec': {'path_rel': '.../PROTOCOL_ON3_exec_v1_2_DRAFT.md',
                      'sha256': sha_file(os.path.join(ONEIL, 'PROTOCOL_ON3_exec_v1_2_DRAFT.md'))},
'freeze_on3_exec': {'path_rel': '.../FREEZE_ON3_exec_v1_2_DRAFT.md',
                    'sha256': sha_file(os.path.join(ONEIL, 'FREEZE_ON3_exec_v1_2_DRAFT.md'))},
...
'protocol': {'file': 'PROTOCOL_ON3_exec_v1_2_DRAFT.md', 'sha256': inputs['protocol_on3_exec']['sha256'],
             'freeze_file': 'FREEZE_ON3_exec_v1_2_DRAFT.md', 'freeze_sha256': inputs['freeze_on3_exec']['sha256']},
```
- **仅 6 行**（2 个 path/sha 行 + 1 个 `protocol` 行组成）变化；执行逻辑/数据/切分/mask/超参/rank/λ/指标/差值/B6/bootstrap/两跑要求**零改动**（diff 中无其他 hunk）。
- 预期正式 `on3_exec.json` 的 `protocol.sha256` = v1.2 protocol `B22A7FC7…`、`freeze_sha256` = v1.2 freeze SHA；不再出现旧 invalid spec。

## 3. 预检（v1.2）

- `run_on3_exec.py` 编译通过；diff 仅 §2 的 6 行。
- **15/15 单测 OK（2.626 s）**：`test_results.txt` SHA `D93AAA067C46B0836E7FD7F604F08CBE3B304F7F790121B669F5313C302E232F`。
- **两跑 selfcheck 逐字节一致**：`selfcheck.json` SHA `3EB44C2552AA6766D230DCADF790E14B34A1514F7C798EF73A82F95AB16E5C5A`（refimpl/test/selfcheck 未变）。
- 新 v1.2 protocol SHA：`B22A7FC791B07C415DE8C8A48DF916DDAC7309A9ECD02CFBE567050F9099A2A8`；v1.2 freeze SHA 见 `FREEZE_ON3_exec_v1_2_DRAFT.md`。
- 旧 `8B4B8FCC…`/`41BC637C…`/`F514347B…` 仍标 invalid spec；v1.1（`8C4B2D9B…`/`14A6E1E3…`）作为已批准基线，仅 input 溯源被 v1.2 superseded（执行语义不变）。

## 4. v1.2 执行（授权重跑一次）

- 按 v1.2 重跑 ON3 **一次**（non-blind/peeked；PEEK_DISCLOSURE_ON3 `B4CAD955…`）：full B6 1,000×5 `refit_cu_only`、bootstrap 5,000、两跑逐字节一致、实测 wall/bootstrap；正式产物 `on3_exec.json`/`report_on3_exec.md`/`record_on3_exec.md`/`usage_on3_exec.json` 写入正确 v1.2 SHA。
- 报告必须含 `peek_disclosure` 与 **runtime deviation**（v1.1 provisional 实测 wall≈19.6/21.6 min > 冻结估计 <15 min；仅计时偏差、未改设计）；v1.2 wall 实测另报。
- 结论边界：仅 O'Neil 内部开发性描述（non-blind/peeked）；不称盲验/独立确认/迁移/决策收益/机制/新颖性；`no_increment` 只表示未达到预注册 δ_min=0.10 描述性增量；点估计/CI/folds 仅描述性，不写成结构成立/不存在/迁移/决策证据。
- 执行中若发现实现偏差→停并重新预注册。

## 5. provisional 隔离（不得引用）

- `tmp/on3_exec_v1_1_provisional.json`（SHA `5698151968…`）、`tmp/report_on3_exec_v1_1_provisional.md`（`7AC71D57…`）、`tmp/record_on3_exec_v1_1_provisional.md`（`4BCC8BAC…`）、`tmp/usage_on3_exec_v1_1_provisional.json`（`11DFF763…`）——**保持 quarantine，不得引用/登记**；本修订/正式 v1.2 报告不引用其任何结果数字（包括 Δρ/CI/folds/verdict）。

## 6. 边界

- 本修订不运行效果/更新器/迁移/决策分析；仅 ON3 开发性描述（non-blind/peeked）。
- 冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则/B6 置换数；冻结 ≠ 资源足够/关系成立/Stage 1/效果。

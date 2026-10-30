# R199-ON2-EX 审计记录（record_calib）

角色：ON1/ON2 执行者（非提案者；不参与效果设计）。任务：R199-ON2-EX —— 在 ON2 v2.2 冻结协议下执行**资格执行阶段**（σ_e 标定 + MDE80 认证 + 确定性单插补敏感性；非效果）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/exec_calibration/` 与 `tmp/`；**未改** ON1/ON2 冻结产物、其它目录、INDEX、SYNTHESIS、git。

## 1. 依据与边界

- 依据：`PROTOCOL_ON2.md` v2.2 §3.2(b)（固定索引分半、σ̂_e²、SE_unit、MDE80、stop rule）、§3.3(2)（确定性行均值单插补，非 MI）、§4/§5（判定与边界）；`ERRATA_ON2_1.md`；`report_on2_1.md`；`record_on2_1.md` §10 冻结文本。
- 边界：不运行效果/训练/更新器比较；不做迁移/决策分析；不称资源足够/关系成立/效果；不称独立确认/迁移/决策收益/机制/新算法；技术重复≠独立培养；n_eff=6 held-out 细胞；只按冻结公式做噪声标定/敏感性。

## 2. 命令、预算、实际耗时

| 命令 | wall | CPU process |
|---|---:|---:|
| `python -X utf8 research/2026-10-27-core-module-design/oneil_dev/exec_calibration/run_calib.py`（run1） | **46.34 s** | **43.83 s** |
| 同上（run2，确定性核对） | **47.34 s** | **45.22 s** |

- 预算 ≤45 min；实际 <1 min/跑；CPU-only，无 GPU；无网络。`PYTHONHASHSEED=0`；Python 3.11.16 / numpy 2.4.6 / pandas 2.3.3。
- 两跑 `calib.json` **逐字节一致**：SHA256 `DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A`。
- `usage_calib.json` 记录 run2 的 wall/CPU、输入字节数、输出 calib SHA。

## 3. 输入 SHA

| 输入 | SHA256 |
|---|---|
| 组合工作簿 | `A0E2E002DC06C34E8AEDF3206877A93BAB7E45190AD8BB8E70ED79FF24C14818` |
| `PROTOCOL_ON2.md` v2.2 | `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7` |
| `ERRATA_ON2_1.md` | `3C6138DF7BA1ACCDC7088FC78070F835D6DF61D0E7BBF77EF6B4DE0E0FE7870B` |
| `report_on2_1.md` | `C6CF64677658AB18F91EA956F236E34DFE0B890431456F5908A30D47B7D569EE` |
| `record_on2_1.md` | `789A01149D7874BED454B6F5EC9F0CC274529438779B384E8EC11A1B07484694` |
| `on2.json`（历史数据产物） | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| `run_calib.py` | `3786576B019D7B44E8C2572006BAD0BE5D507CFDC644CED7232A70C6594579D9` |

## 4. 运行内容（冻结条款）

1. **σ_e 主标定（complete-case）**：cohort = viability1–4 全非空；all batches/all cells；rows_used **363,090**；成员上下文 **44,070**；合法上下文 **2,927**；可替换 Δ 单元 **442,996**。
   - 固定重复列索引 `viability1..4`；k=4 → {v1,v2} vs {v3,v4}（2+2）；**禁按观测值排序**。
   - `σ̂_e² = Σ(Δ_h1−Δ_h2)² / Σdenom`；complete-case 每单元 denom=**1/8**；sumsq=**1,120.7665523745**；sumden=**55,374.5**。
   - **σ̂_e = 0.1422665081**；SE_unit=**0.0251494031**；MDE80=**0.0287644381**；n_eff=6；δ_min=0.10 → **PASS（calibration_passed）**。
2. **Scope 变体（透明性；gate 用 primary）**：batch1 all cells σ̂_e=0.1422146472 / MDE=0.0287539525；batch1 target 30 cells σ̂_e=0.1384458171 / MDE=0.0279919441；batch2 all cells σ̂_e=0.1612883917 / MDE=0.0326104156；**全部 ≤0.10**。
3. **all-available 敏感性标定（rule A）**：rows_used **368,754**；k=1 **78 行排除并计数**；成员上下文 **45,948/46,104**（排除 **156**）；合法上下文 **3,101**；units **470,179**；no-exclusion units **473,906**；units excluded **3,727**；σ̂_e=**0.1434390629**；SE=**0.0253566835**；MDE=**0.0290015134 ≤0.10 → PASS**；仅敏感性，不替代主标定/gate。
4. **确定性行均值单插补敏感性（不是 MI）**：全表 rows **368,832**；units **473,906**；Δ 均值 **0.0059696378**；batch1 target units **363,304**、Δ 均值 **0.0034618085**；**无 m/seed/Rubin/随机抽样**；描述性敏感性，不用于门级/效果推断；complete-case 主 Δ 均值 0.0062839576、all-available Δ 均值 0.0060780967（仅并排描述）。
5. **门控**：MDE80=0.0287644381 ≤0.10 → **calibration_passed**；未触发 `design_invalid: precision_insufficient`，未运行任何效果步骤。输出允许的下一步：**"资格执行完成，可进入开发性描述分析（须另立协议+独立挑战）"**。

## 5. 产物 SHA

| 产物 | SHA256 |
|---|---|
| `run_calib.py` | `3786576B019D7B44E8C2572006BAD0BE5D507CFDC644CED7232A70C6594579D9` |
| `calib.json` | `DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A` |
| `usage_calib.json` | `77D24047F120974F15BE77FB8D9DA6F7DCC89C5F04AD6816733CADCD4AF0158B` |
| `report_calib.md` | `80A7563E3FBDDEA460C53198059CD3E2801A9112CFA4631FDD3A6D3BA3295871` |
| `record_calib.md` | 本文件（SHA 由审计方重算） |

## 6. 决定与理由

- **Primary 标定 scope**：协议只写 "complete-case 行（主）"，未限定 batch；本执行采用 **complete-case all batches/all cells** 作为 primary（最大样本；44,070 成员上下文/442,996 units）；另报 batch1/target/batch2 变体，全部 MDE≤0.10，结论不依赖全 batch 合并的偶然性。该选择已在本报告/record 写死；若后续协议要求 batch1-target 为 gate scope，MDE=0.02799 同样 PASS，结论不变。
- **all-available 敏感性与 rule A**：k=1 行（78）不参与标定；成员上下文 45,948/46,104 可用（排除 156 个 15/16 上下文）；units 470,179；excluded units 3,727；这些排除计数与 v1.1/ON2.1 基线一致。
- **单插补**：严格按冻结规则做单次确定性行均值插补；不是 MI；无 m/seed/Rubin；只作描述性敏感性，不进入 gate/effect。
- **认证通过**：σ̂_e=0.1423 高于借用先验上界 0.109，但 MDE80 仅 0.02876，仍 ≤δ_min=0.10；认证通过仅允许进入"开发性描述分析（须另立协议+独立挑战）"，不声称资源足够/关系成立/效果。

## 7. 偏离/实现说明

- 初版 `run_calib.py` 有两处实现错误（`member_curves` denom merge 列冲突；imputation 的 `np.sum(...)[iu]` 索引错误），已在正式两跑前修复；正式两跑 `calib.json` 逐字节一致，最终 SHA 见 §5。失败草稿未作为产物。
- `contexts_legal` 初次误把"有 complete member 的上下文"计为 legal；正式版按"≥2 complete members"计（2,927/3,101），units/sigma 不受影响。
- 未读/未使用响应值做效果统计；viability 只用于冻结的标定/单插补公式。
- 未重跑 `on2.py`；未改 `on2.py`/`on2.json`/`usage_on2.json`/ON1/协议/报告/记录；只写 `exec_calibration/` 与 `tmp/`。

## 8. 限制与未做

- 本执行只完成资格层（σ_e/MDE 认证 + 单插补敏感性）；**未**运行效果/更新器/训练/迁移/决策分析；**未**声称独立性/新颖性/机制/决策收益。
- 认证通过 ≠ 资源足够/关系成立/Stage 1/效果证据；效果/开发性描述协议须另立 pre-registration + 独立挑战；执行期仍受缺失机制未知、batch3 全失、702 个 15 行 pair-cell、无暴露时间/assay 列、单药参照未用、技术重复≠独立培养等限制。
- `usage_calib.json` 的 peak RSS 未测量（null），GPU 未使用（null）；wall/CPU 为 Python 进程计时。

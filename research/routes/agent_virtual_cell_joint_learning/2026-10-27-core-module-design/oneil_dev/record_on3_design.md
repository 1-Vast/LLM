# R199-ON3 起草审计记录（record_on3_design）

角色：ON1/ON2/ON2.2 执行者（非提案者；不参与效果设计/挑战）。任务：**R199-ON3 协议草案（设计阶段，不运行效果）**（task-68）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/` 新增与 `tmp/`；**未改** ON1/ON2/ON2-EX 产物、其它目录/INDEX/SYNTHESIS/git。

## 1. 范围与性质

- 本任务只写 **DRAFT 协议与设计说明**：`PROTOCOL_ON3.md`（DRAFT v0.1）、`on3_design.md`、本记录、`usage_on3_design.json`。
- **未运行**任何效果/训练/更新器比较/迁移/决策分析；**未解析响应值做统计**；只做既有产物读取 + 二进制 SHA256 哈希（哈希不解析响应值）。
- DRAFT 不是执行依据；须**独立挑战（建议 endpoint-auditor，与 ON1/ON2 同一挑战者）+ Lead 批准**后，冻结为 execution protocol 才可执行；执行仍不得称迁移/决策收益/机制/独立确认/更新器优势/资源足够。

## 2. 必读输入（只读；SHA256 已核）

| 文件 | SHA256 |
|---|---|
| 组合工作簿（只读元数据/端点定义；未解析响应值） | `A0E2E002DC06C34E8AEDF3206877A93BAB7E45190AD8BB8E70ED79FF24C14818` |
| `PROTOCOL_ON2.md`（v2.2 冻结） | `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7` |
| `ERRATA_ON2_1.md` | `3C6138DF7BA1ACCDC7088FC78070F835D6DF61D0E7BBF77EF6B4DE0E0FE7870B` |
| `report_on2_1.md` | `C6CF64677658AB18F91EA956F236E34DFE0B890431456F5908A30D47B7D569EE` |
| `record_on2_1.md` | `789A01149D7874BED454B6F5EC9F0CC274529438779B384E8EC11A1B07484694` |
| `on2.json`（v2.0 历史数据产物；门级数字有效） | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| `exec_calibration/calib.json`（ON2-EX 认证） | `DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A` |
| `exec_calibration/report_calib.md` | `80A7563E3FBDDEA460C53198059CD3E2801A9112CFA4631FDD3A6D3BA3295871` |
| `challenge_ON2_2_confirm.md`（approve_freeze） | `4C2A0A149E2EE385BB011C97DBCF923E6F3529CE4B64D6952D776C9361D51B6C` |

- 另阅读：R199 BRIEF、`PROTOCOL_ON2.md` §0–§6（范围/定义/门/σ_e 条款/边界）、`report_on2_1.md` §2–§10、`exec_calibration/report_calib.md`（calibration_passed 数字）、`challenge_ON2_2_confirm.md`（冻结文本）。

## 3. 起草决定（与协议/设计说明一致；细节见 on3_design.md）

1. **问题仅开发性**：ONeil complete-case 内部细胞留出下 `Δ` 的条件结构描述性预测增量；不外推迁移/决策收益。
2. **数据切分**：complete-case 363,090/98.44%；**主分析 batch1（357,876）**；batch2 不进 primary；batch3 全失披露；30 目标细胞；**继承 ON2 5 折（6/6/6/6/6）**，不重分折。
3. **端点/聚合**：viability 4 重复均值；complete 4×4 网格 Δ 单元；角色分层/符号冻结；k=1 行排除；702 个 15 行 pair-cell 排除并计数；主分析不插补；确定性行均值单插补仅敏感性（非 MI）；**不与 Jaaks ΔEMAX 拼接**。
4. **评价设计**：细胞留出 + held-out 细胞 **20% 单元确定性掩码**（SHA256 key + seed `ON3-mask-20261130`，ceil 20%，只依赖 key/seed）；非掩码 80% 作为 transductive context；掩码值绝不进入模型路径；泄漏审计 9 项前置。**披露：不是纯冷启动**。
5. **比较器**：B0 全局均值 / B1 静态可加 / B2 静态强（partner×member-pair，主基线）/ B3 + cell context offset / B4 层级+低秩（rank/λ 网格冻结，inner CV 仅训练细胞）/ B5 HistGBM 容量对照 + B5-shuf 标签打乱 / B6 打乱零模型；不预设胜出；不比较更新器。
6. **指标**：主 Spearman ρ（掩码单元，per-fold + 5 折 mean/SD）；次 MAE；描述性 top-k（k∈{1,3,5}，无决策含义）；增量规则（Δρ≥0.10、≥4/5 folds、细胞聚类 bootstrap 95% CI 排除 0、>B6 95th）；否则 `no_increment`。
7. **功效**：用 ON2-EX 实测 σ̂_e=0.1422665081 → SE_unit=0.0251494031、MDE80=0.0287644381（n_eff=6）、δ_min=0.10；MDE 用实测不借用；rank 指标用 B6 null 校准；MDE>δ_min → design_invalid。
8. **门控/失败类别/停止**：data_unavailable / design_invalid（含泄漏审计/零模型/MDE）/ evaluation_cannot_distinguish / no_increment；不换指标/切分/端点/掩码/比较器凑结果；不重跑换 seed。
9. **流程**：DRAFT → 独立挑战 → Lead 批准 → 冻结 execution protocol → 执行；执行仍只写开发性描述，不称迁移/决策/机制。

## 4. 边界与 attestation

- **未运行效果/训练/更新器/反馈/迁移/决策分析；未读响应值做统计**；只读既有产物与二进制哈希（哈希 38.5 MB 工作簿用时 0.13 s；输入哈希合计 0.15 s）。
- 未修改 `PROTOCOL_ON2.md`/`on2.py`/`on2.json`/`report_on2_1.md`/`record_on2_1.md`/`ERRATA_ON2_1.md`/`exec_calibration/*`/ON1 产物；未改其它目录/INDEX/SYNTHESIS/git；未联网。
- 不声称新颖性；不写机制/迁移/决策收益；不称资源足够/关系成立/效果/独立确认；技术重复≠独立培养；缺失机制未知；batch3 全失、702 个 15 行 pair-cell 为限制。

## 5. 产出文件与 SHA

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON3.md`（DRAFT v0.1） | `B78197F13C70D024D429A294898880BE295147DDC0B6DB274B14216DDC25557A` |
| `on3_design.md` | `34000CA10AD65312381EB0EB7D4BBAC87B1A0C2626B7A1835EF57E683D90D482` |
| `record_on3_design.md` | 本文件（SHA 由复核方重算） |
| `usage_on3_design.json` | 本记录之后写出（SHA 见复核方重算/usage 自身记录） |

- 输入 SHA 核验：与 ON2/ON2-EX 冻结记录一致（见 §2），无漂移。

## 6. 下一步与待挑战问题

- **下一步**：提交独立挑战（建议 endpoint-auditor）→ Lead 批准 → 冻结 execution protocol；**本任务不执行、不运行效果**。
- **给挑战者的问题**（详见 `on3_design.md` §11）：transductive 掩码设计是否可接受；20% 掩码/seed 是否改成分层随机；增量阈值与 MDE 尺度；B2 是否足够强；单药参照是否另立资格；B5 容量对照是否充分；top-k 是否降为附录；B6 打乱粒度。
- **执行前必须补齐**：掩码/超参/零模型/泄漏测试的代码级 schema；bootstrap B/seed/聚类；报告措辞模板；两跑确定性；单命令 ≤45 min。

## 7. 明确不做

- 未运行效果/训练/更新器比较/迁移/决策分析；未读响应值；未改冻结产物；未声称新颖性；未写机制/迁移/决策收益；阴性/不足完整记录；不把本 DRAFT 当执行依据。

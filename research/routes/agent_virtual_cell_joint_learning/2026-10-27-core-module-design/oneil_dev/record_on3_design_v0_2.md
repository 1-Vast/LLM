# R199-ON3v0.2 起草审计记录（record_on3_design_v0_2）

角色：ON1/ON2/ON2.2/ON3 执行者（非提案者，未参与挑战）。任务：**R199-ON3v0.2**——按 `challenge_ON3.md`（ON3-C1：revise，5 条必改）修订 ON3 协议草案；只写文档，**未运行效果/训练/更新器、未读响应值做统计**；保留 v0.1 原文件；不改 ON1/ON2/ON2-EX 产物。

## 1. 依据（只读）

| 文件 | SHA256 |
|---|---|
| `challenge_ON3.md`（ON3-C1，5 条必改） | `E440F79BE111299A4E37910FFAF8D0D545C936FFD464E7F89B1BE48214A3C374` |
| ON2 v2.2 `PROTOCOL_ON2.md` | `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7` |
| `ERRATA_ON2_1.md` | `3C6138DF7BA1ACCDC7088FC78070F835D6DF61D0E7BBF77EF6B4DE0E0FE7870B` |
| `report_on2_1.md` | `C6CF64677658AB18F91EA956F236E34DFE0B890431456F5908A30D47B7D569EE` |
| `record_on2_1.md` | `789A01149D7874BED454B6F5EC9F0CC274529438779B384E8EC11A1B07484694` |
| `on2.json` | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| `exec_calibration/calib.json`（ON2-EX 认证） | `DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A` |
| `exec_calibration/report_calib.md` | `80A7563E3FBDDEA460C53198059CD3E2801A9112CFA4631FDD3A6D3BA3295871` |
| `challenge_ON2_2_confirm.md` | `4C2A0A149E2EE385BB011C97DBCF923E6F3529CE4B64D6952D776C9361D51B6C` |
| v0.1 `PROTOCOL_ON3.md` | `B78197F13C70D024D429A294898880BE295147DDC0B6DB274B14216DDC25557A` |
| v0.1 `on3_design.md` | `34000CA10AD65312381EB0EB7D4BBAC87B1A0C2626B7A1835EF57E683D90D482` |
| v0.1 `record_on3_design.md` | `747AEC6304834C06B90C0B123EDBDC37944B6BA36AB3CC67A546C99E1185DB0F` |
| v0.1 `usage_on3_design.json` | `05A1A8AF…E4DB9C2` |
| 组合工作簿（仅元数据/空值掩码；未解析响应值） | `A0E2E002DC06C34E8AEDF3206877A93BAB7E45190AD8BB8E70ED79FF24C14818` |

- 另读：R199 BRIEF、ON2 v2.2 §0–§6、report_on2_1、exec_calibration/report_calib、challenge_ON2_2_confirm、challenge_ON3 全文。

## 2. 5 条必改的落实（摘要；详见 protocol/design）

1. **掩码泄漏修复（最高优先）**：改 **整成员块掩码**（选 8/38 药物=20% 药物；held-out 细胞中凡 partner/成员触及 M 的单元全掩码）；**说明整上下文掩码仍不足**（跨上下文恒等式 `Δ(a,a';b)=Δ(b,b';a)+Δ(a,a';b')−Δ(b,b';a')`）；新增 **model-free reconstruction audit**（并查集，设计预计算 **0/157,768** 可重建）与 **context-ablation**；重算覆盖（见 §3）。
2. **唯一 primary comparator**：**B4 vs B2** 唯一增量判定；B3/B5 secondary，B0/B1 层级参照；**删除 B5-shuf**（对不含 cell id 的 B5 无效）；禁止选最佳 X；完整比较表。
3. **MDE/rank 分离**：MDE80=0.0287644381 只用于 mean Δ/MAE；rank 用 `Δρ_min_rank=max(0.10, Q95_null)` + 配对 bootstrap；0.10 为描述阈值非 rank MDE；δ_min 只 mean 尺度；单侧 95th 冻结。
4. **代码级 schema 冻结**：B6 1,000 置换/seed/每置换重拟合/单侧 95th；B5 HistGBM random_state/5 折交叉拟合 TE/容量网格；B4 ALS init/seed/tol/rank/λ/c_cell,U_cell 仅非掩码 context；bootstrap 按 held-out 细胞配对 B/seed/百分位；mask key/tie/scope；两跑逐字节一致、≤45 min、10 项单测、输出 schema。
5. **batch2/覆盖/措辞/流程**：batch2 **disclosure-only**（5,214 行/1,129 单元/136 上下文）；覆盖表重算；top-k 移附录；阴性/阳性模板与失败类别冻结；DRAFT v0.2→同一挑战者复核→Lead 批准→冻结 execution protocol；冻结后不改 mask/seed/fraction/超参。

## 3. 设计性预计算（metadata/空值掩码 only；未读响应值）

- 脚本：`tmp/_on3_v02_mask_design.py`（SHA `39557B04B8D3A70B6ACB7F54C2C870CC2793E319F330ED43D574BCE461A92638`）；输出 `tmp/on3_v02_mask_design.json`（SHA `F49B6F92D3FE42BFBEE058833603053A3149E093DDF0C0EA676229BE7B782026`）；wall **39.24 s**。
- **掩码药物（8/38）**：`dinaciclib, erlotinib, methotrexate, mitomycine, sn38, sorafenib, topotecan, vinorelbine`。
- **覆盖（batch1/target30）**：单元 340,088；**掩码 157,768（46.39%）**；非掩码 context 182,320；每 fold 掩码 **30,824–32,400**、掩码上下文 **368–372**、非掩码 35,680–37,338；每 held-out 细胞掩码 min **4,237**（median 5,400）、非掩码 context min **4,749**（median 6,223）。
- **覆盖门**：fold 掩码 ≥5,000 PASS；cell 掩码 ≥500 PASS；fold 掩码上下文 ≥50 PASS；cell 非掩码 context ≥500 PASS。
- **model-free reconstruction audit = 0 / 157,768**（并查集；系数论证：含 M 药物的 g 节点只出现在被掩码单元中）。
- **batch2 披露**：1,129 单元 / 136 上下文（不进分析）。

## 4. 输出文件与 SHA（v0.2）

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON3_v0_2.md`（DRAFT v0.2） | `97FE124A866F4B47BB2ACB04D8B4B5EBDFE4FCF9FB039B6EE8988E6A1F5F4FB9` |
| `on3_design_v0_2.md` | `4AB51CE57C6360DBB63EA8AA29E6F40D5492DBD30A6E71A6D0644BFC78C58BBA` |
| `record_on3_design_v0_2.md` | 本文件（SHA 由复核方重算） |
| `usage_on3_design_v0_2.json` | 本记录后写出（SHA 由复核方重算） |
| `tmp/_on3_v02_mask_design.py` / `.json` | 见 §3 |

- v0.1 四文件保持未改（SHA 见 §1）；ON2/ON2-EX 冻结产物 SHA 未变。

## 5. 边界与 attestation

- **未运行效果/训练/更新器/迁移/决策分析；未读响应值做统计**；只做既有产物读取、二进制 SHA256、metadata/空值掩码只读预计算（用于覆盖计数与 symbolic reconstruction 审计）。
- 未修改 ON1/ON2/ON2-EX 产物与 ON3 v0.1 文件；未改其它目录/INDEX/SYNTHESIS/git；未联网。
- 不声称新颖性/资源足够/关系成立/效果/独立确认/迁移/决策收益；技术重复≠独立培养；缺失机制未知；batch3 全失、702 个 15 行 pair-cell、无暴露时间/assay、单药参照未用为限制。

## 6. 剩余缺口 / 下一步

1. **同一挑战者（endpoint-auditor）复核 v0.2**（无需再跑数据/效果；如需可只读复算 design 预计算）。
2. Lead 批准 → 冻结 execution protocol（所有 schema/单测/输出模板须先行冻结）。
3. **执行前预算测试**：B6 1,000 置换 × 5 折 × B4（25 ALS）可能紧张；须在冻结前做预算测试；若超 45 min，**在冻结前**调整置换数（如 500）并披露，不得执行时缩减。
4. 执行前须补：B4/B5/B6 参考实现与 10 项单测、输出 schema 校验、两跑确定性、预算测试；`Δρ_min_rank` 与 bootstrap 的具体数值（null 分布）在冻结协议中定义、执行时计算。
5. 其他限制：masked 46.4% 单元（非 20% 单元）、masked-member 选择可能影响结果（冻结后不改）、transductive context 非纯冷启动、B4 小数据过拟合风险、context-ablation 若为 0 需如实写"未观察到 context 描述性增益"。
6. 阴性/阳性措辞模板已在 protocol §7 冻结；任何结果只写 O'Neil 内部开发性描述，不得写迁移/决策收益/机制/独立确认/新颖性。

## 7. 明确不做

- 未运行效果/训练/更新器比较/迁移/决策分析；未读响应值；未改冻结产物；未声称新颖性；不把 v0.2 DRAFT 当执行依据；执行须等挑战复核 + Lead 批准。

# report_m2_stage1 —— R204-M2 Stage 1 受控真值检查报告（机制账；不报增益）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者（endpoint-auditor）。
**状态：Stage 1 完成/受控真值检查通过；仅机制账、compute-only、0 wells；不报效果/增益/方法比较/决策收益；Stage2/3 未执行。**

依据：Lead `DECISION_R204_M2_STAGE1.md`（仅 Stage 1 合成实现）；冻结 v0.2 链 PROBLEM `25BC2663…`、DESIGN `5891858E…`、formalism `DE3C29A9…`、json `A99D31B1…`、schema `3CC31B62…`、timing `14E24027…`；冻结唯一 p=5、A=3、d=4、cohorts=200、T=3。

## 1. 结论

- **Stage 1 全部检查通过**：`failed_checks=[]`、`failure_category=null`；没有 `design_invalid`。
- **三例**：
  1. **线性闭合 positive**：p=5 testbed 闭合残差 **5.47e-16**、K 真值恢复误差 **3.83e-15**；冻结独立算术 p=2 闭合残差 **2.71e-15**；PASS。
  2. **非线性非闭合 negative**：冻结独立算术 **3.7576893**（φ=(1,x,x²)，x′含 x³/x⁴）；p=5 testbed 残差 **294.719**（也显著、含高阶项；与冻结算术是不同维数示例，分开报告）；PASS（negative）。
  3. **部分支持不可识别 negative**：仅 action 0/1 有支持，设计 **rank=50/75、nullity=25**；K_2 不可辨识；PASS（negative）。
- **可辨识**：full K **75/75**；mixed 20 组 **rank=75/nullity=0**（构造性、条件性，不推广）；same-U **3/3**；U 长度 **5**；pure groups **30（10/动作，每动作≥5）**；gauge `K_a→M K_a M^{-1}` norm diff **5.42e-16**；无支持动作不可辨识。
- **随机化合同**：主 testbed PASS（support 全动作、balance SMD≈1e-16、π 先于结果、计数保留、姐妹可交换设计、full action labels）；partial-support 的 support fail 属**预期 identifiability negative**，非 randomization failure。
- **正交设计**：同 U pure vs soft mixes 分离 `K_aU`，**不识别全部 K**；不声称混合优于纯药组；仅算术示例。
- **pilot/canonical timing**：最终代码 pilot **0.00253 s/rep**（10 reps）；stage1 projected **0.0607 s**；full Stage1 wall **0.0667 s**；caps **600 s/2 h/8 GB**；**0 wells**；**文档/JSON 使用同一 canonical snapshot**，未混用旧 .00228/.00247。
- **两跑**：两个独立进程的 `m2_stage1.json`、`m2_stage1_rows.csv`、`m2_stage1_diagnostics.json`、schema **逐字节一致**；timing 单独 telemetry，不进入结果 JSON。

## 2. 三例结果（Stage 1）

| 例 | 观测 | 判定 |
|---|---|---|
| 线性闭合 positive（p=5 testbed） | full K residual **5.47e-16**；K_fit error **3.83e-15**；frozen p=2 arithmetic closed residual **2.71e-15** | PASS（闭合可恢复） |
| 非线性非闭合 negative | frozen arithmetic φ=(1,x,x²) residual **3.7576893**（x³/x⁴ absent from φ）；p=5 testbed residual **294.719**（显著；独立算术示例与 p=5 testbed 分开） | PASS（闭合失败，符合 negative） |
| 部分支持不可识别 negative | 仅 action 0/1；rank **50/75**；nullity **25**；K_2 不可辨识 | PASS（identifiability negative） |

## 3. 可辨识/设计算术

| 检查 | 结果 |
|---|---|
| full K 参数 | A·p²=3×25=**75** |
| pure groups | **30**（10/动作，每动作≥5，U 张成 R⁵） |
| full K rank | **75/75**（nullity 0） |
| mixed 20 组 | rank **75**，nullity **0**（构造性、条件性，不推广） |
| same-U | rank **3/3**（K_aU 可辨识） |
| U 长度 | **5** |
| partial support | rank **50/75**，nullity25；K_2 不可辨识 |
| gauge | `K_a→M K_a M^{-1}`；norm diff **5.42e-16**；PASS |
| 无支持动作 | 不可辨识（expected negative） |

**mixed 75/0 的边界**：这是本设计下的构造性满秩示例；不声称任意 mixed assignment/有限观测都识别全部 K。

## 4. 非闭合/正交/随机化

- **非闭合**：冻结 p=2/p=3 独立算术示例残差 **2.71e-15 vs 3.7576893**；p=5 testbed 的 x′含 x² 递归，残差 **294.719**（显著）；二者均不是真实数据/药理。
- **正交设计**：同 U 的 pure `(1,0)/(0,1)` 分离 `K_aU`；soft mixes 只给线性组合；**不能识别所有 K**；**不保证/不声称 mixed 优于 pure**。
- **随机化合同（主 testbed PASS）**：
  - π 记录先于结果；π 在给定记录历史下与隐藏状态独立；
  - pure groups 采用**记录 X0 匹配的随机化**（各 action 共享同一 block X0 值；记录态估计式仍使用）；
  - support 全 action；balance max SMD **≈1.1e-16 <0.5**；
  - between-cohort assignment only；full action labels；counts retained；姐妹制备可交换设计；
  - partial-support support fail 归 **identifiability negative**，不是 randomization failure。
- **失败处置**：若合同失败→`design_invalid: randomization`；本轮主 testbed 未触发。

## 5. 执行/预算/两跑

- **0 new wells**；compute-only；caps **wall≤600 s / CPU≤2 h / memory≤8 GB**；实际 full wall **0.0667 s**，远低于 cap。
- **两跑独立进程**：result/rows/diagnostics/schema SHA 一致（见 §6）；timing 单独文件，不进入结果 JSON；timing 记录 canonical .00253、projected .0607、full .0667。
- **schema/failure template**先写/冻结：`schema_m2_stage1.json` SHA `3CC31B62…`；结果 JSON 只含检查，不含 telemetry。
- **no effect results**：未输出 regret/决策效用/方法比较/top-k/增益；未做 Stage2/3/真实数据/湿实验。

## 6. 产出 SHA（实算）

| 文件 | SHA256 |
|---|---|
| `m2_stage1.json`（两跑相同） | `3D7DA1026BD779963808BE4D3F23ACDADDB4E3DD612C404A3E915C33C9A0F2A2` |
| `m2_stage1_rows.csv`（两跑相同） | `AA7CBF281247BE015CEDDF1F534F5DA49B890500F1B0D5664D61D4372B6A4772` |
| `m2_stage1_diagnostics.json`（两跑相同） | `0EA73141A0C3DA1FEF862B42CD68EF6BB54A62C0D4FFCFFCBAA0A1FD119D3E40` |
| `schema_m2_stage1.json`（frozen） | `3CC31B62…` |
| `timing_m2_stage1.json`（canonical telemetry） | 见文件；result SHA `3D7DA102…` |
| `run_m2_stage1.py` | 见 usage |

## 7. Stage2 建议/边界

- **Stage1 受控真值条件已满足**（可辨识/非闭合/随机化/schema/两跑/pilot）。
- **但不具备 Stage2 执行条件**：合格多时间功能/数据字典/正交功能当前 **data_unavailable（C203）**；Stage2/3 未获批准，**不执行**；不能用合成/RNA/预测替代独立功能决策。
- **建议**：仅可准备 Stage2 **设计**（不运行），且需独立挑战 + Lead 批准 + 合格数据资源；Stage2 仍需等预算基线、headroom/MDE、两本账。
- 边界：机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定/门槛；不恢复已停止实验；不拼 ΔEMAX；技术重复≠独立培养。

> 本报告只报告 Stage1 受控真值检查，不报告任何效果/增益/方法优劣。

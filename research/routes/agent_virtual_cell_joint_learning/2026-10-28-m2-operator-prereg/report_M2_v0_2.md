# report_M2_v0_2 —— R204-M2.1 修正预注册报告（p=5 冻结；不运行效果）

2026-10-28。对象：R204-M2（D1/M2 首选主线）。依据：M2-C1 挑战（revise：p=5 vs p=4 冲突）、[challenge_M2.md](challenge_M2.md)、R204 BRIEF/report/evidence、R203-P1 链、ERRATA C197/C199/C201/C203。
**只做设计/算术/最终代码 pilot 计时：未运行效果比较/未声称增益；机制账 only；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；v0.1 产物保留不改；合成 compute-only、0 wells。**

## 0. 交付物（v0.2 新文件；v0.1 保留不改）

- 问题定义：[PROBLEM_M2_v0_2.md](PROBLEM_M2_v0_2.md)（`25BC2663…`）
- 执行设计：[DESIGN_M2_v0_2.md](DESIGN_M2_v0_2.md)（`5891858E…`）
- 形式化/可辨识：[formalism_M2_v0_2.py](formalism_M2_v0_2.py)（`DE3C29A9…`）→ [formalism_M2_v0_2.json](formalism_M2_v0_2.json)（`A99D31B1…`）
- Stage1 schema：[stage1_schema_v0_2.json](stage1_schema_v0_2.json)（`3CC31B62…`）
- pilot 计时：[timing_M2_pilot_v0_2.json](timing_M2_pilot_v0_2.json)（telemetry；末次 `14E24027…`）
- 记录/用量：[record_M2_v0_2.md](record_M2_v0_2.md)、[usage_M2_v0_2.json](usage_M2_v0_2.json)

## 1. M2-C1 必改落实

### ① 冻结唯一 p=5（全文一致）

- **选择 p=5 的理由**：v0.1 测试床已冻结 p=5（d=4/A=3/p=5/cohorts=200/T=3，写入 R204 BRIEF/report）；改为 p=4 需改测试床并重写 Stage 规格，收益仅简化算术、不改科学问题；因此**保留 p=5、重算全部算术**，而不是 testbed p=5 + 算术 p=4 并存。
- v0.2 中 **p=4 的 48/48、40/48、nullity8、U 长度4、pure groups 24 全部移除**；p=5 数字见下。

### ② p=5 可辨识算术重算（`formalism_M2_v0_2.py`，显式 Kronecker 设计）

| 项 | p=5 重算值 |
|---|---|
| φ 维 p | **5**（testbed/JSON/schema 一致） |
| A 动作 | 3 |
| full K 参数 dim | **A·p²=75** |
| full K 纯分配设计 | **rank 75/75**（30 pure 组、10/动作；每动作 ≥p=5 纯分配、U_i 张成 R^5） |
| mixed assignments | 20 组、U 变化 → **rank 75/nullity 0**（构造性满秩；条件依赖设计支撑，**不声称任意混合/有限观测都识别全部 K**） |
| same-U pure+mix | **rank 3/3** → `K_aU` 全部可辨识 |
| U 向量长度 | **5** |
| pure groups | **30**（每动作 10≥p=5） |
| 无支持动作 | positivity 违反 → K_a 不可辨识 |
| gauge | `K_a→M K_a M^{-1}`（φ 基变换；基/符号对称） |
| full K 可辨识 | **true（75/75）**；不再用 p=4 的 48/48 冒充 |

### ③ 记录态估计/禁止捷径（保持，p=5 重算 bias）

- `V_i=Σ_aK_aE[1{A=a}φ(X0)|i]`；**禁止**边际 π×均值捷径；p=5 设计算术 naive 偏差范数 **0.2643**（非零）。

### ④ 非闭合反例/正交设计/gauge（保持）

- 闭合正例（φ=(1,x)、线性动态）残差 **2.7e-15**；非闭合反例（φ=(1,x,x²)、x'=x+0.7+0.8x²+ε，含 x³/x⁴ 项）残差 **3.7577**（与 p 无关，保留）。
- 正交设计示例（同 U pure vs soft mixes 分离 K_aU；不识别所有 K；不保证混合优于纯药组）；随机化/可交换性合同不变。

### ⑤ Stage1 pilot（最终 v0.2 代码重跑）

- 10 replicate 设计/估计算术 **0.00228 s/rep**；投影 stage1 **0.1 s**、stage2 **0.3 s**、stage3 **1.1 s**；Stage1 caps **600 s/2 h/8 GB/0 wells**。

### ⑥ schema/两跑

- `stage1_schema_v0_2.json` 写死 p=5、A=3、full K rank=75、mixed rank=75/nullity=0、param dim=75、U 长度=5、pure groups=30、same-U rank=3/3、无支持动作不可辨识、闭合阈值、随机化合同、caps/失败类别/禁报增益。
- `formalism_M2_v0_2.json` 与 schema 两跑**逐字节一致**（JSON `A99D31B1…`、schema `3CC31B62…`）；JSON 无 telemetry；计时仅在 timing 文件。

## 2. 保持不变（M2-C1 PASS 部分逐条保留）

- 形式化：X/φ/闭合声明（待检验）/固定 π 群体矩/记录态正确式/禁止边际捷径/动作标签完整/π=cohort 间分配非细胞自由给药非联用。
- 任务驱动闭环：f_g 条件后继 → 选起始/给药/时点 → 真实新矩检验闭合 → K 乘积/已测功能重组；失败报不可复用作用/时程；函数选择/增补/误差控制仍为开放算法问题。
- 与 KoopCell/DisKO/受控 EDMD 边界：**固定 φ 线性闭合=受控弱 EDMD/系统辨识+最优输入设计等价强基线**；同预算复制/超过→撤主算法（no_increment/rename_edmd）；KoopCell/DisKO/TD-JEPA/BATCHIE 已覆盖部分不称新。
- 三阶段最小验证（受控真值→固定反馈比较学习→固定更新器比较取证→完整闭环；先留出程序再背景；新功能同标定；只换已观测权重=有限任务重组）。
- 主端点=独立功能决策效用/后悔、δ=.05 normalized；headroom/MDE 先检；**6,282 仅 Fisher-z、非通用门**；RNA/预测/算子误差仅 secondary。
- 等预算强基线清单、停止/撤主张规则、失败类别、数据需求（真实阶段当前 data_unavailable）、预算/边界。

## 3. 边界

机制账 only；合成 Stage1 compute-only、0 wells；不称生物学/机制/迁移/真实决策收益/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**Stage 1 执行须另立独立挑战 + Lead 批准**；不批准 Stage 2/3 执行/真实数据/效果/药理。

## 4. 产物/确定性/SHA

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2_v0_2.md` | `25BC2663BC970D21857796E68428D91EA2E867D13AA371DAE817B7C08A94A4BF` |
| `DESIGN_M2_v0_2.md` | `5891858E8647EA5C47549931B6D852C459795A12919798ED223F4C8F9C788255` |
| `formalism_M2_v0_2.py` | `DE3C29A957A73173097331940AEF685FDCE234635FFEC9A060847AAB00D7AD7C` |
| `formalism_M2_v0_2.json` | `A99D31B1731BAB99AABEB49717E011DE33E6B78CAA4EEE9ADBEE2A1A3F119F10` |
| `stage1_schema_v0_2.json` | `3CC31B6237B2562B159A03B7DBA5C2833CA4AD765FA2A75667FF2FE8F2268BB4` |
| `timing_M2_pilot_v0_2.json` | telemetry（末次 `14E24027…`） |
| report/record/usage | 见 `usage_M2_v0_2.json` |

**确定性**：`formalism_M2_v0_2.json` 与 `stage1_schema_v0_2.json` 两跑逐字节一致；JSON 键排序/无时间戳；pilot 计时只在 timing 文件。

## 5. 建议

1. **提交 v0.2 做独立复核/再挑战（不 stop）**（重点：唯一 p=5；full K **75/75**、mixed **75/nullity0**（条件性）、same-U **3/3**、U 长度5、pure groups30、无支持动作不可辨识、gauge；非闭合 2.7e-15/3.7577；schema 写死；pilot .00228 s/rep；两跑一致）。
2. 复核通过后请 Lead 批准 **Stage 1 合成实现**（仅机制账、compute-only、0 wells；不批 Stage 2/3/真实数据/效果/药理/真实决策/迁移/新颖性）；Stage 1 后 Stage 2/3 另立预注册+独立挑战+Lead 批准。
3. **不做**：效果比较/增益声称、代码晋升、旧判定修改、恢复停止实验。

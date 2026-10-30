# record_M2_v0_2.md —— R204-M2.1 修正预注册执行记录（p=5 冻结；不运行效果）

角色：独立设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-146（R204-M2.1）· 日期 2026-10-28
只写 `research/2026-10-28-m2-operator-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/R204/N1/A/B/D**；**未运行效果比较/未声称增益**；机制账 only；合成 compute-only、0 wells。

## 0. 要求与完成对照（M2-C1 5 必改）

| 必改 | 状态 |
|---|---|
| ① 冻结唯一 p 并统一全文 | ✅ **p=5 冻结**（保留理由写入 PROBLEM §0：v0.1 testbed 已 p=5、BRIEF/R204 已冻结 d=4/A=3/p=5/T=3；改 p=4 需重写 Stage 规格且不改科学问题）；**无 p=4 数字残留**（48/48、40/48、nullity8、U 长度4、pure groups 24 全部移除） |
| ② 重算 formalism/JSON+schema | ✅ `formalism_M2_v0_2.py` p=5：**full K 参数 75/75 可辨识**（30 pure 组、10/动作、U 张成 R^5）；**mixed rank 75/nullity 0**（20 组、U 变化；构造性，条件性不推广）；**same-U rank 3/3**；**U 长度 5**；无支持动作不可辨识；gauge `M K_a M^{-1}`；`stage1_schema_v0_2.json` 写死全部字段；两跑逐字节一致；JSON 无 telemetry |
| ③ 更新文档/SHA/最终 pilot | ✅ PROBLEM/DESIGN/report/record v0.2 全部更新数字/SHA；Stage1 pilot 用最终代码重跑：**0.00228 s/rep**、stage1 0.1 s/stage2 0.3 s/stage3 1.1 s；保留形式化/记录态/EDMD 边界/三阶段/端点/6,282/等预算/停止/数据/边界 |
| ④ 不得用 p=4 的 48/48 冒充 p=5 | ✅ v0.2 只用 **75/75**（full K）、**75/nullity0**（mixed，条件性）；v0.1 的 48/48 仅出现在“v0.1 问题”修正说明中，不进入 v0.2 冻结/批准依据 |
| ⑤ 边界 | ✅ 机制账 only；Stage1 仅受控真值/可辨识、不报增益；caps 600 s/2 h/8 GB/0 wells；不称生物学/机制/迁移/真实决策/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage1 执行另立预注册+挑战+Lead 批准 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~11:43 | 读 task-146 并 claim；读 M2-C1 challenge、v0.1 产物、R204/R203 链 |
| ~11:45 | 复制 v0.1→v0.2 脚本；首次补丁因 PowerShell 转义失败未生效（v0.2 脚本仍 p=4），改用 Python patch 文件 |
| ~11:46 | Python patch：p=5、Gp=24→30、G=20、v0.2 路径、schema 写入；运行得 **same-U 3/3、full K 75/75、mixed 75/nullity0、U 长度5、pure groups30、bias .2643、闭合 2.7e-15/非闭合 3.7577** |
| ~11:48 | 两跑 `formalism_M2_v0_2.json` 与 `stage1_schema_v0_2.json` 逐字节一致；pilot 0.00228 s/rep、stage1 0.1/stage2 0.3/stage3 1.1 s |
| ~11:52 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **只做设计/算术/计时**：v0.2 脚本做 p=5 显式 Kronecker 设计 rank、记录态估计偏差 MC、闭合/非闭合解析算术、随机化合同、testbed 规格、pilot 设计算术计时；**不运行方法比较/不计算功能决策端点/不声称增益**。
2. **p 冻结理由**：保留 p=5（testbed 已冻结于 BRIEF/report；改 p=4 会改变 Stage 规格而不改科学问题）；算术/JSON/schema/文档全部统一 p=5。
3. **mixed assignments rank 75/nullity0**：为构造性满秩（20 组、U 变化、显式 Kronecker 设计）；JSON/report 明确**条件性、不声称任意混合/有限观测识别全部 K**；保持 same-U 3/3、无支持动作不可辨识、gauge。
4. **非闭合反例与 p 无关**：闭合 2.7e-15、非闭合 3.7577 保留。
5. **v0.1 不改**：v0.1 文件保留；v0.2 为新增文件。
6. **确定性**：`formalism_M2_v0_2.json`、`stage1_schema_v0_2.json` 两跑逐字节一致；JSON 无 telemetry；pilot 计时只在 timing 文件。

## 3. 关键结果（与 report 一致）

- 唯一 p=**5**；A=3；full K 参数 **A·p²=75**、**rank 75/75**（30 pure 组）；mixed **rank 75/nullity 0**（条件性）；same-U **3/3**；U 长度 **5**；无支持动作不可辨识；gauge `M K_a M^{-1}`。
- 记录态估计 bias（naive 捷径）**0.2643** 非零；闭合正例 2.7e-15、非闭合 3.7577 保留。
- Stage1 pilot（最终代码）：**0.00228 s/rep**、stage1 0.1 s/stage2 0.3 s/stage3 1.1 s；caps 600 s/2 h/8 GB/0 wells。
- 其余形式化/EDMD 等价边界/三阶段/端点/δ/headroom/MDE/6,282/等预算/停止/数据/失败类别/边界不变。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2_v0_2.md` | `25BC2663BC970D21857796E68428D91EA2E867D13AA371DAE817B7C08A94A4BF` |
| `DESIGN_M2_v0_2.md` | `5891858E8647EA5C47549931B6D852C459795A12919798ED223F4C8F9C788255` |
| `formalism_M2_v0_2.py` | `DE3C29A957A73173097331940AEF685FDCE234635FFEC9A060847AAB00D7AD7C` |
| `formalism_M2_v0_2.json` | `A99D31B1731BAB99AABEB49717E011DE33E6B78CAA4EEE9ADBEE2A1A3F119F10` |
| `stage1_schema_v0_2.json` | `3CC31B6237B2562B159A03B7DBA5C2833CA4AD765FA2A75667FF2FE8F2268BB4` |
| `timing_M2_pilot_v0_2.json` | telemetry（末次 `14E24027…`） |
| report/record/usage | 见 `usage_M2_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `4AF84EE0…`、DESIGN `DAFDCBB3…`、formalism py `54B227E9…`、json `107DB450…` 等 |

## 5. 缺口与下一步

- **未运行效果比较/未声称增益**；所有数字为设计算术/合成计时。
- Stage1 执行须另立独立挑战 + Lead 批准（仅合成机制账、compute-only、0 wells）；Stage2/3/真实数据/药理/真实决策/迁移/新颖性不在本批准范围。
- 机制账 only；不晋升代码；不改旧判定；不恢复停止实验。

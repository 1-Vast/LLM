# record_r196.md —— R196 v1 执行记录（verdict 已撤回；数字保留）

角色：独立 runner（未参与 C130/R163 开发）· 任务 task-20 · 日期 2026-10-27
只写 `research/2026-10-27-c130-audit/` 与 `tmp/`；未改 C130/R163 产物、其它目录、INDEX/SYNTHESIS/git。

## 0. 状态与要求对照

| # | 要求（task-20/BRIEF） | 状态 |
|---|---|---|
| 1 | 先冻结 `PROTOCOL_R196.md` 再跑 | ✅ 协议于 17:50 冻结（`r196.py` 17:52 后才存在） |
| 2 | 数据/特征：Jaaks Original、ΔEMAX、38 维双侧通路、130 维身份 | ✅ 108,259 单元/125 细胞/65 药/2,025 有向对；与 C130 同构 |
| 3 | 药物分折 + 分组内层抠 λ + 行级对照 | ✅ 5 折、sorted-grouped 内层 3 折、scaler 折内；row-level 两变体 |
| 4 | arms/零模型：annotation/identity/annotation-only/capacity(10)/shuffle(10) | ✅ 全部执行 |
| 5 | 设计体检先于最终打分 | ✅ D1–D9 全通过后才打分（D5 计数 135=5×27） |
| 6 | CI 细胞聚类 + 药物/双向敏感性；MDE80 同口径 | ✅ 已算；**但药物聚类与 fold dispersion 是首跑后补的（见 §3 偏离）** |
| 7 | 判定 replicated/weakened/inconclusive | ⚠️ 原判 `replicated_under_audit`；**已被 REVOCATION 撤回**，登记为 `inconclusive` ∧ `weakened` |
| 8 | 单命令 ≤15 min、确定性、不改 C130 | ✅ 254–288 s；重复运行产物 SHA256 一致 |
| 9 | 😈 完成后 send_message 给 lead | ✅（v1 已发；v2 完成后再发） |

## 1. 时间线（Asia/Shanghai，2026-10-27）

| 时间 | 事件 |
|---|---|
| 17:41 | 读 task-20、R196 BRIEF、R163/C130 协议与结果、HANDOFF 方法审计、独立重审报告 |
| 17:45–17:49 | 只读勘察：输入结构（296,707 行→108,259 单元）、冻结折设计数字、机制原型（`tmp/r196_design.py`、`r196_proto.py`、`r196_proto2.py`，只跑 identity/打乱/容量 + annotation-only 机制检查） |
| **17:50** | **`PROTOCOL_R196.md` 冻结**（`r196.py` 尚不存在） |
| 17:52–17:58 | 写 `r196.py`；修 2 处实现 bug（折断言、训练标签索引掩码）后成功运行（285 s） |
| 17:58–18:02 | 首跑后增加 drug-cluster bootstrap 与 fold dispersion（**偏离，见 §3**）；复跑两次 |
| 18:02 | `r196.json`/`r196_rows.csv` 最终（确定性两次一致）；原 verdict = `replicated_under_audit` |
| 18:06–18:07 | 独立挑战（task-29, i003-challenger）判 **revise**；Lead 出 REVOCATION_R196.md 生效 |
| 18:12 | 按 Lead 要求重跑前最终哈希采集：`r196.json`=4732b7cf…、`r196.py`=2c77b7b5… |
| 18:14–18:20 | 交付本记录与 `report_r196.md`（撤回后口径）；随后写 AMENDMENT-001 并重跑 v2 |

## 2. 命令与耗时

```powershell
cd D:\MAESTRO\research\2026-10-27-c130-audit
& 'D:\anaconda\envs\maestro\python.exe' r196.py     # 254–288 s；重复两次产物哈希一致
```

- 单命令墙钟 254–288 s（≤15 min 预算）；离线；CPU。
- 记忆：全量设计矩阵 108,259×168 float64 ≈ 145 MB。

## 3. 实现 bug、偏离与披露

1. **Bug（已修，不影响规则）**：
   - 折断言误写 `len(drugs)-N_FOLDS`（应为 `len(drugs)-len(held)`=52）→ 首次运行中止；
   - `select_grouped` 用全局行索引去索引已切片的 `y_train` → IndexError；改为"训练标签 NaN 掩码视图"（非训练位置为 NaN，`gram_solve` 断言有限），同时使 D5"测试标签不进 λ 选择"可在结构上校验。
2. **首跑后补算（关键披露）**：首跑已给出 cell/pair/twoway CI 与 per-fold 数字；**drug-cluster bootstrap 与 fold dispersion 是在看到这些数字之后追加入 `r196.py` 的**（协议 §6 原本只冻结 cell/pair/twoway）。这属于"结果后补敏感性"，虽正是审计目标所需，但**已按挑战要求写进披露**，并在 v2 AMENDMENT 中预注册为主单位。
3. **预冻结 peek（协议 §2 已披露）**：机制原型跑过 annotation-only 臂（per-fold mean ρ≈0.149）与打乱/容量零模型；主臂 annotation、identity、row-level 未在原型中运行。因此本报告不声称"任何响应读取前冻结"，只说"主臂数字在冻结前未见过"。
4. **首跑后判定的内部不一致**：`reliability_qualifier` 已写出 "MAGNITUDE is not pinned at delta_min under held-out-DRUG resampling (MDE80_drug>0.05)"，但 verdict 仍为 replicated（因为冻结主 CI 是 cell 聚类）→ 挑战据此判 **revise**；本记录接受该判定。
5. **λ 网格**：按 HANDOFF 审计建议扩到 10000；结果 row-level 5 折全选 10000/3000 → 复现 C130 口径的措辞越界（挑战 ② 指出）；v2 将加 C130 ≤1000 网格桥接。
6. **内层指标**：grouped 用"3 内层折预测拼接 pooled Spearman"，row-level 用"折均 Spearman" → H196b 差值混口径（挑战 ③ 指出）；v2 统一为折均。

## 4. 结果与登记

- 数字见 [report_r196.md](report_r196.md) §2 与 [r196.json](r196.json)：主增益 +0.1447；cell CI [0.1213,0.1667]、pair [0.0898,0.1876]、twoway [0.0872,0.1958]、**drug [0.0139,0.2233]**；MDE80 cell 0.0320 / pair 0.0721 / twoway 0.0783 / **drug 0.1527**；5 折 per-fold [0.0820,0.2952,0.2682,0.0661,0.0118]，fold SD 0.1281，t-CI [−0.0144,0.3037]。
- **登记判定（REVOCATION）**：`inconclusive`（drug 单位 MDE80=0.1527 > δ_min=0.05）**且** `weakened`（折间 t-CI 含 0；单一 5 折划分）。**不是 replicated**；C130 状态不变（冻结但未被外部/审计级确认）；不得写"C130 被推翻"。

## 5. 审计自查

- 无测试标签泄漏（挑战 ① PASS）：y 只在每臂每折打分函数读一次；D5 计数 135 = 5 folds × 27 arms；外层药物并集分折、内层 held∩inner-train=∅ 断言、scaler 折内拟合。
- 输入 SHA 与 R163 一致；特征矩阵 SHA 记录在 `r196.json`。
- 确定性：两次运行 `r196.json` = 4732b7cf…、`r196_rows.csv` = 236047b5… 完全一致；无时间戳/无随机（固定种子）。
- 未改 C130/R163 产物（本目录外只读）。

## 6. 缺口/未做

- 单一 5 折划分、cell 聚类主推断单位、内层口径混用、δ_min/上界无 operational 理由 → 全部由 AMENDMENT-001 v2 修正。
- 未做外部复现、未换端点/注释系统、未做机制/决策收益声明。
- v2 结果在 task-32 独立挑战通过前不得解释。

## 7. 产物哈希（v1，保留不改）

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_R196.md` | `b7257ea952431211896e0b84b8ff19cefdce52f652b70dc0914af5239763e309` |
| `r196.py` | `2c77b7b522f558ffbecc99df96f0ac6184f92c08ca46fbde08b779bb62e6b788` |
| `r196.json` | `4732b7cf65b54a200f09dce2d559c0e6d4aacce2e28728a89ec44f36a77e99c3` |
| `r196_rows.csv` | `236047b58d919d236adbaf22f692077215badf4f287006272a128d6c84e57bcb` |
| `report_r196.md` / `record_r196.md` | 见 `usage_r196.json` |

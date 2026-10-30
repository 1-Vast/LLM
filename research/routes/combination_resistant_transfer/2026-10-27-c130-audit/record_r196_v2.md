# record_r196_v2.md —— R196 v2（AMENDMENT-001 + 002）执行记录

角色：独立 runner（未参与 C130/R163 开发）· 任务 task-20（v2 重跑）· 日期 2026-10-27
只写 `research/2026-10-27-c130-audit/` 与 `tmp/`；未改 C130/R163 产物、未改 v1 产物与 AMENDMENT-001、其它目录、INDEX/SYNTHESIS/git。

## 0. 要求与完成对照

| # | 要求 | 状态 |
|---|---|---|
| 1 | v1 报告/记录按**撤回口径**交付（不写 replicated） | ✅ `report_r196.md`/`record_r196.md`（verdict 登记为 `inconclusive` ∧ `weakened`） |
| 2 | 写 **PREGISTERED AMENDMENT-001**（5 条必改）再重跑 | ✅ `AMENDMENT_R196.md` 于 18:16 冻结（`r196_v2.py` 尚不存在） |
| 3 | 主推断单位=held-out 药物；≥10 独立划分；统一内层指标；δ_min operational 化；措辞模板 | ✅ 全部落地（见报告 §1） |
| 4 | 写 **AMENDMENT-002**（partition 级进判定、E9 后果、peek 更正、小项） | ✅ `AMENDMENT_R196_002.md` 于 18:34 冻结（v2 verdict 落盘前） |
| 5 | 中间状态落 `tmp/r196_v2_stage_*.json`（含 SHA） | ✅ 5 个 stage + manifest（post-hoc 切分，见 §3.4 偏离披露） |
| 6 | wall/CPU、E9 判定、partition 结果、verdict 汇报 | ✅ 待发送（wall 1,119.7 s；E9 fail；partition CI 下界>0；verdict `inconclusive`） |
| 7 | 不改设计/划分/门槛；不为赶时间跳步 | ✅ 10 划分、drug 主单位、5 折、两套 λ 网格、δ_min=0.05 均按冻结执行 |
| 8 | 结果解释前须过 task-32 | ✅ 报告只给机械 verdict，标注 pending challenge |

## 1. 时间线（Asia/Shanghai，2026-10-27）

| 时间 | 事件 |
|---|---|
| 18:14–18:20 | 按 Lead 要求交付 v1 撤回口径报告/记录（`report_r196.md`、`record_r196.md`） |
| **18:16** | **`AMENDMENT_R196.md`（AMENDMENT-001）冻结**（`r196_v2.py` 尚不存在） |
| 18:16–18:17 | 写 `r196_v2.py`（块 Gram 快速引擎，用于 10 划分×5 折×多臂的可计算性） |
| 18:17:58 | **v2 首次成功运行启动**（此前两次因 int8 码溢出失败：`np.bincount` 负值；把分类码统一 cast 到 int64 后通过） |
| ~18:24 | 打印 `[8/12]`；后续 bootstrap 阶段耗时较长（50 折×B=2000 的聚类 bootstrap × 多臂） |
| ~18:34 | **`AMENDMENT_R196_002.md` 冻结**（partition 合取 + E9 后果 + peek 更正；在 verdict 落盘前） |
| **18:36:40** | v2 run-1 完成：`DONE verdict=inconclusive point=0.1415 primary_ci=[0.062468,0.182579] primary_mde=0.0857`；`DONE wall=1119.7s`；写 `r196_v2.json`（SHA `bd0ada7b…`）、`r196_v2_rows.csv`（SHA `576fb155…`） |
| 18:37 | run-1 产物保留为 `tmp/r196_v2_run1.json` / `tmp/r196_v2_rows_run1.csv` |
| 18:38 | 启动同脚本**第二次完整运行**（确定性校验，后台） |
| 18:41 | 从 run-1 产物切分 5 个 stage 缓存 + manifest（SHA 见 §5） |
| 18:42– | 起草 `report_r196_v2.md`（数字固定）；等待确定性校验完成后回填并与最终哈希核对 |

## 2. 命令与运行事实

```powershell
cd D:\MAESTRO\research\2026-10-27-c130-audit
& 'D:\anaconda\envs\maestro\python.exe' r196_v2.py    # run-1: wall 1119.7 s
& 'D:\anaconda\envs\maestro\python.exe' r196_v2.py    # run-2: 确定性校验（同脚本同输入）
```

- **wall = 1,119.7 s（18.66 min）**（脚本 stdout `DONE wall=1119.7s`）；CPU：run-1 进程在 18:29:07 最后一次读到 **CPU 累计 4,184.94 s**（当时 wall 仅约 660 s——BLAS 多线程使 CPU 时间远高于 wall），进程退出后未能再读最终 CPU，故最终 CPU 记 `null`；E9 按冻结规则以 wall 为准。（第二次确定性运行 wall=1,078.6 s。）
- **E9 判定：不通过**（冻结预算 900 s，实际 1,119.7 s）→ 按 AMENDMENT-002 §B，v2 verdict 必须 `inconclusive`；**未**把超时改记为 deviation 放行。
- 主要耗时来源（如实记录）：10 划分 × 5 折 × 多臂的内层 λ 选择（每折 3 内层拟合 × 两套网格）+ 10 个 shuffle 全设计零模型 + 20 个 capacity 零模型 + 8 组聚类 bootstrap（drug/cell/pair/twoway/annonly/row-diff×2），均为冻结设计所必需的重复计算；BLAS 多线程使进程 CPU 时间显著高于 wall。

## 3. 实现、bug 与运行时偏离（全部披露；不改规则）

1. **快速引擎重写（工程性，非设计变更）**：身份/注释均为 one-hot，故 ridge 的 Gram/Z 可用"计数 + 块结构"在 O(n) 内精确构造，线性方程组仍用同一 `(ZᵀZ+λI+1e-9·diag)` 闭式解。为防实现错误，脚本内置 **E8 等价性自检**：与稠密矩阵实现对比 max|Δpred| = **7.02e-13**（主设计）/ **1.97e-13**（path-only）；自检通过才继续。该改写不改变任何统计量定义。
2. **bug（修复，无产物）**：分类码为 `pd.Categorical.codes`（int8），在 `codes*k + codes` 的 `np.bincount` 中溢出为负 → 两次启动失败；统一 `astype(np.int64)` 后成功。无中间产物写出。
3. **wall 超预算**：实际 1,119.7 s > 冻结 900 s → E9 不通过（AMENDMENT-002 §B 已事先写死该后果）。**没有**改设计、缩划分、减 bootstrap 次数或跳过 ≥10 划分来"赶上"预算；超时如实登记。
4. **分步缓存为 post-hoc**：Lead 要求把中间状态写入 `tmp/r196_v2_stage_*.json`；由于重计算均在单个进程的内层循环中、**无法热落盘**，在 run-1 完成后用 `tmp/r196_v2_stage_cache.py` 从 run-1 产物**确定性切分**出 5 个 stage JSON（含源文件 SHA 与各自 SHA）。这是**运行时/工程偏离**（非统计违背），在报告 §5/§6 披露；未改变任何规则或数字。
5. **identity 不拟合**：按 AMENDMENT-002 §C.3 只做 partition 0 的 5 折实拟合常数性检查（5/5 constant，断言通过），其余 45 折按构造性结论 ρ=0.0；理由与验证写入报告与 JSON（`treatment.identity`）。
6. **`rowlevel_c130_grid` 口径**：折内 scaler（统一口径），与 v1/C130 折前 scaler 不同 → 仅桥接诊断（AMENDMENT-002 §C.4）。
7. **peek 更正**：v2 是"已知 v1 全部结果后的审计重分析"，不是盲验/独立复现；已在 `AMENDMENT_R196_002.md` §C.1 与报告 §6 写死。

## 4. 结果（机械登记；解释待 task-32）

- **verdict = `inconclusive`**；子类型：`design_check_failed`（E7：MDE80_design=0.082267 > δ_min=0.05）、`primary_mde80_gt_delta_min`（主 MDE80_drug=0.085720 > 0.05）、`e9_wall_gt_900s`（AMENDMENT-002 §B）。
- 主增益点估计 **0.141464**；主 CI（drug-cluster）**[0.062468, 0.182579]**；cell [0.128835,0.153969]；pair [0.116415,0.163036]；twoway [0.111766,0.168516]；对应 MDE80 = 0.085720 / 0.018345 / 0.033827 / 0.040218。
- partition 级：mean 0.141464、SD 0.024658、95% t-CI（df=9）**[0.123826, 0.159102]**（下界>0；10 个 partition 全部为正），满足 AMENDMENT-002 §A 的合取条件；fold 级（50 折）SD 0.083518、t-CI [0.117723, 0.165204]、min −0.032480、max 0.301134（仅 formal sensitivity）。
- 零模型：shuffle mean −0.006231（sd 0.046087，含 0，E6 通过）；capacity mean +0.000874；**annotation − capacity_seed0（partition 0）= +0.139692**。
- H196b（同内层指标+同网格）：rowlevel_ext − grouped_ext = **−0.000199**，配对 drug CI [−0.001013, 0.000340]；C130 网格桥接差 +0.000061；`material_optimism_flag=false`。λ 触上限次数：annotation 26/50、grouped_c130 29/50、rowlevel_ext 31/50、rowlevel_c130 43/50。
- E5 测试标签计数 800/800；E8 自检通过；E1–E4、E6 通过；E7、E9 不通过。
- v1 产物未改动（`PROTOCOL_R196.md`/`r196.py`/`r196.json`/`r196_rows.csv` 哈希保持 `b7257ea9…`/`2c77b7b5…`/`4732b7cf…`/`236047b5…`）；AMENDMENT-001 未改动。

## 5. 分步缓存（tmp/，post-hoc；SHA256）

| 文件 | SHA256 |
|---|---|
| `tmp/r196_v2_run1.json`（run-1 保留） | `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4` |
| `tmp/r196_v2_rows_run1.csv` | `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84` |
| `tmp/r196_v2_stage_1_design_and_data.json` | `b4c5e56b22124b5123e93abaa48140ffb8b6c6a994a6a64b1fc4433359b9053e` |
| `tmp/r196_v2_stage_2_null_models.json` | `6749dc20399d2353fb3e39112bf0f3c6b259102e054f062251249289745dcfaa` |
| `tmp/r196_v2_stage_3_treatment_arms.json` | `cb6f58366ddbcd33798b63113f51edb07aae5e5b0cee1465107f4a99c46f24a5` |
| `tmp/r196_v2_stage_4_bootstrap_and_judgment.json` | `7ea6f4084311b98a626351974571991c596253cfab83d7943588d00a1e1f273b` |
| `tmp/r196_v2_stage_5_runtime_and_E9.json` | `a386ca10620757adc7bf9f28d9aefc0b7b236e61169cd18019ebc2e6e25a7e0a` |
| `tmp/r196_v2_stage_manifest.json` | `53c2f2b9c0456c3a12c010a4242f14270c44021e96db2883665d9ad171646f16` |

## 6. 确定性

同脚本、同输入、同冻结协议的第二次完整运行完成：wall = 1,078.6 s（run-1 = 1,119.7 s；两次均 > 900 s，E9 均不通过）。`r196_v2.json`（SHA256 `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4`）与 `r196_v2_rows.csv`（SHA256 `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84`）在两次运行中**逐字节一致** → 确定性通过（固定种子、无时间戳、JSON 键排序）。

## 7. 缺口/未做

- 未做 nested bootstrap（未预注册；AMENDMENT-002 §A 用两阶段口径：partition CI + 固定划分内的 drug bootstrap；限制已披露）。
- capacity 只在 partition 0 上跑（10 seeds；冻结于 AMENDMENT-001 §2"容量对照仅 partition 0"），未做全 10 划分（成本；不参与判定）。
- 未做外部复现/换端点/换注释系统/机制/决策收益；未晋升代码；未改 `src/`。
- v2 结果在 task-32 挑战通过前不得解释/采纳。

## 8. 产物哈希（最终）

| 文件 | SHA256 |
|---|---|
| `AMENDMENT_R196.md`（001，冻结） | `6986b008ca799c3456076a630e92a04912bd3ea389ede3f83734a5607e855289` |
| `AMENDMENT_R196_002.md`（002，冻结） | `fe1836bd8aa02e5399e03eb022df3e89b18d2edf2ce7d7d019650693b0c68432` |
| `r196_v2.py` | `3e4bae43cec54cb06da95774c4c78a762885f757b415c734078c2ac9743c4e17` |
| `r196_v2.json` | `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4` |
| `r196_v2_rows.csv` | `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84` |
| `report_r196_v2.md` / `record_r196_v2.md` | 见 `usage_r196_v2.json` |

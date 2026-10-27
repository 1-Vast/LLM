# R197 v2 审计记录（record_r197_v2）

角色：独立 runner（未参与 A1/A2/Q2 设计；本任务不设计也不解释效果实验）。
工作目录 `D:\MAESTRO`；**只写** `research/2026-10-27-q-structure/`（v2 新增文件）与 `tmp/`；未改 v1 `PROTOCOL_R197.md`/`r197.py`/`challenge_R197.md`/`REVOCATION_R197.md`、其它研究目录、INDEX、SYNTHESIS、git。

## 1. 范围与依据

- 对象：**R197 v2（方案 Q）**——A0 推断重校准（节点级依赖感知 + 键级敏感性）＋ **Q 低秩结构留出预测主实验（H197c 随机条目，B2 主模型）**。
- 依据（运行前冻结）：`AMENDMENT_R197.md`（v2 预注册，方案 Q；运行前冻结）；`AMENDMENT_R197.md` 的运行前更正附录（SHA/键数）；`AMENDMENT_R197-003.md`（**最终 verdict 落盘前**的结果前补写：type-I CP95 上界≤0.10 + 分档扩充 20→30→40→60、Δ_primary 配对 bootstrap、OOF 拼接尺度副指标、**wall>20 min ⇒ verdict 必须 inconclusive**）。
- v1 状态：Lead `REVOCATION_R197.md` 作废（2026-10-27）。**v1 从未产出 `r197.json`/verdict**；唯一一次 v1 `--quick` 调试进程在写 JSON 时因 ndarray 序列化失败（留下无效残片），已删除/覆盖，无 v1 结果可解释。
- 响应值使用边界：`SYNERGY_DELTA_EMAX` 只用于 Q 矩阵与 A0/B 预注册统计；未用 test 调参、未按 Q 大小挑层、未换端点/分层/δ、未启动反馈/Agent/acquisition、未联网、未下载新数据。

## 2. 时间线（本机，Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 17:49 | 接手 R197 任务；读 BRIEF/ERRATA_Q2/ERRATA_A3/PROTOCOL_Q2/q2.py/q2.json/独立重审；重建 Q 结构探针（`tmp/_r197_recon.py`；后因 v1 作废未用于正式结果） |
| 17:57 | 写 v1 `PROTOCOL_R197.md`（含 AMENDMENT-001）；18:02 写 v1 `r197.py`；一次 `--quick` 调试启动后因 Lead 作废通知终止（写盘前；无 r197.json） |
| 18:10 | 独立挑战 `challenge_R197.md`（task-30，revise）+ Lead `REVOCATION_R197.md`（v1 作废）到达 |
| 18:16 | 写 **`AMENDMENT_R197.md`（方案 Q，v2 预注册）** + 运行前事实更正附录（q2.json/PROTOCOL SHA、V5 使用键 4,686） |
| 18:18 | 写 `r197_v2.py`（v1 helper 只读 import + v2 设计/模型/判定） |
| 18:19–18:26 | v2 `--quick` 调试（4 次迭代修复：序列化、字段、代理 SVD 等）；最后仍因 **ndarray row_summaries 写入 JSON** 失败；**无有效 v2 结果**；留下的 `r197_v2.json`（20 KB）为无效残片 |
| 18:24 | `challenge_R197_v2.md`（结果前预审）到达：要求补 AMENDMENT-003（type-I CP 规则、Δ 配对、OOF 尺度） |
| 18:27 | 写 **`AMENDMENT_R197-003.md`**（结果前；type-I CP95≤0.10 + 分档、配对 bootstrap、wall 预算门、OOF 尺度副指标） |
| 18:28:30–18:40:06 | **正式全量 run1**（wall **669.5 s**），产出 v2 第一份有效结果（`inconclusive`：B-D3 可辨识性 + B-D5 MDE 两门失败）；快照 `tmp/_r197_v2_run1*.json` |
| 18:41 | 修正 v1 self-test 的取整-容差 `pass=False`（工程修正，仅布尔，不改统计量；见 §5 偏离） |
| 18:41:13–~18:53 | **正式全量 run2**（同代码；确定性运行 1/2） |
| 18:52:29–19:02:53 | 写 `AMENDMENT_R197-004.md`（telemetry/确定性解耦）+ strip 工程补丁；**正式全量 run3**（post-AMENDMENT-004；确定性运行 1/2；wall **564.5 s**） |
| 19:02:59–~19:12 | **正式全量 run4**（确定性运行 2/2；`r197_v2.json`/`r197_v2_rows.csv` 与 run3 **逐字节一致**；wall 见 `usage_r197_v2.json`） |
| 19:0x | 写 `report_r197_v2.md`、本 record、核对 SHA/双跑一致 |

## 3. 命令、预算与实际墙钟

| 命令 | 实测 |
|---|---|
| `D:\anaconda\envs\maestro\python.exe -X utf8 research\2026-10-27-q-structure\r197_v2.py`（`PYTHONHASHSEED=0`） | **wall 669.5 s / 669.x s**（两次全量）；CPU≈**2,801 s**（多线程 BLAS，非墙钟） |
| 同一命令 run3（确定性验证） | wall ≈ 同量级（见 usage_r197_v2.json 最终值） |
| `python -m py_compile` | <1 s |
| `tmp/_r197_recon.py`（Q 重建结构探针，v1 阶段） | ~7 s |

- **预算门**：AMENDMENT_R197-002 §6 单命令 ≤20 min（1,200 s）；AMENDMENT-003 §4：**wall>1,200 s ⇒ verdict 必须 `inconclusive`**。实测 **669.5 s < 1,200 s → 预算门 PASS**（未触发 inconclusive-runtime；`budget_exceeded=false`，`budget_seconds=1200` 写入 JSON/usage）。
- 分步缓存（工程性，不参与选择）：`tmp/r197_v2_stage_A0.json`（A0+δ_min 冻结后）、`tmp/r197_v2_stage_B.json`（B 主+次设计完成、最终汇总前）；路径写入 `r197_v2.json → budget.stage_cache_paths`、`usage_r197_v2.json`。
- 降级顺序（预注册）：若预计超时，先减次设计 CI B（主设计 CI 不变）→ 再压 type-I 分档 → 仍超则 `inconclusive: runtime budget`；本轮未触发降级。耗时主因是 type-I 30 次模拟（每 sim 5 折 × B0+代理+SVD+ALS+CI200），见 §4。

## 4. 观测（关键事实）

1. **A0 修正式代数正确且与 q2 点估计一致**：σ²_cond=0.00037068、cellpair=0.00102312、total=0.02594441、resid=0.02455061（容差 1e-6）；噪声复现 σ²_single=0.003351/0.011968；ERRATA 例 −8/9 vs −37/18、dyadic n=30=10.33 均复现。
2. **依赖感知推断显著变宽**：V4（cell+condition 节点）SE=4.21e-4（V1 legacy 修正代数 SE=9.1e-5 的 ~4.6×），CI [0.000180,0.001752]（下界>0）；V5 键级敏感性 CI [0.000708,0.002204]（非 like-for-like，仅敏感性）。barcode 级依赖未覆盖（噪声标定仅 1.43% 观测）。
3. **q2 可靠性 0.868 未认证**：依赖感知解析式=0.282 [0.160,0.650]；**经验 cell 半分 Spearman–Brown median=−0.705**（raw r −0.261；20 splits，覆盖 225–229/229 条件对，Jaccard 中位 0.996）。→ A0 status=`q2_inference_not_robust_under_dependence`（R_split<0.50）。条件级均值跨细胞子集不可复现/反相关；旧 `condition_structure_present` 解释与 0.868 引用作废（1.43% 只保留"加性条件主效应份额"含义）。
4. **H197c 主结果点估计很大但设计门失败**：B2 OOF Spearman=**0.7206**（R²=0.603），B0=0.2073 → **Δ_primary=+0.5133**，配对 CI [+0.4458,+0.5756]，置换 p=0.001；但 **B-D5 MDE80=0.0942 > δ_min=0.0734**，**B-D3 可辨识性检查 FAIL**（列训练 min=3<20、5.1% 列<20、8.6% 列测试<5；行全部通过）→ 按冻结规则 **`inconclusive`**，不得判 present。
5. **type-I 按 AMENDMENT-003 认证**：20 次 0 失败 CP95=0.139>0.10 → 预注册扩充到 30 次仍 0 失败 → **CP95=0.0950≤0.10 ✓**。
6. **特征块消融（H197c）**：BM −0.122（纯元数据劣于加性）、BMono +0.214、B3 +0.019（交互块）；主模型 B2 不含特征 → 特征-端点构造重叠不影响主对比，但含单药块的增量不得称结构。
7. **次设计（描述性）**：H197a Δ(B3−B0)=+0.280 [+0.193,0.361]，Δ(B3−BMono)=−0.0126 [−0.035,0.009]；H197b Δ(B3−B0)=+0.107 [+0.073,0.141]，Δ(B3−BMono)=+0.005 [−0.002,0.013] → 特征增量主要由单药块解释（构造重叠披露），且 B0 冷 cell-pair 基线弱（Spearman=−0.026）；**B2 在次设计不可辨识、未拟合**（只报告代数退化）。
8. rank 选择 5 折全部 r=5（预注册网格上限）；内层 MSE 单调下降 → 网格上限约束是限制（不事后扩网格）。
9. v1 self-test `pass=False` 为取整-容差实现瑕疵（1e-9 容差比较 8 位小数）；v2 用 1e-6 容差复算同一存储值（数值未变），v2 JSON 中保留 `pass_v1_raw=False` 与说明。
10. **第一次正式 run1 的 `r197_v2.json` 在 self-test 修正前**；修正后 run2/run3 为最终产物（唯一差异是 self-test 布尔与说明；所有统计量不变——已用 run1 快照逐 key 对比确认非 self-test 字段无变化，见 §6）。

## 5. 决定（预注册 + 实现选择）

1. **方案 Q**：主设计 H197c（随机条目，B2 可辨识）为主；H197a/H197b 降为次设计描述性；主 verdict 只用 H197c。
2. **判定不因点估计大而改**：两条设计体检（B-D3 可辨识性口径、B-D5 MDE）按预注册 FAIL ⇒ **`inconclusive`**；未事后改门槛/检查/判定，也未把超时或强点估计写成放行理由。
3. **type-I**：按 AMENDMENT-003 = CP95 上界≤0.10 + 预注册分档（20→30→40→60，固定 seeds）；本轮在 n=30 认证（0/30）。
4. **Δ_primary 配对 bootstrap**：同一节点 multiplicity 同时用于 B2 与 B0、同一测试条目/同一 OOF 折（实现 `cluster_bootstrap_delta` 内 `idx` 同时用于两模型；JSON `paired_cluster_bootstrap=true`）。
5. **δ_min**：`0.10·sqrt(1−share_noise_clipped)=0.0734`，A0 后冻结、运行期断言先 A0 后 B；不用 q2 0.868/旧 CI；`δ_min_alt` 因 R_split 为负不可计算→null。
6. **B2 秩选择**：训练内 80/20 + 单步截断 SVD 代理（内层 MSE）选 rank，随后 ALS 重拟合（预注册实现选择；选择只用训练）。
7. **次设计不拟合 B2**：整列/整行留出 ⇒ 因子不可辨识、预测退化为 B0；只报告代数证明（AMENDMENT-001/挑战已确认，本轮不冒充低秩）。
8. **工程修正（pre-rerun）**：self-test 容差修正；预注册文本 SHA/键数运行前更正；分步缓存。均记录、不改统计/设计/门槛。
9. **措辞**：报告与本 record 逐字遵守 AMENDMENT-002 §4.8 允许/禁止句式；`inconclusive` 不读成阴性/阳性结论；不写可迁移/反馈有用/机制/新算法；阴性不关闭低秩/其他表示/其他留出研究。

## 6. 确定性与验证

- 固定 `PYTHONHASHSEED=0`；种子全表见 `r197_v2.json → seeds`（含 AMENDMENT-003 分档 seeds 20261110/20261310/20261410/20261510、键级 20261112、折 20261106 等）；JSON 键排序、无时间戳、`allow_nan=False`。
- **run3 vs run4**（同代码、同 `PYTHONHASHSEED=0`、post-AMENDMENT-004 strip）：`r197_v2.json` 与 `r197_v2_rows.csv` **逐字节一致**（SHA256 见 §7.1）；两次 wall 均 <1,200 s，`budget_exceeded=false`。
- **run1（self-test 修正前）vs run2（self-test 修正后）**：除 `A0.self_tests.weighted_moment_example.pass/pass_v1_raw/pass_tolerance_note`、各段 `seconds`、脚本 bytes/sha 与 wall/CPU 外，**全部数值/判定/体检/CIs 一致**（用 `tmp/_r197_v2_run1.json` 逐 key 对比验证）；确认 self-test 容差修正不影响任何统计量。run1/run2 早于 AMENDMENT-004 strip，不作为确定性验收对象。
- 输入 SHA256 全部断言并写入 JSON：Original fitted `1188968C…`、matched_conditions `73FD5085…`、q2.json `94C5CD9B…`、PROTOCOL_R197 `36EF1873…`、AMENDMENT-002/003、challenge_v1/v2、REVOCATION、v1/v2 脚本。
- 无 v1 产物可混用：v1 `r197.json` 从未存在；调试残片被 run1 覆盖（最终为 run3 产物）。

## 7. 产物清单（最终）

| 文件 | 说明 |
|---|---|
| `AMENDMENT_R197.md` | v2 预注册（方案 Q；含运行前更正附录） |
| `AMENDMENT_R197-003.md` | 结果前补写（type-I CP 规则、配对 bootstrap、OOF 尺度、wall 预算门） |
| `r197_v2.py` | 确定性 v2 runner（导入 v1 冻结 helper 只读） |
| `r197_v2.json` | A0 全表（V1–V5/置换/可靠性/δ_min）、H197c 主结果+体检+type-I、H197a/b 次设计、判定、预算、SHA |
| `r197_v2_rows.csv` | 每 condition-pair 行：A0 均值/sd/rel_old/rel_dep + H197c 主模型 OOF 预测/残差均值 |
| `report_r197_v2.md` | v2 报告（判定先行 + 全部数字/局限/措辞/复现） |
| `report/record` 之外未写其它目录 | 只写本目录与 `tmp/` |
| `usage_r197_v2.json` | wall/CPU/预算/缓存路径/环境；未知=null |

`tmp/` 内相关：`_r197_recon.py`（结构探针）、`r197_v2_run1.log`、`r197_v2_run2.log`、`r197_v2_run3.log`、`r197_v2_stage_A0.json`、`r197_v2_stage_B.json`、`_r197_v2_run1*.json`（run1 快照）。

## 7.1 最终产物 SHA256（run3=run4 确定性验收，2026-10-27 19:1x）

| 文件 | SHA256 |
|---|---|
| `r197_v2.json` | `B0DBE7982677FE9269B47EA39C83659166D4E4A5BFF04E8F590FC04BA64435CB` |
| `r197_v2_rows.csv` | `D19B51B8DEC52467DB00D5C1DD78175BD6D66A966E430CCF2E0124B0EC9FB7FD` |
| `r197_v2.py` | `B0C997B0D7C2F691EE133CAC94F4CE24F6CD9DD0207D968B44C3F71F46D57E5C` |
| `AMENDMENT_R197.md` | `E1CB303B8CE4DF701D20BB3A32387381338B3E18E2DB759EF1556EDA63019056` |
| `AMENDMENT_R197-003.md` | `973A95BB895FE1E1CEE9554A944893F72465FE97F95070C687D5860204A6BABF` |
| `AMENDMENT_R197-004.md` | `73AC438B559B1574F0779CABB10F47923019F2ECF2272E5D31CCF2254B116993` |
| `report_r197_v2.md` | `A99B0E3C763BC81DAA31EE6AF7D4BBFBE2BA0AB9C299598EB9FDB7389056D567` |
| `record_r197_v2.md` | 本文件（SHA 由审计方重算；写入后不再变更） |
| `usage_r197_v2.json` | `E0D43803567D042FEC70D6406851404922BD277B9431113D76F104670617E11A`（telemetry：wall=525.4 s、CPU=1800.9 s；不参与逐字节比较） |

- run3/run4 实测 wall：564.5 s / 见 usage（两次均 <1,200 s，预算门未触发）。`n_type_i_main=20` 是 type-I 初始档常量；**认证档位 n=30（0/30，CP95=0.0950）** 见 `r197_v2.json → B_v2.designs.H197c.type_i.final`（`initial` 档保留 20）。

## 8. 未做 / 明确不做

- 未解释/采纳 v2 结果（等待 task-34 挑战）；未把 `inconclusive` 写成阴性或阳性；未写可迁移/反馈有用/机制/新算法/共同学习。
- 未改 v1 协议/脚本/challenge/REVOCATION、未改 A1/A2/A3/Q2 产物、未改 INDEX/SYNTHESIS/git、未联网、未下载数据、未启动反馈/Agent/acquisition/RSI。

# R200-D5-EXEC 记录（record_d5_exec）

2026-10-28 ｜ 执行：cellstate-lit（task-101） ｜ 工作目录：`D:\MAESTRO`。
对象：按 `DECISION_D5_DESCRIPTIVE_EXEC.md` 对 D5 v0.4 做**一次纯描述性执行（descriptive_only，非 confirmatory）**。
只写 `research/2026-10-27-direction-mechanism-expansion/d5_temporal/execution/` 与 `tmp/`；**v0.1–v0.4 协议文件未改**。

## 0. 授权与范围

- Lead 批准：仅 descriptive_only；冻结 v0.4（protocol `8a317664…`、JSON `3d6fbf82…`、code `d4d627a1…`、report `67e02b0a…`、record `d6c3fcd9…`、tuning-grid `4d3b6d02…`）；v0.1–v0.3 冻结。
- 允许读 h5ad 表达（仅本次执行）；**未读任何晚期功能/响应值**；无湿实验；无网络。
- 不做 confirmatory H-D5-1、G3/G4 通过失败、`evaluation_cannot_distinguish` 推断；不写 biology/功能/迁移/决策/机制/新颖性/真实轨迹；BRD3379 永不进 primary。

## 1. 读取/输入

| 输入 | 用途 |
|---|---|
| `DECISION_D5_DESCRIPTIVE_EXEC.md`（SHA 记录于 d5_exec.json） | 授权与冻结对象 |
| `PROTOCOL_D5_v0_4.md`、`d5_v0_4.json`、`d5_revision_v0_4.py` | 冻结协议/预算/门/描述性 schema |
| `d5_v0_2.json`（`folds_v0_2`、`v2_corrected.paired_line_sets`） | V1 折清单、V2 配对线集 |
| `data/external/mixseq_scperturb/mcfarland_2020.h5ad`（SHA `94a72400…`） | obs/var 元数据 + **表达 `X`**（pseudobulk；本次执行允许） |
| `data/external/depmap_19q4/CCLE_expression.csv`（300 MB） | 静态特征（train-fold PCA） |
| 已装库版本 | sklearn 1.9.0 / numpy 2.4.6 / pandas 2.3.3 / scipy 1.17.1（执行时记录于报告） |

**未读**：任何 viability/apoptosis/regrowth/IC50/response 矩阵；其它研究目录 effect 结果；网络。

## 2. 执行顺序（按 Lead 要求）

```text
1) EX-G0a/G0b（metadata-only）→ 未失败
2) synthetic timing test（不读表达/响应）→ pass（投影 24.74 min < 120 cap）
3) 描述性执行：
   - build groups 428（V1 active+control 6/24；V2 hashed Tram/DMSO 5 时点）+ half groups 140
   - pseudobulk 列循环（CSC h5ad，128 基因/批；group sums → means）
   - CCLE 静态特征（18,099 genes；209 线匹配；train-fold PCA20）
   - V1：5 折 leave-cell-line-out；train-only top-200 panel；6h logFC → 24h logFC mean
   - V2：paired 15/16/15；target24/48；固定 alpha ridge + B8 8×5 调参
   - 零模型：V1 N1/N2/N6 各 1,000；N5 sentinel；V2 capacity/time-shuffle 各 1,000
   - 两跑（同 seed/单线程 BLAS）→ v1+v2 JSON 相同
4) 输出 d5_exec.json / timing_test.json
```

命令（最终执行）：
```powershell
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
D:\anaconda\envs\maestro\python.exe research\2026-10-27-direction-mechanism-expansion\d5_temporal\execution\run_d5_exec.py
```

## 3. 运行轮次与排错（全部在 execution/ 内；v0.4 未改）

| 轮次 | 问题 | 修复 |
|---|---|---|
| 1 | `ROOT` 少一级导致 h5ad FileNotFound | `ROOT = BASE/../../..`（execution→d5_temporal→direction→research→MAESTRO 的三级） |
| 2 | `hash_assignment` categorical `.map` 返回 tuple 报错 | `.astype(str).map(parse_hash)` |
| 3 | h5ad obs index 为 barcode，`groups[idx]` IndexError | `obs.reset_index(drop=True)`，位置索引 |
| 4 | CCLE `dtype=float32` 把 ACH index 当 float | 先 `read_csv` 后 `astype(np.float32)` |
| 5 | V2 使用 v0.2 旧键 `v2_hashed_arm` KeyError | 改 `v2_corrected.paired_line_sets` |
| 6 | V2 `_time` 被 pandas 转 float，key 不匹配，V2 全 0 | `str(int(row["_time"]))` |
| 7 | 两跑 `v1/v2` 结果被后置 null 合并 mutate，`two_runs=false` | 先算两跑 SHA，再合并 null 到输出 |
| 8 | BLAS 多线程导致 V2 微小差异 | 首部设 `OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS=1`；最终两跑一致 |

最终连续执行：`run_d5_exec.py` → `exit=0`；**两跑 `equal=true`**。

## 4. 验证与结果

```text
EX-G0a: pass（22/24/24）
EX-G0b: pass_metadata_level_with_limitation（dose/ChEMBL/vehicle/source/assay 记录；无独立实测）
timing_test: pass（投影 24.74 min；cap 120）
actual wall: 135.83 s（prep 4.31 + CCLE 2.97 + two-run analysis 125.37）
two runs: equal=true, sha_run1=sha_run2=295f5206ae76f2e20838625f9135b5642de5e8530112a9438c2b6f394e18a21e
d5_exec.json SHA256 13c4d3aebc0114e3b12c2434ad7a8be007f80bc753cdb6ea02ad38218d142588 (27,200 B)
timing_test.json SHA256 6cb48586592fe96f38ae977e276ba3ecdabd099fa790fac02e81600d4f1800bf (512 B)
run_d5_exec.py SHA256 2a4ba0aef63002123faed7b33a60dfc80abe084f2b5a18ab341e6459800e21b9 (48,259 B)
```

**描述性数据摘要（完整见 `d5_exec.json` / `report_d5_exec.md`）**
- V1：Δρ Bortezomib 0.1954、Idasanutlin 0.1757、Trametinib 0.1209；均值 0.1640；CI 均跨 0；MDE80 0.686/0.667/0.706；room 1.2355/0.9617/1.0791；reliability 0.920/0.944/0.979。
- V2：paired Δρ 0.0679（24h E1/E2）、0.0235（48h E1/E2）、0.0714（48h E2/E3）；CI 均跨 0；exploratory。
- V1 零模型：N1 p95 0.1743 / fraction 0.064；N2 0.2337/0.654；N6 0.2342/0.142；N5 oracle ρ 0.9895（管道 sentinel 正常）。
- 两跑结果一致；未触发 protocol_deviation；cap 未放宽。

## 5. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `run_d5_exec.py` | 48,259 | `2a4ba0aef63002123faed7b33a60dfc80abe084f2b5a18ab341e6459800e21b9` |
| `d5_exec.json` | 27,200 | `13c4d3aebc0114e3b12c2434ad7a8be007f80bc753cdb6ea02ad38218d142588` |
| `timing_test.json` | 512 | `6cb48586592fe96f38ae977e276ba3ecdabd099fa790fac02e81600d4f1800bf` |
| `report_d5_exec.md` | 8,462 | `f44d3e4d1c3273130a3522c4daf06019a79bebfed8f4a406a4f34356ebd7f08a` |
| `record_d5_exec.md`（本文件） | — | 见 `usage_d5_exec.json` |
| `usage_d5_exec.json` | — | 见文件 |

**v0.1–v0.4 未改**；本次只新增 execution/ 文件与 `tmp/` 缓存（`d5_exec_base.npy`、`d5_exec_half.npy`，非交付）。

## 6. 偏差 / 限制（与报告一致）

1. **非 confirmatory**：无 H-D5-1 检验、G3/G4 判定、`evaluation_cannot_distinguish` 推断。
2. **V2 exploratory 简化**：E1/E2/E3 固定 alpha ridge（无网格）；B8 8×5 调参 600 fits；n<20 不能升级。
3. **V1 B3/B7 重复**：均为 single-early ridge；各计 600 fits；不作两个独立证据。
4. **EX-G0b metadata-level**：无独立 compound/dose/vehicle 实测。
5. **静态特征**仅 CCLE 匹配线（209）；B1 缺失线被排除，ρ 在共同线计算（n_used≤n_eligible）。
6. 无同细胞配对/批次/暴露/独立培养/重复；`time_axis_unverified`；功能 `not_qualified`；RNA 代理≠功能；BRD3379 secondary only。
7. MDE/room/CI 仅 precision descriptor；**不得**写成时间预测成立/不存在、biology/功能/迁移/决策/机制/新颖性/真实轨迹。

## 7. 下一执行者注意

- 本结果只可作描述性/开发层记录；**不进入候选/L2/决策**；不得引用为 confirmatory 或 biology 证据。
- 若需 confirmatory：需新测量（每药约 1,571 独立细胞系或认证 r_err≥0.987/0.985；配对/功能/batch 新测量），按协议 stop + 规格；不得用本次描述性运行替代。
- v0.1–v0.4 冻结不改；BRD3379 永不回 primary；不重开 R196v2/R197v2。

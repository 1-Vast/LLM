# report_h1b_run —— R204-M1 H1b 可分辨 TV 测量执行报告（机制账；不报效果）

2026-10-28 · 角色：独立实现者（endpoint-auditor）。依据：Lead `DECISION_R204_H1B_EXEC.md`；H1b 预注册链；C215/C216/C217；M1 Stage2 链。
**状态：H1b 测量执行完成；机制账 only；compute-only；0 wells；未执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定。**

## 0. 判定（一屏）

- **H1b verdict = `h1b_measurement_pass`**；`failure_category=None`；**16/16 cells TV≤tol_d**。
- **旧 C216 旧 H1 0/16 FAIL、`design_invalid: projection`、C217 归因、旧容差全部不变**；**H1b 是新单独协议，不是旧 gate 修正/重跑，不能写成旧 gate 通过**。
- **链核验 PASS**（H1b 预注册 + C215/C216/C217 + Lead 决定全部实算 match）；无 chain_mismatch。
- **final pilot（16 cells）**：wall **178.299 s**、CPU **271.984 s**、memory **0.23053 GB**；caps 1800s/2h/8GB/0 wells PASS。
- **main（16 cells）**：wall **172.548 s**、CPU process cumulative **541.125 s**、memory **0.23173 GB**；caps PASS。
- 两跑 result JSON 逐字节 **`2ECA912B…B21F06C9`**；cells/diagnostics 一致；timing 单独；JSON 无 telemetry。

## 1. 旧/新协议严格分离

| 项 | 状态 |
|---|---|
| C216 旧 H1 | **0/16 FAIL；`design_invalid: projection` 不变** |
| C217 归因 | **oracle 有限样本 floor 归因不变** |
| 旧 H1 容差 | d8 [.12,.10,.08,.07]、d16 [.14,.11,.09,.08]、d32 [.16,.13,.11,.10]、d64 [.18,.15,.13,.12] **不变** |
| H1b | **新单独预注册测量协议**；不是旧 H1 修正/重跑/通过；不改变 C216/C217 |
| 本次改 C216/C217 | **无** |

## 2. H1b 冻结测量

- **Pθ**：K=3 截断 GMM，权重 [.5,.3,.2]；c∼N(0,.5²)、M∼N(0,.1²)、d∼N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；box [-2,2]^4；param seed 20261301。
- **测量**：固定 a=0；X∼N(0,I_d)；Y∼Pθ 截断；hash 分箱：8-bit/维→code→cell=code mod **B=16**；TV=½Σ|p̂1−p̂2|。
- **N_eval=32768、K=1**；候选 C-MDN 训练一次/cell；oracle 独立同 N；hash TV。
- **floor**：q95_worst **0.01642609**、mean **0.01221141**；B/N/K 由 floor 选择。
- **tol_d**：d8 **.049**、d16 **.050**、d32 **.049**、d64 **.048**；floor_q95≤tol/3。
- C-MDN 结构/训练按 M1 Stage2 冻结；y 标准化/grad clip≤10 仅数值稳定，不改分布假设；target 样本不作标签；Doob 不可执行。

## 3. 16 cells（全部 PASS）

| d \ N_train | 512 | 1024 | 2048 | 4096 | tol_d |
|---|---:|---:|---:|---:|---:|
| 8  | .010529 | .013306 | .009644 | .012939 | .049 |
| 16 | .018311 | .013733 | .017365 | .013519 | .050 |
| 32 | .010223 | .013123 | .016937 | .015625 | .049 |
| 64 | .011169 | .015900 | .019318 | .023376 | .048 |

- **16/16 PASS**；max TV **.023376**（d64/N4096）<.048；无 `design_invalid: projection`。
- 仅 H1b 内部测量通过；**不是旧 H1 通过**；不写"旧 gate 通过"。

## 4. 链/seeds/一跑

- H1b 预注册 7 文件 + C215/C216/C217 6 文件 + Lead 决定实算 match；chain.pass=True。
- seeds：floor 20261801–10；data **20261811**；eval **20261812**；cells **20261821–36**；与旧集 disjoint；未改 seed。
- **final pilot**：16 cells（C-MDN 训练 16 次 + N_eval 32768 + oracle）；wall 178.299/CPU 271.984/mem .23053；canonical。
- **main**：16 cells；wall 172.548/CPU cumulative 541.125/mem .23173；caps PASS。
- 未用 floor 校准 MC 时间替代 pilot；未减 grid/N_eval；两跑同 seeds。

## 5. 两跑/telemetry/产出

- 两独立进程 `h1b_result.json` 逐字节 **`2ECA912BF74100674AF8E6B02FFCECD000E22ED3D44611FB5EB5FEB6B21F06C9`**；`h1b_cells.csv`、`h1b_diagnostics.json` 一致；timing 单独。
- 结果 JSON 无 telemetry；schema/失败模板先写；未输出 effect/decision utility/regret/top-k/方法比较。
- 主要 SHA：
  - `run_h1b.py` 见 usage
  - `h1b_result.json` `2ECA912B…B21F06C9`
  - `h1b_cells.csv` `D48A5022…27CE2D`
  - `h1b_diagnostics.json` `C7D78F1B…F087AF`
  - `schema_h1b_run.json` 见 usage
  - `timing_h1b_run.json` 见 usage
  - report/record/usage 见各文件

## 6. 边界/结论

- H1b 通过仅表示：在冻结合成 Pθ/C-MDN/新测量协议下，**可分辨 hash-bin TV 达到 tol_d**；**不是旧 H1 通过、不是药理/真实决策/迁移/机制/新颖性证据**。
- 旧 C216 `design_invalid: projection` 与 C217 归因不变；不修改旧文件；不改旧容差/阈值/判定。
- 机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；用户 public-only。

# R204-M1 H1b 可分辨测量预注册独立挑战（task-192）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 H1b、不运行 C-MDN/不运行效果/不读真实数据）。对象：[PROBLEM_H1B.md](PROBLEM_H1B.md)（SHA `AE8BEE2A…`）、[DESIGN_H1B.md](DESIGN_H1B.md)（`10EF642A…`）、[floor_calib_h1b.py](floor_calib_h1b.py)（`9A0380B5…`）、[floor_calib_h1b.json](floor_calib_h1b.json)（`88715AA8…`）、[schema_h1b.json](schema_h1b.json)（`A077BCCD…`）、report/record/usage、C215/C216/C217 旧协议。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_to_lead（仅批准 H1b 可分辨 TV 测量执行：机制账、compute-only、0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

核验 PASS：
- **旧/新严格分离**：C216 旧 H1 **0/16 FAIL、design_invalid: projection 不变**；C217 归因不变；**旧容差全部不变**；H1b 是**新单独预注册测量协议**，不是修正/重跑旧 gate；H1b 失败不改旧判定 ✓。
- **floor 校准**：冻结 Pθ（c .5²/M .1²/d .1²、σ 公式、box[-2,2]^4、K=3/[.5,.3,.2]、param seed 20261301）；hash 分箱 TV（8-bit/维→code→cell=code mod B；a=0、X~N(0,I_d)、截断 Y）；网格 B∈{16..256}×N_eval∈{2048,8192,16384,32768}×K∈{1,4,16}×d∈{8,16,32,64}；MC 300/p 400k/d；选择 q95_worst≤.02 最小成本；**选定 B=16/N_eval=32768/K=1、floor mean .01221141、q95 .01642609**；floor json 两跑逐字节 ✓。
- **容差/可判定性**：`tol_d=ceil(3·floor_q95_d·1000)/1000` → **d8 .049/d16 .050/d32 .049/d64 .048**；floor q95 分别 .01611633/.01642609/.01622467/.01580963，≤tol/3；**不按 M1 结果调**；可检出 excess **.03288367/.03357391/.03277533/.03219037**；旧 C217 excess median .0599/max .2037 → **power≈1、pass≈0**；无 precision_insufficient/stop ✓。
- **H1b 预注册**：16 cells d∈{8,16,32,64}×N_train∈{512,1024,2048,4096}；每 cell 候选采样 N_eval=32768、独立 oracle 同 N；hash B=16；TV≤tol_d pass、超→design_invalid: projection（仅 H1b 内部）；独立 seeds（floor 20261801–10、data 20261811、eval 20261812、cells 20261821–36）与旧集 disjoint；两跑同 seeds 独立进程/逐字节/telemetry 单独；caps 1800s/2h/8GB/0 wells；schema/失败/停止；执行前 final pilot 实测冻结；不输出 decision utility/regret/top-k/方法比较/效果 ✓。
- **边界**：机制账 only；不运行 C-MDN/不报效果；不改 C216/C217/旧容差/旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；H1b 执行另立独立挑战+Lead 批准 ✓。

**结论：可提交 Lead 批准 H1b 可分辨 TV 测量执行（仅机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 旧/新分离 | **PASS** | C216 旧 H1 0/16 FAIL/design_invalid: projection 不变；C217 归因不变；旧容差不变；H1b 新协议、不是重跑；H1b 失败不改旧判定 ✓。 |
| ② | floor 校准 | **PASS** | 冻结 Pθ/σ/box/K/param seed；hash TV 定义；B/N/K/d 网格；MC300/p400k；选择 q95_worst≤.02 最小成本；**B16/N32768/K1、mean .01221141、q95 .01642609**；两跑 json ✓。 |
| ③ | 容差/可判定性 | **PASS** | tol=ceil(3·q95_d·1000)/1000 → .049/.050/.049/.048；q95_d .01611633/.01642609/.01622467/.01580963；excess .03288367/.03357391/.03277533/.03219037；旧 C217 excess .0599/.2037→power≈1/pass≈0；无 precision_insufficient ✓。 |
| ④ | H1b 预注册 | **PASS** | 16 cells d×N_train；N_eval32768/独立 oracle；B16；TV≤tol→pass/超 projection；独立 seeds（20261801–10/11/12/21–36）；两跑/caps/schema/失败/停止；final pilot；无 effect 输出 ✓。 |
| ⑤ | 边界 | **PASS** | 机制账 only；不运行 C-MDN/不报效果；不改 C216/C217/旧容差/旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；H1b 执行另立挑战+Lead ✓。 |
| ⑥ | 总判决 | **approve_exec_to_lead** | 仅 H1b 测量；不批真实数据/效果。 |

## 2. 非阻塞实现备注（不改批准范围）

1. **容差是 floor-derived，不是“旧 H1 放宽”**：`.049/.050/.049/.048` 只用于 H1b 新测量；旧 H1 仍 0/16 + `design_invalid: projection`，旧容差表不得改；报告必须并列写“旧 H1 不变”与“H1b 新协议”，不能写成旧 gate 通过。
2. **`detectable_excess` 是相对 floor q95 的近似**：`.03288/.03357/.03278/.03219` 不是对所有备择的精确 power；power≈1 只针对 C217 旧 excess median .0599，报告需标 approx。
3. **H1b 16 cells/N_eval32768 的最终 pilot**：执行前必须用最终实现测 16 cells 的 wall/CPU/memory；caps 1800s/2h/8GB/0 wells；若超 caps→`compute_budget_exceeded`，不能用 floor 校准的 MC 时间替代。
4. **H1b 两跑/结果 JSON**：同 seeds 独立进程逐字节；telemetry 单独；JSON 不含 C-MDN 性能/效果字段；失败只写类别；旧 C216/C217 文件不修改。

## 3. Lead H1b 可分辨 TV 测量执行批准文本（建议）

> **批准范围**：批准 **R204-M1 H1b 可分辨 TV 测量执行**（仅机制账、compute-only、0 new wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：旧 C216 旧 H1 0/16 `design_invalid: projection`、C217 归因、旧容差全部不变；H1b 为新单独协议、不是重跑旧 gate；H1b 失败不改旧判定。冻结 Pθ（c .5²/M .1²/d .1²、σ、box[-2,2]^4、K=3/[.5,.3,.2]、param seed 20261301）；hash TV（8-bit/维、code mod B、a=0、X~N(0,I_d)、截断 Y）；**B=16/N_eval=32768/K=1**、floor mean .01221141/q95 .01642609；**tol_d .049/.050/.049/.048（ceil(3·q95_d·1000)/1000，不按 M1 结果调）**；16 cells d×N_train∈{512,1024,2048,4096}、N_eval32768、独立 oracle、B16；TV≤tol_d pass、超→`design_invalid: projection`（仅 H1b 内部）；seeds floor 20261801–10/data 20261811/eval 20261812/cells 20261821–36；两跑同 seeds 独立进程/逐字节/telemetry 单独；caps 1800s/2h/8GB/0 wells；schema/失败/停止；final pilot 实测冻结；不输出 effect/regret/top-k/方法比较。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；改旧 C216/C217/旧容差/旧判定；把 H1b 写成旧 H1 的修正/重跑/通过；改公式/阈值/端点；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不运行 C-MDN/不运行效果/不读真实数据**：只读 H1b 预注册/floor JSON/schema/C216/C217 链；只写本文件与 `tmp/`；未改 H1b/C215-217 产物。
- **总判决：approve_exec_to_lead**。旧/新分离、floor 校准（B16/N32768/K1/mean .01221141/q95 .01642609）、tol 推导（.049/.050/.049/.048）、excess/power、16 cells/独立 seeds/两跑/caps/schema/失败/停止/边界均核验通过；仅 floor-derived 容差解释、power 近似、16-cell final pilot、两跑/JSON 为非阻塞执行备注。仅批准 H1b 测量执行（机制账/compute-only/0 wells）；不批真实数据/效果/药理/真实决策/迁移/新颖性。

**一句话：H1b 预注册的旧/新分离（旧 H1 0/16 projection/旧容差不变）、floor 校准（B16/N32768/K1、mean .01221141/q95 .01642609）、tol=ceil(3·q95·1000)/1000（.049/.050/.049/.048）、16 cells/独立 seeds/两跑/caps/schema/边界都核验通过——判 approve_exec_to_lead（仅 H1b 可分辨 TV 测量：机制账/compute-only/0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

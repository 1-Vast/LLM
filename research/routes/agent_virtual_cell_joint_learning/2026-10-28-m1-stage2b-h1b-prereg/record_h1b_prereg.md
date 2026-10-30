# record_h1b_prereg.md —— R204-M1-S2B H1b 预注册执行记录（floor 校准；不运行方法）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-190（R204-M1-S2B-H1B-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m1-stage2b-h1b-prereg/` 与 `tmp/`；**未改 C215/C216/C217、M1 设计链、其他产物**；**未运行 C-MDN/未报效果/未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 明确旧/新协议分离 | ✅ C216 旧 H1 0/16/`design_invalid: projection` 不变；C217 归因不变；旧容差表不改；H1b 是新单独预注册协议、非修正/重跑旧 gate；H1b 失败不改旧判定 |
| ② floor 校准先于方法结果 | ✅ 冻结 Pθ（param 20261301、c .5²/M .1²/d .1²、σ 公式、box[-2,2]^4、K=3/[.5,.3,.2]）；B∈{16,32,64,128,256}×N_eval∈{2048,8192,16384,32768}×K∈{1,4,16}×d∈{8,16,32,64}；MC 300 reps、p 400k/d；选择规则（q95≤.02 最小成本，否则 min q95；>0.03 stop）；选定 **B=16/N=32768/K=1**、q95 **.01642609**、mean **.01221141**、decision=selected |
| ③ H1b 预注册 | ✅ 测量定义（hash 分箱 TV、B/N/K、eval seed 规则、16 格 d×N_train）、容差表（tol=ceil(3·q95·1000)/1000 → d8 .049/d16 .050/d32 .049/d64 .048）、pass/fail、失败类别、独立 seeds（floor 20261801–10；data 20261811/eval 20261812/cells 20261821–36；与旧集 disjoint）、两跑、caps 1800 s/2 h/8 GB/0 wells、schema/失败模板、pilot 实测冻结、停止条件 |
| ④ 可判定性 | ✅ required candidate TV=tol_d；detectable excess=.032–.034；旧 C217 excess median .0599→近似 power≈1/pass≈0；selected 满足 floor q95≤tol/3；无 precision_insufficient |
| ⑤ 边界 | ✅ 不运行 C-MDN/不报效果；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open |
| ⑥ report/record/usage+floor JSON/schema；标 completed+send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~15:32 | 读 task-190 并 claim；读 C217/C216/DECISION、M1 Stage2 v0.2/exec plan、ERRATA |
| ~15:36 | 写 `floor_calib_h1b.py`（冻结 Pθ 采样、hash 分箱、p 估计、floor MC、选择/容差/可判定性、schema） |
| ~15:39 | 首跑 18 s 成功；修 seeds 重叠（floor 20261801–10 vs exec 20261811+）、json telemetry（wall 移出 JSON）、power/pass 标签语义；最终两跑逐字节一致 |
| ~15:44 | 写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做 floor 校准**：冻结 Pθ 采样、hash 分箱 cell 概率、oracle-vs-oracle 两样本 TV floor MC、tolerance/decidability 算术；**不训练 C-MDN、不生成方法结果、不计算效果**。
2. **旧/新分离**：C216/C217 原样引用为只读；旧 H1 容差未改；H1b 明确定位新协议、非旧 gate 修正/重跑。
3. **选择规则先于方法结果**：q95≤.02 最小成本 → B=16/N=32768/K=1；tol 由 floor q95 推导（3×q95），不按 M1 结果。
4. **可判定性**：pass 要求 TV≤tol_d；detectable excess .032–.034；旧 excess .0599 下 power≈1、pass≈0；说明 H1b 可检出旧量级误差且不被 floor 判死。
5. **seeds/两跑**：floor 20261801–10；H1b data 20261811/eval 20261812/cells 20261821–36；与旧 Stage2 seeds disjoint；两跑同 seeds/独立进程/Result JSON 逐字节；telemetry 单独。
6. **确定性**：`floor_calib_h1b.json`（`88715AA8…`）两跑逐字节一致；JSON 无 telemetry；wall≈16–17 s 仅记录在 usage/报告。
7. **边界**：机制账 only；未运行 C-MDN/未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 选定测量：**B=16、N_eval=32768、K=1**；oracle floor mean **.01221141**、q95 **.01642609**（worst-case over d）。
- tolerance：d8 **.049**、d16 **.050**、d32 **.049**、d64 **.048**（global .050）；floor q95≤tol/3。
- detectable excess：d8 **.03288**、d16 **.03357**、d32 **.03278**、d64 **.03219**。
- 旧 C217 excess median **.0599**/max **.2037**；old-excess 下近似 power≈1、pass≈0。
- H1b 16 cells d×N_train；seeds floor 20261801–10/data 20261811/eval 20261812/cells 20261821–36；caps 1800 s/2 h/8 GB/0 wells；两跑/schema/失败/停止。
- 无 C-MDN/无效果；本轮仅 floor 校准+预注册。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_H1B.md` | `AE8BEE2A66DC8ABDBB80839B01A61AA8C432BEC474B406C28E1209D318A48B66` |
| `DESIGN_H1B.md` | `10EF642AD62707ADE406E458657FCC8D53D2B4AA69423234C1E86769E8E598D1` |
| `floor_calib_h1b.py` | `9A0380B551173F2E2C1F96942745314B4591C4FACDC3DED0487E97DE65F13663` |
| `floor_calib_h1b.json` | `88715AA8C60613AB7675923A67BC919B1B2F9361112EBCF9B29CD9BB33AB3214` |
| `schema_h1b.json` | `A077BCCDF793192861EB1E725FCE16FA70C2627652DF298A50D3633CF57C5F31` |
| report/record/usage | 见 `usage_h1b.json` |
| 只读引用（未改） | C216 `m1_stage2_rerun.json` `B2CD0195…`；C217 `diag_m1_s2.json` `6FBD1016…` |

## 5. 缺口与下一步

- **H1b 尚未执行**；本文件仅 floor 校准+预注册，未训练 C-MDN/未读真实数据/无效果。
- 执行前：独立挑战 + Lead 批准 + floor/参数复核 + 最终实现 pilot 实测冻结 + 两跑/schema/失败模板核验。
- 不改变 C216/C217；不改旧 H1 容差；机制账 only；不晋升代码/不改旧判定/不恢复停止实验。

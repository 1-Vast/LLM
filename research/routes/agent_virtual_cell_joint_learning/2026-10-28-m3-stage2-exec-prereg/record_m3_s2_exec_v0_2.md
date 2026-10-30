# record_m3_s2_exec_v0_2.md —— R204-M3-S2.1 修订预注册记录（3 必改；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-176（R204-M3-S2.1）· 日期 2026-10-28
只写 `research/2026-10-28-m3-stage2-exec-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/M3 预注册/Stage1/M1/M2/N1/A-B-D**；**未运行 Stage2 训练/效果/真实数据**；支撑研究/机制账 only；compute-only、0 wells。

## 0. 3 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① 失败类别补全 13 项（含 chain_mismatch） | ✅ failure list **13 项**，含 `design_invalid: chain_mismatch`；schema/stop 映射同步；单测 count=13/`chain_mismatch_present=true` |
| ② per-arm 诊断字段/判据/schema | ✅ `per_arm`/`arm_result` **13 字段**（arm_id、replicate_id、allocation_weights、realized_allocation_frequency、H_summary、delta_summary、allocation_Q、variance_term、clipping、equal_budget_audit、two_run_sha、pass、failure_category）；每 arm 通过判据/失败映射；**仍不输出 decision utility/regret/top-k/学习效果比较**；分配诊断口径保留，标准 DR/TMLE+最优分配等价判定留 Stage3 |
| ③ 冻结 sample 语义 + pilot 实测 | ✅ R=**10**；data seed **20261401**；replicate seeds **20261401–10**；每 replicate **300 initial** + **每 arm 300 alloc**（6 arms）；**total 21,000**、**alloc/feedback 18,000**；arm seed=**20261411+10a+r**；每 arm 等预算账写死；**执行前必须跑最终实现 pilot（2 reps×6 arms×300）实测冻结 canonical**；Stage1 pilot 仅历史参考 |
| ④ 保留 | ✅ 17 文件链/Stage1、独立 seeds/两跑、H=3/A=3/Y binary、p/μ/b/π/m/C_H=20、六 arms（含 decision_AL/optimal design）、G1–G6、caps 1800 s/2 h/8 GB/0 wells、schema 先写、无 telemetry、单测算术、π=b/截断/共线/分离/支持规则、边界 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~13:40 | 读 task-176 并 claim；读 M3-S2-EXEC-C1 挑战、v0.1 产物、M3 v0.2/Stage1 链 |
| ~13:43 | 写 v0.2 脚本（13 类失败/per-arm 13 字段/R=10 sample 语义/arm seeds 20261411+10a+r/最终实现 pilot 实测要求/schema v0.2） |
| ~13:45 | 运行成功：chain_pass=true、failure_categories=13、per-arm 13 字段、sample 21,000/18,000、overlap=[]、all_pass=true；两跑 plan/schema 逐字节一致 |
| ~13:49 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：链核验、seeds/sample 语义、环境/六 arms/per-arm 字段、13 类失败、G1–G6、预算/pilot 政策/schema、DR 恒等/截断/共线/π=b/分配 ratios 算术；**不训练、不采样方法、不执行分配比较、不计算效果/regret/top-k**。
2. **v0.2 修正**：① 失败类别 13（补 chain_mismatch）；② per-arm 13 字段/判据/失败映射，schema `per_arm`；③ R=10、data seed 20261401→replicate seeds 20261401–10、每 rep 300 initial+6×300 alloc、总 21,000/分配 18,000、arm seed 20261411+10a+r、每 arm 预算账；执行前最终实现 pilot 实测冻结（Stage1 pilot 仅历史参考）。
3. **seeds**：replicate seeds 20261401–10、arm seeds 20261411–70；与禁用集交集 []；执行时重核。
4. **确定性**：`exec_plan_m3_s2_v0_2.json`（`F16D1C04…`）与 `schema_m3_s2_exec_v0_2.json`（`987089F8…`）两跑逐字节一致；JSON 无 telemetry。
5. **边界**：支撑研究/机制账；Stage2 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210）。

## 3. 关键结果

- 链：17/17 SHA、chain_pass=true；Stage1 19 checks PASS。
- 失败类别：**13 项**，含 chain_mismatch。
- per-arm 字段：**13**（arm_id…failure_category）；每 arm 判据/失败映射冻结；无效果输出。
- sample：R=10；每 rep 2,100 units；总 21,000；alloc/feedback 18,000；每 arm 300/300/≤20/caps。
- seeds：replicate 20261401–10、arm 20261411–70；overlap=[]。
- 算术单测：DR gap 1.1e-16；clip detected bias −0.026407185629；collinear rank 1；π=b H−1 0.0；ratios [1.21722846, 1.16686763]；all_pass=true。
- 预算：caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 pilot 实测冻结 canonical；Stage1 pilot 仅历史参考。
- 无训练/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S2_EXEC_v0_2.md` | `FE9180FA4A82A71ABA77F7080A848BEBD7C6CA24482DD3BE397F6B5138398F32` |
| `DESIGN_M3_S2_EXEC_v0_2.md` | `2569079C63320EC0518D913B26A65A2CCA7E35D6DB47D178B48AE904AF7ED89F` |
| `exec_plan_m3_s2_v0_2.py` | `C85C1AEA651E844D4D9B26EC793D10037960B3B516BC97FA6F48C5942B1192C4` |
| `exec_plan_m3_s2_v0_2.json` | `F16D1C04F5E63ECDA082F10FD5EB4AEC486B902829DA1FCAD027CA92BF0184C8` |
| `schema_m3_s2_exec_v0_2.json` | `987089F84330DF97338513163570DDA47E91ABA3B26E73981DF44E0FC188B3B1` |
| report/record/usage | 见 `usage_m3_s2_exec_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `4690A50A…`、DESIGN `AD18DC25…`、script `83EFB2CD…`、JSON `92D00E0C…`、schema `A0A43078…` |

## 5. 缺口与下一步

- **Stage2 尚未执行**；本文件仅预注册修订，未训练/未读真实数据/无效果。
- 执行前：轻量复核 + Lead 批准 + 重核 17 文件链 + 最终实现 pilot 实测冻结 canonical timing + seed/两跑/schema/失败模板核验。
- Stage3 另立预注册；真实功能数据仍 data_unavailable（C203/C205/C210）；支撑研究/机制账；不晋升代码/不改旧判定/不恢复停止实验。

# record_m1_s2_exec.md —— R204-M1 Stage2 合成执行预注册记录（仅机制账；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-168（R204-M1-S2-EXEC-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m1-stage2-exec-prereg/` 与 `tmp/`；**未改 M1 Stage2 设计/Stage1/M2/M3/N1/A-B-D**；**未运行 Stage2 训练/效果/真实数据**；机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 链核验 v0.2 设计链+Lead 接受决定；不匹配→chain_mismatch | ✅ `exec_plan_m1_s2.py` 只读核验 **12 文件 SHA 全匹配**（chain_pass=true、mismatches=0）；含 M1 Stage2 v0.2 八件 + Lead 接受决定 `6EC860D2…` + Stage1 三件；不匹配→`design_invalid: chain_mismatch`、执行时重核 |
| ② 独立执行 seeds（不复用 C208/Stage1/M2/M3；两跑同 seeds 独立进程逐字节；telemetry 单独） | ✅ param/train/eval **20261301/02/03**；H1 20261310–25、H2 20261326–30、H3 20261331–32、reps 20261340–49；禁用 C208/Stage1 20261112/13、M1 v0.2 20261201–03、M2 Stage2 20261200–39、M2 Stage3 20262100–39、M3 保留 20261500–99；**overlap=[]、unique=true**；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |
| ③ 仅 Stage2 诊断：唯一 Pθ（3 分量截断 GMM/条件异方差）、C-MDN、H1/H2/H3 写死；不输出效果/regret/top-k/比较 | ✅ Pθ/candidate/H1（d/N 网格+容差表 N 顺序+256-bin TV）/H2（ε 5/maxiter2000/marg 1e-8/至少一收敛）/H3（small-case d2/A2/Y2、oracle GL128/dim、TV≤.05）全部冻结；**无效果/regret/top-k/方法比较**；H3 明确非高维 oracle |
| ④ G1–G6 继承；B1–B5 仅规格；失败类别 | ✅ G1–G6（含失败映射）；B1–B5 spec-only 不执行；失败类别 12 项（projection/support/calibration/leakage/compute_budget_exceeded/rename_maxent/two_run_mismatch/chain_mismatch + unreachable_gate/precision_insufficient/no_increment/inconclusive） |
| ⑤ caps 1800s/2h/8GB/0 wells；执行前 pilot 最终实现重跑冻结 canonical；schema/失败模板先写；JSON 无 telemetry | ✅ caps/0 wells；执行前 pilot 重跑冻结规则；schema `schema_m1_s2_exec.json` 先写；JSON 无 telemetry；planning 参考 prep timing（.00115028 s/rep、.011503 s、.00668467 GB）仅参考、执行必须重测 |
| ⑥ 停止/撤主张：B2 等价/一步投影已撤不得写 M1 增量；H1 超容差/H2 不收敛/H3 TV>.05→projection；不改旧判定/门槛 | ✅ 全部写死；任何失败不改旧判定/门槛；不放宽容差/改阈值/换端点 |
| ⑦ 边界：机制账 only、不执行 Stage3/真实数据/湿实验、不称药理/真实决策/迁移/机制/新颖性、不晋升代码、M1 不与 M2/M3 混同、N1 不作证据、data readiness open C203/C205/C210 | ✅ 全部写入 PROBLEM/DESIGN/report/JSON |
| ⑧ report/record/usage；标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~12:44 | 读 task-168 并 claim；读 M1 Stage2 v0.2 设计/接受决定、Stage1/C208、prep plan/timing/schema、ERRATA |
| ~12:48 | 写 `exec_plan_m1_s2.py`（链核验、独立 seeds、H1/H2/H3、G1–G6/B1–B5、budget/schema/失败、骨架单测） |
| ~12:50 | 修 einsum 形状/截断公式/Sinkhorn 对偶缩放（三次补丁）；重跑成功：chain_pass=true、seeds overlap=[]、unit tests all_pass=true、sinkhorn 23 iter |
| ~12:52 | 两跑 `exec_plan_m1_s2.json`（`3DC88FEF…`）与 `schema_m1_s2_exec.json`（`181A77E3…`）逐字节一致；写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：链核验、独立 seeds、H1/H2/H3 协议/容差冻结、G1–G6/B1–B5 规格、预算/schema/失败模板；骨架单测只检查形状/权重和/截断质量/reward 边界/seed 复现/tiny Sinkhorn（4×4，ε=.5，23 iter，marginal≤1e-8）/H1 容差表/H2 网格/H3 小例；**不训练 C-MDN、不运行 Pθ 采样比较、不计算效果**。
2. **链核验**：12/12 SHA 匹配；Stage1 `failed_gates=[]`、`no_effect_results=true`、B2 rename_maxent 检出、一步投影撤。
3. **seeds**：20261301+ 独立区间；与 C208/Stage1、M1 v0.2、M2 Stage2/Stage3、M3 保留区间交集 []；执行时重核。
4. **预算**：caps 1800 s/2 h/8 GB/0 wells；planning 参考来自只读 prep timing（.00115028 s/rep、.011503 s、.00668467 GB），**执行前必须用最终实现重跑 pilot 并冻结 canonical timing**；JSON 无 telemetry。
5. **边界**：机制账 only；Stage2 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210）。
6. **确定性**：plan/schema 两跑逐字节一致；JSON 无时间戳；无 telemetry。

## 3. 关键结果

- 链：12/12 SHA、chain_pass=true；Stage1 PASS 状态。
- seeds：36 个执行 seeds unique、overlap=[]；区间 20261301+。
- H1：4×4 网格、容差表 N 顺序 [512,1024,2048,4096]、256-bin TV、超→projection。
- H2：ε [.1,.25,.5,1,2]、maxiter2000、marg 1e-8、至少一收敛；tiny Sinkhorn 23 iter 收敛。
- H3：d2/A2/Y2、oracle GL128/dim、TV≤.05、small-case only。
- G1–G6 继承；B1–B5 spec-only；失败类别 12；停止/撤主张写死。
- 骨架单测全 PASS；0.1 s wall；无训练/效果。
- budget caps/planning 参考：per-rep .00115028 s、projected .011503 s、memory .00668467 GB；执行重测。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2_EXEC.md` | `F7ED4520C00EBEEC5D18371050634C3ECAA5B1E61FAB860924C0709FAC93A0CD` |
| `DESIGN_M1_S2_EXEC.md` | `503618F4CBA53F6C15A2BB144A31CB29F6C5D8B6BAE7CD3E3DBEB2B40DD30806` |
| `exec_plan_m1_s2.py` | `CFF1C734FADA3E6679B5482D5BCB20C3B4D0766AE9A9E957E86977C62FADB3A8` |
| `exec_plan_m1_s2.json` | `3DC88FEF2860E5374F781CF642DD55B62079586E3618E1E04915F99137407B5C` |
| `schema_m1_s2_exec.json` | `181A77E377FE0CD4870CB8D977F7ACDB127730F6598A96950FB13DEE7917B682` |
| report/record/usage | 见 `usage_m1_s2_exec.json` |
| 只读冻结链（未改） | M1 Stage2 v0.2 八件 + Lead 接受 + Stage1 三件（见 exec_plan JSON） |

## 5. 缺口与下一步

- **Stage2 尚未执行**；本文件仅预注册草案，未训练/未读真实数据/无效果。
- 执行前：独立挑战 + Lead 批准 + 重核 12 文件链 + 重跑最终实现 pilot 冻结 canonical timing + seed/两跑/schema/失败模板核验。
- Stage3 另立预注册；真实功能数据仍 `data_unavailable`（C203/C205/C210）；机制账 only；不晋升代码/不改旧判定/不恢复停止实验。

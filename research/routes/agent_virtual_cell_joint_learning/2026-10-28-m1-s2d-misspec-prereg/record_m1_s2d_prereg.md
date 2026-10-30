# record_m1_s2d_prereg.md —— R204-M1-S2d 预注册执行记录（headroom 设计；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-199（R204-M1-S2D-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m1-s2d-misspec-prereg/` 与 `tmp/`；**未改 S2c/H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D 产物**；**未训练 C-MDN/未运行候选规划/未报效果/未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 分离 | ✅ S2c 仅合成 known-truth；C216/C217/H1b/C208 不变；S2d 新预注册不改 S2c |
| ② 源/目标 Pθ' | ✅ 源 Pθ 同 H1b/S2c；目标 3 种：T1 c'~N(0,1.0²)（seed 20262001）、T2 M'~N(0,.2²)（seed 20262002）、T3 X'~N(0,1.5²I)；π0' full；候选仅源训练、目标数据禁用训练/调参；known-truth 目标解析 |
| ③ 六比较 | ✅ primary candidate vs P_empirical_mean_source；secondary target-adapted empirical mean（3584 源+512 目标/动作同预算）、max-entropy、conditional-density-MC（共用 C-MDN、预计 D=0）、random、softmax-expected；D<0、δ=.05、Holm family=6、单侧下尾 |
| ④ 设计期 headroom | ✅ 目标 Pθ' 上 P_empirical_mean_source baseline regret：T1 **.51107412** CI[.46843293,.55371531]、T2 **.56758207** CI[.56039835,.57476580]、T3 **.39007047** CI[.38530525,.39483569]；均≥.10 → executable；未重设环境；不降 δ/不换 seed |
| ⑤ seeds/两跑/caps/schema/失败 | ✅ headroom 20262011–30；执行 data 20262031/target eval 20262032/cells 20262041–88；overlap=[]；两跑逐字节；caps 1800 s/2 h/8 GB/0 wells；schema/11 失败；pilot 冻结要求 |
| ⑥ 等价审计 | ✅ candidate 与 empirical-mean/max-entropy/conditional-density 等价→equivalence/no increment；不得目标训练/调参制造差异 |
| ⑦ 停止条件 | ✅ headroom<.10（任一 target）→重设/冻结或 unreachable_gate；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定 |
| ⑧ report/record/usage+schema+headroom；标 completed+send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~17:29 | 读 task-199 并 claim；读 S2c/C223、H1b/C222、C216/C217、C220/C221、M1 Stage2 v0.2 |
| ~17:34 | 写 `headroom_design_m1_s2d.py`（源/目标 Pθ'、analytic 真值、source baseline headroom、六比较/Holm/equivalence/seeds/schema） |
| ~17:36 | 运行成功：T1 .51107、T2 .56758、T3 .39007，均≥.10；executable；两跑逐字节一致 |
| ~17:40 | 写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做设计期 headroom**：源 Pθ 采样 + 目标 Pθ' 解析已知真值；P_empirical_mean_source（N_train=4096/动作、动作级经验均值、忽略 x）在目标独立 eval X=4096 上；R=20；真值目标解析截断正态矩。
2. **目标漂移**：T1 尺度（c' 1.0²）、T2 斜率（M' .2²）、T3 背景（X' 1.5²I）；target param seeds 20262001/20262002；π0' full；候选仅源训练、目标禁用训练/调参。
3. **headroom 结果**：T1 .51107412 CI[.46843293,.55371531]；T2 .56758207 CI[.56039835,.57476580]；T3 .39007047 CI[.38530525,.39483569]；均≥.10 → executable；未重设环境；不降 δ/不换 seed。
4. **六比较/Holm**：primary candidate vs P_empirical_mean_source；secondary target-adapted（3584+512 同预算）、max-entropy、conditional-density-MC（共用 C-MDN、D=0 不称独立）、random、softmax；D<0、δ=.05、Holm family=6、单侧下尾；raw/paired 分存；CI replicate≥20；主成功仅 T1，T2/T3 泛化/敏感性。
5. **执行 seeds**：headroom 20262011–30；data 20262031、target eval 20262032、cells 20262041–88；overlap=[]；两跑逐字节；caps 1800/7200/8GB/0 wells；schema/11 失败/停止。
6. **确定性**：`headroom_design_m1_s2d.json`（`12A9B91B…`）两跑逐字节一致；JSON 无 telemetry；headroom wall≈5.3–5.7 s 仅 usage/报告。
7. **边界**：机制账 only；未训练 C-MDN/未运行候选/未读真实数据；不改旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 目标 Pθ'（3）：T1 c'~N(0,1.0²)、T2 M'~N(0,.2²)、T3 X'~N(0,1.5²I)；π0' full。
- headroom on target（source P_empirical_mean baseline）：T1 .51107412 CI[.46843293,.55371531]、T2 .56758207 CI[.56039835,.57476580]、T3 .39007047 CI[.38530525,.39483569]；均≥.10 → executable；未重设。
- 六比较族/Holm 6/δ=.05/raw-paired/CI replicate；target-adapted empirical mean 同预算 3584+512；candidate 源训练/目标禁用训练调参；等价审计。
- seeds 20262011–88；caps 1800/7200/8GB/0 wells；schema/11 失败/停止。
- 无 C-MDN/无候选规划/无效果；本轮仅 headroom+预注册。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2D.md` | `00394113A84DF84F50FF709BC841B74F84ED26F4984DC35329CF044E447AC68D` |
| `DESIGN_M1_S2D.md` | `86F5B08F37CFBE6C8F9C08670638EF8B66D5AFD98640CCD7B576C853283CE439` |
| `headroom_design_m1_s2d.py` | `552F746C4C5E4A1B2C63F2A47FF8ED4A71CD03E1ECD2ACF9AC410B8484EA47D8` |
| `headroom_design_m1_s2d.json` | `12A9B91BDEF709DFE413E5E63DC2EBFAB640807C6FFAE27D6BDDC6A91CD4E646` |
| `schema_m1_s2d.json` | `20B13ADD7A3EC832279103E4AE1366D514436DC50991A752F8BB888A9C5CD8D2` |
| report/record/usage | 见 `usage_m1_s2d_prereg.json` |
| 只读引用（未改） | S2c result `4977B74E…`；H1b result `2ECA912B…`；C216 `B2CD0195…`；C217 `6FBD1016…` |

## 5. 缺口与下一步

- **S2d 尚未执行**；本文件仅 headroom 设计，未训练/未运行候选/无效果。
- 执行前：独立挑战 + Lead 批准 + 重核环境/headroom/六比较/seeds/两跑/schema/失败模板 + 最终实现 pilot 冻结；不改旧判定。
- 机制账 only；不晋升代码/不改旧判定/不恢复停止实验。

# record_m3_s3b_prereg_v0_2.md —— R204-M3-S3B.1 修订预注册记录（seed 201/7 arms；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-208（R204-M3-S3B.1）· 日期 2026-10-28
只写 `research/2026-10-28-m3-s3b-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/M3 Stage1/2/3/M1/M2/N1**；**未训练/未运行候选、未报效果、未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① seed 计数 201 | ✅ **EXEC_SEEDS 补入 headroom 20**：env 20262200 + headroom 20262201–20 + feedback 20262221–40 + eval 20262241–60 + arms 20262261–2400（7×20）= **201**；`all_exec_seeds_count=201`；保留 7 arms/family=6；181 作废；不删 arm |
| ② schema/JSON 可判字段 | ✅ **`n_arms=7`、`n_arm_seeds=140`、`n_exec_seeds=201`**；`all_exec_seeds_count` 由 `len(EXEC_SEEDS)` 程序化；`seed_block_counts={env1,headroom20,feedback20,evaluation20,arms140}`；schema/report/record 同步；`unique=true`、`overlap=[]` 保持 |
| ③ 保持 | ✅ 分离/纠正；高 regret H3/A3/Y binary/p/μ/b/π2'/m_wrong/C_H/b_min；H_max 18.91778<C_H 无 clipping；DR gap 0<1e-10；headroom **P_empirical_mean/P_standard_DR_TMLE .14841667 CI [.10382916,.19300417]**；learner 合同；六比较/Holm6/δ=.05/单侧下尾/raw-paired/CI R=20/等价审计；seeds blocks；两跑/caps/schema/13 失败/停止/边界；不训练/不拟合候选 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~18:40 | 读 task-208 并 claim；读 M3-S3B-C1 挑战、v0.1 产物/JSON seed blocks |
| ~18:43 | 复制 v0.1→v0.2 脚本；patch：EXEC_SEEDS 补 headroom 20、N_ARMS=7/N_ARM_SEEDS=140/N_EXEC_SEEDS=201、schema/output 字段、seed_block_counts、task/status/路径 |
| ~18:45 | 运行成功：n_arms=7/n_arm_seeds=140/n_exec_seeds=201/all_exec_seeds_count=201、unique=true/overlap=[]；headroom 值不变；两跑 JSON/schema 逐字节一致 |
| ~18:50 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **仅预注册修订**：不训练/不运行候选；headroom 值保留；只改 seed blocks/计数/schema/文档。
2. **seed blocks**：env 20262200（1）+ headroom 20262201–20（20）+ feedback 20262221–40（20）+ evaluation 20262241–60（20）+ arms 20262261–2400（20262261+20a+r；a=0..6，r=0..19；140）= **201**；`EXEC_SEEDS` 包含全部五块；`all_exec_seeds_count=len(EXEC_SEEDS)=201`。
3. **schema/JSON**：n_arms=7、n_arm_seeds=140、n_exec_seeds=201、seed_block_counts；schema/report/record 同步；unique=true、overlap=[]。
4. **高 regret/headroom（未变）**：P_empirical_mean/P_standard_DR_TMLE **.14841667 CI [.10382916,.19300417]**；均≥.10；H_max 18.91778<C_H；DR gap=0.0<1e-10。
5. **learner 合同/六比较/等价/停止/边界（未变）**：真实 ε NLL/L-BFGS/score<1e-6；standard same m no ε；禁假变换；family=6 Holm/δ=.05/单侧下尾/raw-paired/CI R=20；等价审计；13 失败；caps 1800/7200/8GB/0 wells；不训练/不运行候选。
6. **确定性**：`headroom_design_m3_s3b_v0_2.json`（`E7D9EC3D…`）两跑逐字节一致；JSON 无 telemetry；wall≈0.1–0.2 s 仅 usage/报告。
7. **边界**：机制账 only；未训练/未运行候选/未读真实数据；不改旧判定；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；Stage3 no_increment 保留；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- EXEC_SEEDS 201（env1+headroom20+feedback20+eval20+arms140）；n_arms=7、n_arm_seeds=140、n_exec_seeds=201；all_exec_seeds_count=201；unique=true、overlap=[]；seed_block_counts 对账。
- 高 regret/headroom（未变）：P_empirical_mean/P_standard_DR_TMLE .14841667 CI [.10382916,.19300417]；H_max 18.91778<C_H；DR gap=0.0<1e-10。
- 六比较/Holm6/δ=.05/单侧下尾/raw-paired/CI R=20/等价审计；13 失败；caps 1800/7200/8GB/0 wells；seeds blocks；两跑/schema/pilot。
- 无候选训练/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3B_v0_2.md` | `5EAB7A5188438B6875F77C5866FF3821A69B1992AE471E6F33FC0F6F9E38AEFB` |
| `DESIGN_M3_S3B_v0_2.md` | `73245C43F6E21CABD88E38B7371DB8374F76E0F4DF9E74F1F89B294C859C84B5` |
| `headroom_design_m3_s3b_v0_2.py` | `F63135BD90D852657F13473A9AAF38877E310D765E1C0BF785D0FAF848BA5327` |
| `headroom_design_m3_s3b_v0_2.json` | `E7D9EC3DFE07E6BD4217E5AABE165960F6FCAACA8BCE56F07695117DD95F1EC5` |
| `schema_m3_s3b_v0_2.json` | `CBD748B79E6D3A8B0BF499D2866B3EF7A310A451CE7B7A08F1FE3B20DE33F17D` |
| report/record/usage | 见 `usage_m3_s3b_prereg_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `869690F9…`、DESIGN `79E1E109…`、script `68EF6698…`、JSON `77F113FF…`、schema `29747B9C…` |

## 5. 缺口与下一步

- **S3b 尚未执行**；本文件仅预注册修订（seed 计数/schema）。
- 执行前：轻量复核 + Lead 批准 + 重核高 regret/headroom/DR identity/learner 合同/seed blocks/两跑/schema/失败模板 + 最终实现 pilot 冻结；不改旧判定。
- 机制账 only；不训练/不运行候选/不报效果；不晋升代码/不改旧判定/不恢复停止实验。

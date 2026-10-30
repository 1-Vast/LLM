# R204-M3 S3b.1 轻量复核（task-209）：v0.2 seed count 201

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S3b、不训练/不拟合候选/不读真实数据）。对象：[PROBLEM_M3_S3B_v0_2.md](PROBLEM_M3_S3B_v0_2.md)（SHA `5EAB7A51…`）、[DESIGN_M3_S3B_v0_2.md](DESIGN_M3_S3B_v0_2.md)（`73245C43…`）、[headroom_design_m3_s3b_v0_2.py](headroom_design_m3_s3b_v0_2.py)（`F63135BD…`）、[headroom_design_m3_s3b_v0_2.json](headroom_design_m3_s3b_v0_2.json)（`E7D9EC3D…`）、[schema_m3_s3b_v0_2.json](schema_m3_s3b_v0_2.json)（`CBD748B7…`）、report/record/usage、C218/C220 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_v0_2_to_lead（仅批准 M3-S3b 候选 learner 比较执行：机制账、compute-only、0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

v0.2 已修掉 v0.1 的 seed count 不一致：
- **seed blocks/count**：env **20262200（1）**、headroom **20262201–20（20）**、feedback **20262221–40（20）**、eval **20262241–60（20）**、arms **20262261–2400（20262261+20a+r；a=0..6,r=0..19；140）**；total **201**；**181 作废**；7 arms/family=6 保留；`unique=true`/`overlap=[]` ✓。
- **schema/JSON 可判字段**：`n_arms=7`、`n_arm_seeds=140`、`n_exec_seeds=201`；`execution_seeds.all_exec_seeds_count=201`；`seed_block_counts={env:1,headroom:20,feedback:20,evaluation:20,arms:140}`；schema/report/record 同步 ✓。
- **保持项**：分离/纠正（C218 Stage3 no_increment 保留、C220 解释不成立、C208 撤）；高 regret 环境（H3/A3/Y binary、π2' .82/.09、H=π2/w、**H_max=18.91777778<C_H=20 无 clipping**）；**DR gap 0.0<1e-10**；headroom P_empirical_mean/P_standard_DR_TMLE **.14841667 CI [.10382916,.19300417]**；learner 合同（真实 ε NLL/L-BFGS/score<1e-6；standard same m no ε；禁假变换/缩放/λ/类名）；六比较/Holm6/δ=.05/单侧下尾/raw-paired/CI R=20/等价审计；两跑/caps 1800s/2h/8GB/0 wells/schema/13 失败/停止/边界 ✓。
- **边界**：机制账 only；不执行真实数据/湿实验；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；public-only ✓。

**结论：可提交 Lead 批准 M3-S3b 执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | seed blocks/count | **PASS** | env1+head20+fb20+eval20+arms140=201；181 作废；7 arms/family6；unique/overlap=[] ✓。 |
| ② | schema 可判字段 | **PASS** | n_arms7/n_arm_seeds140/n_exec_seeds201；execution_seeds.all_exec_seeds_count=201；seed_block_counts；schema/report/record 同步 ✓。 |
| ③ | 保持项 | **PASS** | 分离/纠正；高 regret H_max18.91778<C_H20 无 clipping；DR gap0<1e-10；headroom .14841667 CI[.10382916,.19300417]；learner 合同；六比较/Holm6/δ=.05/单侧/raw-paired/CI R20/等价审计；两跑/caps/schema/13失败/停止/边界 ✓。 |
| ④ | 边界 | **PASS** | 机制账 only；不执行真实数据/湿实验；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；public-only ✓。 |
| ⑤ | 总判决 | **approve_exec_v0_2_to_lead** | 仅 S3b 执行；不批真实数据/效果。 |

**非阻塞实现备注**：
1. `all_exec_seeds_count`/`seed_block_counts` 位于 `execution_seeds` 块（顶层同名键为 null）；执行器应读 nested/schema，不要读顶层 null 误判缺失。
2. `seed_block_counts` 不在 schema top_keys，但 schema 有 n_* 三字段；执行器可用 blocks 程序化校验 `len(EXEC_SEEDS)=201`。
3. H_max=18.91778 距 C_H=20 很近但**未 clipping**；执行仍要断言 H≤C_H，不得因接近上限而 clipping；若上游改 π2/w 需重算。
4. final pilot 实测冻结 canonical；两跑同 seeds/telemetry 分开；不训练/不拟合候选；旧 Stage3 no_increment/C220/C208 不改。

## 2. Lead M3-S3b 执行批准文本（建议）

> **批准范围**：批准 **M3-S3b 候选 learner 比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：C218 Stage3 no_increment 保留；C220 解释无效；S3b 新预注册、不重跑旧 Stage3；C208 一步投影撤；高 regret H3/A3/Y binary、p=[.3,.4,.3]、μ/b Stage2、m_wrong=.5、C_H=20、b_min=1e-6、π2' .82/.09、Q/w/H=π2/w、**H_max18.91778<C_H20 无 clipping**；headroom P_empirical_mean/P_standard_DR_TMLE **.14841667 CI [.10382916,.19300417]**，均≥2δ=.10；headroom<.10→redesign/freeze 或 unreachable_gate，不执行/降δ/换seed/环境；DR gap0<1e-10；learner 合同（真实 ε weighted Bernoulli NLL/L-BFGS/score<1e-6；standard same m no ε；禁 0.5+0.5*score/sigmoid/无 NLL/缩放/λ/类名）；六比较 family6（primary candidate vs P_standard_DR_TMLE；secondary empirical/IW/full-history/DR-targeting/value-aware）、D<0、δ=.05、Holm6、单侧、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired、CI R20/cluster；等价审计；**seeds env20262200(1)+headroom20262201–20(20)+feedback20262221–40(20)+eval20262241–60(20)+arms20262261–2400(140)=201**；两跑/caps/schema/13失败/停止；不输出effect/真实数据。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把181 count 配7 arms；把旧 Stage3 no_increment 改写；改 learner 合同/缩放/λ/类名；改旧判定/阈值；晋升代码；恢复停止实验。

## 3. 声明

- **本轮不训练/不拟合候选/不读真实数据**：只读 S3b v0.2 预注册/headroom JSON/schema/C218/C220 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：approve_exec_v0_2_to_lead**。seed count 201/181作废、n_arms7/n_arm_seeds140/n_exec_seeds201/程序化、headroom .14841667 CI[.10382916,.19300417]、H_max18.91778<C_H20 无 clipping、DR gap0、learner 合同、六比较/Holm/δ/CI/等价/失败/停止/边界均核验通过；仅 nested count 读取、H 接近上限断言、final pilot 为非阻塞执行备注。仅批准 S3b 执行（机制账/compute-only/0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性。

**一句话：v0.2 已把 seed count 修为 201（env1+head20+fb20+eval20+arms140），n_arms7/n_arm_seeds140/n_exec_seeds201/程序化/seed_block_counts 落 schema，181 作废；headroom .14841667 CI[.10382916,.19300417]、H_max18.91778<C_H20 无 clipping、DR gap0、learner 合同、六比较/边界保持——判 approve_exec_v0_2_to_lead（仅 M3-S3b 候选 learner 比较执行：机制账/compute-only/0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

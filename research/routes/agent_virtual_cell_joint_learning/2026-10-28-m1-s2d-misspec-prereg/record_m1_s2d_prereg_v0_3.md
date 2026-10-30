# record_m1_s2d_prereg_v0_3.md —— R204-M1-S2D.2 修订预注册记录（T3 避开 M2 Stage3；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-203（R204-M1-S2D.2）· 日期 2026-10-28
只写 `research/2026-10-28-m1-s2d-misspec-prereg/` 下 v0.3 文件与 `tmp/`；**未改 v0.1/v0.2/S2c/H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D**；**未训练 C-MDN/未运行候选规划/未报效果/未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① T3 避开 M2 Stage3 | ✅ T3 改为 **20262141–20262160**（20）；T1 20262041–60、T2 20262061–80 不变；60 cells/R20；**20262100 不再使用**；旧 T3 20262081–20262100 作废 |
| ② forbidden 补全 | ✅ M1 Stage1/C208 20261112–13；M1 v0.2 20261201–03；M2 Stage2 20261200–39；M1 Stage2 exec 20261300–49；M3 Stage2 20261400–99；M3 20261500–99；M3 Stage3 20261600–90；H1b 20261800–49；S2c 20261900–59；M2 Stage3 20262100–39；`forbidden_old_seeds_count=533`；**overlap_with_forbidden=[]、cell_blocks_disjoint=true** |
| ③ 保持 | ✅ 60 cells/R20；schema 五字段；T2 valid=4093（nominal 4096、不谎报）；headroom 值/CI；目标 θ'；候选仅源训练/目标禁用训练调参；六比较/Holm6/δ=.05/单侧下尾/raw-paired/T2T3 不合并/主成功仅 T1/等价审计；headroom seeds 20262011–30/data 20262031/eval 20262032；两跑/caps/schema/11 失败/停止/边界；不训练/不执行候选 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~17:40 | 读 task-203 并 claim；读 M1-S2D.1-C1 复核/挑战、v0.2 产物、M1 Stage2 exec seed 清单 |
| ~17:43 | 复制 v0.2→v0.3 脚本；patch：T3 block 20262141–60；forbidden ranges 补全；overlap/disjoint 重算；schema/output 同步 |
| ~17:46 | 运行成功：T3 20262141–60、60 cells/20 per target、forbidden count 533、overlap=[]、disjoint=true；headroom 值不变；两跑 JSON/schema 逐字节一致 |
| ~17:52 | 写 PROBLEM/DESIGN/report/record/usage v0.3；标 completed + send_message |

## 2. 实现与披露

1. **仅预注册修订**：不训练/不运行候选；headroom 值保留；只改 T3 seed 块/forbidden/重叠检查/文档。
2. **T3 重划**：20262141–20262160（20）；T1/T2 不变；每 target R=20、总 60；20262100 不再使用；M2 Stage3 保留区 20262100–39 不解除。
3. **forbidden 补全**：ranges 见 PROBLEM/JSON；去重计数 533；`overlap_with_forbidden` 用 data/eval + 全部执行 cells 对全集重算=[]；`cell_blocks_disjoint=true`。
4. **schema/JSON**：R_execution_per_target=20、n_targets=3、n_cells=60、cluster=replicate、CI_method 95% t(df=19)；`forbidden_ranges`/count；T2 valid=4093（nominal 4096）note。
5. **headroom（未变）**：T1 .51107412 CI[.46843293,.55371531]；T2 .56758207 CI[.56039835,.57476580]；T3 .39007047 CI[.38530525,.39483569]；均≥.10 → executable；未重设环境。
6. **确定性**：`headroom_design_m1_s2d_v0_3.json`（`B4C99ADD…`）两跑逐字节一致；JSON 无 telemetry；wall≈5.1–5.9 s 仅 usage/报告。
7. **边界**：机制账 only；未训练 C-MDN/未运行候选/未读真实数据；不改旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 执行 cells：T1 20262041–60、T2 20262061–80、**T3 20262141–60**；每 target R=20、共 60；20262100 不再使用。
- forbidden ranges 10 组（M1 Stage1/M1 v0.2/M2 Stage2/M1 Stage2 exec/M3 Stage2/M3/M3 Stage3/H1b/S2c/M2 Stage3）；去重 533；overlap=[]；cell_blocks_disjoint=true。
- schema/JSON 五字段保持；T2 valid_eval_rows=4093 冻结（T1/T3=4096；nominal 4096），不谎报。
- headroom（未变）：T1 .51107412、T2 .56758207、T3 .39007047，均≥.10；executable；未重设。
- 六比较/Holm/δ=.05/raw-paired/目标分层/等价审计；headroom seeds 20262011–30、data 20262031/eval 20262032；两跑/caps/schema/11 失败/停止。
- 无 C-MDN/无候选规划/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2D_v0_3.md` | `33EE4312969D34832AA657DB009D67965F243B17E11B15E8D0281240BB73A444` |
| `DESIGN_M1_S2D_v0_3.md` | `58E26FB0A181529CED49CC46253BC0CC0A32A28AF2050EF511C53A4E9A186FA9` |
| `headroom_design_m1_s2d_v0_3.py` | `34B9243630930DE75BB7FC6A8A131D67F3B876181111E9AE40920230142323A3` |
| `headroom_design_m1_s2d_v0_3.json` | `B4C99ADD968F8C8173C56C726FD77E3382AA74F6EA7418715E2A132AA286BED7` |
| `schema_m1_s2d_v0_3.json` | `5C6D95D9B596F73BEC0AFAA567FE7DB528A23F4CCFD1FBC4D812D52CE920D94D` |
| report/record/usage | 见 `usage_m1_s2d_prereg_v0_3.json` |
| v0.1/v0.2 只读（未改） | v0.2 PROBLEM `25114A56…`、DESIGN `1676FD5E…`、script `CA56B472…`、JSON `B2095AEF…`、schema `A9D0D197…` |

## 5. 缺口与下一步

- **S2d 尚未执行**；本文件仅预注册修订（T3 块/forbidden 补全）。
- 执行前：轻量复核 + Lead 批准 + 重核环境/headroom/每 target R=20/forbidden/两跑/schema/失败模板 + 最终实现 pilot 冻结；不改旧判定。
- 机制账 only；不训练 C-MDN/不运行候选/不报效果；不晋升代码/不改旧判定/不恢复停止实验。

# record_m1_stage2_prep_v0_2 —— R204-M1-S2.1 三项必改执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者。
**任务：R204-M1-S2.1（reward 有界性/唯一 Pθ 生成器/Stage2 近似方法与容差；设计，不运行效果）。** 只写 `research/2026-10-28-m1-stage2-prep/` v0.2 文件与 tmp/；未改 v0.1/M1 预注册/Stage1/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；未运行效果/训练/真实数据/湿实验；0 wells；Stage2/3 未执行。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-165、M1-STAGE2-PREP-C1（challenge）、v0.1 prep/plan、M1 Stage1 C208 |
| — | 新建 v0.2 工作：先写 `stage2_m1_schema_v0_2.json`（reward/Pθ/C-MDN/H1–H3/G/失败/caps） |
| — | 写 `stage2_m1_plan_v0_2.py`：reward 边界、生成器形状、截断质量、seed、Sinkhorn、内存单测；pilot 计时 |
| — | 修正 truncation mass 的标量尺度/权重括号；canonical 通过 `all_pass=True` |
| — | 两独立进程 result JSON 逐字节 `73B8C025…99C1527`；写 PROBLEM/DESIGN/report/record/usage |

## 1. 三项必改

1. **reward 有界性**：Y 冻结 compact box [-2,2]^4；Pθ 截断 GMM；`r=w^T y−λ||y||²`，w=[.4,.3,.2,.1]，λ=.2；**r_max=.375、r_min=−5.2**；target Q 归一化有限；G1/H3 前提成立；不 clip/不把无界核当有界。
2. **Pθ 唯一生成器**：唯一 3 分量截断 GMM（对角协方差、条件异方差；无 Student-t 选项）；参数形状/seed/σ/h(X)/截断/Z/quadrature/train/eval 全部写死；H1–H3 同一生成器。
3. **Stage2 候选/近似**：C-MDN（K=3、hidden 128、NLL/Adam 设置、采样规划、复杂度）；H1 d/N 子采样+TV 容差表；H2 Sinkhorn ε/迭代/收敛；H3 exact small-case oracle/TV 指标/容差；全部冻结。

## 2. 单测/规划结果

- reward 边界：min observed **−5.2**、max observed **.3663≤.375**；bounded PASS。
- 生成器形状 c(4,3,4)/M(4,3,4,64)/d(4,3,64) PASS；截断质量 finite/positive；seed 可复现；Sinkhorn 收敛；内存 cap PASS。
- H1/H2/H3 状态 `planned_not_run`；容差/ε/迭代/oracle 已冻结；**未执行比较/训练**。
- 两跑：`stage2_m1_plan_v0_2.json` 逐字节 `73B8C0251A42ED229D5B3BA6D48C367730FD6A284AB47E110E224D56399C1527`；timing 单独。
- pilot：1.35687e-03 s/rep；projected .013569 s；full wall .046166 s；caps 1800s/2h/8GB；0 wells。
- `all_pass=true`、`failure_category=null`；无 effect/gain。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `PROBLEM_M1_STAGE2_v0_2.md` | v0.2 形式/生成器/候选/容差/边界 |
| `DESIGN_M1_STAGE2_v0_2.md` | v0.2 执行设计（不运行） |
| `stage2_m1_plan_v0_2.py` | 规划/单测/计时；不跑效果 |
| `stage2_m1_plan_v0_2.json` | 规划结果（两跑一致；无 telemetry） |
| `stage2_m1_schema_v0_2.json` | schema/失败模板（先写） |
| `timing_m1_stage2_prep_v0_2.json` | canonical timing |
| `report_m1_stage2_prep_v0_2.md` | 报告 |
| `record_m1_stage2_prep_v0_2.md` | 本记录 |
| `usage_m1_stage2_prep_v0_2.json` | 命令/SHA/attestation，最后写出 |

## 4. 边界

- 不运行 Stage2/3/训练/真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX。
- **一步投影已撤**；B2 等价是 rename_maxent 证据，不写 M1 增量；M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据。
- Stage2 执行须另立预注册+独立挑战+Lead 批准；Stage3 需合格真实功能数据（当前 data_unavailable C203/C205）。

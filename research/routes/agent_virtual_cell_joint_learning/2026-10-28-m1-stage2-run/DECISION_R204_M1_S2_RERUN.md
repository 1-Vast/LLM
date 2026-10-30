# Lead 裁定：R204-M1 Stage2 本次执行无效（protocol_deviation），须按冻结尺度重跑

2026-10-28。事实：
- 冻结设计（DESIGN_M1_STAGE2_v0_2 line 23；PROBLEM_M1_STAGE2_v0_2 line 31/34）明写 Pθ 尺度：`c~N(0,.5²)`、`M~N(0,.1²)`、`d~N(0,.1²)`，以及 σ=.1+.4·sigmoid(dᵀx)。
- 本次执行（task-170）将尺度改为 `c~N(0,.05²)`、`M~N(0,.005²)`、`d~N(0,.05²)`（10× 缩小），并声称"冻结链只给形状未给抽样尺度"；与冻结文档不符。
- 因此该次运行的 `qualification_pass`、H1 16/16 TV、H2 收敛、H3 TV、G1–G6 与两跑一致（90DE7498…）**均不能作为证据**。

## 裁定
1. **本次运行登记为 `invalid_run: protocol_deviation`（C215）**；不得称 qualification_pass、不得引用其 H1/H2/H3/G 数字。
2. **不得以"结果好"为由 post-hoc 修改设计尺度**（违反预注册纪律）。
3. **批准重跑一次（corrected execution）**：必须严格使用冻结尺度 `c~N(0,.5²)`、`M~N(0,.1²)`、`d~N(0,.1²)`、σ 公式、同一 seeds（param/train/eval 20261301/02/03；H1/H2/H3/reps 与 exec prereg 相同）、同一 H1 容差与 N 顺序、同一 H2 ε/迭代/容差、同一 H3 small-case TV 阈值、同一 caps 1800s/2h/8GB/0 wells、同一两跑逐字节要求；**不得改容差/顺序/阈值/预设**。
4. 重跑必须：先核对冻结文档中的尺度（给出文件行锚）→ 实现 → 最终实现 pilot 实测（Pθ/C-MDN/H1–H3/Q_g GL64/H3 GL128）冻结 canonical → 主执行 → 两跑逐字节 → report/record 中**显式披露上次无效运行与偏离点**。
5. 若按冻结尺度重跑失败（H1 超容差→projection、H2 不收敛→projection、H3 TV>.05→projection、G1–G6 失败→对应类别），**按设计停止并把失败类别写入结果**；不得改尺度/阈值救结果。
6. 重跑仍仅机制账、compute-only、0 wells；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据。

## 执行角色
- 由独立实现者（endpoint-auditor）执行 corrected re-run；cellstate-auditor 的本次运行产物保留为无效运行记录，不删除、不改写。

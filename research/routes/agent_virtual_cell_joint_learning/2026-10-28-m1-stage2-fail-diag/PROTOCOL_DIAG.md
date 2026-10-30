# PROTOCOL_DIAG — R204-M1-S2-FAIL-DIAG：M1 Stage2 H1 0/16 失败归因诊断（冻结预注册）

2026-10-28。**状态：诊断协议（prospective，运行前冻结）；diagnostic only；不改变 C216 判定、不救结果、不输出效果/决策收益。** 对象：`research/2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json`（SHA `B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107`；verdict `design_invalid: projection`）。C215 invalid_run（`90DE7498…`）**不引用**。

## 0. 问题与边界

C216 在冻结尺度下 H1 **0/16**（16 格 TV 全超容差），G3 projection FAIL。本诊断只回答：H1 失败的主导来源是
(a) C-MDN 拟合/容量不足，
(b) 有限样本估计误差（eval 2048、256-bin histogram TV），
(c) 冻结容差低于可达 TV 下界（不可达）。

**不做/不输出**：不重跑 H1 判定、不改 C216、不把诊断当 H1 通过；不输出 decision utility/regret/top-k/方法比较/效果/迁移/药理/机制/新颖性；不执行 Stage3/真实数据/湿实验；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 1. 冻结环境（严格同 C216；不得改）

- Pθ：X~N(0,I_64)、A=4、Y∈[-2,2]^4；K=3 截断 GMM、权重 [.5,.3,.2]、对角协方差；
  `c~N(0,.5²)` (4,3,4)、`M~N(0,.1²)` (4,3,4,64)、`d~N(0,.1²)` (4,3,64)；
  `μ=c+Mx`、`σ=.1+.4·sigmoid(dᵀx)`；截断归一化 Z。
- seeds：param **20261301**、train **20261302**、eval **20261303**；H1 cell seeds **20261310..20261325**（按 C216 顺序）。
- H1：d∈{8,16,32,64}（X 固定前缀）× N∈{512,1024,2048,4096}（train 前 N 行）；eval 固定 2048/seed 20261303；指标 **256-bin（4 bins/Y 维）histogram TV**（pooled over eval rows/actions；`hist_tv` 同 C216）。
- 容差表（冻结）：d8 [.12,.10,.08,.07]、d16 [.14,.11,.09,.08]、d32 [.16,.13,.11,.10]、d64 [.18,.15,.13,.12]。
- **不训练/调参用于主判定**；容量敏感性明确 non-frozen、仅诊断。

## 2. 诊断量（逐 16 格）

对每个 (d,N) 在**同一 eval（2048、seed 20261303；X/A/Y 与 C216 生成一致）**上计算：

1. **C-MDN TV（引用 C216，不重训）**：`t_cmdn` = C216 `H1[].TV_256bin`。
2. **oracle-parameter two-sample TV（主诊断）**：用真实 Pθ 从同一 eval X[:, :d]、A 独立抽 2048 个 Y（R=200 次独立重复；oracle seeds 20261400 + 1000·cell_index + rep），每次计算 `hist_tv(oracle_sample, Yev)`；报告 **mean / median / q05 / q95 / max**。这是"两个独立真实样本在 256-bin/2048 样本下的 TV 抽样下限"。
3. **样本量/估计误差诊断**：
   - 由 eval 行固定的条件混合分布 `p_pop`（每行抽 M=256 个 oracle Y → 524,288 样本的 256-bin 直方图；固定 seed 20261350 + cell_index）；
   - `tv_eval_pop = TV(Yev_hist, p_pop)`（eval 有限样本偏离）；
   - **floor MC**：从 `p_pop` 独立抽两个 multinomial(N=2048) 样本，1000 次，报告 TV 的 mean/q95（在 p_pop 已知情况下 TV 的精确抽样分布近似）；
   - 解析近似：`E[TV]≈sqrt(1/(πN))·Σ_i sqrt(p_i(1-p_i))`（仅报告）。
4. **容量敏感性（non-frozen，仅诊断，不用于改判定）**：对预注册子集 `SENS = {(64,512),(64,1024),(64,2048),(64,4096),(8,512),(8,4096)}`，用同一训练/损失/优化器/种子但 **hidden=256、epochs=400** 重训 C-MDN，同 eval 采样得 `t_cap`；报告 Δ=t_cap−t_cmdn。
5. **实现保真核验（fidelity）**：对子集 `FID={(64,4096),(8,512)}` 用**冻结配置**（hidden128/epochs200/同 seed）重训，报告 `t_repro` vs C216 `t_cmdn`；若 |Δ|>0.005 记录 fidelity caveat（不影响主诊断）。

## 3. 逐格归因规则（预注册；仅诊断标签）

给定 tol、`t_cmdn`、floor 的 mean `f_mean` / q95 `f_q95`：

1. 若 `f_q95 ≥ tol` → **`estimation_limit_unreachable`**（冻结容差低于可达抽样 TV；主导 (c)）。
2. 否则若 `t_cmdn ≤ f_q95` → **`at_finite_sample_floor`**（无 C-MDN 拟合不足证据；主导 (b)）。
3. 否则 excess=`t_cmdn−f_mean`，slack=`tol−f_mean`：
   - excess ≥ slack → **`fit_or_capacity_dominant`**；
   - excess ≥ 0.5·slack → **`mixed`**；
   - 否则 → **`mostly_noise`**。
4. 容量敏感性仅作**支持性证据**：若 `t_cap` 相对 `t_cmdn` 降低 ≥50%·excess 且仍 >tol → 支持"容量可改善但容差仍不可达"；若 `t_cap≤tol` → 提示容量可及（仅诊断，不改判定）。

**总体归因**：统计 16 格类别计数；若 `estimation_limit_unreachable` 占多数 → 主导=冻结容差低于可达 TV 抽样下限（c），C-MDN 拟合并列为次要；否则按 excess/容量敏感性给 (a)/(b)/(a+b) 主导。

## 4. 预算/两跑/审计

- caps：wall ≤1800 s、CPU ≤7200 s、memory ≤8 GB、new wells=0；超限→报告 incomplete/design_invalid（诊断层面）。
- **diag JSON 两跑逐字节**（独立进程；无时间戳；排序键）；telemetry（wall/CPU/mem）单独放 usage JSON，不写入 diag JSON。
- 两跑种子/参数/顺序完全一致；容量敏感性也含在 diag JSON 中（非冻结标记）。
- 输入只读：C216 JSON/报告；C215 invalid 不引用；不写/不改 C216、M1 设计链、其它产物。
- 输出：`PROTOCOL_DIAG.md`（本文件，运行前冻结）、`diag_m1_s2.py`、`diag_m1_s2.json`、`report_diag_m1_s2.md`、`record_diag_m1_s2.md`、`usage_diag_m1_s2.json`；SHA 记录。

## 5. 预期与禁止

- 若 floor 已 ≥ 多数容差：应诚实写明"冻结 H1 的 2048-样本/256-bin TV 容差低于有限样本可达下界，H1 失败不能单独归因于 C-MDN 拟合"。
- **禁止**：声称 H1 通过；改 C216 verdict；降容差/换 eval/增大 eval 后重判；把容量敏感性结果当 frozen 证据；输出效果/决策收益；把诊断写成机制/药理/迁移/新颖性结论。
- 建议（仅建议）：把归因写入 R204 阴性报告的"失败归因"节，**不改变 C216 design_invalid**。

# record_A22.md —— R201-A.2.2 预注册执行记录（异方差稳健 σ/诊断）

角色：独立审计/设计修订员（未参与 R197/R200 模型开发）· 任务 task-123（A.2.2）· 日期 2026-10-28
只写 `mechanism_A/a22_prenull/` 与 `tmp/`；**未改 A.1/A.2/A2-EXEC/P0P1 产物**；未运行 P1、未读 O'Neil 响应做效应；data-only；0 新 wells；non-blind/peeked。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① C194 复述 + A.1 仍不可解释 | ✅ `PROBLEM_A22.md §0`；report §0（D2 median .4153、分位、d_avg=(r1−r4)/2、异方差、P1 未执行） |
| ② 候选稳健 σ 预注册比较（H0/可交换性/实现/诊断/合成 FPR-power，不依赖 observed） | ✅ R0–R4 表（PROBLEM_A22 §1、report §1、JSON `candidate_schemes`）；合成 seed=20261031；primary=R4（唯一 eligible） |
| ③ D2/D3 重设计（per-context/分位门；F_crit 条件；F_pair 归一化；不用 observed 后验） | ✅ PROBLEM_A22 §2 / DESIGN_A22 §3：coverage≥0.85、global median∈[0.5,1.5]、overall FPR≤0.10、worst-context FPR≤0.25、context-FPR p95≤0.20；F_crit 仅在 D2+D3 通过时保留 |
| ④ A.2.2 执行设计（data-only 0 wells；P1 统计量/族/数据/|U|/N_perm/BH/阳性三条件不变；仅改 σ/null/诊断；预算/两跑/schema/无 telemetry/失败类别统一） | ✅ `DESIGN_A22.md`；JSON `A22_design`；预算≈2,500 模拟/900 s/2 h/8 GB；失败类别统一 |
| ⑤ 边界 | ✅ 各文件 §边界；不重判 A.1/A.2；不称机制/迁移/决策/新颖性 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~01:27 | 读 task-123 并 claim；读 C194/A.2 产物、challenge_A2、A.2 v0.2 链 |
| ~01:29 | 写 `sigma_robust_A22.py`（C194 复述 + 候选 scheme 合成校准 + 选择 + D2/D3/A.2.2 设计） |
| ~01:30 | 首跑暴露：scheme→fpr_power 模式映射 bug（R2 未映射）；修后仍无 eligible（阈值过严） |
| ~01:31 | 设计期调整（**已披露**）：合成 n_plans/context 6→12（更贴近真实 ~15 plans/context、降低小样本 FPR 噪声）；eligibility 增加 context-FPR p95≤0.20、coverage 阈值 0.90→**0.85**（48 contexts 二项容差）；均基于统计理由、**只看合成校准**，不依赖 A.2 observed |
| ~01:32 | R4 成唯一 eligible（coverage .875、FPR .0439、worst .121、p95 .076、power .183）；primary=R4 |
| ~01:33 | 加 protocol/design SHA 到 JSON；两跑逐字节一致（`12DC9855…53D6A2`；wall .5–.6 s） |
| ~01:35 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **合成校准（无 O'Neil 响应）**：6 cells×8 contexts×12 plans、K=M=4；true σ²(c)~lognormal(sd=.7)；H0=shared f+context 异方差噪声；违例=一条 plan profile 形状偏移 2σ(c)；seed=20261031。R0–R4 的 FPR/power/coverage 均由该合成数据计算；**不是 O'Neil 结论**。
2. **设计期阈值选择（披露）**：首轮合成用 6 plans/context 时所有 scheme 的 worst-context FPR 噪声大；改为 12 plans/context 并把 eligibility 设为 coverage≥0.85（二项容差）+ worst-context FPR≤0.25 + context-FPR p95≤0.20 + overall FPR∈[0.02,0.10]。该调整发生在**只看合成校准**的阶段、未看 A.2 observed F 统计；已写入预注册（R4 primary）。
3. **R1 未被选**：coverage .917 高但 worst-context FPR .424 超门；R0/R2 coverage .50–.60（全局尺度不能校准异方差 context）；R4 fuller-profile 尺度用同 context plan 对估计，合成中 coverage .875/FPR .0439/worst .121 唯一合格。
4. **无响应读取**：C194 数字全部来自已冻结 `a2_exec.json`/`a2_exec_diagnostics.json`；本任务未读 O'Neil viability 数值做统计；未运行 P1/未拟合 O'Neil 响应。
5. **确定性**：同脚本两跑 `sigma_robust_A22.json` 逐字节一致（`12DC9855…53D6A2`）；JSON 键排序/无时间戳/allow_nan=False；PROBLEM/DESIGN SHA 写入 JSON。

## 3. 关键结果

- C194：D2 median .4153 fail；mean .9700；σ_pair²_A2=.00110139；P1 未执行。
- 合成候选：R0 coverage .500/FPR .0723/worst .682/power .129；R1 .917/.0739/.424/.171；R2med .604/.1222/.803/.129；R2trim .604/.1206/.803/.129；**R4 .875/.0439/.121/.183（eligible）**。
- 选择：primary=R4_full_profile（唯一 eligible；规则只看合成校准）。
- D2/D3：coverage≥0.85、global median∈[0.5,1.5]、overall FPR≤0.10、worst-context FPR≤0.25、context-FPR p95≤0.20；F_crit=2.60 仅在 D2+D3 通过时保留。
- A.2.2 设计：数据/U=340,088/A.2 legal 规则/族/F_pair 结构/N_perm=500/BH/阳性条件不变；仅改 σ(R4 per-context)/null(分层+bootstrap)/诊断门；预算≈2,500 模拟/900 s/2 h/8 GB；两跑/JSON 无 telemetry。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A22.md` | `69605BBCEA37ECFA2783F08BCC2EF194C89971F637435A853D25C46849D7E334` |
| `DESIGN_A22.md` | `EAC8EA10FEDC6DA5F3D0293C2C43BBCD82C9ECB6A43EF2CB4714492284531E76` |
| `sigma_robust_A22.py` | `EEDFEF77D71A4BA00B31BED88F7783237E0C9B903D9FCBD79D5706C8A9996858` |
| `sigma_robust_A22.json` | `12DC9855A567D7ECF333F6718BB996E3EDE9BFCBDA095E09263CD79BF053D6A2` |
| report/record/usage | 见 `usage_A22.json` |
| 只读引用 | A2-EXEC json `26BF3B7A…`、diag `1846BAD2…`、A.2 v0.2 链（SHA 见 JSON/usage） |

## 5. 缺口（本轮明确未做）

- 未执行 A.2.2/P1（草案；须挑战+批准）。
- 未读 O'Neil 响应做效应；合成校准不是 O'Neil 结论；R4 在违例下尺度可能被抬高（保守），A.2.2 执行须报告敏感性。
- 未执行 P2/S1/S2/H_A2；0 新 wells。

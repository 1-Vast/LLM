# record_N1_design_v0_4.md —— R203-N1.3 修正预注册执行记录（V4 独立验证；不运行效果比较）

角色：独立设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-137（R203-N1.3，机制账）· 日期 2026-10-28
只写 `research/2026-10-28-n1-synthetic-prereg/` 下 v0.4 文件与 `tmp/`；**未改 v0.1–v0.3 产物/A-B-D 线/R203-P1 产物**；未运行效果比较；未读 O'Neil 响应；0 wells/compute-only。

## 0. 要求与完成对照（N1.2-C1 3 必改）

| 必改 | 状态 |
|---|---|
| ① V4 独立验证 | ✅ **V4_MODEL_SPEC 运行前冻结**（spec SHA `A69B845D…`）；**独立 seed=20261062、200 组新样本 V4 PASS：503.0425/64.4214/[376.779,629.306]** → **gate mode=V4_independent（valid gate）**；首轮 FAIL −456.6、oracle +4147.6、filter 等权→soft-responsibility/weighted ridge(λ=1) 全披露；dev seed=20261061 的 306.16 明确标 post-hoc 诊断不作 gate；oracle gate（seed=20261063：4988.236/248.226/[4501.72,5474.75]）仅 fallback |
| ② 代码注释残留 | ✅ `generator_n1_v0_4.py` 无 359/288 残留（grep 确认）；full 摘要 143/600（rank140/nullity3）；129 仅出现在明确标注的 v0.1 历史算术上下文 |
| ③ PROBLEM/DESIGN 预注册正文披露 | ✅ PROBLEM §4/DESIGN §4 写入首轮 FAIL/oracle/filter 改动/post-hoc 性质/独立 PASS 数字；不再只写最终 PASS |
| ④ 其余冻结 | ✅ n_units=300/MDE .04798/n_req278；G1 .0488/.05187；G2 1.000；B1–B6/B2 审计；v0.4 final-implementation pilot .05622 s/rep、25.3 s main、.037 GB（逐方法 B1 .00376/B2 .00254/B3 .00251/B4 .03587/B5 .00038/B6 .00275/M .00841）；caps 1800 s/2 h/8 GB/0 wells；两跑/schema/失败类别/边界 |
| ⑤ 无法独立验证则 stop | ✅ 不适用：独立 V4 PASS；oracle fallback 亦 PASS，未触发 stop |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~10:45 | 读 task-137 并 claim；读 N1.2-C1 复核；复制 v0.3→v0.4 脚本 |
| ~10:47 | 修 v0.4 脚本：路径、V4_MODEL_SPEC 冻结、run_v4 独立 seed 参数、run_oracle_v4、独立验证/门选择、pilot 重跑冻结、注释残留修复；syntax 修一处 status 块 |
| ~10:49 | 独立/开发/oracle V4 运行：dev 306.16（post-hoc）、**independent 503.04/64.42/[376.78,629.31] PASS**、oracle 4988.24/248.23/[4501.72,5474.75] PASS；canonical v0.4 pilot 生成（.05622/25.3/.037，B2 审计 PASS） |
| ~10:51 | 写 PROBLEM/DESIGN v0.4（披露首轮 FAIL/oracle/模型改动；独立验证 gate；代码残留修复） |
| ~10:53 | 主脚本两跑：`generator_n1_v0_4.json` 及 `V4_validation_v0_4.json` 逐字节一致（10.7/11.0 s） |
| ~10:57 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **V4 独立性**：最终 nonstatic filter 规格（soft responsibilities/weighted ridge λ=1、features 21+12、初始化 1/S、forward posterior、无调参）在运行前写入 `V4_MODEL_SPEC` 并计算 SHA；独立验证使用 **seed=20261062**（不同 RNG 流、200 组新样本），未使用开发 seed 20261061；开发结果 306.16 仅作 post-hoc 诊断。**无同 seed post-hoc PASS 作 gate、无迭代到通过**。
2. **首轮 FAIL 披露**：初始等权 filter 的 V4 FAIL（mean −456.6）与 oracle +4147.6 均写入 PROBLEM/DESIGN/JSON/V4_validation；模型改动被视为 post-hoc 事件，独立验证才作 gate。
3. **代码注释修复**：v0.4 脚本内无 359/288；full 参数化 143/600（h 2-basis 72）与 compact 107/312 一致；129 仅在 v0.1 历史算术明示。
4. **pilot**：用最终实现重跑真实 generator+7 方法（含 B2），生成 v0.4 canonical telemetry；结果 JSON 只含 snapshot 数值 + B2 审计，无逐时 telemetry；两跑一致。
5. **无效果比较**：V4/oracle 为 pre-effect 校准；未比较方法效果、未报告 regret/mis-selection；未读 O'Neil 响应；未用 A/B 资源。
6. **确定性**：结果 JSON 与 V4_validation 两跑逐字节一致；JSON 键排序/无时间戳；文档 SHA 写入 JSON。

## 3. 关键结果（与 report 一致）

- V4：dev post-hoc 306.1577/65.4612/[177.856,434.459]（不作 gate）；**independent seed=20261062：503.0425/64.4214/[376.779,629.306] PASS → gate**；oracle fallback：4988.236/248.226/[4501.72,5474.75] PASS。
- full 12-pair：params 143/obs 600/rank 140/nullity 3（参数 gauge 3）；compact 107/312/95/12；函数空间 compact 129/full 255（仅历史/冗余说明）。
- n_units=300；MDE80=.04798；n_req278；G1 .0488/.05187 PASS；G2 1.000；pilot .05622 s/rep、25.3 s main、.037 GB；B2 审计 PASS。
- 结果 JSON SHA `35E41136…`；V4_validation SHA `254BEBAB…`；timing `A4C7E0F6…`。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_4.md` | `5C513D9461FAEDBD3372463A4FDD1868C927EB4850BC0CDEB7643FF6FA0649A` |
| `DESIGN_N1_v0_4.md` | `94BAB8052EF4864BD745986326F4869D9054C2935794FEDAD8733733B57C029C` |
| `generator_n1_v0_4.py` | `AA5D454A82366BF3B7FC9E7F67FAA3499098621FAD45B84804485550E6EDCC97` |
| `generator_n1_v0_4.json` | `35E41136E344AAF6C51A73B19418FF5CBEAD9460697BB8B1EE92F9E16D610263` |
| `V4_validation_v0_4.json` | `254BEBAB201AA8A0EA33AEA8A47BC7D37A99ADE1436319D159603061DC8E2ECF` |
| `timing_n1_pilot_v0_4.json` | `A4C7E0F675B0020B99A93CC022572B3E85F30A26E391493AF45FAA3C005586C7` |
| report/record/usage | 见 `usage_N1_design_v0_4.json` |
| v0.1–v0.3 只读 | v0.3 SHA 见 v0.3 usage（未改） |

## 5. 缺口与下一步

- **未运行 N1 效果比较**（V4 为 pre-effect 校准；无效果指标）；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准。
- 执行前须以最终实现重跑 pilot 并冻结预算（本轮已用最终实现重跑并冻结 v0.4 canonical telemetry）。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验。

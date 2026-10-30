# R204 阶段综合（2026-10-28）：合成/机制账部分收口；真实数据仍为硬瓶颈

## 1. 本轮目标与判据回顾
R204 主线：Agent 主动学出可复用药理控制模型；三机制 M2（首选，任务驱动主动辨识群体功能算子）、M1（第二主线，可执行生成式规划）、M3（支撑，决策反馈信用）。全部以独立功能决策效用/后悔、可靠性、跨任务迁移为最终判据；先机制账/合成资格，再真实数据。

## 2. 已收口（机制账/合成证据；均不称药理/真实决策/迁移/机制/新颖性）

| 机制 | 证据 | 结论 |
|---|---|---|
| **M2** | Stage1 受控真值 PASS（C206：full K 75/75、mixed 75/0 条件性、same-U 3/3、gauge、闭合/非闭合、partial support 50/75）；Stage2/3 设计已接受（不执行） | 形式化/可辨识/闭合边界在**合成设定**成立；真实多时间功能数据 data_unavailable |
| **M1** | Stage1 合成检查 PASS 但 **B2 max-entropy 与候选 π* 解析等价 → 一步投影主算法主张撤回**（C208）；Stage2 高维近似设计接受；纠正重跑 H1 0/16 → `design_invalid: projection`（C216）；失败归因诊断：**主导 estimation_limit_unreachable（16/16 oracle 抽样 floor q95≥冻结容差）**、次要 C-MDN excess（C217） | **M1 无算法主张成立**；一步投影非创新；高维近似在冻结判据下不可判（判据本身低于 oracle floor），不可单独归因于方法；若要使 H1 可判定需另立预注册（增大 eval N/多 seed/更少 bins）+Lead |
| **M3** | Stage1 诊断 PASS（C209：19 checks；DR gap0/clip bias −.0264/root −.5626/rank1/ratios 1.217/1.167）；Stage2 合成分配诊断 PASS（C213：60/60 per-arm）；Stage3 固定反馈学习比较 **`no_increment`**（C218：candidate vs standard DR-TMLE mean ΔR +.0100、CI [−.0096,.0296]、Holm p 1.0） | M3 合成线收口：Stage1/Stage2 通过诊断，Stage3 **未显示优于标准 DR/TMLE**；不推广为标准方法无效；真实确认需另立预注册+挑战+Lead+合格数据 |
| **N1** | 受控合成测试 `no_increment`（C207；Lead 独立复算 mean .0060516455、CI [.003284,.008819] 一致） | 仅 own primary 判定；不推广 |

## 3. 数据侧（唯一硬瓶颈）
- 公开数据路线已多次有界检索+下载核验：C203（AZ 导出覆盖）、C205（获取性 partial）、C210（公开代码无 mapping/功能数值）、C211（下载+本地复算；readiness=`same_platform_structural_only/dev_only`）、C212（多时间群体数据 not_qualified）、C214（功能时间进程 not_qualified）。
- **可用但仅 dev_only**：AZ/GDSC 同平台结构/描述（68,710 单元/84,055 matrix/4,398≥2/301 exact-18/161 6×3；代理键 cell/drug/dose/plate/cmatrix/QC-date/SCAN）。
- **仍缺（真实阶段 data_unavailable）**：独立培养/板重复、官方 6 occasion/per-barcode 18 映射、正交功能 numeric（caspase/PARP/western/regrowth/live imaging）、记录 π/随机化、跨背景留出、独立功能决策收益。
- **精确测量规格**见 `2026-10-28-data-readiness/DECISION_R204_DATA_READINESS.md`；不写"只能新湿实验/不存在"：mapping 可由作者补充，真实功能确认需新测量。

## 4. 边界与纪律（保持）
- 无药理/真实决策/迁移/机制/新颖性主张；无代码晋升；不改旧判定/门槛；不恢复已停止实验；技术重复≠独立培养；6,282 仅 Fisher-z 参考；不拼 ΔEMAX。
- 阴性结果≠不存在；未运行/资格失败≠科学失败；不合并阴性；预注册先于效应；冻结判据不得事后改。

## 5. 下一步（需要用户决定）
1) **数据路径**：授权/协助发起 AZ DATA1 P0/P1 请求（公开联系方式；不伪造联系人/不绕许可）；或提供其它合格真实功能资源/湿实验预算；或
2) **收束路径**：接受当前"机制账阶段收束"——M2/M3 合成证据 + M1 阴性/判据不可达归因 + 数据测量规格；把真实决策收益/迁移留待数据到位再启动；
3) 可选：若要使 M1 H1 可判定，另立预注册（增大 eval N/多 seed/更少 bins）并走独立挑战+Lead 批准（仅机制账）。

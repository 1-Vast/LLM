独立首评（仅据所附材料，不新增实证、不改动任何已冻结设定）

一、先列最邻近历史失败/文献（排除项）
- PTV‑1/ProteinTalks 双核回放：ppODE 劣于最强常规预测；轨迹通路与分子/功能反馈无增益；LLM 编辑 A1=A2=A0；STOP_THIS_TASK_CONFIGURATION，联合主张 NOT_TESTED。
- Beat AML G1：低秩状态模型未过净一轮门槛（候选−ridge +0.098，严格下界 −0.005）；保留 exploit‑first 反馈+ridge，停止低秩分支。
- feedback_propagation：ridge+反馈优于结构先验，但类比修复不优于 ridge/kNN；价值贪婪闭环劣于固定 A‑optimal。
- functional_dynamics_gate：继承更新器 0.230026、全重训 0.229256、强直接 0.179086；50/50 混合与等预算搜索精确复现继承更新器；常见起点更新增益 0.073564 低于 0.10 绝对边际。
- STACK conditional：全历史 MAE 0.219490 vs live‑only 0.227450，增益 3.50%，未过 0.05/10% 有用性门。
- az_paid_reference_gate：效应坐标 MAE .077667654 劣于全直接 .066206799；U .048597279 劣于无 mono 直接 .098467776；两主门失败。
- rsi_later_task_literature：通用反馈→诊断→局部修订→记忆/继承、可编辑改进器、共同起点测试均 NO‑GO 作为新颖性主张；无新核心被清除。
- 其他：procedure_inheritance（112 移植全拒，内容迁移未测）、self_repair（仅普通漂移修复）、innovation_validation（合成流未过边际）、observable_state（Agent 不优于枚举器）、implementation_identifiability（ASSET_BLOCKED）。

二、机制（至多一个，具真实反馈菜单）
候选：固定线性两创新反馈假设——用 Middle 2h 分子状态误差预测 High 剂量状态修复，用 Middle 24h 功能残差提供跨剂量校正信息；在固定 M、固定线性读出下展开为普通全历史直接/联合创新预测器。菜单为已认证 TG‑GATEs 24h L/M/H 样本键与已购 2h RNA 观测，反馈为实际测得的 Middle RNA 与 Middle 24h DNA/LDH 功能值；不新增购买、不改剂量菜单。若线性展开与普通联合预测器等价，则不主张新算子，仅检验有限样本跨块限制是否有用。

三、具体应用
在 tggates_feedback_headroom 冻结的 45 proxy 标签/39 块、24 source/7 development/8 later 分配上，DNA 为主线性目标、LDH 为完整次要目标；仅数值转换 source/dev，later 全剂量密封。先比较预筛常数、Middle copy/offset、化学邻居迁移、强同 M ridge/kernel 直接基线；仅当 dev DNA‑MAE >0.02（数值空间存在）才进入 RNA 成本。

四、可获得数据与缺口
可获得：已认证 24 source/7 dev 标签、45 proxy 结构/39 依赖组、2h RNA 已购观测（结果未出，不作已有数据）、固定 MAS5 单阵列预处理通过源基准（54,675 有限探针、16.484s、633MiB 采样峰值）。缺口：RNA 实验无结果；proxy 身份不证明样本材料/供体独立；无 development High‑state 精度；2h 采样不证明 2h 结果可用性或相对 24h 功能测定的成本优势；六批人肝细胞不构成供体独立任务；MAS5 为相对表达非绝对 RNA/细胞。

五、可证伪创新主张
主张：在固定 M、同信息、同预算下，上述跨块状态/功能误差限制相对普通全历史直接/联合预测器、普通重训/CL、简单混合、等预算搜索，在 dev 上产生 >0.02 绝对 DNA‑MAE 改善；若线性展开精确等价，则主张退为“有限样本限制有用”，且必须被上述对照组复现性检验。不以模块命名替代等价论证。

六、最小成功/停止条件
最小成功：dev DNA‑MAE 基线 >0.02 且候选相对最强普通对照的改善下界 >0（预注册区间），LDH 次要方向一致；所有对照组同标签/历史/预算。最小停止：dev 基线 ≤0.02（完美预测也无法 >0.02，停此配置）；或候选未优于最强普通对照；或任一完整性/校准门失败→NO_DEVELOPMENT_SIGNAL。不设临床阈值、不设未验证样本量；later14/AZ413reserve 不开；RNA 结果未出前不预测、不改阈值、不重跑停止分支。

七、world/agent/继承/联合/C4 的独立归因（逐一）
- world：以 no‑observed‑query‑Middle‑RNA 家族为对照（注意其仍保留 f_M/f_H、b_M/b_H、g(预测 Middle/High RNA) 与对预测 Middle 状态的残差，故非 world‑free）；候选优于它只支持本模型族内的部署测量信息，不单独证明世界模型贡献。
- agent：当前无合格 agent 对比；本轮不应测试 agent 扩展（无先验正信号、菜单受 47/45 标签限制），不得写成完成。
- 继承：需在共同 solver/历史/权限/搜索预算下做 old/new improver 交换；本轮不测试，不写成完成。
- 联合：world×policy 交互需 2×2 分开测量；本轮不测试。
- C4：需共同起点下新改进器产生更有效后续改进；本轮不测试；不得以本 pilot 替代。
- 本轮可指出不应测试 agent/继承/联合/C4 任一项，但均不得记为完成；pilot 仅完成“测量 Middle RNA 是否改善功能预测”与“状态校正路线是否改变功能误差”两诊断，且后者受选择暴露限制。

八、必须正面比较的强同信息对照
全历史直接/联合预测器（线性精确展开即等价）、普通重训/CL、简单预测空间算术平均（无搜索）、等预算搜索、ridge/kernel 强直接、no‑observed‑RNA 家族、四基因先验+共享 alpha 同 nuisance bank。不以通用逼近能力或模块名替代实际等价论证；若精确等价，须明示并只保留有限样本限制主张。

九、结论
无可信新核心被清除；pilot 结果未出，不预测、不捏造。允许结论：本轮无可信候选，仅保留上述可证伪的普通经验筛选与独立归因边界。总体目标 ACTIVE/NOT_ACHIEVED。
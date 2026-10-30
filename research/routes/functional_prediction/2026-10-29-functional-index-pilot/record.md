# 普通常见功能索引：原件资格与单一必要前提试验

2026-10-29。前轮分类progress：四类型多目标索引的建设例/未知对应成本已fresh挑战，733个登记ID共同三药支持已独立派生复算，新核L2M/AFA-ITD方法且Terra实际整理；尚无新增算法或独立药物收益。父预算../2026-10-29-assay-relation-identification/budget_usage.json，保留历史36研究单元、19次Harness。本次goal续接新增最多3研究单元，累计cap39；不是重置旧线或开放式再搜索。

本轮三单元：①对已授权AZ/GDSC007原ZIP，修复已知GDSC007/GDSC_007成员名匹配的工程阻点，完成身份/剂量原件重建和观测来源条件核读，保留旧冻结失败原字节；②若资格足以支持明确限定的导出响应开发比较，先冻一个H、强对手、完整算法、数据/角色、预算/指标/停止门，后执行一次最小试验；③独立实现/关键结果核查与科学判定。否则不强行运行，完成具体资格缺口及下一可访问证据。每候选最多2次实质修订，不因阴性换菜单/模型/门槛救回。

基础输入仍为普通公开cell×drug×physical-dose×functional-y，不要求组学、影像、谱系、稀有配对靶点或新wetlab。使用现有 `tmp/extq1/gsdc_well_stats.zip`，SHA256 e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259；唯一成员combo_well_stats_GDSC_007_05May22.csv。矩阵ID/name仅在资格需要时使用既有tmp/extq1/gdsc-007_matrix_results.csv，不读组合结果。原输入其他成员不展开。protected .env、PRISM24Q2、CTRP、sealed/confirmation不打开。

源资格阶段先0响应语义读取：仅PROJECT_ID、MASTER_CELL_ID、CELL_LINE_ID（若原header有）、lib1/lib2的drug_id、drug(ref)、conc；元数据以原字符串/Decimal处理。CSV整行会暂时分词，禁止解析/保留y/yhat/IC50/AUC/组合抑制等结果值。先核ZIP身份再检查原header/成员；精确成员名/central-directory信息不是反复碰响应调试。核元数据重复、选定ref、共同支持并与上一主派生比对，但不重做化学支持/MMP映射。测量语义来源优先既有glossary/正式paper与公开处理脚本，只静态阅读，不执行作者代码。

原件资格不隐含全部条件通过。允许的经验试验上限是“同筛导出坐标的回放条件信息”，不是独立培养真值/真实省孔/靶点作用机制。若读取lib1_y/lib2_y，须在单一H及实现/切分冻结后；禁止yhat、IC50、AUC、组合结果作为输入/标签。导出相同键冲突、不明单位/方向或无法保持角色隔离则停止，不平均/clip/挑有利ref。既往前20000行已开发暴露，新的模型未见划分也不冒充生物独立确认。

CPU每次≤120s、wall≤180s、采样RSS≤1GiB、总CPU≤360s；原件metadata主重建与一个独立实现可各一次，效果主运行与独立实现各最多一次。≤20MB输出，metadata/key集合超限则摘要保留必要可重放身份。无大模型训练、GPU、安装、作者代码执行。新实验仅research/与maestro环境；0src/tools修改/晋升、0提交/发布/物理移动删除。

公开访问共享最多8逻辑动作、2主题query，direct成功body≤10,000,000B、单件≤5,000,000B、30s、同host≥1.1s，0自动重试/redirect。优先复用129源library；只补当前判断的源协议或最近操作先例，非穷尽检索。native web字节unknown时不宣称全网络硬字节cap已验证。root保留4动作，资格来源worker最多4；其余agent不联网。

root负责机制/唯一H与最终判断；source/metadata worker只处理资格不选效应方法/指标；fresh挑战在H冻结后启动，独立实现须与主稿隔离到结果落盘。实际requested/effective遥测分开。nativeTerra本轮可用，阶段整理实际请求后记录，6luna仅已授权备选。

Harness最多新增DS028一次，历史19、累计cap20：新隔离workspace/DSH_HOME，180s/2048输出tokens/≤12000B stdin、tools disabled、0重试/换后端；USD0.025为声明，硬美元cap和实付unknown。只派固定source字段/单位/规则复算与格式台账，不选科学H/指标/方法。每小步先查正式新任务；有则优先，无则按明确输入/规则/预算续source-well/time/control/repeats/mask/模型预测vs实测；局部歧义记录并继续获准独立字段，无额度不虚称后台。DS007/008和DS024历史断点保留不重跑。

停止门：原始资格不足则park其对应主张，不将工程/数据问题记效应阴性；预定H未达就停止该具体优势线，不扫参数。任何阳性只决定后续研究与独立功能确认，不达成总目标。总体ACTIVE_NOT_ACHIEVED。

本轮收口：3单元均已消耗，累计39/39，网络0/8、Harness20/20。H_FI主/独立各一次均training_precondition_absent，开发H未评价；110模型选择和27候选关键数值由root封存后比较一致，0bootstrap。独立worker在结果交付后native额度错误，不重跑数据；root完成比较。native gpt-6.1-terra/high内容审阅实际已交，预算链接随后由root补核。DS028字段限定采纳，协调三文档已更新；完整事实及适用范围以report.md、冻结协议及原receipt为准。下一轮须保留本停止结论和8052坐标开发暴露状态，不能将当前203ID重命名确认集。

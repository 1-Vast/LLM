**提案：TG 24h LDH 肝毒性分诊的“同尺度双assay discordance-gated feedback”**  
不作疗效、donor、lot、同细胞轨迹或原始LDH泄漏推断；只做条件对齐的相对生存均值/排序。

- **药物发现决策**：对TG三剂量化合物，在固定预算下决定哪些化合物值得进入/降级到后续24h LDH细胞毒性确认；输出held-out化合物在Low/Mid/High的24h LDH(%)排序。  
- **exact allowed fields**：`condition_id`、compound label、`dose_level(L/M/H)`、归一化剂量+单位（仅47药三剂量子集）、`time(2/8/24h)`、`assay_type(DNA/LDH)`、`relative_survival_percent`、missing flag；若开RNA，仅用TG同condition现有human hepatocyte expression（gene/probe ID + expression）并先冻结QC。禁用donor/lot/sample映射、原始LDH泄漏量、birth/death拆分、面板外剂量外推。  
- **真实feedback bundle**：按预注册condition列表打开/整理现有TG 24h LDH与配对DNA相对生存值，附missing flag；不假设新湿实验、不买新化合物。  
- **later-task单位**：held-out compound的3-dose 24h LDH向量；不是482个barcode任务，也不是独立研究任务。  

**主张**：在TG三剂量双assay化合物中，按“模型预测的24h DNA%与LDH%同尺度不一致度”选择LDH反馈条件，在等标签预算下能改善held-out化合物的24h LDH排序；但若不一致度只是剂量/时间/化合物噪声或assay噪声，则失败。  

**操作（≤12行）**  
1. 冻结47药三剂量双assay身份；主pilot取12个held-out化合物，其余反馈/备用，绝不按结果改split。  
2. 冻结RNA QC、特征和所有arms的same auxiliary RNA；无合格RNA则kill。  
3. world预测每个condition的24h DNA%与LDH%相对生存均值，并输出经compound/dose/time调整的DNA-LDH discordance。  
4. 固定反馈预算B（如30个24h LDH condition labels），每轮选discordance最高且在dose/compound分层内的condition。  
5. 揭示所选LDH值，更新联合两输出模型与discordance校准；不要用LDH解释为死亡比例。  
6. 重复至B；对held-out 12化合物预测3-dose LDH并排序。  
7. 主终点：化合物级mean Spearman；副终点：top-3低LDH召回。预注册实用门：ΔSpearman≥0.10且top-3不降；小N仅描述。  
8. 公平arms：same-RNA strong direct、ordinary refit、CL replay、AL(uncertainty/diversity/random)、simple dose/time mixture、等预算program-search。  
9. 分离继承：policy-only同模型换选择器；model-only同选择器换更新；full两者都换。  
10. C4：old/new improver同base、同history前缀、同later solver、同budget common-start；12 later task仅探索，正式C4需≥24 held-out compound tasks（72 dose-conditions）；TG最多给单panel低功效C4，不承诺迁移。  

**最便宜kill**：metadata gate：若<10个held-out化合物同时有3剂量、24h DNA+LDH和2h RNA，直接停。数值pilot前冻结split、B、主/副终点、实用门和停条件；打开最小12化合物后，用ordinary strong direct检验discordance对LDH残差无增量关联，或选择器退化为高剂量/缺失模式，即kill。合成数据只作代码检查，不称生物证据。  

**必要模块/成本/反对解释**：模块仅需元数据harmonizer、RNA QC、联合两assay模型、discordance选择器、反馈更新器、C4 runner；成本为数据整理与少量计算，无新湿实验，购买数据/湿确认另按实际合同。最强反对解释：discordance只是剂量/时间/化合物或assay噪声，等价于普通uncertainty AL/stratified sampling；用metadata-only selector、dose/time分层、simple mixture和等预算search控制。创新性未建立；本提案不是上一轮residual-kernel改名，不传播早RNA响应几何，只用同尺度双assay不一致作为反馈采集门。
# STACK 资格阶段的真实双向质询

2026-10-22。双方独立稿均先落盘；随后互读并通过实际消息发问/答复。反方的 `INDEPENDENT.md` 不回写。反方无 GET、workbook response/QC 值访问、fit 或新 API。peer 原始来源叙述与 root 后提供 metadata 均明确列为稿后暴露；不假称所有数据全球封存。

## 反方向 functional_auditor 提问，对方实际答复

**Q1：library screen 的原文是否真的映射每 compound 独立 run/三重复？三 screen 是否仅两个 cell lines/三个 backgrounds，而非 1,833 个独立科研任务？**

答：同意有限同screen/背景转移的边界。P055 “Except where noted … three biological replicates” 是正面作者复制声明，且未明确排除大screen；因此不能反向把大screen称为已证单run。它仍未给逐screen/compound的 run映射，待实际schema资格。双方共同保留“positive but unmapped”，不用不确定性抹去原文正面声明，也不由正面声明虚构每文件/run对应。

**Q2：时序>10-fold censor、起始荧光/seed QC、未来LFmax/LED选择不同。仅processed/QC后数据是否仍可做同mask、明示条件cohort的预测？**

答：同意。未来LFmax/LED选择只能支持已选cohort的条件表现，不能给 prospective 全库定义资格。processed不是自动不可分析，所有信息臂使用相同选择，报缺失与筛选边界。

**Q3：LF用running maxSG且存在doublepositive。LD胜Lonly预测futureLF是否最多为markerLF信息？future red gate是否需D0/Dend与同信息direct/ordinarykinetic？**

答：没有一手理由反对该窄gate。futureLF阳性最多支持markerLF可预测性；future red需上述对照，red也不等于true viability。

## 审计方向反方提问，反方实际答复

**A：是否保留P055为positive未映射证据，不把single-run当事实？**

答：同意。独立稿只拒绝自动分配三重复给大screen；若被读成single-run已证，此处明确否定该推断。真正 observation bundle 可能是各孔、各run或已平均的序列，需身份map决定。

**B：若预注册应用是markerLF triage，是否可不强制red为唯一主终点？**

答：可以。这是不同且合法的应用，须禁止把含D的markerLF成功替代D对later-red/viability增量。保留截至prefix的 current/running-max LF persistence、D0/end snapshot、普通同信息direct/kinetic等强对照。futureLFmax/AUC仅为标签，不能做prefix feature或筛cohort；若AUC包含已观测prefix，必须明确已知部分或评分未来部分，避免把已知量重构包装成未来预测能力。LF测量定义合格也不免除真实信息实验。

**C：Full目前只有Compound/phenotypic_Marker与row1，库有CAS/Plate/Position/SMILES。exactname、salt/CAS冲突、多marker行、无runid最低规则是什么？**

答：保存全部原始label，先做raw compound×marker×time 的身份计数/重复/空值；library exact-name join报告0/1/many，Catalog/CAS/SMILES冲突，不静默fuzzy或salt merge。same-label重复行都在同split；不能用row order推rep配对，也不能把库plate/position直接当各screen原runplate。

library join歧义不必使整个数据不可用：可停用歧义metadata join，保留raw-label grouped的同screen预测，不因缺SMILES/plate删除响应样本。red/SG pairing若多对多不明，不得假装well级latent state；只有原始身份支持且数值前定义固定label-level聚合时，才可做明确限定的label层预测，承认rep/pairedness未知。无runid限制run外推，不自动禁止这种开发。

审计方随后再实际挑战两点，反方明确接受：如果同一chemical的别名跨split无法排除，只能称 **unseen recorded label**，不能称unseen chemical/scaffold；只对已认证aliases/CAS作保守分组，不无证据merge。预注册聚合不解决身份实证缺口；“原始身份支持”必须是schema/primary确能识别同一处理条件组，才可预定该组均值estimand。否则joint marker配对资格是partial，停止该joint LD问题，不能由固定聚合制造well/rep对应或增加n；只有另有已定且资格足够的单通道问题才可继续。双方不把“事前写了规则”当成身份缺口被证据解决。

**D：eight/九名单、U2OS七/缺逗号、common lethal80/79是否全部保留不手修？**

答：接受，不从叙述手修mask或发明差异解释，暂无反例推翻。source methods与实际文件的membership应以后续身份/QC provenance明确核对，不按性能挑版本。

## root稿后metadata与反方给root的具体挑战

独立稿完成后，root报告exact v1四个objects acquired、manifest/source-derived route、size/SHA256匹配；本反方未重复GET，也未自行打开raw workbook验证该获取声明。所给结构为 Full A1=Compound、B1=phenotypic_Marker、A2=(-)-Blebbistatin/B2=SG+；dimensions为T98GDMSO A1:BA1924、TMZ A1:BI1921、U2OS A1:DS1921；库字段包含Catalog/Compound/Plate/Position/CAS/Target/SMILES。QC sheet仅知Time(h)标签，未读其成员/decisions。root将保留原始Full panel，不以QC后选择替换。

反方已实际向root提出：dimensions不证明条件/rep数；A/B仅是候选label，须time/channel header、每compound×marker的series个数、空/重复以及library0/1/manyjoin；不由库字段存在推raw可唯一join，不由roworder赋plate/run。Full的未选panel是更诚实的开发入口，但后续数值合法性/missingness规则仍需单独冻结。缺plate/well/run可以限制claim并继续label层开发，而不虚构独立性。

## 共识、未决与决定

共识：**允许诚实同screen、compound-group开发与少量背景转移；无当前world/agent/inheritance/RSI实测或新算法。** 多compound/multi-drug与少数cell/background是有应用价值的覆盖，不是同数独立科研任务。三个screen不提供广泛RSI泛化；可把将来的共同初始状态、固定反馈/预算、disjoint compound-cohort序列当窄开发诊断，仍需冻结improver与改进后improver的后续改进效果直接比较，不能用普通多训练数据/一次选超参代替。

未决：exact raw marker/time列含义；Compound到库的唯一映射及duplicates/salts；screen内well/plate/run/rep含义；raw与processed/censor/QC关系；不同screen共同chemical与source重复；实际response数值域和完整性尚未打开。任何一项缺失都应限制具体claim，不凭空变成全局不可分析要求。

阶段决定：继续root已授权的exact identity/time/header资格，不打开response/QC decisions来挑cohort。资格足够后再预注册具体endpoint、prefix/target、same-information direct/ordinaryworld baselines、budget/阈值/停止条件。availability或双方一致本身不能晋升核心创新；若只有partial来源资格，报告partial，不写信息阴性。

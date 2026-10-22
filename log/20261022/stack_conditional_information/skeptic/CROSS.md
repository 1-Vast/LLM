# 真实交叉与数值前 V2/V3 设计审查

2026-10-22。双方 V1 独立稿先落盘再读peer稿/实际消息问答。无raw/XLSX、assay、QC值、fit、GET或provider call；不修改root protocol、原V1独立稿或sourcephase。当前只审设计，实施/white-list tests/freeze仍需另审。

## 支持方发问，反方实际回答

**1. ≥95% complete case可能选择性排除强反应，仅分报coverage并声明conditional estimand是否足够，还是实质阻塞？**

答：足够支持限定实验，无实质阻塞；95%不是MAR或全库utility保证，也未见任何实际missing pattern。分母必须是冻结全部role×screen named rows，另报L-prefix-valid/dual-valid及D额外失效，所有信息臂共同mask。live-only也条件于D成功取得，不能称无需D采集即可覆盖全库。每组all-three资格和test最终不救子集规则需明确，source无效目标只触发qualification，不当channel negative。

**2. 相同L特征、14configs、history含snapshots，若仅称finite-model预测价值还有什么必须改的公平性问题？**

答：同监督、scaler、metric和14候选是合理有限家族信息比较，无需强行补一切可能模型。V1 ratio可提供L的额外非线性坐标、不同dim会改变bias，故不是条件互信息证明。每screen只需正值、overall才双阈值，bootstrap描述条件entry而非生物/run误差。root随后自选V2简化解决ratio问题，非数值驱动。

## 反方发问，支持方实际回答

**A. 应用称triage，但MAE不测top-k/hit enrichment/湿实验预算，是否只能叫forecast surrogate？**

答：明确接受；阳性仅同源marker-density forecast surrogate，不能称节省实验/成像、发现新hit或实际triage决策收益。

**B. 胜D0-only与D24-only仍可能联合D0+D24足够；是否收窄为超越任一单snapshot，不称五个interior或全七点必要？**

答：明确接受。支持方恰在收到反方这问前独立发过同一自查；双方均接受可仅收窄措辞，不强求第五臂。若真检验interior value，才需joint endpoints对照。root在零响应阶段另选择加第五臂，两份V1稿与原先“收窄即可”的判断保留，不假称最初已有第五臂。

支持方另接受coverage分母、L/dual eligibility分报、finite-pipeline解释与per-screen门槛；双方无剩余设计级blocking concern，仍以实现/资格检查为条件。

## root 的 V2：反方实际评价

数值前末段changelog明确采用全部named-row denominator、每member全三context的group min、L/dual/target/complete counts、train/validation资格失败fit前停、test失败不得缩cohort救结果。反方接受。这些改变让mask代价与分母可审计，没有要求all-complete、不插补sourcecensor、未改后期目标或成功幅度。

root进一步删除所有D/Lratio与D slope，四臂一度为onlynothing/z0/z24/all7z、dims19/20/20/26。反方接受prospective simplification：只改变dead-channel坐标，消除额外非线性L表示混杂；slope本由序列可推，不是丢失观测信息。仍有有限模型dim/bias限制，不能由这个简化升级严格conditional-MI。未改变split/endpoint/14config grid/threshold，V1维度留在历史稿。

## root 的 V3：反方实际评价

root选择新增 `dead_endpoints=[z0,z24]`，五臂dims19/20/20/21/26；每臂14trials+1refit，合计70trials+5refits=75fits。primary仍dead_history vs live_only；history进一步要对D0、D24、joint endpoints各过原.05+10%overall和三screen各正的门槛。

反方接受V3：这是有具体更简单解释的低成本falsification control，pre-response理由明确，不是test上增加候选臂追阳性，也不是让history获取更多标签或调参预算。四臂收窄会更小，但root为了实际interior集合增量选择第五臂合理，无需用户再授权。预算描述必须更新为五臂75fits，不能沿用56+4。

若history胜joint endpoints，只支持注册forecasters下intermediate观测集合的额外可用价值；仍不证明每个interior各自必要、时间顺序被模型使用、真实death events/损伤被辨识或causal D→L。没有permutation/leave-one-timeout实验，也无需本gate装作有这些证据。

root所报sample weights `N/(3*n_screen)` 在每次实际拟合集三screen均有数据时正确：每screen总权重N/3、全样本sum=N；refit必须依自己的train+validation集合重算。五臂+两anchor的全部test predictions/abstentions保存并SHA256记录后才授权test L72，是正确顺序。SHA记录支持文件顺序/完整性审计，不是raw XML被加密封存，代码仍需实际whitelist测试。

## 当前裁决

V3设计 **CONDITIONAL_GO**。资格阈值和预定point gates可做所声明的有限来源预测判断；interval必须完整保留且不声称独立复现。world/refit/mixture/search/agent/CL/AL/inheritance/RSI均NOT_TESTED；阳性不提前晋升，阴性只停止精确已注册设置。等root提交实际实现/测试与freeze后做运行前核对，本交叉不代替代码审计或未见数值的域资格。

## 与 functional_auditor 的追加真实双向交叉

审计方先封存其V1独立稿再读反方稿，实际发三问。反方回答：V3仅支持注册forecasters下intermediate SG坐标集合价值，不是各点/顺序/因果/CMI；all-member×three-context完整group数是资格guard，**不是额外整组删除mask**，各screen依其共同prefix+target有效rows拟合/评分；若点门槛通过但95%group-bootstrap interval跨零，原样报告point-pass与固定test-cluster重采样方向不稳，不追加CI门槛、不称显著/稳健复现。bootstrap不含selection/refit/训练/缺失机制/生物不确定性。

反方实际反问三点，审计方逐项接受：

1. 必须用synthetic case验证row eligibility与group guard分离：collision pair某member在某context无效，group不计full-contributing，但其他合法member/context rows照常进入panel；不得为凑阈值删除整组或放宽guard。
2. cluster-bootstrap要抽367 frozen test groups的multiplicity，让每个原合法row随group multiplicity重复，再重新算每screen rowmean及macro；不能先算各group均值再等group平均，否则双member group/不完整contexts会改变原estimand。
3. train/validation资格不够fit前停；test资格失败只有DATA_QUALIFICATION_INSUFFICIENT/no useful verdict，不从残余子集MAE救结果。若保留任何可算诊断误差，必须diagnostic-only、不能留下可误用qualified pass字段；最清楚是不生成usefulpass。

上述实际回复已由审计方另存其CROSS并告root作为实施检查。没有新assay暴露或额外model/metric搜索。

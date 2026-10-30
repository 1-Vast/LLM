# 方向4与5的本轮最小尝试

方向4：读取本地真实 Mix-seq h5ad 的 obs 元数据（未读表达矩阵），得到182,875个细胞。确实存在6h、24h及两个混合时间标签，因此不能以“本地没有任何时间数据”为失败理由。失败在更强主张所需的证据：没有核验到竞争机制及独立机制参照，混合时间标签不能任意拆成各细胞准确时间，破坏性快照不能直接当同细胞轨迹。额外执行端点不可辨识数值反例：两个单调路径端点相同而内点差0.079577。该检查支持门槛合理性，不证明生物学动态模型不可行。

方向5：新下载BATCHIE官方PAIR_SCREEN（不是读取旧封存结果），核对manifest MD5成功。先写PROTOCOL.md，再运行Viability读出分析；此前用于查看schema的预览输出剔除了Viability，但包含Raw count，未用于筛选或调整阈值，因此整个结果仍只算探索性分析。固定细胞、iteration、伙伴、双方剂量统计真实可替换的设计结构，再按预设0.1生存比例容差和非平凡约束检查。139,764行中135,936行QC通过；共有1,012,615个匹配比较机会，其中93,104个通过描述性非平凡均值约束。不是独立样本数或有效等效关系数量。每个条件最多2个文件、4个well；按至少3个重复文件且可确认独立性的门槛，没有可执行等效检验。未硬凑TOST或用差异不显著冒充等效。若要降低到技术重复推断，应另立新协议并限制结论，而非改写本次预设。

复跑（从D:/MAESTRO）：`.venv/Scripts/python.exe research/eight_directions_20261026/evidence_audit/run_audit.py`

结果：direction4_results.json、direction5_results.json；逐时间设计计数：mixseq_time_census.csv、mixseq_design_census.csv；来源manifest：zenodo_manifest.json。原始PAIR_SCREEN保存在raw/，SHA256在结果中。没有修改现有研究或打开旧sealed/holdout响应。

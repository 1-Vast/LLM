MAESTRO低成本干实验数据流模拟（2026-10-07）

这是可复跑的探索性分析包，不是已验证的收益改进模型。
数据基线：1-Vast/LLM commit 96f264312b9296053c1202611b2496e2deb630ac。
未修改或提交上游仓库，没有调用LLM API，没有购买或运行湿实验。

运行：
  python -m pip install -r requirements.txt
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_simulation.py
  python build_report.py
Windows可直接运行python命令；线程环境变量为可选的性能设置。

run_simulation.py：公开菜单白名单、结果隔离、预算及轮次检查、真实数据回放。
PROTOCOL.json：第一次模拟之前固定的实验设置；属于已曝光数据的开发约定，并非确认性预注册。
FEATURE_CONTRACT.json：下一项公开功能数据实验的输入、来源、排除、对照和验收规范；尚未运行。
public_data_requests.csv：65个现有药物的公开数据获取队列。名字搜索只是候选解析，不代表身份已认证或数据已下载。
data/predictions.csv.gz：上游保存的4519候选及预测、重复标签；推断策略只取得显式PUBLIC白名单。
data/raw_pairs.csv.gz：上游4424条直接原孔重复端点；反馈只读取已购raw_y1。
data/targets.csv、drug.csv：上游药物及目标注释；方向和测定依据缺失仍按缺失处理。
results/summary.csv：汇总。
results/campaigns.csv：每细胞、方向、策略、置乱种子的结果。
results/fold_choices.csv：14折的训练选择。
results/sensitivity_grid.csv：事后敏感性全网格，不将最佳点当确认结果。
results/purchase_traces.jsonl：逐次购买、轮次、释放观测及累计支出。索引对应源表的细胞/方向分组原始行顺序；manifest固定源文件。
results/diagnostics.json：10项合成边界/泄漏检查、合成正负控制、描述性细胞bootstrap。
results/manifest.json：输入、脚本和协议哈希。

主要结论：静态混合92次；留一细胞预算选择92次；同采购三轮静态92次；药物反馈88次；靶点反馈89次。
扩大首筛不能直接兑现闲置预算。简单传播早期响应未改善原确认合同。不要部署这些新反馈头。

范围：14条已曝光细胞，28组并非独立。多数重复共享培养来源。主确认标签为发布的拟合call，可能有共享拟合结构。
原始端点归一化未重新构建；缺失95个候选仍保留在全菜单；已购原孔值缺失时不参与反馈，不能填成零。三轮的等待成本未换算为金钱。
反馈参考均值只用其他13条细胞的原孔R1，仍为暴露数据上的开发模型；没有111历史细胞原始训练表，未冒充重训该模型。
Python对象隔离是代码合同，不是安全沙箱。合成实验只证明流程可利用人为存在的信息，不能证明生物学增益。
bootstrap条件于现有模型及药物菜单，未做训练重拟合及药物对多重聚类；区间不是确认性检验。

来源（数据版权及许可归原发布者，重用需遵守其条款）：
https://github.com/1-Vast/LLM/tree/96f264312b9296053c1202611b2496e2deb630ac/research/astra/repeat_signal_20261005
https://doi.org/10.1038/s41586-022-04437-2
https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services
https://clue.io/releases/data-dashboard
https://depmap.org/portal/data_page/

from pathlib import Path
import importlib.metadata
import json
import html
import urllib.parse
import zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parent
R=ROOT/'results'
labels={
 'frozen_prior_control_score':'静态先验混合，固定70%',
 'LOCO_static_budget':'留一细胞选择首筛比例',
 'LOCO_score_and_budget':'留一细胞选择得分与比例',
 'three_round_static':'三轮静态，相同探针采购',
 'three_round_drug_feedback':'三轮反馈，共享药物核',
 'three_round_target_feedback':'三轮反馈，共享靶点核',
 'three_round_shuffled_feedback':'三轮置乱反馈，10种映射平均'}
summary=pd.read_csv(R/'summary.csv')
table=summary[summary.arm.isin(labels)].copy()
table['arm']=table.arm.map(labels)
table=table[['arm','confirmations','spent','rounds']]
table.columns=['策略','累计确认数','测量积分','轮数']
grid=pd.read_csv(R/'sensitivity_grid.csv')
grid=grid[grid.column.eq('prior_control_score')].groupby('fraction')[['confirmations','spent']].sum().reset_index()
grid.columns=['首筛比例','累计确认数','实际测量积分']
diag=json.loads((R/'diagnostics.json').read_text())
drugs=pd.read_csv(ROOT/'data/drug.csv',dtype={'drug_id':str})
requests=[]
for x in drugs.itertuples():
 requests.append({'drug_id':x.drug_id,'name':x.name,'entity_type':'mixture_requires_explicit_mapping' if '|' in x.drug_id else 'single_compound',
  'chembl_name_search_url':'https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q='+urllib.parse.quote(x.name),
  'identity_status':'unresolved_do_not_take_first_search_hit','gdsc_lookup':'Use registered DRUG_ID and source release; preserve assay units',
  'lincs_lookup':'Resolve compound ID then check cell, concentration, duration and signature QC metadata before download'})
pd.DataFrame(requests).to_csv(ROOT/'public_data_requests.csv',index=False)
(ROOT/'requirements.txt').write_text('\n'.join(f'{p}=={importlib.metadata.version(p)}' for p in ['numpy','pandas'])+'\n')
readme='''MAESTRO低成本干实验数据流模拟（2026-10-07）

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
'''
(ROOT/'README.txt').write_text(readme)
report='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MAESTRO低成本干实验方案与模拟结果</title><style>
body{font-family:system-ui,"Noto Sans CJK SC","Microsoft YaHei",sans-serif;color:#17232e;background:#fff;line-height:1.7;max-width:1000px;margin:auto;padding:32px 22px}h1{font-size:28px}h2{font-size:21px;margin-top:32px}h3{font-size:17px}p,li{font-size:15px}table{border-collapse:collapse;width:100%;font-size:14px;margin:18px 0}th,td{padding:10px;border-bottom:1px solid #d9e0e5;text-align:left}th{background:#eef3f6}code,pre{background:#f2f5f7;padding:3px 6px;overflow:auto}a{color:#006f91}.notice{border-left:4px solid #167f98;padding-left:16px}.small{font-size:13px;color:#536471}.flow{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.node{padding:10px;background:#edf4f6}.panel{overflow-x:auto} @media print{body{padding:0}h2{break-after:avoid}table{break-inside:avoid}}</style>
<h1>MAESTRO低成本干实验：数据流、实跑结果与下一项解决实验</h1>
<p class="small">2026-10-07 · 固定源码96f2643 · 4519候选 / 14细胞 / 28回放 · 无GPU、无模型API、无新湿实验</p>
<p class="notice"><b>建议执行的方案：</b>以已有公开实测数据构建盲化回放环境，保留强静态混合为回退，仅检验新增的剂量、药理和扰动功能信息。先证明信息改善首轮边界选择，再检验信息采购策略。当前实跑未找到可部署的增益，不把模拟流程成功等同于生物学成功。</p>
<h2>1. 已执行的数据流</h2>
<div class="flow"><span class="node">公开身份与冻结得分</span><span>→</span><span class="node">候选选择</span><span>→</span><span class="node">预算与轮次检查</span><span>→</span><span class="node">仅释放已购R1</span><span>→</span><span class="node">更新未测候选</span><span>→</span><span class="node">合格候选购买R2</span></div>
<p>目标R2仅由评价器在确认采购后释放。早期更新读取直接原孔raw_y1，避免用发布拟合y1作为新增反馈；终局仍保留原发布阳性call，因此没有伪称重建了事件独立的确认标签。整个目标菜单来自已有重复完整子集，属于回顾性评价。</p>
<p>两轮：一次筛选、一次确认。三轮：4个先导候选、剩余筛选、确认。先导候选从静态前列菜单按药物组件多样性选出；所有三轮对照购买相同先导候选，且先导费用从同一预算扣除。单位测量积分不等于真实货币成本，轮次也不代表认证的小时数。</p>
<h2>2. 真实历史回放结果</h2><div class="panel">'''+table.to_html(index=False,border=0,float_format=lambda x:f'{x:g}')+'''</div>
<p>静态混合的92次确认、762测量与上游保存结果完全一致。四个生物信息臂的确认集合亦逐组复现。三轮药物反馈相对同采购静态对照在1条细胞改善、5条变差、8条不变；靶点反馈为1条改善、4条变差、9条不变。原孔参考值只使用当前目标之外13条细胞，新增头不使用目标未购结果。</p>
<p>反馈核采用有向共享药物或靶点集合相似度。用4个已购原孔响应相对外部参考的残差，经过正则化核更新，修正静态百分位分数；强度0.25、正则1在第一次运行前固定，没有在看到结果后追加调参。真实反馈优于部分置乱结果不能代替优于强静态策略。</p>
<h2>3. 预算敏感性与对上一轮判断的修正</h2><div class="panel">'''+grid.to_html(index=False,border=0,float_format=lambda x:f'{x:g}')+'''</div>
<p>915个总预算单位中153未用，并不自动表示可通过扩大首筛获益。80%和90%首筛比例挤压确认容量，实际确认下降。14折留一细胞开发选型均选择70%。这是已曝光数据上的内部开发验证，不能把它宣称为普遍最优分配。</p>
<h2>4. 下一项真正值得做的廉价信息实验</h2>
<table><tr><th>阶段</th><th>公开数据</th><th>形成的输入</th><th>防止重复旧路线</th></tr>
<tr><td>A：剂量支持</td><td>已登记Jaaks设计、GDSC单药及曲线记录</td><td>实际浓度相对效价范围、斜率、最大效应、测试上下界、时间匹配、外推状态</td><td>必须引入实际条件/响应形状，不能只重训同一IC50预训练头</td></tr>
<tr><td>B：药理实现依据</td><td>ChEMBL机制与测定记录</td><td>作用方向、靶点效价范围、实验类型、证据可信度、缺失标记</td><td>Ki/Kd/IC50分开；不推导未经测量的细胞占有率</td></tr>
<tr><td>C：公共扰动功能</td><td>LINCS/CLUE匹配签名</td><td>按药物、细胞、剂量、时间和QC限定的有符号通路响应</td><td>外部参考状态不冒充当前培养状态；跨细胞迁移单列</td></tr></table>
<p>先下载元数据并核验65个药物的实体映射和覆盖，不下载全量多组学。public_data_requests.csv已提供获取队列。对无数据候选保持静态回退；全菜单与有覆盖子集分别报告。按信息来源一次增加一层，不在小样本上同时堆多种模型。</p>
<p>推荐首个模型为带收缩的小条件残差排名器：静态先验 + 候选×背景×剂量条件修正，允许修正项为零。首筛比例和验证策略固定。对照包括仅设计条件、缺失标记、相同容量真实输入、条件内置乱。只有在边界换入/换出和终局确认上有增益，才继续下一层数据。</p>
<h2>5. 决策准入与工程接入</h2>
<ol><li>先以静态基线接通完整组件、角色、剂量、时间、候选哈希、全菜单预测引用和筛选—确认规则。</li>
<li>执行器强制预算及合法顺序，不能由LLM自律；独立重复、采购重提交和失败尝试使用不同身份。</li>
<li>现有14条线只作开发。外层按完整细胞分组，所有方向及重复同折；内层选择收缩。药物对留出与细胞留出分开。</li>
<li>真实新增信息须超过对应强静态对照和破坏性对照。只提高相关性、只胜随机、或收益来自预算变化，不能准入。</li>
<li>有可观测且可计价的补证菜单后，再比较确定性信息价值策略、智能体、世界模型及组合。当前没有运行LLM臂。</li></ol>
<h2>6. 本次验证与边界</h2>
<p>10项断言全部通过：目标结局污染不改变公开菜单与首批；R2污染不改变采购；超预算、负索引、小数索引、批内重复、无前置确认、截止轮筛选、重复采购均拒绝。另以200种合成正/负信息场景验证了流程对人为可用信息的响应，合成结果不作为生物学证据。</p>
<p>限制：14条细胞已多轮曝光；28个方向回放不是28个独立生物单位；多数重复共享培养来源；95候选缺原孔端点仍保留原菜单。未重新归一化大型原始强度文件，未重训111历史细胞模型，未跑全仓库pytest。区间仅为固定模型下按细胞bootstrap的描述性诊断，未处理全部跨细胞药物对依赖。</p>
<h2>7. 复跑与来源</h2><pre>python -m pip install -r requirements.txt
python run_simulation.py
python build_report.py</pre>
<p>模拟主脚本只依赖numpy/pandas；本次计算时间约'''+f'{diag["wall_seconds"]:.1f}'+'''秒，不含下载和报告生成。包内包含输入、协议、全部比较、逐购买日志与哈希。未来数据获取条目是待执行计划，不代表ChEMBL/LINCS已完成覆盖或验证。</p>
<ul><li><a href="https://github.com/1-Vast/LLM/tree/96f264312b9296053c1202611b2496e2deb630ac/research/astra/repeat_signal_20261005">固定版本研究数据</a></li>
<li><a href="https://doi.org/10.1038/s41586-022-04437-2">Jaaks et al., Nature 2022</a></li>
<li><a href="https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services">ChEMBL官方API文档</a></li>
<li><a href="https://clue.io/releases/data-dashboard">LINCS数据覆盖</a></li>
<li><a href="https://depmap.org/portal/data_page/">DepMap数据门户</a></li></ul></html>'''
(ROOT.parent/'maestro_drylab_report.html').write_text(report)
with zipfile.ZipFile(ROOT.parent/'maestro_drylab_solution.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(ROOT.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:
   z.write(p,Path('maestro_drylab_solution')/p.relative_to(ROOT))
 z.write(ROOT.parent/'maestro_drylab_report.html','maestro_drylab_solution/report.html')
print(json.dumps({'report':str(ROOT.parent/'maestro_drylab_report.html'),'package':str(ROOT.parent/'maestro_drylab_solution.zip'),'drug_requests':len(requests)},ensure_ascii=False))

"""One new evidence-conditioned proposal; never execute returned code."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/feedback_shift_mechanism/api'
PROMPT = '''你是独立科研方法设计者。请基于新实测证据提出最多一个值得最小证伪的简洁机制；没有就NONE。不能检索，别虚构引用。不是重跑已失败配置或给架构改名。
目标：药物发现中的虚拟细胞干预世界模型+自主研究agent，优先RSI，但当前先找有用且可继承的更新操作。允许常规数学组件，不要求全新基础算子；需要具体操作、科学假设或反馈/计算优势超出最接近普通方法。
新实测事实：2025真实序贯抗癌给药数据（10.1126/sciadv.adt1851, Zenodo14890340），FAC:一个MCF7三药campaign，32个方案汇总CV终点，gen0..3各8；OLA-IBET:单个PDX-derived类器官，两药27方案，gen0..2各9。输入只匿名seq+t0,t1原始时间代码（非直接小时），没有中途状态或独立patientID，CV是荧光衍生endpoint非cellcount，以上100保留。六个固定普通模型：mean、seq×duration ridge、fullregimen1NN，各G0冻结或累计gen<g重拟合。G1训练相同只sanity；真比较FACg2/3与OLAg2，25querymeans。无调参、G0scaler、未让querycv进predictor，先保存预测后评分，两独立审计通过。
FAC累计ridge MAE16.4435→6.55535，MSE319.668→48.7602。mean/NN两指标也改善。FACg2 NN MAE5.676优ridge6.067，g3mean6.309优ridge7.044。OLA累计ridge MAE8.87054→9.77315，MSE112.891→129.121；mean/NN加入历史也皆变差。冻结mean7.094最佳。不能由此断言生物漂移、measurementshift或covariateshift；更多历史同时增加labels和actioncoverage。这些query已暴露，只是开发证据，不能在本panel选择新window/mixture/超参救配置。
新读一手MetaComb2026 DOI10.3389/fgene.2026.1811927明确普通MAML source celllines initialization+fewshotpatient finetune；不是递归改进策略。已知普通参照应包括sameinfo direct predictor、union/refit、CL、AL、shrinkage/recency/modelselection、等总预算search。泛称'分离batch和biology'可被普通covariate/mixed-effect模型解释；加queryimportanceweights是常规weightedrefit，不能只改名。单control只能约束某些measurement变换，不要假设不可得groundtruth或同皿trajectories。全潜状态识别不是功能决策的必要前提。
请给：(1) <=8行具体操作/公式，清楚是F预测器、U更新器还是G改进策略；(2)它能修什么可观测错误、同信息普通对手具体为什么未必相同，若只是常规已知方法诚实说明；(3)最小可获得的数据/控制，哪些当前缺失；(4)一个非随机可手算反例或可证伪实验；(5)继承U共同起点比较与继承G同U同历史等预算后代效用的分别测试，不要求当前就具完整多代任务库；(6)成功与停止条件。一个方法家族已存在不自动否决，但严格操作等价或无新机制/贡献不能算创新。不要写泛架构或长清单。2500字以内。'''

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'PROMPT.md').exists()
    (OUT / 'PROMPT.md').write_text(PROMPT, encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    receipt = dict(started_utc=datetime.now(timezone.utc).isoformat(), logical_completion_requests=1,
                   prompt_sha256=hashlib.sha256(PROMPT.encode()).hexdigest(), thinking_enabled=False,
                   transport_attempts='NOT_EXPOSED_BY_CLIENT', monetary_cost='NOT_EXPOSED',
                   generated_code_executed=False)
    try:
        response = client.complete([dict(role='user', content=PROMPT)], temperature=.6,
                                   max_tokens=5000, thinking_enabled=False)
        (OUT / 'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as exc:
        receipt.update(status='FAILED_RETAINED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
    receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
    (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

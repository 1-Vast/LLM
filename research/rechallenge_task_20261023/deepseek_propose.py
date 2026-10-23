"""One evidence-grounded API proposal; generated code is never executed."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/rechallenge_task/api'

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    prompt = '''请基于以下已认证的新证据，独立提出最多一个简洁、可实现、可证伪的学习操作；若只剩普通方法请明确NONE。不是给架构命名或文献清单。你无检索工具，不得虚构论文或数据。
应用是历史依赖的再次给药功能响应预测，最终药物研究agent和RSI。2025真实TRAIL/TBQ实验（DOI10.1038/s44320-025-00150-0）的公开Gitlab固定版本包含experiment3/4，各AAAA（连续凋亡刺激）、ANAN（凋亡/坏死性凋亡交替）、Naive工作簿表。表头Measurement Time、Cell Density、Death Modality、Drug Input Time in Simulation、Death Time in Simulation、Measurement Time in Simulation。密度为固定染色的培养皿面积比例，各时点不同皿；模拟死亡时刻不是实测死亡。尚未读密度数值。论文已有一药敏感/耐受状态模型PSM1D，组合成PSM2D不重新拟合参数但用双药RMSE选拓扑；这本身不是新方法。未经新检验不能用目标选出的拓扑预测同目标。
另有单细胞FRET轨迹与morphology死亡，但header直接含Dying/Surviving标签、列顺序可能编码命运；全轨迹minimum归一化会给levels泄漏，差分可能消常数；无认证跨文件cell配对。原黑色素瘤4周CTG面板的周期规则总体好却在关键组输给持平；不要修这个暴露面板。原72h挑战表9history×4labels×12doses，但无独立culture/run认证；不能把72h后才出的反馈提前用于给药决定。
已排除的空泛候选：h+=Kresidual是普通filter；共享转移拟合+episode推断是systemID；低秩、正则、普通uncertainty acquisition、pairedcredit REINFORCE、语义缓存、保存参数、普通程序搜索都不能仅改名创新。常规方法家族允许，具体操作差异或反馈/计算优势须可说明；direct可表达不是自动否决。别用没有的数据当可实现机制。当前仅小数据可以做必要诊断，不要求已具备完整RSI多代资产。
请回答：一个具体操作(最多8行公式)，何种可观测误差让它值得测、如何以相同信息超过history直接模型/普通refit/filter/mixture、最小假设及可推翻反例、需要哪些尚未认证的数据、可继承U是什么以及为何不是theta/h。若没有独特操作直接NONE和精确理由。禁止把生物适应叫agent RSI。2500字以内。'''
    prompt_file = OUT / 'PROMPT.md'
    assert not prompt_file.exists(), 'Do not repeat an initiated logical request'
    prompt_file.write_text(prompt, encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    receipt = dict(started_utc=datetime.now(timezone.utc).isoformat(), logical_completion_requests=1,
                   transport_attempts='NOT_EXPOSED_BY_CLIENT', thinking_enabled=False,
                   prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), generated_code_executed=False)
    try:
        response = client.complete([dict(role='user', content=prompt)], temperature=.5,
                                   max_tokens=5000, thinking_enabled=False)
        (OUT / 'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error, 'code', None))
    receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
    (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

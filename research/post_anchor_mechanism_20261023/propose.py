"""Request a concrete new mechanism; no generated code execution."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings
OUT=ROOT/'log/20261023/post_anchor_mechanism/api'
PROMPT='''请作为计算生物学方法研究者，给至多一个具有明确可证伪操作的候选创新，或NONE。不要代码、不要编造文献/数据访问。没有检索能力的你只能提出假设，出处待核。目标仍是以干预细胞世界模型服务药物发现的科研agent及可继承研究程序，最终检验新旧改进器的下游效率，但当前缺的是先能独立超过强普通模型的共享限制。
新证据：官方EmeraldBay五日混池released growth score，36开发背景×44单药+固定Adagrasib/Galunisertib组合anchor→15查询条件7其他药物对。严格36LOCO/3inner source-only，15对15普通程序，全部选linear ridge lambda1。单药MSE.105082 vs sourcequerymean.239526(改善56.1%)；加anchor MSE.106043(恶化.914%)，组内剂量nominationregret.098798→.094100(改善4.76%)，pairMSE改善2/7，预定jointgate失败STOP。不得换anchor/子集/核/阈值重开，也不能据此断言anchor无信息(菜单不嵌套ignore-anchor)。16reserve不许开。全部是已知query组合跨context遮蔽，非独立湿实验、省钱或新组合。
旧证据/禁止重复：CDK中期组成小益，功能Abema排序恶化、Palbo联合留出不可估；Broad16line实测RNA→Chronos函数仅3.47%MSE且排序输geneprior；Norman73pair diagonal混合规律输ridge2.96%；Jaaks同target action substitution负；AZ paidmono特征输direct。sharedpotencyprofile=普通sameforwardMAP；supportmean gate=EB；capacityactivecut有不可辨识反例；控制序列Lie/梯度重组/观测噪声纠偏/普通OED/套元优化均已有具体等价操作，不要再包装它们。不要求新数学原语，允许普通组件的明确有限样本或总成本优势，但需具体结构与非任意数据假设。
强同信息对手必须包括：非线性episodic/direct supportquery、conditionalEB、普通sameforwardrefit/CL、simplemix、AL、同预算全程序搜索。不能把对手弱化成点预测/错噪声/无源经验。最终world/agent/继承/联合/G1G0须各自证据。只说部分可辨识、decisionaware、meta更新、反例记忆或可复用程序不是差异。
请在1500中文字符以内回答：1) 一个<=4行公式的具体限制/更新器与可观察输入；2) 它何以能留下超强普通对手的可测有限资源差异，最可能被什么精确普通对手吸收；3) 什么已知公开数据类型能测试且不需要查询实测RNA当免费输入，不假定数据事实；4) 一个最小真实diagnostic及停止条件，禁止只造toy equivalence；5) 如何接上可继承对象及G1/G0后代测试，哪个是当前未证假设。没有合理候选就NONE，并指出一个实质新可获得观测会如何改变下一步，别再列泛泛方向。'''
if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'RECEIPT.json'
    assert not path.exists()
    (OUT/'PROMPT.md').write_text(PROMPT,encoding='utf-8')
    receipt=dict(start=datetime.now(timezone.utc).isoformat(),logical_requests=1,
        thinking_enabled=False,prompt_sha256=hashlib.sha256((OUT/'PROMPT.md').read_bytes()).hexdigest(),
        transport_attempts='NOT_EXPOSED',generated_code_executed=False)
    path.write_text(json.dumps(receipt,indent=2))
    client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=180.))
    try:
        response=client.complete([dict(role='system',content='给出诚实的具体可证伪研究建议，不编造验证。'),
            dict(role='user',content=PROMPT)],temperature=.8,max_tokens=5000,thinking_enabled=False)
        (OUT/'PROPOSAL.md').write_text(response.content,encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED',model=response.model,finish_reason=response.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED',error_type=type(error).__name__,error_code=getattr(error,'code',None))
    finally:
        receipt.update(end=datetime.now(timezone.utc).isoformat(),provider_usage=client.provider_usage)
        path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))

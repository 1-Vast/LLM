"""Retained independent proposal or adversarial method request; never run output."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT=ROOT/'log/20261022/intervention_program_renewal'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n')


def main(mode):
    assert mode in ('mechanism','improver')
    folder=OUT/mode
    folder.mkdir(exist_ok=True)
    if (folder/'STARTED.json').exists():
        raise FileExistsError('single_logical_request_already_started')
    paths=[ROOT/'research/REPORT.md',ROOT/'log/20261022/stack_conditional_information/DECISION.md',
           ROOT/'src/virtual_cell/combination_world.py']
    common='''你是有创造力但诚实的科研方法设计者。目标是虚拟细胞世界模型驱动的药物发现研究智能体，并让其改进策略在后续任务中更会改进。请认真推导最多一个最强可执行机制，不是写大架构或资格清单。你没有搜索工具；未知数据/参考文献必须标未核验，不编造DOI或声称下载过。
明确区分新操作、新可识别性质、新实证现象与已有技术组合。已知组件可以产生可发表的非平凡新机制/性质/实际收益，不能因通用NN或穷举搜索能表示它就宣布等价；但若普通算法可在同信息、同反馈、同预算下逐步产生相同结果，就必须承认并寻找真正差异。若无新数学也可以提具体可证伪的结构性新经验主张，不能仅改名字。
已停：时间扭曲=普通系统辨识；history MDL分裂=同信息MDL树；Gaussian gene残差写回=kernel conditioning；显式haplotype mutation-selection普通且边际频率不能定haplotype；ADCC终点factorization是普通rank-one；semigroup一致性已有DeepOSG；固定类型选择界是普通missing-outcome feasibility；已知查询成本不是学习问题；turningpoint普通分段回归。HTS001 scalar inheritance=.2300MAE，fullrefit=.2293、direct=.1791，mixture/search精确匹配inherited，EB新颖性停。HCT116目标有负值，未得模型结果。最新STACK fullD比强L-only仅+3.5%，joint endpoints后仅1.44%，用途门未过，不得改该已暴露test救关。
Hyperagents/AIDE²/SpecRSI/MetaShare已有task/meta程序编辑、失败/成功经验检索、后继improvement credit和共同起点对照。普通AL、学习优化器、校准、模型集成、更新权重/选超参不能只改名当RSI。RSI须检验psi1相对冻结psi0在共同theta起点、同后续反馈机会下使后续改进更有效，而非只使theta更好。
不要强迫所有世界模型具备washout/RNA/单细胞谱系，真实静态药物功能screen也可支持一个先行机制测试。源内合法留出可作有限范围证据，不必每个探索都先有新wetlab/独立run；但独立生物/跨任务泛化不得伪造。当前任务是产生能尽快反证的实质机制，不是把缺独立run作为万能NONE。
请给：(1)具体药物功能应用、最小真实可得数据/动作/反馈/后续任务结构，核验缺口；(2)最多10行公式/伪码，明确一处技术实质；(3)最接近普通方法/已知文献何处可精确归约，何处只是表达能力相同；(4)最便宜决定性实验及成功/停止门槛；(5)同信息强direct、普通重训/CL、AL、simplemix、等预算程序搜索各如何公平；(6)world/agent/继承/联合/psi1>psi0各自可证伪预测。若严肃推导仍NONE，必须给具体归约或可检查缺口，不以模板谨慎替代研究。输出≤4000中文字符。'''
    focus={'mechanism':'本次优先从干预条件下的细胞状态→真实药物功能响应出发，提出一个对普通世界拟合/直接预测有实质差异的最小可学习更新或实验算子。优先真实可获得数据，不局限于历史三个源。',
           'improver':'本次优先研究改进策略psi本身的更新机制：它如何利用细胞世界模型的实验反例，把将来改进所需计算/标注变少；提出具体算子及不被固定搜索、普通meta-learning直接解释的可证伪新性质。先行代数/经验gate可以分开，但toy不能充药物效果。'}[mode]
    prompt=common+'\n\n'+focus
    for path,cap in zip(paths,(18000,14000,9000)):
        prompt+='\n\n'+str(path.relative_to(ROOT))+':\n'+path.read_text(encoding='utf-8')[:cap]
    with (folder/'PROMPT.md').open('x',encoding='utf-8') as stream:
        stream.write(prompt)
    write(folder/'STARTED.json',{'utc':datetime.now(timezone.utc).isoformat(),
          'mode':mode,'logical_requests':1,'code_sha256':sha(Path(__file__)),
          'prompt_sha256':sha(folder/'PROMPT.md'),'inputs':{str(p):sha(p) for p in paths}})
    receipt={'logical_requests':1,'transport_attempts':'NOT_EXPOSED_BY_MAINTAINED_CLIENT',
             'thinking_enabled':True,'generated_code_executed':False,'biological_fit':False}
    client=None
    try:
        client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=180))
        response=client.complete([{'role':'system','content':'你是独立科研方法设计者。具体推导、区分假设与证据，不编造引用。'},
            {'role':'user','content':prompt}],temperature=.7,max_tokens=12000,thinking_enabled=True)
        with (folder/'RESPONSE.md').open('x',encoding='utf-8') as stream:
            stream.write(response.content)
        receipt.update(status='RESPONSE_RETAINED',model=response.model,finish_reason=response.finish_reason,
                       content_characters=len(response.content),response_sha256=sha(folder/'RESPONSE.md'))
    except Exception as exc:
        receipt.update(status='FAILED_RETAINED',error_type=type(exc).__name__,error_code=getattr(exc,'code',None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(),
            usage=client.provider_usage if client is not None else {},
            reasoning_text='NOT_EXPOSED_BY_MAINTAINED_CLIENT')
        write(folder/'RECEIPT.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False),flush=True)
    return 0 if receipt['status']=='RESPONSE_RETAINED' else 1


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1]))

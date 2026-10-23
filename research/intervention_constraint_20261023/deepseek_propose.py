"""One independent API proposal; retain usage, never execute generated code."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/intervention_constraint/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'PROMPT.md').exists():
        raise FileExistsError('Already initiated; inspect retained state before any new call')
    instructions = '''请作为独立科研机制构造者，最多给一个具体有技术贡献的约束/更新操作。
目标：真实干预反馈驱动的虚拟细胞功能预测与药物/靶点组合发现，后续再检验研究智能体和RSI。已有单基因RNA+功能反馈的普通核范数补全有14%-16%源集误差收益，但不是新方法。早期kernel混合更新输给普通全数据重训，已停止。线性状态Wphi、固定beta功能读出、rank-one residual写回精确等价标量归一残差回归，也已停止。不要换名字重开。
我们正在找可测试的生物共享约束，例如同一干预在不同背景/组合/读出中的结构；泛低秩/双线性/多任务学习/对比损失/不确定性选点不足。功能残差本身不能识别beta正交状态变化。两算子同时更新有二阶项，但非线性不自动创新。RNA更准不自动药物决策更好。
最新已核验TDAL在线学习扰动筛选(Hellinger successor+leave-batch-out)、T2-z冻结world拟合contextlatent、PatchWorld反例修世界程序、HarnessTTT学harness proposer；这些泛机制已有先例。我们不要求全新基础算子或direct无法表达，具体样本/计算优势可作为差异。
请独立严肃构造一个数学上明确、可实现且可能失败的生物约束。最多10行公式，给出最强常规模型怎样精确复制/何处不同；数据需求须对应真实公开可获得类型，未认证部分标假设。Norman单图不能拆成后续生物任务；SCHEMATIC多背景只是来源线索未读数；继承/RSI另需后续任务。不要只列来源或再给空泛框架。
给最小反证(可先源集，不能toy冒充药效)、同信息direct/refit/CL/AL/mixture/等预算搜索对照、哪些继承对象及improved-improver额外预测、成功停止标准。若推导仅剩现成方法，直接NONE并给具体归约，而非虚构新颖性。你无检索工具，引用不得编造。2500中文字符左右。
'''
    context_path = ROOT / 'log/20261023/function_update_renewal/DECISION.md'
    prompt = instructions + '\n已完成证据：\n' + context_path.read_text(encoding='utf-8')
    (OUT / 'PROMPT.md').write_text(prompt, encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'logical_completion_requests': 1,
               'transport_attempts': 'NOT_EXPOSED_BY_CLIENT', 'thinking_enabled': True,
               'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
               'context_sha256': hashlib.sha256(context_path.read_bytes()).hexdigest(),
               'generated_code_executed': False, 'biological_experiment': False}
    try:
        response = client.complete([{'role': 'system', 'content': '你是独立科研方法构造者，严格区分具体机制、常规归约和待验证假设。'},
                                    {'role': 'user', 'content': prompt}],
                                   temperature=.7, max_tokens=10000, thinking_enabled=True)
        (OUT / 'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error, 'code', None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
        (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'RESPONSE_RETAINED' else 1


if __name__ == '__main__':
    raise SystemExit(main())

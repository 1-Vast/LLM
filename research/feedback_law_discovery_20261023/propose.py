"""One independently generated law proposal; never execute generated model code."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/feedback_law_discovery/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'RECEIPT.json').exists(), 'Inspect the live/retained request rather than repeat'
    prompt = '''提出一个简洁且可证伪的“反馈改变虚拟细胞干预响应更新规律”的候选。不是架构或候选列表。
目标是通过真实状态/功能反馈，在未来干预任务上比强直接预测、普通union refit/持续学习/主动学习/简单混合及等总成本程序搜索更有效；最终可继承更新器，并独立检验编辑器是否更会产生有效更新器。预算不是限制，但数据独立性不能编造。
现有事实：有反馈可使普通条件预测改善。Norman73对8gem103readout的重叠更新曾小幅赢强线性direct约0.7–1%，但同1参数全局parent收缩赢约2.9–5.7%并超过它；不再分析这份残差寻找新头或阈值。CDK12culture中期组成小收益不稳，已实际功能测试Abema排序更差，Palbo联合留出不可估。BeatAML exposed RNA/AUC可作新机制探索但旧lowrank分支STOP。其他候选曾与普通WLS/MAP/OED、标量ridge、固定feature线性functionhead、constrainedLS严格等价。Bare meta-learning/contextlatent/learnedproposer/AL+refit/ODEwashout/transport/知识nullspace都是已有机制，不构成新贡献。
可以用常规数学，不要求新基础算子；具体生物约束、可检验更新结构、有限样本或成本优势可构成贡献。不要用任意门控把2模型混合，也不要先假设强direct错误。请构造具体formula，给出最接近常规方法、为什么该具体差异不被它直接复制、一个最小数学失败见证及一个合法真实功能实验。若现有数据无法测试该law应明确，而不能建议重开身份资格循环。
特别要求：只推荐一个operation（至多8行公式），其中要区分predictor参数、updater参数、editor参数；给出同predictor与同history重置如何检验更新器继承。不要求你证明新颖性，但要主动识别可能严格等价。你无检索工具，不得捏造论文/数据/数值；没有可辩护的候选则NONE并指出还缺什么具体假设。不要代码，限3000中文字符。'''
    (OUT/'PROMPT.md').write_text(prompt, encoding='utf-8')
    receipt = dict(status='INITIATED', utc=datetime.now(timezone.utc).isoformat(), logical_requests=1,
                   prompt_sha256=hashlib.sha256((OUT/'PROMPT.md').read_bytes()).hexdigest(),
                   transport_attempts='NOT_EXPOSED', generated_code_executed=False)
    (OUT/'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    try:
        response = client.complete([{'role':'system','content':'你是严格的科学方法构造者，主动提出最强反对意见。'},
                                    {'role':'user','content':prompt}], temperature=.8, max_tokens=11000, thinking_enabled=True)
        (OUT/'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error,'code',None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
        (OUT/'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

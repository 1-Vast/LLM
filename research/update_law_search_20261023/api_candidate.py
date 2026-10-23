"""One new evidence-conditioned proposal, never execute generated code."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/update_law_search/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'PROMPT.md').exists():
        raise FileExistsError('Already initiated; inspect receipt before any continuation')
    prompt = '''请作为独立算法构造者，仅提出至多一个具体可证伪的更新规律，不要框架或文献清单。
任务是细胞干预功能预测与靶点组合发现。我们已有单基因RNA+功能标签普通低秩补全14%-16%误差收益但不是新算法；kernel反馈混合输给同信息union refit，已停止。当前新证据：裸隐式微分/resolvent低秩修改精确就是IFT+Sherman–Morrison，没有新增估计器。定向ODE已有PerturbODE先例；GO adapter+动态敏感loss已有PertAdapt。单轴完整轨迹/control Jacobian也不足识别mixed curvature；但真实source pair功能反馈当然能约束它。
最新实际取得SCHEMATIC多背景功能表：7line(两breast、两headneck、两lung、MCF10A)，12282行，仅元数据未读功能值。可有真实跨context研究，但不能造很多独立任务。其GI分数经每anchor全panel回归/标准化，稀疏mask并不等价新实验省钱；原始counts需单独取得并合法定义endpoint。缺pairedRNA，不得虚构。Norman现有source组合功能+singleRNA可先source-only试验，不要求完整RSI才允许探索；但所有已暴露数据须披露。
请考虑一个足够具体、简洁的更新估计/选择机制：可以属于已知统计家族，重点是一个非平凡的受限估计器或反馈结构，为什么比同信息ordinary refit/direct/CL/AL/mixture/equal-cost program search更省样本或计算。不要把更大网络、低秩、层级pooling、梯度history、泛global epistasis、优化器/prompt变化本身叫创新。不要要求direct表达不了；样本效率也可贡献。必须明确真实法定输入，继承的是何种规则，改进器如何进一步改善，哪些仅未来HYPOTHESIS。
输出：不超过8行公式定义完整可实现运算；最近普通操作如何复制/何处确有新增限制；最小数学或source实验反证；成功/停止条件。若没有明确额外操作，直接NONE并给具体归约。你没有检索工具，禁止编造引用或已验证实验。不要输出代码。限2500中文字符。
'''
    contexts = ['mechanism/INDEPENDENT.md', 'task/INDEPENDENT.md']
    hashes = {}
    for name in contexts:
        path = OUT.parent / name
        prompt += '\n证据报告：\n' + path.read_text(encoding='utf-8')
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    prompt_path = OUT / 'PROMPT.md'
    prompt_path.write_text(prompt, encoding='utf-8')
    receipt = {'status': 'INITIATED', 'started_utc': datetime.now(timezone.utc).isoformat(),
               'logical_completion_requests': 1, 'transport_attempts': 'NOT_EXPOSED_BY_CLIENT',
               'thinking_enabled': True, 'prompt_sha256': hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
               'context_hashes': hashes, 'generated_code_executed': False, 'biological_fit': False}
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    try:
        response = client.complete([{'role': 'system', 'content': '严谨的科研算法构造者。不要把未验证机制写成成果。'},
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


if __name__ == '__main__':
    main()

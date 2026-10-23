"""One evidence-conditioned action-rule proposal; never execute generated code."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/action_rule_search/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'RECEIPT.json').exists(), 'Inspect initiated request instead of duplicating it'
    prompt = '''请独立构造至多一个简洁的“药物作用规律更新器”，不是框架、模块清单或新名词。
应用必须是由真实功能反馈修订干预后的细胞状态/功能预测，并迁移到后续药物发现任务。
新线索：实际2026 GRNvelo原文把Criz模拟成MET mRNA编辑+GRN传播，这不自动等价受体激酶活性抑制；有真实D3组合表达比较，但模拟D11耐药状态距离不等于真实后续增殖/杀伤效用。我们不能仅指出错误，还须给出可实现的、相比同信息普通方法有明确有限反馈优势的修复规律。
已有强正向仅常规RNA条件补全14–16%MSE，成本约9.77倍；没有WM/agent/RSI成功。以下已做并STOP，不能重命名：Jaaks同target动作替换、kinobeads结合谱kernel、同partner残差收缩；decryptE高剂量蛋白增量；剂量tangent shift+nuisance profile等于joint WLS，第二点区分是普通OED；固定分子梯度传送预条件器等于同结构bilevel optimizer；裸IFT+Sherman Morrison无独特修订器；73真实双扰动的对角混合law输强线性ridge；裸transport/growth/capture已被UOT占据且采样不识别。
可用资料：现有Norman source单/双扰动状态+单/双功能（一个K562背景）；已曝光Jaaks/decryptE有上述STOP；SCHEMATIC7line功能表仅schema认证、无pairedRNA，publishedGI依赖全panel归一化；不能想象新的独立后续任务已存在。可以给明确新公共数据线索但不能假称取得。预算/API不是限制。不要为盲识别加入一个任意网络。
候选可以采用常规数学；创新需要一个具体且非任意的可继承限制/统计或成本性质，不能因属于GN/ridge/dual control就自动否定，也不能仅复制候选改名成ordinary便声称已有先例。请明确实际相同信息强direct/ordinary union refit为什么未直接复制新增性质；需要实测的地方标HYPOTHESIS。
输出至多8行公式完整定义更新操作、一个最小合成反例/等价检验和一个有实际功能终点的有界真实实验；预设成功和STOP。说明如何把更新器继承收益与新旧编辑器改善后代能力分开检验。没有新操作就NONE；不要为了交卷造无根据的创新、论文、数据或性能。你无检索工具，禁止捏造引用。不要输出代码，限2500中文字符。'''
    (OUT / 'PROMPT.md').write_text(prompt, encoding='utf-8')
    receipt = {'status': 'INITIATED', 'utc': datetime.now(timezone.utc).isoformat(),
               'prompt_sha256': hashlib.sha256((OUT / 'PROMPT.md').read_bytes()).hexdigest(),
               'logical_requests': 1, 'transport_attempts': 'NOT_EXPOSED',
               'generated_code_executed': False, 'biological_values_read': 0}
    (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    try:
        response = client.complete([{'role': 'system', 'content': '严谨的研究构造者，提出操作并主动寻找反证。'},
                                    {'role': 'user', 'content': prompt}],
                                   temperature=.7, max_tokens=10000, thinking_enabled=True)
        (OUT / 'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__,
                       error_code=getattr(error, 'code', None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
        (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

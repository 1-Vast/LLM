"""Retain one independent biological update-mechanism derivation."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/renewal_application'
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    folder = LOG / 'root_proposal'
    folder.mkdir(parents=True, exist_ok=True)
    assert not (folder / 'STARTED.json').exists()
    prompt = '''你是独立科研方法设计者。请真正推导一个最强、简洁、可实现并可反证的核心机制，不写大架构或空泛数据集清单。
最终目标：以虚拟细胞干预世界为根基的药物发现agent，反馈改善细胞状态/功能模型及研究程序，把有效能力继承到后续任务；优先RSI，须old/new improver在同一later starting solver/history/permissions/budget下使后续改进更好。
已有大量精确阴性，不能重命名：药物latent world被strongdirect胜过；Gaussian residual writeback=kernel conditioning；同historyMDL状态split=普通树；timewarp=systemID；semigroup已有DeepOSG；固定类型marginalbound=missingoutcome feasibility；potency-alignedfunctionaltransport虽较小模型好却输fullstrongdirect；signed-update V=2δTb−δTCδ是squareloss恒等式，b含未来y，学习V/embedding/记策略本身是ordinary taskvalue regression。Hyperagents/AIDE²/SpecRSI/MetaShare及CellScientist已有program/meta-program editing、失败/成功memory、diagnosticrouting、equalbudgetcandidate search和commonstart评价。不能把这些模块作为新core。
但不要因为一个通用MLP能表达就判完全等价；必须区分表达能力、同数据/预算能精确复现、真实biologicalstructure带来的sampleefficiency/transport/decision收益。可发表贡献可以是具体新性质或非平凡实证机制，不必发明数学名词。不强迫每个world有同celltrajectory，static actionconditioned预测合法；RNA/形态proxy有方法价值，不能称viability或疗效。
本次重点从细胞干预的某种真实结构出发（例如扰动方向与状态特异性、分布异质性、稀疏因果模块、功能与分子失配，或你推导的更强结构），找到为什么小量功能反馈可以改变以后如何改进，而不只是增加监督样本或普通调超参。要使结构可被实验否定，不给先验不可验证解释。不要提出需要不存在真实数据的神奇state。
仅给最多一个机制：(1)具体药物发现用途和最小可得数据/合法feedback/later-task单位，区分核验与猜测；(2)≤12行公式或伪码，点明唯一技术实质；(3)与最近ordinary direct/kernel/meta learning/learnedoptimizer/search的精确差异；如果完全归约请诚实停，不造新名字；(4)最便宜决定性实验及合理success/stop，不以toy当药效；(5)分别可证伪world、agent、inheritance、joint、C4，以及公平baseline预算。若不能给出新core，给一个真正可改变决策的可执行检查，不要仅说缺independentwetlab。未知paper/DOI必须未核验。输出≤4500中文字符。
'''
    paths = [(ROOT / 'research/REPORT.md', 15000),
             (ROOT / 'log/20261022/prism_profile_opportunity/DECISION.md', 6500),
             (ROOT / 'src/virtual_cell/combination_world.py', 8000)]
    for path, limit in paths:
        prompt += '\n\n' + path.relative_to(ROOT).as_posix() + '\n' + path.read_text(encoding='utf-8')[:limit]
    (folder / 'PROMPT.md').write_text(prompt, encoding='utf-8')
    write(folder / 'STARTED.json', {'utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1,
          'code_sha256': sha(Path(__file__)), 'prompt_sha256': sha(folder / 'PROMPT.md'),
          'inputs': {p.relative_to(ROOT).as_posix(): sha(p) for p, _ in paths}})
    receipt = {'logical_requests': 1, 'generated_code_executed': False, 'new_fits': 0,
               'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT'}
    client = None
    try:
        client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=240))
        response = client.complete([{'role': 'system', 'content': '具体推导、诚实核验，不编造数据或引用。'},
                                    {'role': 'user', 'content': prompt}],
                                   temperature=0.7, max_tokens=16000, thinking_enabled=True)
        (folder / 'RESPONSE.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason,
                       content_characters=len(response.content), response_sha256=sha(folder / 'RESPONSE.md'))
    except Exception as exc:
        receipt.update(status='FAILED_RETAINED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(),
                       usage=client.provider_usage if client is not None else {}, reasoning_text='NOT_EXPOSED_BY_CLIENT')
        write(folder / 'RECEIPT.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    return 0 if receipt['status'] == 'RESPONSE_RETAINED' else 1


if __name__ == '__main__':
    raise SystemExit(main())

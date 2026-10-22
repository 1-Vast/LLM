"""One reasoning-enabled research proposal, retained without executing output."""
from datetime import datetime, timezone
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT/'log/20261022/functional_dynamics_gate'


def main():
    prompt_path = OUT/'DEEPSEEK_PROMPT.md'
    receipt_path = OUT/'DEEPSEEK_RECEIPT.json'
    if prompt_path.exists() or receipt_path.exists():
        raise FileExistsError('proposal_already_started')
    history_path = ROOT/'research/REPORT.md'
    current_path = ROOT/'log/20261022/intervention_dynamics_renewal/DECISION.md'
    instructions = '''请独立提出最多一个极简、技术实质清楚且可证伪的科研机制，目标是以虚拟细胞世界模型为根基的药物发现research agent，并优先使改进程序自身在后继任务中更会改进（RSI）。不需要所有贡献一开始都成立，但须明确实验链。
你无检索工具，不得编造参考文献或假装数据已认证。我们正在优先寻找公开time-resolved drug growth/death数据：多drug/dose、earlyprefix→later功能、独立run/background。RNA/wholelineage/washout不是任何worldmodel通用要求；不能每次只设计必须新wetlab的空候选。可以先exposeddevelopment gate，不能冒充独立验证。
已知组件可以产生新的经验性质/识别条件/计算样本性质；不能因为通用directpredictor也可表示就否定。反之不能把evaluationprotocol、knownnullbound、ordinaryrefit/CL/AL/meta-learning/search换名当新算子。请明确10行内operation和最近普通方法能否逐项精确复现。
已停：TGtimewarp是普通系统辨识，historyMDLsplit被同信息direct匹配；Gaussiangenewriteback等于kernelconditioning；haplotypemutationselection普通且数据未合格；ADCCendpoint factorization普通rankone且不识别dynamics；semigroup consistency已有DeepOSG；fixedtype selection bounds是标准missingoutcome/common-domination；drug turningpoint普通segmentedregression。Hyperagents/AIDE²/SpecRSI/MetaShare已有task/meta程序编辑、失败检索、后继improvementcredit，泛称critic/自改prompt/程序继承不够。
请给：(1)具体可用类型的真实药物应用和最小可获得数据；(2)最小公式/操作及具体可证伪主张；(3)与最接近普通方法的精确差异/可能归约；(4)最便宜可能失败的realdata gate，不把toy当药效；(5)sameinformationdirect、ordinaryrefit/CL、AL、mixture、equalbudgetprogramsearch公平控制；(6)world、agent、weight/procedure inheritance、joint、psi1胜psi0的各自证据；(7)成功/停止条件。
优先一个做得成且有实质的想法。若严肃推导后只剩普通方法，允许NONE并具体解释缺少什么，仍给一个有用可执行的下一步，不要虚构新颖性。输出最多3000中文字符。
'''
    prompt = instructions+'\n\n当前决策：\n'+current_path.read_text(encoding='utf-8')
    prompt += '\n\n历史决策节选：\n'+history_path.read_text(encoding='utf-8')[:15000]
    with prompt_path.open('x', encoding='utf-8') as f:
        f.write(prompt)
    settings = replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.0)
    client = DeepSeekChatClient(settings)
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(),
        'logical_completion_requests': 1, 'transport_attempt_count': 'NOT_EXPOSED_BY_CLIENT',
        'thinking_enabled': True, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_files': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (history_path, current_path)},
        'biological_experiment': False, 'generated_code_executed': False}
    try:
        response = client.complete([
            {'role': 'system', 'content': '你是严谨且有创造力的科研方法提案者。明确操作和证据，不编造来源。'},
            {'role': 'user', 'content': prompt}],
            max_tokens=12000, temperature=0.7, thinking_enabled=True)
        with (OUT/'DEEPSEEK_PROPOSAL.md').open('x', encoding='utf-8') as f:
            f.write(response.content)
        receipt.update({'status': 'RESPONSE_RETAINED', 'model': response.model,
            'finish_reason': response.finish_reason, 'content_characters': len(response.content)})
    except Exception as exc:
        receipt.update({'status': 'FAILED_RETAINED', 'error_type': type(exc).__name__,
            'error_code': getattr(exc, 'code', None)})
    finally:
        receipt.update({'ended_utc': datetime.now(timezone.utc).isoformat(), 'provider_usage': client.provider_usage})
        with receipt_path.open('x', encoding='utf-8') as f:
            json.dump(receipt, f, indent=2)
            f.write('\n')
    print(json.dumps({k: receipt.get(k) for k in ('status', 'finish_reason', 'provider_usage', 'error_type')}))
    return 0 if receipt['status'] == 'RESPONSE_RETAINED' else 1


if __name__ == '__main__':
    raise SystemExit(main())

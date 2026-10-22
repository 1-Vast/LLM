"""Seal completed independent directions, then actually exchange all three texts."""
import hashlib,json
from pathlib import Path
P=Path('log/20261022/tggates_rna_feedback_pilot')
ROLES=['next_mechanism_constructive','next_mechanism_skeptic','next_mechanism_operational']

def main():
    opinions={};hashes={}
    for role in ROLES:
        d=P/'api_reviews'/role
        receipt=json.loads((d/'RECEIPT.json').read_text())
        assert receipt['status']=='RESPONSE_RETAINED' and receipt['finish_reason']=='stop'
        raw=(d/'RESPONSE.md').read_bytes();assert raw.strip()
        opinions[role]=raw.decode('utf-8');hashes[role]=hashlib.sha256(raw).hexdigest()
    with (P/'NEXT_MECHANISM_FIRST_OPINIONS_SEAL.json').open('x',encoding='utf-8') as f:
        json.dump(dict(first_opinion_sha256=hashes,all_completed_before_peer_exchange=True),f,indent=2)
    root=('Root具体质疑，必须逐条接受或反驳，不能仅复述STOP：'
          '(1)建设方从旧基线.02335714直接写排除了叠加最小机制的余量空间，推论过强；只有候选MAE<.00335714的必要条件，不能凭它预知RNA结果。'
          '(2)建设方说未来主张必须是普通预测器的受限子族，不是用户的要求；不得人为排除全新机制。'
          '(3)应用方把成功改成改善下界>0且LDH同向，非本pilot门；原门是相对最强非同构普通对照严格>.02绝对且>=10%相对，并含固定mixture；不改任何门。'
          '(4)应用方继承一项要求old/new improver交换：那是C4，继承本身是后来任务transfer vs restart；两者不能混同。joint收益不要求交互正或超加性，除非主张synergy。'
          '(5)各方说无可信候选是本次材料/搜索结论，不是全领域无新机制的证明；历史阴性只STOP exact配置，不能整体停用户目标。'
          '(6)应用方列普通CL/等预算搜索并不代表当前RNApilot已运行全部这些比较；它们属于未完成的完整目标，不能写当前成功或已全对照。'
          '(7)没有任何当前RNA性能/开发HighRNA/独立供体任务；不得把历史暴露源dev叫全新确认。'
          '若仍NO_GO，提出一个具体而有限的下一证据问题，或明确等待当前结果即可。别制造新阈值、额外实验或新数据权限。\n')
    peer='\n\n'.join('--- '+r+' ---\n'+opinions[r] for r in ROLES)
    gate=(P/'NUMERICAL_PROTOCOL.md').read_text(encoding='utf-8').split('## Scoring and stops',1)[1]
    for role in ROLES:
        d=P/'api_reviews'/(role+'_cross');d.mkdir()
        prompt='你继续原立场'+role+'。下面是真实其他独立首评原文。最多1500中文字符，回应具体观点及root七条质疑，保留实质分歧，明确纠错；不是投票或强求新候选。\n'+root+peer+'\n--- 原冻结判定及完整目标边界 ---\n'+gate
        with (d/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(prompt)
    print(json.dumps(dict(status='ALL_FIRST_OPINIONS_SEALED_AND_PEER_TEXTS_EXCHANGED',roles=[r+'_cross' for r in ROLES])))

if __name__=='__main__':main()

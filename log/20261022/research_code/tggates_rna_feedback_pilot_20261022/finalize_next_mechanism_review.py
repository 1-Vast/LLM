"""Verify the actual six-call exchange and bind the root's reviewed disposition."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    evidence=json.loads((P/'NEXT_MECHANISM_REVIEW_EVIDENCE.json').read_text())
    for name,digest in evidence['files_sha256'].items():assert sha(ROOT/name)==digest,name
    first=json.loads((P/'NEXT_MECHANISM_FIRST_OPINIONS_SEAL.json').read_text())
    for role,digest in first['first_opinion_sha256'].items():assert sha(P/'api_reviews'/role/'RESPONSE.md')==digest
    calls=[]
    for role in evidence['roles']+[r+'_cross' for r in evidence['roles']]:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text())
        assert r['status']=='RESPONSE_RETAINED' and r['finish_reason']=='stop' and (d/'RESPONSE.md').read_text(encoding='utf-8').strip()
        request=(d/'EXACT_REQUEST.txt').read_text(encoding='utf-8')
        assert hashlib.sha256(request.encode('utf-8')).hexdigest()==r['request_sha256']
        assert r['generated_code_executed'] is False
        calls.append(dict(role=role,model=r['model'],usage=r['usage'],request_sha256=r['request_sha256'],
                          serialized_request_sha256=sha(d/'EXACT_REQUEST.txt'),
                          request_hash_convention='UTF8 logical text with universal-newline decoding',
                          response_sha256=sha(d/'RESPONSE.md'),receipt_sha256=sha(d/'RECEIPT.json')))
    result=dict(status='SIX_ACTUAL_CALLS_AND_CROSS_EXCHANGE_VERIFIED_ROOT_DECISION_RETAINED',
                utc=datetime.now(timezone.utc).isoformat(),calls=calls,total_tokens=sum(c['usage']['total_tokens'] for c in calls),
                root_decision_sha256=sha(P/'NEXT_MECHANISM_REVIEW_DECISION.md'),full_goal='ACTIVE_NOT_ACHIEVED',
                new_candidate_promoted=False,new_biological_experiment=False,pilot_unchanged=True)
    with (P/'NEXT_MECHANISM_REVIEW_TERMINAL.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='calls'}))

if __name__=='__main__':main()

"""Audit sealed artifacts and summarize existing fixed results; no fit or new outcomes."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'

def read(name):return json.loads((P/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    seal=read('PREDICTION_SEAL.json');result=read('RNA_PILOT_RESULT.json')
    for name,digest in dict(seal['files'],**seal['code']).items():assert sha(ROOT/name)==digest,name
    assert result['prediction_seal_sha256']==sha(P/'PREDICTION_SEAL.json')
    assert read('REFERENCE_ASSEMBLY_AUDIT.json')['status']=='PASS'
    assert read('AUTONOMOUS_PILOT_TERMINAL.json')['status']=='PILOT_COMPLETE_REQUIRES_RESULT_REVIEW'
    assert read('ARRIVAL_PROCESSING_TERMINAL.json')['status']=='ALL_172_COMPLETE'
    receipt=read('NUMERICAL_RECEIPT.json');assert receipt['estimator_fits']==receipt['operations']['coefficient_fits']==4336
    assert receipt['pipeline_evaluations']==1552 and receipt['base_packs']==602
    scores=result['scores'];c=scores['rho_0']['dna_mae']
    assert c==scores['route_11']['dna_mae']
    for family,losses in result['losses'].items():
        assert len(losses)==7
        for assay in ['dna','ldh']:
            assert np.isclose(np.mean([r[assay+'_absolute_error'] for r in losses]),scores[family][assay+'_mae'],rtol=0,atol=1e-15)
    gains={name:s['dna_mae']-c for name,s in scores.items()}
    assert np.isclose(gains['refit'],result['absolute_dna_gain'],rtol=0,atol=1e-15)
    selected=read('SOURCE_SELECTION.json')['selected'];states=read('SOURCE_STATE_ERRORS.json');state_summary={}
    for family in ['rho_0','rho_0.5','rho_1']:
        key=json.dumps(selected[family]['config'],sort_keys=True,separators=(',',':'))
        rows=states[key];assert len(rows)==24
        prior=float(np.mean([r['prior_mse'] for r in rows]));updated=float(np.mean([r['updated_mse'] for r in rows]))
        state_summary[family]=dict(config=selected[family]['config'],prior_mse=prior,updated_mse=updated,
            relative_error_reduction=(prior-updated)/prior,groups_improved=sum(r['updated_mse']<r['prior_mse'] for r in rows),
            groups=len(rows),selection_exposed=True,independent_development_state_accuracy=False)
    roles=['post_result_support','post_result_skeptic','post_result_support_cross','post_result_skeptic_cross']
    reviews=[]
    for role in roles:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text())
        assert r['status']=='RESPONSE_RETAINED' and r['finish_reason']=='stop'
        assert (d/'RESPONSE.md').read_text(encoding='utf-8').strip()
        assert hashlib.sha256((d/'EXACT_REQUEST.txt').read_text(encoding='utf-8').encode()).hexdigest()==r['request_sha256']
        reviews.append(dict(role=role,response_sha256=sha(d/'RESPONSE.md'),usage=r['usage']))
    summary=dict(status='SEALED_RESULT_AND_FIXED_SUMMARIES_VERIFIED',utc=datetime.now(timezone.utc).isoformat(),
        candidate='rho_0',candidate_scores=scores['rho_0'],scores=scores,candidate_dna_gain_vs_each=gains,
        route_dna_gains=dict(state_on_given_function=scores['route_01']['dna_mae']-c,
                            function_on_given_state=scores['route_10']['dna_mae']-c,
                            both_vs_none=scores['route_00']['dna_mae']-c),
        direct_vs_no_observed_query_rna=scores['no_rna']['dna_mae']-scores['direct']['dna_mae'],
        source_state=state_summary,decision=result['decision'],original_gate_passed=result['useful_gain_gate'],
        independent_state_confirmation=False,world_free_ablation=False,new_fits=0,new_target_reads=0,
        completed_post_result_reviews=reviews,receipt=receipt,
        files_sha256={n:sha(P/n) for n in ['RNA_PILOT_RESULT.json','SOURCE_SELECTION.json','SOURCE_STATE_ERRORS.json',
                                         'PREDICTION_SEAL.json','NUMERICAL_RECEIPT.json','REFERENCE_ASSEMBLY_AUDIT.json']})
    with (P/'ROOT_RESULT_AUDIT.json').open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2)
    for role in ['post_result_identity_support','post_result_identity_skeptic']:
        d=P/'api_reviews'/role;d.mkdir()
        peer='\n\n'.join('--- '+r+' ---\n'+(P/'api_reviews'/r/'RESPONSE.md').read_text(encoding='utf-8') for r in roles)
        prompt=('你是'+('支持方' if role.endswith('support') else '质疑方')+'，请对下面四份真实首评与交叉回复和机械核验摘要作简短纠错，最多1200中文字符。'
            '两首评把主候选rho_0误认rbf：候选DNA .027315340891917134/LDH .009035285110724236；rbf是对照。'
            '首评的-0.008364303766192367确实来自refit-rho0，不能搭配rbf指标。LDH不在DNA主门内，不要再编造LDH门。'
            'source state是选择暴露诊断而非独立state确认；no_rna仍保留source-trained world。'
            '实际direct=.022567071922444528满足已证明的d<=.04条件，故此已选direct的候选半混合门确实不可达；refit<.02还单独使严格>.02改善不可能。'
            '这不是全领域不可能，也不改变STOP，候选即使去掉门槛也实际差于direct/noRNA/refit，不能只归因门几何。'
            '一般继承transfer vs restart与C4 old/new improver共同起点不同；joint不必超加。'
            '明确回应对方/自身错误，接受或具体反驳，引用正确候选及源状态数字，列保留证据、反对证据、未决和后续最小证据。'
            '没有新实验/改阈值/开保留集授权，不把同模型角色共识当实证。\n')
        prompt+=peer+'\n--- 机械核验摘要 ---\n'+json.dumps(summary,ensure_ascii=False)
        with (d/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(prompt)
    print(json.dumps({k:summary[k] for k in ['status','candidate','candidate_scores','route_dna_gains','direct_vs_no_observed_query_rna','source_state','decision']},indent=2))

if __name__=='__main__':main()

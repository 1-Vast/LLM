"""Post-freeze comparison; independent_result.json must already exist."""
import hashlib
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parents[1]
A = json.loads((R/'review/independent_result.json').read_text(encoding='utf-8'))
B = json.loads((R/'pilot_result.json').read_text(encoding='utf-8'))
MAP = {'None':'00','IFNG':'10','TNFA':'01','IFNG_TNFA':'11'}
MODELS = {'gain':'H_gain','additive':'B_add','constant_interaction':'B_const','no_drug_control':'B_control'}
checks, discrepancies = [], []


def check(path, a, b):
    if isinstance(a, (float,int)) and not isinstance(a,bool):
        equal = math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7)
        delta = abs(a-b)
    else:
        equal, delta = a == b, None
    record = dict(path=path, independent=a, primary=b, agreement=equal, absolute_difference=delta)
    checks.append(record)
    if not equal:
        discrepancies.append(record)


check('protocol_sha256',A['protocol_sha256'],B['protocol_sha256'])
for code, b in B['preparations'].items():
    a=A['preparations'][code]
    check(code+'/source_sha256',A['source_sha256'][f'cxcl9_raw_{code}.body'],b['source_sha256'])
    for w in b['well_records']:
        key='|'.join((w['drug'],MAP[w['stimulus']],w['technical_well']))
        aw=a['wells'][key]
        for x,y in [('mfi','mfi'),('n_raw','events'),('n_kept','retained')]:
            check(code+'/wells/'+key+'/'+x,aw[x],w[y])
    for key in ['eligible','D0','N0','S0','I0','kappa']:
        check(code+'/controls/'+key,a['controls'][key],b['controls'][key])
    for stim, value in b['controls']['means'].items():
        check(code+'/controls/means/'+stim,a['controls']['means'][MAP[stim]],value)
    for x,y in [('D_interval','D_envelope'),('N_interval','N_envelope'),('kappa_interval','kappa_envelope')]:
        for i in range(2):
            check(code+'/controls/'+x+'/'+str(i),a['controls'][x][i],b['controls'][y][i])
    for pm,am in MODELS.items():
        check(code+'/MAE/'+am,a['MAE'][am],B['mae_by_preparation'][code][pm])
    check(code+'/gain_minus_constant_MAE',a['gain_minus_constant_MAE'],
          B['mae_by_preparation'][code]['gain']-B['mae_by_preparation'][code]['constant_interaction'])
assert len(B['targets']) == 20
for b in B['targets']:
    code,drug=b['preparation'],b['drug']
    a=A['preparations'][code]['targets'][drug]
    base=code+'/'+drug+'/'
    for i,s in enumerate(['00','10','01']):
        check(base+'calibration/'+s,a['calibration'][s],b['calibration_means'][i])
    check(base+'observed',a['observed'],b['observed'])
    check(base+'scale',A['preparations'][code]['controls']['S0'],b['scale'])
    for pm,am in MODELS.items():
        for af,bf in [('predictions','predictions'),('signed_normalized_errors','normalized_signed_errors'),
                      ('absolute_normalized_errors','normalized_absolute_errors')]:
            check(base+af+'/'+am,a[af][am],b[bf][pm])
        if pm != 'gain':
            check(base+'gain_minus_comparator_error/'+am,a['gain_minus_comparator_absolute_errors'][am],
                  b['normalized_absolute_errors']['gain']-b['normalized_absolute_errors'][pm])
    for af,bf in [('gain_prediction_interval','gain_prediction_technical_envelope'),('observed_interval','observed_technical_envelope')]:
        for i in range(2):
            check(base+af+'/'+str(i),a[af][i],b[bf][i])
    check(base+'technical_overlap',a['technical_overlap'],b['technical_envelope_overlap'])
    check(base+'gain_minus_constant_normalized',a['gain_minus_constant_prediction']/b['scale'],b['gain_minus_constant_normalized'])
    check(base+'gain_minus_constant_formula',a['gain_minus_constant_prediction'],a['gain_minus_constant_formula'])

result = dict(independent_sha256=hashlib.sha256((R/'review/independent_result.json').read_bytes()).hexdigest(),
              primary_sha256=hashlib.sha256((R/'pilot_result.json').read_bytes()).hexdigest(),
              tolerances=dict(relative=1e-9,absolute=1e-7), check_count=len(checks),
              discrepancy_count=len(discrepancies), discrepancies=discrepancies, checks=checks,
              note='Agreement verifies arithmetic only. Extra independent quartiles, endpoint products and ordering retained in frozen result; primary stores final envelopes.')
(R/'review/numeric_comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
lines=['# Independent numeric review: E001','',
       'Independent implementation was frozen before primary results or implementation were read. Primary implementation was never imported or read. The frozen result SHA256 is '+result['independent_sha256']+'.', '',
       f"{len(checks)} scalar/hash/Boolean comparisons, {len(discrepancies)} discrepancies at relative 1e-9 or absolute 1e-7 tolerance. All 192 wells, raw/retained event counts, control calibration quantities, 20 target calibrations and outcomes, 80 predictions and signed/absolute normalized errors, final technical envelopes and overlaps, all four preparation MAEs, and gain-minus-constant contrasts are covered. All 48 groups per export are retained. Independent quartiles, trimming boundaries, control endpoint ratios and all four inhibitor endpoint products remain in independent_result.json.", '',
       '| Preparation | Gain MAE | Add MAE | Constant MAE | Control MAE | Gain − constant MAE | Envelope overlap |',
       '|---|---:|---:|---:|---:|---:|---:|']
for code,a in A['preparations'].items():
    m=a['MAE'];n=sum(t['technical_overlap'] for t in a['targets'].values())
    lines.append(f"| {code} | {m['H_gain']:.6f} | {m['B_add']:.6f} | {m['B_const']:.6f} | {m['B_control']:.6f} | {a['gain_minus_constant_MAE']:+.6f} | {n}/5 |")
lines.extend(['',
    'The exact common-gain restriction is not supported as a general predictive replacement across these five interventions and preparations. Gain is worse than constant interaction in three preparations; its small advantage in E3DA does not repeat in E3DB. Eleven of twenty gain prediction envelopes do not overlap observed technical-well ranges. Taselisib departs in both BxPC3 preparations, while trametinib departs in both AsPC1 preparations. These are descriptive observations about the prespecified full set, not selected validation subgroups. All qualifying controls merely make the denominator well defined; they do not validate common gain.', '',
    'This is calibration-conditioned target holdout in one existing assay, with two source-described independent screenings/preparations per line. Original Par18 already exposes inhibitor-dependent response patterns. Par57 gives different cytokine doses by line (AsPC1 10 ng/mL; BxPC3 1 ng/mL); Par59–60 describes capture-bead sandwich-assay PE readout and APC-based capture-bead gating. The exported PE-only channel cannot verify that original gate. MFI is not secretion concentration without a calibrated mapping. Source minmax scaling and apoptosis correction were deliberately not used, per protocol. This computation yields no cell/molecular mechanism, external validation, biological-noise guarantee, CI, p-value, new algorithm, or acquisition advantage.', '',
    'B_const is the scientifically relevant competing restriction; B_add alone is inadequate for establishing common gain. The gain restriction is ordinary proportional response/rank-one structure, and even arithmetic agreement cannot establish its scientific validity. Negative/crossing drug effects were retained and interval multiplication used all endpoint products. Broad technical envelopes can leave some target discrimination uninformative; overlap cannot be read as confirmation. In particular, the all-control kappa ranges were E3CA [2.2020, 4.5193], E3CB [2.7484, 3.4867], E3DA [2.4592, 3.1408], E3DB [2.1984, 3.6071].', '',
    'Independent numeric execution: wall '+str(A['usage']['wall_seconds'])+' seconds; process CPU '+str(A['usage']['cpu_seconds'])+' seconds; zero network calls, external science API calls, or monetary cost. Review/comparison scripts are confined to review/.'])
(R/'review/numeric_review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))

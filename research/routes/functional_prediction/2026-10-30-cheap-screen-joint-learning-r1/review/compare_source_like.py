"""Compare frozen source-like diagnostic with primary result after freeze."""
import hashlib, json, math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
A=json.loads((R/'review/source_like_result.json').read_text(encoding='utf-8'))
B=json.loads((R/'pilot_result.json').read_text(encoding='utf-8'))
MODELS={'gain':'H_gain','additive':'B_add','constant_interaction':'B_const','no_drug_control':'B_control'}
STIM={'None':'00','IFNG':'10','TNFA':'01','IFNG_TNFA':'11'}
DRUGS=['Momelotinib','BMS-345541','Salirasib','Trametinib','Taselisib']
records=[]; discrep=[]
def rec(path,a,b):
  if isinstance(a,(int,float)) and not isinstance(a,bool):
    ok=math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7); d=abs(a-b)
  else: ok=a==b; d=None
  x={'path':path,'source_like':a,'primary':b,'agreement':ok,'absolute_difference':d};records.append(x)
  if not ok: discrep.append(x)
summary={}
for code,b in B['preparations'].items():
  a=A['preparations'][code]; wells=b['well_records']; changed=0; count_changed=0; max_mfi=0.0
  bw={ '|'.join((w['drug'],STIM[w['stimulus']],w['technical_well'])):w for w in wells }
  for key,w in bw.items():
    aw=a['wells'][key]
    for x,y in [('n_raw','events'),('n_kept','retained'),('mfi','mfi')]: rec(code+'/wells/'+key+'/'+x,aw[x],w[y])
    if aw['n_kept']!=w['retained'] or not math.isclose(aw['mfi'],w['mfi'],rel_tol=0,abs_tol=0): changed+=1
    if aw['n_kept']!=w['retained']: count_changed+=1
    max_mfi=max(max_mfi,abs(aw['mfi']-w['mfi']))
  # Controls and per-preparation model outcomes
  for x,y in [('eligible','eligible'),('D0','D0'),('N0','N0'),('S0','S0'),('I0','I0'),('kappa','kappa')]: rec(code+'/controls/'+x,a['controls'][x],b['controls'][y])
  for s,v in b['controls']['means'].items(): rec(code+'/controls/means/'+s,a['controls']['means'][STIM[s]],v)
  for x,y in [('D_interval','D_envelope'),('N_interval','N_envelope'),('kappa_interval','kappa_envelope')]:
    for i in range(2): rec(code+'/controls/'+x+'/'+str(i),a['controls'][x][i],b['controls'][y][i])
  mae={}
  for pm,am in MODELS.items(): mae[pm]=a['MAE'][am];rec(code+'/MAE/'+pm,a['MAE'][am],B['mae_by_preparation'][code][pm])
  rec(code+'/gain-minus-constant-MAE',a['gain_minus_constant_MAE'],mae['gain']-mae['constant_interaction'])
  summary[code]={'changed_wells':changed,'count_changed_wells':count_changed,'max_well_mfi_absolute_difference':max_mfi,'source_like_MAE':mae,'source_like_gain_minus_constant_MAE':a['gain_minus_constant_MAE'],'primary_MAE':B['mae_by_preparation'][code],'source_like_overlap_count':sum(t['technical_overlap'] for t in a['targets'].values()),'primary_overlap_count':sum(t['technical_envelope_overlap'] for t in B['targets'] if t['preparation']==code)}
  for btar in [t for t in B['targets'] if t['preparation']==code]:
    drug=btar['drug']; t=a['targets'][drug]; base=code+'/'+drug+'/'
    for i,s in enumerate(['00','10','01']): rec(base+'calibration/'+s,t['calibration'][s],btar['calibration_means'][i])
    rec(base+'observed',t['observed'],btar['observed'])
    rec(base+'scale',a['controls']['S0'],btar['scale'])
    for pm,am in MODELS.items():
      for af,bf in [('predictions','predictions'),('signed_normalized_errors','normalized_signed_errors'),('absolute_normalized_errors','normalized_absolute_errors')]: rec(base+af+'/'+pm,t[af][am],btar[bf][pm])
    for af,bf in [('gain_prediction_interval','gain_prediction_technical_envelope'),('observed_interval','observed_technical_envelope')]:
      for i in range(2): rec(base+af+'/'+str(i),t[af][i],btar[bf][i])
    rec(base+'technical_overlap',t['technical_overlap'],btar['technical_envelope_overlap'])
    rec(base+'gain_minus_constant_normalized',t['gain_minus_constant_prediction']/btar['scale'],btar['gain_minus_constant_normalized'])
    rec(base+'gain-minus-comparator-gain-vs-const',t['gain_minus_comparator_absolute_errors']['B_const'],btar['normalized_absolute_errors']['gain']-btar['normalized_absolute_errors']['constant_interaction'])
  # model winner counts in source-like vs primary
  summary[code]['source_like_best_model']=min(mae,key=mae.get);summary[code]['primary_best_model']=min(B['mae_by_preparation'][code],key=B['mae_by_preparation'][code].get)

result={'source_like_sha256':hashlib.sha256((R/'review/source_like_result.json').read_bytes()).hexdigest(),'primary_sha256':hashlib.sha256((R/'pilot_result.json').read_bytes()).hexdigest(),'method_mismatch':'Primary trims separately within preparation×stimulus×drug×technical well using closed bounds; source-like pools both technical wells within each preparation×stimulus×drug, uses strict bounds, then averages surviving technical-well means. Neither source-like nor this diagnostic combines P12/P14.','comparison_tolerance':{'relative':1e-9,'absolute':1e-7},'comparison_count':len(records),'discrepancy_count':len(discrep),'discrepancies':discrep,'summary':summary}
(R/'review/source_like_comparison.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Source-like trimming sensitivity review','',f"Source-like result was frozen before primary inspection (SHA256 `{result['source_like_sha256']}`). It used the archived `01_preparing_inputs.R` method for each preparation separately: pool Sample1 and Sample2 events per stimulus×drug, use NumPy linear quartiles, retain strict inequalities, then equal-average surviving technical-well MFIs. The primary E001 method trims each technical well separately with closed bounds. The source script itself combines E3DA/E3DB in its preparation workflow, but this diagnostic deliberately keeps them separate as requested.",'',f"Compared {len(records)} arithmetic/Boolean fields against pilot_result.json; {len(discrep)} differ at rel 1e-9 / abs 1e-7, as expected from the trimming mismatch. The mismatch is therefore material to numerical values, while the processing question is explicitly a post hoc robustness diagnostic.",'','| Prep | changed wells | changed retained counts | max MFI change | source-like Gain MAE | source-like B_const MAE | source-like overlap | best model |','|---|---:|---:|---:|---:|---:|---:|---|']
for c,s in summary.items(): lines.append(f"| {c} | {s['changed_wells']}/48 | {s['count_changed_wells']}/48 | {s['max_well_mfi_absolute_difference']:.6g} | {s['source_like_MAE']['gain']:.6f} | {s['source_like_MAE']['constant_interaction']:.6f} | {s['source_like_overlap_count']}/5 | {s['source_like_best_model']} |")
lines += ['', 'The qualitative negative conclusion does not change. Source-like Gain MAE remains worse than B_const in E3CA, E3CB and E3DB; E3DA remains the sole small Gain advantage. The same full-set pattern therefore survives this post hoc trimming diagnostic. This is descriptive robustness evidence only, not validation, a protocol revision, or a new candidate.', '', 'The mismatch matters because pooled trimming lets one technical well influence the other well’s cutoffs, while strict versus closed inequalities can differ at exact boundaries. The primary per-well method avoids that cross-well influence and was the frozen protocol used for the E001 decision. The source-like result should not replace it.', '', 'The assay remains capture-bead PE readout with unverifiable APC gating in these exports. Results are calibration-conditioned target holdout in the same assay, not external validation. No cell/molecular causal inference, biological-noise guarantee, CI, p-value, mechanistic novelty, or acquisition advantage is supported.', '', f"Diagnostic execution: wall {A['usage']['wall_seconds']:.6f} s; CPU {A['usage']['cpu_seconds']:.6f} s; no network/API calls or cost."]
(R/'review/source_like_review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'source_like_sha256':result['source_like_sha256'],'primary_sha256':result['primary_sha256'],'comparison_count':len(records),'discrepancies':len(discrep),'summary':summary},indent=2))

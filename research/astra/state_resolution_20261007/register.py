"""Freeze diagnosis-driven follow-up without altering historical protocols."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.with_name('state_dual_core_20261007')


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    protocol = {
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'status':'diagnosis-driven exploratory follow-up; all old c39 historical exposure retained',
        'question':'Does condition-paired STATE information survive decoder bias and sampling-noise controls, and can sequential planning use real observations better than exact myopic acquisition?',
        'hypotheses':{
            'primary_world':'K_M1 + gamma*K_counterfactual256 predicts native RNA change better than BOTH matched extra-basal nonSTATE control and basal-only model on downstream held-out drug groups.',
            'secondary_endpoint':'Signed finite-cell-noise-corrected squared transcriptomic effect is predictable beyond zero/count/basal controls.',
            'staged_agent':'Two-step empirical planning improves acquired-information decisions over exact myopic planning with the same legal forecasts, empirical samples, source access, three-unit maximum budget and deadline.',
            'interaction':'Fixed-policy difference-in-differences on selected signed corrected effect, not RMS noise. No LLM benefit attributed to a nonLLM policy.'},
        'root_causes_tested':[
            'Original (4*K_M1+K_STATE)/5 changes effective regularization of every original feature; additive gamma0 must reproduce M1 exactly.',
            'f(basal,drug)-basal includes model common reconstruction displacement; test f(basal,drug)-f(basal,DMSO) using identical real basal tensor.',
            'Compare supported short32 and configured256-cell sets;256 resamples existing cells and supplies no new biological information.',
            'Observed squared RNA RMS includes estimated finite-cell sampling variance; do not optimize raw RMS as a validated biological-strength target.',
            'Depth alone may add nothing under exchangeable action-value distributions; require a real dev opportunity, do not rename a heuristic as an LLM gain.'
        ],
        'partitions':'unchanged24train6development6calibration12evaluation chemical parents; all doses/aliases together; old eval already inspected, exploratory',
        'world_methods':{
            'base':'old M1 chemistry/targets/dose/basal kernel, fixed alpha0.1 from old development; frozen base kept intact',
            'additive_controls':['base + gamma*basal_kernel','base + gamma*permuted_counterfactual256_kernel','basal_only','no_change'],
            'representations':['raw_delta32','raw_delta256','paired_DMSO_delta32','paired_DMSO_delta256'],
            'primary_representation':'paired_DMSO_delta256 fixed before outcome fitting, never choose best of four on eval',
            'gamma_grid':[0.0,0.25,1.0],
            'selection':'training fit/development error only; identical3gamma budget; exact ties prefer0; no alpha search; no checkpoint adaptation',
            'preprocessing':'training-only centering and total-variance scale; no changes to actual checkpoint coordinates',
            'pre_relu':'diagnostic only, never treated as valid RNA output or selected model'
        },
        'primary_metric':'per-chemical-group mean native-delta coordinate MSE over3doses,12evaluation groups; paired bootstrap2000 seed1907 conditional on this one source',
        'primary_success':'paired256 additive improvement over matched basal-additive AND basal-only, upper95% group-bootstrap difference<0; exploratory only',
        'endpoint_correction':{
            'formula':'U=mean_g((meanT_g-meanC_g)^2)-mean_g(sample_varianceT_g)/nT-mean_g(sample_varianceC_g)/nC; ddof1',
            'preserve_negative':True,'no_sqrt_or_clipping':True,
            'source':'actual original full144conditions and frozen highdose48screen/validation disjoint cells; source controls unchanged',
            'assumption':'unbiased finite-cell correction under iid cells within source pool; correlated cells/cultures can violate this; no independent biological confirmation',
            'registered_after':'training/development diagnosis only; evaluation corrected values not inspected for this endpoint before this freeze',
            'uncertainty':'six chemical calibration groups absolute scalar residual;80% split-conformal descriptive interval, shared source dependence not certified; positive effect claims require lower bound>0',
        },
        'scalar_heads':{
            'roles':['full_native_corrected','screen_corrected','validation_corrected'],
            'methods':['zero','training_mean','count_only','basal_only','matched_nonSTATE_additive','paired256_STATE_additive'],
            'fit':'same fixed alpha0.1, same gamma[0,.25,1] for last2, train-only normalization; screen and validation fit separately on highdose24train compounds, common selected gamma by validation development error',
            'counts':'available deposited source count metadata only; retrospective availability, never prospective experiment success',
            'reference_selection':'best nonSTATE scalar candidate by development error, never evaluation',
            'refusal':'if interval includes zero retain unknown sign; preserve all candidates and fallback forecast rather than label no effect'
        },
        'agent_gate':'development-only conditional opportunity; no API unless useful specifically LLM choice demonstrated; common myopic comparator both worlds; exact lookahead is explicitly nonLLM',
        'agent_registration':'separate freeze before evaluation after development diagnosis; old and new unsuccessful menus preserved',
        'budgets':{'STATE_forwards':316,'checkpoint_loads':1,'checkpoint_tuning':0,'gamma_choices_each':3,'new_API_calls_allowed_at_this_stage':0},
        'inputs':{str(p.relative_to(OLD)):sha(p) for p in [OLD/'world/metadata_freeze.json',OLD/'world/contract.json',OLD/'world/conditions.csv',OLD/'model_run1/kernels.npz',OLD/'world/sealed_outcomes.npz',OLD/'world/technical_screen_freeze.json']},
        'new_representation_sha256':sha(HERE/'world/representations.npz'),
    }
    for name,obj in [('PROTOCOL.json',protocol),('HISTORICAL_MANIFEST_START.json',{'path':str(OLD/'RUN_MANIFEST.json'),'sha256':sha(OLD/'RUN_MANIFEST.json')})]:
        with (HERE/name).open('x',encoding='utf-8') as f: json.dump(obj,f,indent=2)
    with (HERE/'PROTOCOL_FREEZE.json').open('x',encoding='utf-8') as f:
        json.dump({'created_utc':datetime.now(timezone.utc).isoformat(),'sha256':sha(HERE/'PROTOCOL.json'),
            'correction_evaluation_arrays_exist':(HERE/'verification/bias_corrected_observations.npz').exists(),
            'register_source_sha256':sha(__file__)},f,indent=2)


if __name__=='__main__': main()

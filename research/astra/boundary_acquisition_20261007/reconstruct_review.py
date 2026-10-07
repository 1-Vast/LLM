"""Append-only proof that review-to-freeze changes added audit fields, not math."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent

REVERSE={
    'register.py':[(
        '        permutation="Identical full292source-well key ordering and dose/plate seed42 row permutation for training and target STATE; training matchedsource masks permuted alongside forecasts before subsetB and LOOcentering. Target nativeSTATEdeviation permuted in same292ordering. Preserve identity strata and report changed rows. Same residual model capacity and fitted train-only normalization, no label exclusion.",',
        '        permutation="STATE source-deviation rows shuffled within dose/plate seed42 for both training feature/error construction and target forecasts; preserve identity strata and report changed rows. Same residual model capacity and fitted train-only normalization, no label exclusion.",')],
    'execute.py':[(
        "        sourceaudit.append(dict(context=context,full146source_qualified=True,basal_distance=distance,\n            state_permutation=detail,\n            scaled_covariance_min_eigenvalues={name:float(np.linalg.eigvalsh(method.scale_covariance(cov,\n                public[token+'__ratio_'+name])).min()) for name in models},\n            features_finite=bool(np.all(np.isfinite(x))),priors_finite=bool(np.all(np.isfinite(public[token+'__M2'])))))",
        "        sourceaudit.append(dict(context=context,full146source_qualified=True,basal_distance=distance,\n                                state_permutation=detail))"),
        ("def episode(prior,cov,var,offset,evaluator,arm,tau,normals):\n    started=time.perf_counter()",
         "def episode(prior,cov,var,offset,evaluator,arm,tau,normals):"),
        ("        actual_credits=snapshot.spent,common_cap=13,unused_cap=13-snapshot.spent,stopreason=stopreason,\n        elapsed_seconds=time.perf_counter()-started)",
         "        actual_credits=snapshot.spent,common_cap=13,unused_cap=13-snapshot.spent,stopreason=stopreason)")]
}
EXPECTED={'register.py':'56b511d286e440ebf12dddf2e8205c3c3e88cf41a42d5909e939a3e187cb844a',
          'execute.py':'a374d4216985aa4d42facbf070577f5cd78aed692339e877342d7be31ad3fb6c'}


def main():
    results={}
    for name,substitutions in REVERSE.items():
        raw=(HERE/name).read_bytes();s=raw.decode('utf-8')
        for current,reviewed in substitutions:
            if '\r\n' in s:
                current=current.replace('\n','\r\n');reviewed=reviewed.replace('\n','\r\n')
            if s.count(current)!=1:raise ValueError('Nonunique reversal:'+name)
            s=s.replace(current,reviewed)
        reconstructed=hashlib.sha256(s.encode()).hexdigest()
        results[name]=dict(frozen_current_sha256=hashlib.sha256(raw).hexdigest(),
            reconstructed_review_sha256=reconstructed,expected_review_sha256=EXPECTED[name],
            exact_match=reconstructed==EXPECTED[name],reverse_substitutions=substitutions)
    receipt=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        reason='Verifier requested finite/covariance diagnostics and exact292permutation wording; parent requested per-armCPU. Last prefreeze changes implement only those audit fields. No fit, acquisition, threshold, normaldraws or model changed.',
        no_canonical_files_modified=True,results=results)
    with (HERE/'REVIEW_DELTA_RECONSTRUCTION.json').open('x',encoding='utf-8') as f:
        json.dump(receipt,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({name:r['exact_match'] for name,r in results.items()}))


if __name__=='__main__':main()

"""Exact synthetic observation-equivalence witness; reads no biological values."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/observation_law_search/biology'


def main():
    worlds = {
        'A': {'U': (Fraction(1), Fraction(1, 10)),
              'V': (Fraction(1, 2), Fraction(1, 5))},
        'B': {'U': (Fraction(1, 2), Fraction(1, 5)),
              'V': (Fraction(1), Fraction(1, 10))},
    }
    # N0 fixed at 1000. Independent survival followed by capture gives
    # Binomial(1000, survival*capture), exactly, not merely equal expectations.
    observed = {w: {u: str(s * c) for u, (s, c) in uv.items()}
                for w, uv in worlds.items()}
    assert observed['A'] == observed['B'] == {'U': '1/10', 'V': '1/10'}
    best_killing = {w: min(uv, key=lambda u: uv[u][0]) for w, uv in worlds.items()}
    assert best_killing == {'A': 'V', 'B': 'U'}
    # Identical conditional survivor UMI distribution is stipulated in both
    # worlds; normalized expression and UMI/depth summaries are then identical.
    survivor_umi = [10, 20]
    normalized = [str(Fraction(x, sum(survivor_umi))) for x in survivor_umi]
    assert normalized == ['1/3', '2/3']
    # Even if total survival is supplied, the preselection states of removed
    # cells are not recovered. Survivor state=1; half survive in both worlds.
    preselection_mean = [str(Fraction(1, 2) * 1 + Fraction(1, 2) * z)
                         for z in (0, 2)]
    assert preselection_mean == ['1/2', '3/2']
    result = {
        'status': 'PASS_EXACT_SYNTHETIC_NONIDENTIFIABILITY',
        'biological_files_opened': 0,
        'N0': 1000,
        'worlds_survival_capture': {
            w: {u: [str(s), str(c)] for u, (s, c) in uv.items()}
            for w, uv in worlds.items()},
        'observable_capture_binomial_probability': observed,
        'conditional_survivor_UMI_both_worlds': survivor_umi,
        'normalized_survivor_expression_both_worlds': normalized,
        'best_tumor_killing_intervention': best_killing,
        'preselection_mean_same_survivors_same_survival': preselection_mean,
        'scope': 'unknown intervention-dependent capture/QC; not a claim that actual Norman residuals arise from selection',
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'WITNESS.json'
    assert not target.exists(), 'Existing evidence must be inspected rather than overwritten'
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

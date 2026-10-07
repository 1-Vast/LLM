"""Exploratory knowledge-value study, reusing the original frozen campaign engine.

No changes to original frozen studies, no Vis outcomes, no paid API calls. Execute
from repository root with PYTHONPATH=src:. and BLAS thread counts set to 1.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

import numpy as np

from .acquire import ASSETS, HERE, digest
from .model import METHODS, WEIGHTS, history_lines, pair_kernel, transfer
from research.astra.confirmation_campaign_20261004.design import campaign as c
from research.astra.feedback_validation_20261003.jaaks import build_panels
from tools.datasets.combination_screens import open_vault

ROOT = HERE.parents[2]
PARTITION = ROOT / 'research/astra/confirmation_campaign_20261004/protocol/partition.json'
REGIMES = {'all': (None, [0]), 'n4': (4, [11, 23, 47]), 'n8': (8, [11, 23, 47])}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c.jsonable(value), indent=2, allow_nan=False)+'\n')


def freeze():
    path = HERE / 'freeze.json'
    if path.exists():
        raise FileExistsError('existing freeze is immutable; do not refreeze after outcomes')
    imported = [PARTITION, Path(c.__file__),
                ROOT / 'research/astra/feedback_validation_20261003/jaaks.py',
                ROOT / 'research/astra/feedback_validation_20261003/study.py',
                ROOT / 'research/certified_discovery/screens.py',
                ROOT / 'tools/datasets/combination_screens.py']
    files = list(HERE.glob('*.py')) + [HERE/'PLAN.md', HERE/'contract.json',
             HERE/'download_manifest.json'] + list((HERE/'knowledge').iterdir()) + imported
    dump(path, dict(status='EXPLORATORY; all Jaaks data previously exposed',
                    frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    files={str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files)) if p.is_file()},
                    historical_freezes='read-only; original CRLF hashes not rewritten',
                    raw_outcomes_sha256=digest(ASSETS/'jaaks.csv')))
    print('Frozen metadata, exact model, protocol, and read-only imported code.', flush=True)


def make_kernels(full, drug_kernels):
    pairs = [None] * (int(full.pid.max()) + 1)
    for pid, p in zip(full.pid, full.pairs):
        if pairs[pid] is not None and set(pairs[pid]) != set(p):
            raise AssertionError('pair-ID mismatch')
        pairs[pid] = p
    return {m: pair_kernel(drug_kernels[m], pairs, drug_kernels['drug_ids']) for m in METHODS}


def run_target(full, history, sidm, allowed, forbidden, kernels, choices=None):
    """Predict from history first, then pass target truth solely to the campaign engine."""
    hs = history.arrays['SV']['h_s'].astype(float)
    hv = history.arrays['SV']['h_v'].astype(float)
    pred = {m: transfer(kernels[m], history.pid, (hs + hv) / 2) for m in METHODS}
    records, targets = [], {}
    for role in c.ROLES:
        tg = c.make_target(full, history, sidm, role, allowed_history=allowed, forbidden=forbidden)
        base, verify = tg.scores['C_mean']
        arms = list(c.SIMPLE) if choices is None else ['C_mean']
        if choices is not None and choices['simple'] not in arms:
            arms.append(choices['simple'])
        for m in METHODS:
            weights = WEIGHTS if choices is None else [choices[m]]
            for w in weights:
                arm = f'{m}:{w:g}'
                tg.scores[arm] = ((1-w) * base + w * pred[m][tg.pid], verify)
                arms.append(arm)
        # Target truth is used only after all predictions and orders are fixed.
        truth = c.truth_of(full, tg)
        for arm in arms:
            records.append(c.run_p2(tg, truth, arm, 30))
        targets[(tg.tissue, sidm, role)] = tg
    return records, targets


def average_lines(records):
    values = {}
    for r in records:
        values.setdefault((r['tissue'], r['line']), []).append(r['confirmed'])
    return {k: float(np.mean(v)) for k, v in values.items()}


def average_pair_matrices(records, targets, keys, seeds):
    matrices = [c.pair_matrices([r for r in records if r['seed'] == s], targets, keys) for s in seeds]
    return {t: sum(x[t] for x in matrices) / len(matrices) for t in matrices[0]}


def run():
    out = HERE / 'results'
    if (out/'summary.json').exists():
        raise FileExistsError('evaluation already exists; keep single-pass results intact')
    out.mkdir(exist_ok=True)
    ticket = open_vault(HERE/'freeze.json', HERE/'outcome_access.jsonl',
                        purpose='New exposed-data knowledge-transfer hypothesis; not prior confirmatory reopening',
                        source=ASSETS/'jaaks.csv', root=ROOT)
    panels, builder_report, candidates = build_panels(ticket, path=ASSETS/'jaaks.csv')
    tissues = c.build_tissues(panels, candidates)
    dump(out/'builder_report.json', builder_report)
    split = json.loads(PARTITION.read_text())['split']
    drug_kernels = np.load(HERE/'knowledge/drug_kernels.npz', allow_pickle=False)
    kernels = {t: make_kernels(T, drug_kernels) for t, T in tissues.items()}
    all_records, targets, selections, summaries = [], {}, {}, {}
    for regime, (count, seeds) in REGIMES.items():
        dev = []
        for tissue, full in tissues.items():
            hd, ev = split[tissue]['HD'], split[tissue]['E']
            assert not set(hd) & set(ev)
            for seed in seeds:
                for sidm in hd:
                    hist = history_lines(hd, sidm, count, seed, full.code)
                    rec, _ = run_target(full, c.restrict(full, hist), sidm, hd, ev, kernels[tissue])
                    for r in rec:
                        r.update(seed=seed, regime=regime, phase='HD', history_lines=hist)
                    dev.extend(rec)
        arms = sorted({r['arm'] for r in dev})
        totals = {arm: sum(average_lines([r for r in dev if r['arm'] == arm]).values()) for arm in arms}
        choices = {m: min(WEIGHTS, key=lambda w: (-totals[f'{m}:{w:g}'], w)) for m in METHODS}
        choices['simple'] = min(c.SIMPLE, key=lambda a: (-totals[a], c.SIMPLE.index(a)))
        selections[regime] = dict(choices=choices, development_confirmed=totals)
        dump(out/'development_selection.json', selections)
        print(f'{regime}: HD choices fixed: {choices}', flush=True)
        evaluation = []
        for tissue, full in tissues.items():
            hd, ev = split[tissue]['HD'], split[tissue]['E']
            for seed in seeds:
                for sidm in ev:
                    hist = history_lines(hd, sidm, count, seed, full.code)
                    rec, tgs = run_target(full, c.restrict(full, hist), sidm, hd, ev, kernels[tissue], choices)
                    targets.update(tgs)
                    for r in rec:
                        r.update(seed=seed, regime=regime, phase='E', history_lines=hist)
                    evaluation.extend(rec)
        selected = {m: f'{m}:{choices[m]:g}' for m in METHODS}
        selected.update(C_mean='C_mean', simple_selected=choices['simple'])
        lv = {name: average_lines([r for r in evaluation if r['arm'] == arm]) for name, arm in selected.items()}
        keys = c.sort_keys(lv['C_mean'])
        xs = {name: np.array([vals[k] for k in keys]) for name, vals in lv.items()}
        ii = c.boot_indices(keys)
        baseline = xs['C_mean']
        summary = dict(choices=choices, n_lines=len(keys), seeds=seeds,
            status='EXPLORATORY; known-library new-line prediction, no cell-state features',
            vs_C_mean={name: c.boot_contrast(x, baseline, keys, ii) for name, x in xs.items()},
            totals={name: float(x.sum()) for name, x in xs.items()},
            by_tissue={name: {t: float(sum(lv[name][k] for k in keys if k[0]==t)) for t in tissues} for name in xs},
            per_seed_totals={name: {str(s): sum(average_lines([r for r in evaluation if r['arm']==arm and r['seed']==s]).values())
                                   for s in seeds} for name, arm in selected.items()},
            resource_totals={name: {f: sum(r[f] for r in evaluation if r['arm']==arm)/(2*len(seeds))
                                  for f in ('n_screens','n_verifications','spent','unused')}
                             for name, arm in selected.items()})
        matrices = {name: average_pair_matrices([r for r in evaluation if r['arm']==arm], targets, keys, seeds)
                    for name, arm in selected.items()}
        summary['network_contrasts'] = {}
        for comparator in ('C_mean', 'simple_selected', 'drug_id', 'annotation', 'permuted_network'):
            comparison = c.boot_contrast(xs['network'], xs[comparator], keys, ii)
            comparison['line_pair_sensitivity'] = c.two_way(matrices['network'], matrices[comparator], keys, resamples=5000)
            summary['network_contrasts'][comparator] = comparison
        if regime == 'all' and abs(summary['totals']['C_mean'] - 117.5) > 1e-8:
            raise AssertionError('baseline parity failed: original C_mean must equal 117.5')
        summaries[regime] = summary
        dump(out/f'{regime}_summary.json', summary)
        dump(out/f'{regime}_per_line.json', [{'tissue':k[0], 'line':k[1], **{name:lv[name][k] for name in lv}} for k in keys])
        # Keep campaign purchase/outcome audit, omit lengthy per-round score arrays.
        for r in dev + evaluation:
            r.pop('rounds', None)
        all_records.extend(dev + evaluation)
        print(f'{regime}: E totals {summary["totals"]}', flush=True)
    with (out/'campaigns.jsonl').open('w') as f:
        for r in all_records:
            f.write(json.dumps(c.jsonable(r), separators=(',',':'))+'\n')
    dump(out/'summary.json', summaries)
    print('Completed all prespecified comparisons.', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze', action='store_true')
    args = ap.parse_args()
    freeze() if args.freeze else run()

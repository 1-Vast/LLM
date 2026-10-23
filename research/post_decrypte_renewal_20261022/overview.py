"""Reproduce the design-only overview and lab/pair overlap calculations."""
from collections import Counter
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/post_decrypte_renewal/root/almanac_archive'


def save_or_verify(name, result):
    target = OUT / name
    if target.exists():
        assert json.loads(target.read_text(encoding='utf-8')) == result, name
    else:
        target.write_text(json.dumps(result,indent=2),encoding='utf-8')


def main():
    rows = json.loads((OUT/'ELIGIBLE_DESIGN_ROWS.json').read_text(encoding='utf-8'))
    result = {'by_lab':{},'metadata_grid_counts_by_numericcell':dict(Counter(':'.join(r['context'][2:]) for r in rows))}
    labs, nsc = {}, {}
    for lab in sorted(set(r['context'][0] for r in rows)):
        selected = [r for r in rows if r['context'][0] == lab]
        result['by_lab'][lab] = {'grids':len(selected), 'cells':len(set(tuple(r['context'][2:]) for r in selected)),
            'sameplate':sum(r['single_agent_plates']==[r['plate']] for r in selected),
            'samplepairs':len(set(tuple(tuple(d) for d in r['drug_samples']) for r in selected))}
        labs[lab] = {tuple(sorted(tuple(d) for d in r['drug_samples'])) for r in selected}
        nsc[lab] = {tuple(sorted(d[0] for d in r['drug_samples'])) for r in selected}
    overlap = {'sample_pair_overlap_FF_FG':len(labs['FF']&labs['FG']),
               'nsc_pair_overlap_FF_FG':len(nsc['FF']&nsc['FG']),
               'canonical_sample_pair_counts':{k:len(v) for k,v in labs.items()},
               'nsc_pair_counts':{k:len(v) for k,v in nsc.items()}}
    save_or_verify('ELIGIBLE_OVERVIEW.json',result)
    save_or_verify('LAB_PAIR_OVERLAP.json',overlap)
    print(json.dumps({'existing_metadata_outputs_reproduced':True,'pair_overlap':overlap}))


if __name__ == '__main__':
    main()

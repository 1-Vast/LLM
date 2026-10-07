"""Independently reconstruct report totals from campaign receipts and verify scope."""
from __future__ import annotations
import json
from collections import defaultdict
from .acquire import HERE,digest


def main():
    root=HERE.parents[2]
    split=json.loads((root/'research/astra/confirmation_campaign_20261004/protocol/partition.json').read_text())['split']
    report={}
    for phase in ('','context','interaction'):
        folder=HERE/phase
        freeze=json.loads((folder/'freeze.json').read_text())
        changed=[p for p,h in freeze['files'].items() if digest(root/p)!=h]
        assert not changed,changed
        summary=json.loads((folder/'results/summary.json').read_text())
        values=defaultdict(list);n=0
        with (folder/'results/campaigns.jsonl').open() as f:
            for line in f:
                r=json.loads(line);n+=1
                hd=set(split[r['tissue']]['HD']);ev=set(split[r['tissue']]['E'])
                assert set(r['history_lines'])<=hd
                assert r['line'] not in r['history_lines']
                assert r['line'] in (hd if r['phase']=='HD' else ev)
                assert r['spent']==len(r['screens'])+len(r['verifies'])<=r['cap']
                assert set(r['verifies'])<=set(r['screen_hits'])<=set(r['screens'])
                assert r['confirmed']==len(set(r['verification_hits'])&set(r['screen_hits']))
                if r['phase']=='E':values[(r['regime'],r['arm'],r['tissue'],r['line'])].append(r['confirmed'])
        totals=defaultdict(float)
        for (regime,arm,tissue,line),v in values.items():totals[(regime,arm)]+=sum(v)/len(v)
        for regime,s in summary.items():
            for name,expected in s['totals'].items():
                if phase=='':
                    arm='C_mean' if name=='C_mean' else s['choices']['simple'] if name=='simple_selected' else f'{name}:{s["choices"][name]:g}'
                else:arm='simple' if name=='simple' else f'{name}:{s["choices"][name]:g}'
                assert abs(totals[(regime,arm)]-expected)<1e-9,(phase,regime,name)
        report[phase or 'graph']=dict(records_checked=n,frozen_files_checked=len(freeze['files']),
          history_isolation=True,budget_accounting=True,reported_totals_reproduced=True,freeze_unchanged=True)
    (HERE/'receipt_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

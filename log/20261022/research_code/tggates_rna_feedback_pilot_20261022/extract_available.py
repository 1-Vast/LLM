"""Verify finished official archives and decode only frozen CEL members."""
import json,zipfile
from pathlib import Path
import rna_archive_acquire as a

def main():
    _,jobs,msha=a.load_inputs()
    a.check_freeze(a.PHASE/'ACQUISITION_FREEZE.json',msha,jobs)
    freeze=a.PHASE/'EXTRACTION_FREEZE.json'
    if not freeze.exists():
        inspections=[]
        for job in jobs:
            archive=a.PHASE/'raw_archives'/f"{job['compound_label']}.zip"
            if not archive.exists():continue
            digest=a.verify_archive(job,archive,a.PHASE/'receipts/archive_downloads')
            with zipfile.ZipFile(archive) as z:
                names=[a.safe_member_basename(i.filename) for i in z.infolist() if not i.is_dir()]
            counts={n:names.count(n) for n in sorted(job['allowed_basenames'])}
            assert all(v==1 for v in counts.values()),counts
            inspections.append(dict(compound=job['compound_label'],archive_sha256=digest,selected_counts=counts))
        assert inspections,'No authenticated archive available'
        record=dict(status='CEL_EXTRACTION_FROZEN_AND_AUTHORIZED',manifest_sha256=msha,
            heads_sha256=a.sha256_file(a.HEADS),script_sha256=a.sha256_file(Path(a.__file__)),
            helper_sha256=a.sha256_file(Path(__file__)),selected_basename_rule_verified=True,
            directory_only_inspections=inspections,utc=a.utc_now(),
            scope='Exact 172 basenames; no CEL parsing; all other ZIP payloads stay compressed.')
        with freeze.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    record=a.check_extraction_freeze(freeze,msha)
    assert record['helper_sha256']==a.sha256_file(Path(__file__))
    for job in jobs:
        archive=a.PHASE/'raw_archives'/f"{job['compound_label']}.zip"
        if not archive.exists():continue
        digest=a.verify_archive(job,archive,a.PHASE/'receipts/archive_downloads')
        members=a.extract_selected(archive,job['allowed_basenames'],a.PHASE/'selected_cel_flat',
                                   a.PHASE/'receipts/cel_members')
        receipt=dict(outcome='complete',compound_label=job['compound_label'],archive_sha256=digest,
                     utc_finished=a.utc_now(),member_count=len(members),members=members)
        a.write_receipt(a.PHASE/'receipts/cel_extraction',job['compound_label'],receipt)
        print(json.dumps(dict(compound=job['compound_label'],selected_members=len(members))),flush=True)

if __name__=='__main__':main()

"""Write-once correction of ExpressionSet QC accessor; preserve failed version."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def put(path,text):
    with path.open('x',encoding='utf-8') as f:f.write(text)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
raw=(C/'mas5_single_array.R').read_text()
assert raw.count('se.exprs(calls)[,1]')==1
put(C/'mas5_single_array_v2.R',raw.replace('se.exprs(calls)[,1]','assayDataElement(calls,"se.exprs")[,1]'))
runner=(C/'run_mas5.py').read_text().replace('mas5_single_array.R','mas5_single_array_v2.R').replace("PHASE/'mas5'","PHASE/'mas5_v2'")
put(C/'run_mas5_v2.py',runner)
protocol=(P/'PREPROCESS_PROTOCOL.md').read_text()
protocol+='\n## QC accessor technical revision2\n\nFirst source run completed MAS5 and detection computation but failed before output because se.exprs has no ExpressionSet method. Verified actual affy mas5calls.AffyBatch source constructs ExpressionSet with assayData element se.exprs. Replace only se.exprs(calls) by assayDataElement(calls,"se.exprs"). Keep all numeric transformation/thresholds. Preserve attempt1 code, logs and receipt. Revision2 outputs use mas5_v2; same source barcode, no substitution. Retest source before any remaining array.\n'
put(P/'PREPROCESS_PROTOCOL_V2.md',protocol)
auth=json.loads((P/'PREPROCESS_FREEZE.json').read_text())
auth.update(protocol_sha256=sha(P/'PREPROCESS_PROTOCOL_V2.md'),utc=datetime.now(timezone.utc).isoformat(),
    revision='QC_ACCESSOR_ONLY_AFTER_RETAINED_TECHNICAL_FAILURE')
for old,new in [('run_mas5.py','run_mas5_v2.py'),('mas5_single_array.R','mas5_single_array_v2.R')]:
    del auth['artifacts_sha256'][(C/old).relative_to(ROOT).as_posix()]
    auth['artifacts_sha256'][(C/new).relative_to(ROOT).as_posix()]=sha(C/new)
put(P/'PREPROCESS_FREEZE_V2.json',json.dumps(auth,indent=2))
print(auth['protocol_sha256'])

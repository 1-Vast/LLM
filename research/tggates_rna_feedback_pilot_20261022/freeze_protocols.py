"""Freeze method/preprocessing decisions before the first real CEL parse."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
CODE=ROOT/'research/tggates_rna_feedback_pilot_20261022'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    method=P/'NUMERICAL_PROTOCOL.md'
    amendments=(P/'NUMERICAL_AMENDMENTS.md').read_text(encoding='utf-8')
    with method.open('x',encoding='utf-8') as f:
        f.write(amendments+'\n\n--- Adopted independent contract; amendments above take precedence ---\n\n')
        f.write((P/'ASTRA_METHOD_INDEPENDENT.md').read_text(encoding='utf-8'))
    manifest=json.loads((P/'RNA_IDENTITY_MANIFEST.json').read_text(encoding='utf-8'))
    first=min(s['identity']['BARCODE'] for s in manifest['samples'] if
              s['role']=='source' and s['identity']['COMPOUND_NAME']=='WY-14643')
    artifact_paths=[CODE/'run_mas5.py',CODE/'mas5_single_array.R',P/'RNA_IDENTITY_MANIFEST.json',
        P/'r_dependencies/hgu133plus2cdf_2.18.0.tar.gz',
        P/'r_dependencies/cdf_diagnostic_source/hgu133plus2cdf/data/hgu133plus2cdf.rda',
        P/'annotation/FOUR_GENE_MAPPING.json',method]
    record=dict(preprocessing_authorized=True,utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=sha(P/'PREPROCESS_PROTOCOL.md'),first_source_barcode=first,
        benchmark_peak_rss_limit_bytes=4*1024**3,benchmark_elapsed_limit_seconds=1800,
        artifacts_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in artifact_paths},
        numerical_execution_authorized=False,
        note='Method definitions frozen. Numerical code still requires implementation audit and separate execution freeze.')
    with (P/'PREPROCESS_FREEZE.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()

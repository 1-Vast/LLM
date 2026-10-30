"""Prepare a small English phase handoff; preserve exact selected outcome bytes."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
out = root / "log/20261029"
ev = out / "functional_screen_evidence"
ev.mkdir(parents=True, exist_ok=True)
files = {
 "c6_summary.json":"2026-10-29-paid-feedback-reuse/experiment_summary.json",
 "c6_independent_comparison.json":"2026-10-29-paid-feedback-reuse/independent_comparison.json",
 "g1_summary.json":"2026-10-29-conditional-response-geometry/g1_run/summary.json",
 "g1_independent_comparison.json":"2026-10-29-conditional-response-geometry/root_independent_comparison.json",
 "hl_summary.json":"2026-10-29-local-relation-pilot/primary_summary.json",
 "hl_independent_comparison.json":"2026-10-29-local-relation-pilot/comparison.json",
 "hfi_summary.json":"2026-10-29-functional-index-pilot/primary_summary.json",
 "hfi_independent_summary.json":"2026-10-29-functional-index-pilot/independent_hfi_result.json",
 "hfi_numeric_comparison.json":"2026-10-29-functional-index-pilot/numeric_comparison.json"}
manifest = {"scope":"Selected exact project-owned numerical outputs, not raw measurements or a complete experiment replay",
            "state_interpretation":"Frozen result state fields describe execution time; read later comparison and this handoff for current interpretation",
            "files":[],"local_only_source_reports":[]}
for name, rel in files.items():
    src = root / "research" / rel
    raw = src.read_bytes()
    json.loads(raw)
    assert len(raw) < 2000000
    dest = ev / name
    assert not dest.exists(), "No silent publication overwrite"
    dest.write_bytes(raw)
    manifest["files"].append({"publication_path":name,"source_path":src.relative_to(root).as_posix(),
                              "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})

draft = here / "phase_experience_draft.md"
text = draft.read_text(encoding="utf-8")
paths = []


def local_link(match):
    label, target = match.groups()
    if target.startswith(("https://","http://","#")):
        return match.group()
    src = (here / target).resolve()
    assert src.is_file(), str(src)
    if src not in paths:
        paths.append(src)
    return label + f" [L{paths.index(src)+1}]"


text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",local_link,text)
for i, src in enumerate(paths,1):
    raw = src.read_bytes()
    manifest["local_only_source_reports"].append({"id":f"L{i}","source_path":src.relative_to(root).as_posix(),
                                                 "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
manifest["organization_draft_sha256"] = hashlib.sha256(draft.read_bytes()).hexdigest()

text = text.replace("This synthesis itself performs no network access, experiment, model training or response-data reading.",
                    "The organization pass performed no network access, experiment, model training or response-data reading. The separate reopening source pass below acquired and inspected primary papers; it did not run a new scientific experiment.")
text += '''

## Current primary-source checks and what they change

The 2026-10-29 reopening obtained three recent originals and one foundational pharmacological prior. These are targeted method readings, not a comprehensive novelty survey or reproduced author experiments.

| Original source | Method actually inspected | Consequence for this research |
|---|---|---|
| [Zeng et al., CVPR 2026, Label What Matters](https://openaccess.thecvf.com/content/CVPR2026/html/Zeng_Label_What_Matters_Modality-Balanced_and_Difficulty-Aware_Multimodal_Active_Learning_CVPR_2026_paper.html) | Complete 9-page official PDF; coordinator read p1 and pp3-5. RL-MBA selects samples for labels with multimodal inputs already supplied, updates fusion and selection, uses a fixed validation split and optionally a reward relative to precomputed baseline curves. | A useful example of adaptive information use. It supplies neither a paid modality-acquisition action nor evidence that measuring a different drug or dose saves functional assays. Validation and policy-training information must enter a fair accounting. The original 8 MB truncated attempt remains inadmissible; the complete 8,093,426-byte replacement is separately identified. |
| [Chen et al., ACL 2026, Reasoning While Asking: Transforming Reasoning Large Language Models from Passive Solvers to Proactive Inquirers](https://aclanthology.org/2026.acl-long.1619/) | Complete 22-page official PDF; p1 and pp3-5 inspected. Teacher uncertainty is operationalized as mean negative log probability of observed tokens. SFT includes simulated response tokens; RL masks simulator responses and rewards correct, helpful interaction. | Asking/feedback coupling has a concrete prior, with a simulator carrying hidden intent and a designed interaction reward. A simulator answer is not an independent biological measurement. Neither clarification wording nor the generic closed loop establishes a new common-screen mechanism. The initial search-note title was corrected against the actual PDF. |
| [Rank-guided learning accelerates automated enzyme engineering, Nature Communications 2026](https://doi.org/10.1038/s41467-026-76264-2) | Formal JATS, Sec3,4,12-16,26 and license inspected. REAP combines a frozen protein-model backbone, a trainable head, ranking plus regression, 100-network uncertainty, UCB selection and new automated experiments. Pair subsampling is optional and was not used in the study. | Rank supervision and experimental feedback already have a recent concrete precedent. Its enzyme sequence, assay and validation resources differ from common drug-response tables. A claim based merely on adding rank loss, uncertainty or an agent to a closed loop would not distinguish our method. |
| [Gujral, Peshkin and Kirschner, PNAS 2014, Exploiting polypharmacology for drug target deconvolution](https://doi.org/10.1073/pnas.1403080111) | Official PMC HTML: s3 panel selection; main s5 deconvolution/collinearity paragraph; s6 validation paragraphs; s8/s10 assumptions and dose. B4/PCA selects inhibitors; elastic net relates a quantitative drug-kinase matrix to migration. The paper states collinearity limits and uses expression filtering and siRNA validation. | The intervention-dictionary lead has a direct domain prior, beyond generic active learning. The source assumes comparable intracellular accumulation and in-vitro/in-cell behavior, and uses a 500 nM target profile with a dose-response-derived phenotype at 500 nM. Its molecular interpretation cannot be attributed to ordinary functional data plus categorical labels alone. A new contribution still needs a different, useful operation and attainable evidence. |

The common-screen data policy survives these checks. Molecular target attribution remains conditional on credible drug/dose intervention information. Lack of such information is not a reason to reject ordinary functional prediction; it limits which biological explanation may be claimed. The shared dose-map lead is already part of the old A.v1 potency family. No new algorithmic winner or fresh hypothesis test is declared in this phase handoff.

## Evidence and replay boundaries

The following files preserve exact project-owned outcome bytes. [The evidence manifest](functional_screen_evidence/evidence_manifest.json) binds published copies to original local paths and SHA256 identities, and separately identifies local-only reports. L1 and subsequent L identifiers above are provenance labels, not promises that those local reports were published. No relative link requires an unpublished research directory.

| Study | Selected original outputs included here |
|---|---|
| C6 | [Primary summary](functional_screen_evidence/c6_summary.json), [independent comparison](functional_screen_evidence/c6_independent_comparison.json) |
| G1 | [Primary summary](functional_screen_evidence/g1_summary.json), [independent comparison](functional_screen_evidence/g1_independent_comparison.json) |
| H_L | [Primary summary](functional_screen_evidence/hl_summary.json), [independent comparison](functional_screen_evidence/hl_independent_comparison.json) |
| H_FI | [Primary summary](functional_screen_evidence/hfi_summary.json), [independent summary](functional_screen_evidence/hfi_independent_summary.json), [numeric comparison and limits](functional_screen_evidence/hfi_numeric_comparison.json) |

These summaries permit inspection of reported outcomes and computational-comparison scope. Full frozen protocols, implementations, training assets, complete raw data, protected confirmation material and third-party full texts are not included in this dated supplement. A new clone cannot fully replay these studies from this supplement alone. Hash equality preserves bytes; it does not establish scientific validity. Original execution-time status strings remain unchanged, including C6's pending-verification status; later comparison records document the completed calculation audit.

The requested organization worker was gpt-6.1-terra; a request is not effective-backend telemetry. Effective model, native token use and native cost are unknown. The coordinator inspected primary outputs and source passages; independent content review is recorded in the accompanying review. DeepSeek DS029 formatted five prescribed source-status rows: all thirty fields matched. Parser qualification and scientific judgments came from the coordinator. Its one isolated tool-disabled call reported 861 input, 385 output and 256 cache-read tokens; paid cost and effective model were not supplied. No result is accepted because an agent, process or test reported PASS.
'''
(ev/"evidence_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
target = out/"functional_screen_research_experience.md"
assert not target.exists(), "No silent publication overwrite"
target.write_text(text,encoding="utf-8")
print(json.dumps({"report":str(target),"report_bytes":target.stat().st_size,"exact_outputs":len(files),
                  "local_only_source_identities":len(paths),"draft_sha256":manifest["organization_draft_sha256"]}))

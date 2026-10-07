"""Draft and then freeze one bounded top-five evidence acquisition comparison."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / "research/astra/decision_opportunity_20261007"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def draft():
    previous = json.loads((PREVIOUS / "PROTOCOL.json").read_text())
    arms = [dict(name="M0_KG8", model="M0", acquisition="KG", uncertainty="common", max_A=8, stopping=False),
            dict(name="M2_KG8", model="M2", acquisition="KG", uncertainty="common", max_A=8, stopping=False),
            dict(name="M2_KG4096", model="M2", acquisition="KG", uncertainty="common", max_A=8, stopping=False, normal_draws=4096),
            dict(name="M0_fixed8", model="M0", acquisition="fixed", uncertainty="common", max_A=8, stopping=False),
            dict(name="M2_fixed8", model="M2", acquisition="fixed", uncertainty="common", max_A=8, stopping=False),
            dict(name="M2_fixed5", model="M2", acquisition="fixed", uncertainty="common", max_A=5, stopping=False),
            dict(name="M0_boundary_common", model="M0", acquisition="boundary", uncertainty="common", max_A=8, stopping=True),
            dict(name="M2_boundary_common", model="M2", acquisition="boundary", uncertainty="common", max_A=8, stopping=True),
            dict(name="M2_boundary_common_no_stop", model="M2", acquisition="boundary", uncertainty="common", max_A=8, stopping=False),
            dict(name="M2_boundary_residual", model="M2", acquisition="boundary", uncertainty="residual", max_A=8, stopping=True),
            dict(name="M2_boundary_design", model="M2", acquisition="boundary", uncertainty="design_missingness", max_A=8, stopping=True),
            dict(name="M2_permuted_boundary", model="M2_permuted", acquisition="boundary", uncertainty="residual", max_A=8, stopping=True)]
    obj = dict(schema="boundary_evidence_acquisition_v1", created_utc=datetime.now(timezone.utc).isoformat(),
        status="Exposed-development diagnostic only; all five whole public profiles were exposed in predecessor studies",
        question="Which top-five incumbent-versus-challenger comparisons warrant another paid first-well observation, and can native frozen STATE reduce their cost?",
        contexts={"PANC-1":"c20.h5ad", "HepG2/C3A":"c27.h5ad", "HOP62":"c31.h5ad", "Hs 766T":"c12.h5ad", "C32":"c26.h5ad"},
        exposure="All five evaluated descriptively; none is a new holdout. HOP62 fixed-vsKG miss previously identified posthoc, with no drug-specific fix permitted.",
        world_model=dict(checkpoint_sha256="2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3",
                         adaptation="No STATE weight or global coefficient update; M2=M0+0.5 source-matched frozen STATE deviation"),
        menu=previous["menu"], endpoint=previous["primary"], arms=arms,
        training=dict(contexts=45, exclusion="Five test/development contexts excluded from all fits and threshold choices",
                      empirical_error="For reference context l, M0_LOO uses precision weights renormalized after excluding l; M2_LOO adds 0.5*(STATE_l minus STATE mean over other44 source-qualified references).",
                      target="log((M2_LOO_B - observed_reference_B)^2 + floor); floor=0.01*median positive training residual squared, with numerical lower bound1e-12",
                      features=["log(abs(0.5 source-matched STATE context deviation)+1e-12), i.e. STATE-vs-empirical scalar disagreement", "nearest centered-basal cosine distance to other44 references", "log10 dose_uM", "B plate one-hot", "reference availability fraction", "STATE source coverage fraction", "log reference-B response variance with floor1e-12", "availability/STATE-coverage missingness flags"],
                      fit="Standardize from training rows; ridge lambda1000 fixed with unpenalized intercept. No hyperparameter grid. Genuine nested whole-context OOF: excluded outer context cannot enter any inner reference mean, STATE mean, basal distance, variance, coverage, error target, floor, normalization or fit. Row context also excluded when constructing its reference features. Refit all45 for exposed-context inference.",
                      control="Design/missingness-only has identical stored column dimensions/ridge, STATE disagreement/basal distance/response-variance columns zeroed. It has fewer active parameters, so equal width is not claimed as equal effective capacity; no parameter selection opportunity",
                      covariance="Same training-only commonC,obsvar,offset as predecessor. Candidate variance ratio r=clip(exp(0.5*(predicted_logerror-mean training predicted_logerror)),0.5,2). Prior covarianceD*C*D whereD=diag(sqrt(r)); observation noise remains common.",
                      calibration_limit="STATE reference outputs are in-sample. OOF empirical/residual fitting does not make checkpoint residual uncertainty independently calibrated."),
        source_support="Training error rows require observed A/B and a present matched STATE-B source; absent STATE is never encoded as measured zero. Missing reference rows are explicitly counted. Every one of146target A/B sources and matchedSTATEforecast must qualify or execution blocks without trimming menu.",
        acquisition=dict(boundary="Current incumbent top5 and all outside candidates; each j,k gap=mean_j-mean_k>=0. For an A candidate i, observation-induced gap SDs=abs(Cji-Cki)/sqrt(Cii+obsvar_i). Score expected positive crossing max_jk[s*phi(gap/s)-gap*Phi(-gap/s)]. Zero for s=0. This is a correlated Gaussian surrogate, not calibrated information gain.",
                         tie="Highest score, then lowest canonical menu index",
                         update="Same common Gaussian observation update yA-offset; final highest5 posterior means",
                         fixed="Screen original prior topK, retaining same posterior update",
                         KG="Predecessor64 seed42 normal draws; controls retain nonpositive-MonteCarlo-gain stop. One registered M2KG4096 comparator uses4096 seed42 draws (extraCPU only) to check analytical boundary vs MonteCarlo resolution; no drawcount tuning.",
                         stop="Boundary arms stop when best surrogate crossing gain <= tau; tau=0.1*median initial maximum boundary score over45 LOO M0 reference contexts using their own excluded-context common covariance/noise. Shared M0-based heuristic fraction gives STATE no threshold privilege, no reward/cost claim or outcome-tuned threshold.",
                         minimum_A=0, maximum_A=8, B=5, common_resource_cap=13, cost_A=1, cost_B=1),
        permutation="Identical full292source-well key ordering and dose/plate seed42 row permutation for training and target STATE; training matchedsource masks permuted alongside forecasts before subsetB and LOOcentering. Target nativeSTATEdeviation permuted in same292ordering. Preserve identity strata and report changed rows. Same residual model capacity and fitted train-only normalization, no label exclusion.",
        controls="M0/M2 common KG8, M0/M2 fixed8, M2 fixed5; M0/M2 unscaled boundary isolates world-model effect under the same policy; M2 boundary no-stop isolates stopping; design/missingness-only isolates supported condition/missingness advantage; matched permutation checks correct STATE-candidate alignment.",
        diagnostics=["OOF train-context residual ranking, shrink factors and covariance eigenvalues", "All5context raw B utility and actual costs", "Every screen decision and stop reason", "Initial/final flags and swapBcontributions", "Paid original source identity/duplicates/unused credits", "AllK saved-prefix cost curves including harmful points", "Source bytes/CPU, no new wet/API/inference"],
        primary="Descriptive raw differences for each context vs M0KG8 and M2KG8; report mean and all contexts; no population CI, selected success threshold or new biological evidence claim",
        promotion="No scientific policy promotion merely from this exposed diagnostic; any reusable paid-scope/budget contract may be separately verified.",
        no_tuning="No additional target, model, dose-specific override, covariance floor, threshold fraction, ridge or arm after target evaluation.",
        execution="First build training fit/threshold and public-prior/evaluator-private scalar packet after reviewed protocol freeze; acquisition sees priors and only chargedA reveals; fiveB commits before release; CaseStore sole cost/result ledger")
    write(HERE / "DRAFT_PROTOCOL.json", obj)
    print(str(HERE / "DRAFT_PROTOCOL.json"))


def freeze():
    obj = json.loads((HERE / "DRAFT_PROTOCOL.json").read_text())
    sources = [HERE / "register.py", HERE / "method.py", HERE / "execute.py", HERE / "test_boundary.py",
               PREVIOUS / "run.py", PREVIOUS / "PROTOCOL.json",
               ROOT / "research/astra/zeroshot_context_20261007/world_models.py",
               PREVIOUS / "sources/genesets.apoptosis.json"]
    obj["created_utc"] = datetime.now(timezone.utc).isoformat()
    obj["source_dependencies"] = {str(path.relative_to(ROOT)).replace("\\", "/"):digest(path) for path in sources}
    split=json.loads((ROOT/'research/astra/zeroshot_context_20261007/SPLIT.json').read_text())
    cache=ROOT/'data/external/tahoe_zeroshot_20261007'
    upstream=[cache/kind/(f'c{i}.h5ad.npz') for i in range(50) for kind in ('observations','state_forecasts')]
    checkpoint=ROOT/'data/external/arc_state/weights/zeroshot/state_generalization_zeroshot_X_hvg/checkpoints/final.ckpt'
    upstream.append(checkpoint)
    upstream.append(ROOT/'data/virtual_cell/tahoe_c39_x_hvg_feature_names.json')
    obj['upstream_dependencies']={str(path.relative_to(ROOT)).replace('\\','/'):digest(path) for path in upstream}
    if obj['upstream_dependencies'][str(checkpoint.relative_to(ROOT)).replace('\\','/')]!=obj['world_model']['checkpoint_sha256']:
        raise ValueError('Native STATE checkpoint identity changed')
    write(HERE / "PROTOCOL.json", obj)
    write(HERE / "FREEZE.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=digest(HERE / "PROTOCOL.json"), new_boundary_target_projections_before_freeze=False,
        whole_profiles_previously_exposed=True, all_parameters_fixed_without_target_reward_selection=True))
    print(digest(HERE / "PROTOCOL.json"))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["draft","freeze"])
    args=parser.parse_args()
    (draft if args.command=="draft" else freeze)()

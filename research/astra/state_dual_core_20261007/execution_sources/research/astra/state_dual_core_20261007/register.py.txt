"""Write-once bounded native-RNA registration, before reading treated RNA."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def main():
    from agent.llm import MAESTROSettings
    settings = MAESTROSettings.from_workspace(ROOT, require_provider=False)
    write(HERE / 'ENVIRONMENT.json', {
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'logical_cpu_count': psutil.cpu_count(),
        'memory': dict(psutil.virtual_memory()._asdict()),
        'disks': {p: dict(psutil.disk_usage(p)._asdict()) for p in ['C:/', 'D:/']},
        'gpu': subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,driver_version', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip(),
        'packages': {p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'torch', 'arc-state', 'anndata', 'scikit-learn', 'rdkit', 'psutil']},
        'chat_provider_configured': bool(settings.api_key and settings.base_url and settings.chat_model),
        'chat_model': settings.chat_model, 'credentials_recorded': False,
        'execution_budget': 'one resident STATE model; 2 CPU threads for linear algebra; 48 compounds, 144 conditions, 32 real control samples per request; no parameter adaptation',
    })
    protocol = {
        'study': 'Condition-qualified native STATE information acquisition v1',
        'status': 'EXPLORATORY; c39 previously exposed and checkpoint pretraining overlap unresolved',
        'registered_utc': datetime.now(timezone.utc).isoformat(),
        'scientific_decision': 'Choose which of two single-drug high-dose conditions to characterize for a larger native transcriptomic response after optionally buying one lower-dose signature.',
        'supported_endpoint': 'Mean squared error of same-plate-reference-normalized native 2000-coordinate X_hvg pseudobulk change. Secondary response magnitude is RMS of that change. Not ATP, survival, synergy or a named pathway.',
        'unit': 'Chemical parent connectivity group; all three doses and aliases grouped. Only one historically exposed cell context; source plates shared, independent cultures unknown.',
        'initial_information': 'Exact drug/dose/time/cell/plate metadata, public chemical structures and target annotations, official processed control cells and frozen checkpoint predictions; no held-out treated RNA. Retrospective public reference controls are NOT certified prospective basal samples.',
        'H1_primary': 'Frozen STATE intervention-change features improve held-out chemical-group native delta MSE over BOTH the strong metadata/chemistry/target/basal non-STATE model and the strongest simple mean/no-change baseline selected on development data.',
        'H2_secondary': 'An LLM acquisition/selection policy increases selected observed high-dose RNA magnitude over decision-sensitivity acquisition using the same forecasts, tools, one acquisition and one reveal.',
        'H3_secondary': 'Positive additive interaction (D-C)-(B-A) on selected observed RNA RMS, unexplained by different information budgets. Six disjoint evaluation comparisons; descriptive only, no powered synergy claim.',
        'selection': 'world/metadata_freeze.json; 48 distinct chemical parents ordered by SHA256 drug name, source metadata eligibility only. 24 train,6 development,6 calibration,12 evaluation compounds, 3 doses each.',
        'pretraining_holdout': False,
        'source_transfer_claim': False,
        'source_confounding': 'Doses may reside on different plates. Each response uses its own same-plate controls. Low-to-high acquisition is a learned dose+plate transport association validated on development groups, never direct same-condition evidence.',
        'methods': {
            'M0': 'No change and training-only per-dose mean change; stronger chosen by development group MSE.',
            'M1': 'Kernel ridge on equal-weight chemical Morgan Tanimoto, public target cosine, dose equality and real basal-context linear kernels.',
            'M2': 'Same four M1 blocks plus a frozen STATE predicted intervention-change linear kernel; small dual ridge head, no checkpoint update.',
            'controls': ['metadata-only chemistry/target/dose', 'basal-only plus dose', 'public-metadata-missingness plus dose', 'M2 with drug identity permuted within split, preserving dose and plate strata when possible', 'raw frozen STATE delta', 'no-change'],
            'M3': 'Not run in this bounded study; a negative M2 requires a distinct diagnosed adaptation hypothesis, not an automatic tuning expansion.',
        },
        'model_selection': 'Each learned kernel gets identical alpha grid [0.1,1,10], training-only centering/scaling, train fitting and development MSE selection. No refit on development. Scalar RMS head uses same kernel and selected vector alpha, no separate search. No clipping predicted signs or endpoints.',
        'preprocessing': 'Use stored official X_hvg unchanged. All 2000 coordinates are numerical native features, 31 unnamed axes never assigned gene identities. Basal normalization/kernel scales from training only.',
        'primary_statistic': 'Per-drug average over three dose-level coordinate MSEs, then average evaluation drugs. Paired chemical-group bootstrap 2000 resamples seed731; descriptive uncertainty conditional on this context/plates, not independent culture CI.',
        'primary_success': 'M2 lower error than both registered comparators, with upper 95% paired drug-bootstrap bound below zero for both; exploratory evidence only regardless of outcome.',
        'secondary_metrics': ['coordinate MAE', 'scalar RMS error', 'high-dose candidate pair ordering, ties score half', '80% split-conformal simultaneous-across-doses intervals calibrated on six drug-group max absolute scalar residuals', 'selective risk by interval width', 'dose/plate error', '6,12,24-training-drug label efficiency with fixed alpha selected in full-training run; exploratory, no model reselection'],
        'agent_gate': 'Development-only acquisition diagnostic first. A separate DECISION_PROTOCOL and hash freeze before evaluation. No LLM calls if returned observations cannot change a useful comparison. Replay access units are not laboratory credits.',
        'inference': 'One resident exact pinned STATE checkpoint; native homogeneous predict_step,32 real same-plate basal cells with replacement, seed731. No real treated values passed into prediction. Native short sequence permitted by implementation; no full 256-cell inference equivalence claim.',
        'budgets': {'chemical_groups': 48, 'dose_conditions': 144, 'hyperparameters_each_learned_model': 3, 'checkpoint_adaptations': 0, 'llm_calls_cap': 24, 'new_wet_experiments': 0},
        'failed_attempts': 'Persist failures, unsupported menu rows and previous drafts; no silent backend substitution.',
        'frozen_inputs': {str(p.relative_to(HERE)): sha(p) for p in [HERE/'world/metadata_freeze.json', HERE/'world/conditions.csv', HERE/'world/basal_controls.npz', HERE/'world/contract.json']},
        'drug_metadata': {'path': 'tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/tahoe_drugs.raw', 'sha256': sha(ROOT/'tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/tahoe_drugs.raw')},
    }
    write(HERE / 'PROTOCOL.json', protocol)
    write(HERE / 'PROTOCOL_FREEZE.json', {'sha256': sha(HERE/'PROTOCOL.json'), 'frozen_utc': datetime.now(timezone.utc).isoformat(), 'treated_outcomes_exist': (HERE/'world/sealed_outcomes.npz').exists(), 'registration_source_sha256': sha(__file__)})


if __name__ == '__main__':
    main()

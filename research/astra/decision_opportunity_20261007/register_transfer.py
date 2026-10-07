"""Freeze the previously exposed three-context transfer before target projections."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent = json.loads((HERE / "PROTOCOL.json").read_text())
    sources = [HERE / "PROTOCOL.json", HERE / "PROTOCOL_FREEZE.json", HERE / "run.py",
               HERE / "transfer.py", HERE / "budget_frontier1/SUMMARY.json",
               HERE / "compact_packet2/PACKET_MANIFEST.json",
               ROOT / "research/astra/zeroshot_context_20261007/world_models.py"]
    arms = [dict(name="M0_fixed5", model="M0", policy="fixed_top_prior", screens=5, cap=10),
            dict(name="M2_fixed5", model="M2", policy="fixed_top_prior", screens=5, cap=10),
            dict(name="M0_KG8", model="M0", policy="knowledge_gradient", screens=8, cap=13),
            dict(name="M2_KG8", model="M2", policy="knowledge_gradient", screens=8, cap=13),
            dict(name="M2_fixed8", model="M2", policy="fixed_top_prior", screens=8, cap=13)]
    protocol = dict(schema="state_direction_task_transfer_v1", created_utc=datetime.now(timezone.utc).isoformat(),
        status="Exploratory task transfer to three contexts with whole RNA profiles exposed by prior studies; NOT untouched confirmatory validation",
        contexts={"HOP62": "c31.h5ad", "Hs 766T": "c12.h5ad", "C32": "c26.h5ad"},
        exposure=dict(training="45 checkpoint-training contexts fit all panel means/covariance/noise; they are not evidence of STATE generalization",
                      development="PANC-1 and HepG2/C3A selected 39-coordinate direction and diagnostic K5 after their direction outcomes were exposed",
                      transfer="These three contexts were not used to choose direction or K in this study, but their entire RNA profiles were exposed by earlier world-model/agent studies. The newly frozen task is not new blind data.",
                      newly_computed_task_projections_before_freeze=False),
        menu=parent["menu"], primary=parent["primary"], arms=arms,
        world_model=dict(checkpoint_sha256="2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3",
                         coefficient=.5, adaptation="None; native pretrained STATE weights remain frozen",
                         M0="Same precision-weighted 45-context empirical native RNA mean",
                         M2="M0 plus 0.5 frozen STATE target-context deviation from training STATE mean"),
        acquisition=parent["gaussian_heuristic"], final_flags=5,
        primary_comparison="M2_fixed5 vs M0_KG8: report all three raw per-context signed RNA utility differences and arithmetic mean. Success requires mean M2_fixed5 utility >= mean M0_KG8 utility while spending 3 fewer credits per context; no fitted noninferiority margin.",
        paired_controls="M0_fixed5 provides equal10credit information envelope; M2KG8 and M2fixed8 disclose fixed13credit comparisons. All146 labels stay; condition mismatch blocks rather than trims.",
        costs="One simulated credit per purchased public source profile; 5A+5B=10 or8A+5B=13. Actual cached data/CPU, not new cultures; both costs reported separately.",
        no_future_tuning="No candidate/menu/target/K/coefficient/covariance/normal seed changes after projection. Report negative contexts and all arms.",
        nonclaims=["Apoptosis function or protein activity", "Independent population-level biological gain", "LLM agent superiority", "New STATE architecture", "Calibrated Gaussian information gain"],
        future_confirmation="Requires sealed independent contexts/measurement units; no fresh holdout is constructed from these previously exposed profiles.",
        source_dependencies={str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in sources})
    path = HERE / "TRANSFER_PROTOCOL.json"
    with path.open("x", encoding="utf-8") as f:
        json.dump(protocol, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")
    receipt = dict(created_utc=datetime.now(timezone.utc).isoformat(), protocol_sha256=digest(path),
                   task_transfer_projection_read_before_freeze=False,
                   prior_full_profiles_and_development_direction_already_exposed=True)
    with (HERE / "TRANSFER_FREEZE.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()

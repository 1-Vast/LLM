"""Write FREEZE.json (immutable): SHA256 of the protocol, S0 contract, code and inputs, before any label is read."""
import json
import time

from . import common as cm

FILES = (
    [p for p in sorted(cm.HERE.glob("*.py")) if p.name != "make_freeze.py"]
    + [cm.HERE / "PROTOCOL_V1.md", cm.HERE / "PROTOCOL_V1_1.md", cm.HERE / "PLAN.md", cm.FREEZE_V1]
    + sorted((cm.HERE / "archive_v1").glob("*.py"))
    + [cm.HERE / "results" / n for n in ("s1_g1.json", "s1_mono_config.json", "s1_value_checks.json", "s2_dev_selection.json", "s2_dev_summary.json", "s2_gates.json", "s2_dev_records.pkl")]
    + [cm.S0 / n for n in ("observation_contract.json", "s0_facts.json", "source_manifest.json", "cell_identity_map.csv",
                           "drug_identity_map.csv", "coverage_all_gdsc2_records.csv.gz", "ceiling_diagnostic_target_line_counts.csv",
                           "S0_REPORT.md", "overlap_with_jaaks.md")]
    + sorted((cm.HERE / "decisions").glob("*.md")) + [cm.HERE / "literature" / "DESIGN_LESSONS.md"]
    + [cm.ROOT / p for p in (
        "research/astra/confirmation_campaign_20261004/design/campaign.py",
        "research/astra/feedback_validation_20261003/jaaks.py", "research/astra/feedback_validation_20261003/study.py",
        "research/certified_discovery/screens.py", "research/certified_discovery/xlsx.py",
        "tools/datasets/combination_screens.py",
        "research/astra/confirmation_campaign_20261004/protocol/partition.json",
        "research/astra/knowledge_transfer_20261004/context/raw/GDSC_progeny_activities.csv",
        "data/external/gdsc2_fitted/GDSC2_fitted_dose_response_27Oct23.xlsx",
        "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv")]
)


def main():
    if cm.FREEZE.exists():
        raise FileExistsError("freeze is immutable; record amendments in AMENDMENTS.md instead")
    files = {str(p.relative_to(cm.ROOT)).replace("\\", "/"): cm.file_sha256(p) for p in FILES}
    cm.FREEZE.write_text(json.dumps(dict(
        status="PROTOCOL V1.1 (post-outcome DEVELOPMENT-ONLY repair of the fine-tune grid; v1 results retained) FROZEN BEFORE THE REPAIRED DEV RUN",
        frozen_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=files), indent=1) + "\n", encoding="utf-8")
    print(f"frozen {len(files)} files")


if __name__ == "__main__":
    main()

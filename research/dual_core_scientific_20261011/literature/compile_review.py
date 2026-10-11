"""Compile verified source receipts and a bounded, evidence-aware reading list."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def html_metadata(path: Path) -> dict:
    metadata = {}
    source = path.read_text(encoding="utf-8")
    for tag in re.findall(r"<meta\s+([^>]+)>", source):
        attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))
        name = attrs.get("name", "")
        if name.startswith("citation_"):
            metadata.setdefault(name, []).append(html.unescape(attrs.get("content", "")))
    return metadata


def source_receipt(path: str) -> dict:
    full = HERE / path
    body = full.read_bytes()
    return {"path": path, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


SPECS = [
    ("strong2015evsi", "raw/evsi_primary.html", "html", 2015, "journal",
     "EVSI is expected improvement in the best posterior terminal decision relative to the current best decision, before subtracting acquisition cost.",
     "Information gain or prediction improvement alone is not the same quantity. A model-based estimate need not equal realized net benefit.",
     "Evaluate each observation against the remaining terminal decision and retain a no-purchase option.",
     "EVSI is established methodology; an EVSI implementation is not a new scientific algorithm."),
    ("frazier2009kg", "raw/kg_crossref.json", "crossref", 2009, "journal",
     "Correlated Gaussian beliefs support sequential information acquisition in ranking and selection.",
     "Gaussian-belief assumptions and model adequacy are separate from biological validity.",
     "Keep a correlated Gaussian or ridge-based acquisition policy as a strong cheap baseline.",
     "Correlated belief updates and knowledge gradient predate MAESTRO."),
    ("gupta2025feedback", "raw/gupta_arxiv.html", "html", 2025, "arxiv_preprint_verified",
     "In genetic perturbation and molecular discovery benchmarks, permuting experimental feedback did not change tested LLM agents' performance; linear bandits and GP optimization outperformed them.",
     "This does not prove every LLM fails, or establish MAESTRO-specific efficacy.",
     "Separate language-derived priors from quantitative posterior updates; include real-versus-permuted feedback and GP/linear controls.",
     "Decoupling LLM priors from posterior acquisition and nearest-neighbour hybrid sampling is already prior art."),
    ("roohani2025biodiscovery", "raw/biodiscovery_primary.html", "html", 2025, "conference",
     "An LLM agent designs genetic perturbation experiments using literature, code and critique, evaluated against Bayesian optimization across six datasets.",
     "Its reported improvement is for its endpoints and comparators, not proof of chemical selectivity or MAESTRO's dual-core loop.",
     "Test the agent's distinct action proposals under the same measured-observation budget and compare with conventional LLM-plus-tool and deterministic design.",
     "Literature-guided closed-loop biological experiment design is not a new workflow."),
    ("tosh2025batchie", "raw/active_combo_2025.html", "html", 2025, "journal",
     "BATCHIE uses probabilistic models and information theory to select adaptive batches; retrospective and prospective combination screens include independent follow-up experiments.",
     "Combination viability and prospective validation do not certify an L1000-to-PRISM bridge or LLM contribution.",
     "Respect physical batches, shared experiments and turnarounds; compare realized endpoint benefit and uncertainty, not only entropy reduction.",
     "Probabilistic adaptive batch drug design and uncertainty-driven biological screening already exist."),
    ("wang2026cxcl9", "raw/active_mechanistic_2026.html", "html", 2026, "journal",
     "Active learning with prior-knowledge logic-ODE models guides perturbation experiments and identifies regulators of measured CXCL9 in pancreatic cancer cells.",
     "The two-background CXCL9 dataset is not killing, clinical efficacy or proof of an autonomous language agent; model-input time grids are not a measured time course.",
     "Use observed perturbation-response endpoints and experimentally distinguishable hypotheses; the small published dataset can check assay-bound contracts.",
     "Mechanistic-model plus active-learning architecture is already directly overlapping work."),
    ("demeo2025drugreflector", "raw/drugreflector_crossref.json", "crossref", 2025, "journal",
     "Transcriptomics-based active deep learning with lab-in-the-loop signature refinement improves phenotypic hit rates in two hematological campaigns.",
     "Its reported fold gains are not transferable to context-selective killing or current replay budgets.",
     "Compare adaptive refinement against an unchanged transcriptomic baseline and independent measured endpoints.",
     "Transcriptomics plus adaptive phenotypic hit-finding is existing prior art."),
    ("fannjiang2022feedbackshift", "raw/feedback_conformal_primary.html", "html", 2022, "journal",
     "Model-driven biomolecular design creates dependence between training and selected test inputs; feedback-covariate-shift conformal sets explicitly account for this dependence.",
     "Ordinary split-conformal marginal coverage does not automatically protect adaptively selected high-score candidates; feedback-shift assumptions and weighting must be satisfied.",
     "Calibrate and audit the deployed policy or complete episode on independent calibration units; report selected-set and shift-stratum performance.",
     "Feedback-aware conformal prediction is an established statistical idea."),
    ("angelopoulos2022crc", "raw/conformal_risk_arxiv.html", "html", 2022, "arxiv_first_posted_2022_current_version_2025",
     "Conformal risk control extends coverage calibration to expected monotone loss, with stated finite-sample guarantees.",
     "Expected-risk control does not certify arbitrary cost-adjusted EVSI, every subgroup, or causal mechanism; assumptions cannot be inferred from a confidence field.",
     "Bind a specific loss, calibration population and policy version to every purported risk certificate.",
     "Risk-calibrated abstention is prior art; local promotion still needs independent validity tests."),
    ("angelopoulos2021ltt", "raw/learn_then_test_arxiv.html", "html", 2021, "arxiv_preprint_verified",
     "Learn then Test treats tuning for finite-sample risk guarantees as a multiple-testing problem, independently of model fitting.",
     "Data used to choose policies cannot silently double as untouched certification data; published guarantees remain assumption-bound.",
     "Freeze candidate policies and registered contrasts before confirmation; control multiplicity and retain refusal if no policy passes.",
     "An independent calibration gate is established methodology."),
    ("ahlmanneltze2025baselines", "raw/baseline_doi.json", "crossref", 2025, "journal",
     "Five single-cell foundation models and two other deep models did not outperform deliberately simple transcriptomic perturbation baselines in the studied tasks.",
     "Failure on these tasks does not show that all world models fail; prediction and decision value are different endpoints.",
     "Retain mean, additive/linear, ridge and nearest-neighbour baselines, evaluated with the same information and task splits.",
     "A larger neural model is not evidence of algorithmic novelty or useful decisions."),
    ("wenteler2025perteval", "raw/perteval_primary.html", "html", 2025, "conference",
     "PertEval-scFM benchmarks zero-shot foundation-model embeddings and finds limited gains over simple baselines, especially under distribution shift.",
     "The study evaluates perturbation prediction, not MAESTRO experiment procurement.",
     "Use context, perturbation and platform holdouts; declare training or previous-experiment exposure explicitly.",
     "Systematic perturbation-model benchmarking is existing work."),
    ("mao2026inthewild", "raw/arxiv_virtual_cell_benchmark.html", "html", 2026, "arxiv_preprint_verified",
     "A benchmark evaluates unseen contexts, unseen perturbations and cross-dataset transfer, and reports performance overestimation in common simplified settings.",
     "Preprint benchmark findings are not a guarantee for a new measured phenotype; a reused drug split is not a fresh biological holdout.",
     "Report strict deployment-matched splits and separate retrospective policy evaluation from biological generalization claims.",
     "Out-of-distribution benchmarking is a required control, not the proposed contribution."),
    ("miladinovic2025lpm", "raw/lpm_doi.json", "crossref", 2025, "journal",
     "The large perturbation model represents perturbation, readout and context as disentangled dimensions to integrate heterogeneous experiments.",
     "Shared representation does not make different assays, doses, times or culture units interchangeable.",
     "Make assay, dose, time and context explicit in the observation contract rather than hide them in a generic score.",
     "Factorized perturbation-readout-context modeling is existing work."),
    ("adduri2026state", "raw/state_crossref.json", "crossref", 2026, "journal",
     "State predicts transcriptomic perturbation responses across cellular contexts and provides the Cell-Eval evaluation framework.",
     "Transcriptomic prediction performance is not proof of viability, apoptosis, protein engagement, mechanism causality or experiment value.",
     "Keep world-model forecast evidence separate from the same-assay, same-unit endpoint bridge and terminal decision evaluation.",
     "State modeling and multi-context perturbation prediction are existing capabilities."),
    ("saunders2025perturbmulti", "raw/perturb_multimodal_pmc.html", "html", 2025, "journal",
     "Perturb-Multimodal combines CRISPR, transcriptomic profiling and morphology in intact mammalian tissue; its pipeline assigns RNA molecules and morphological images to cell segmentations.",
     "Its in-vivo cell-level correspondence does not validate a PRISM cell-line drug viability bridge or a universal image-to-apoptosis classifier.",
     "For a future image-RNA bridge, preserve shared cell or culture identifiers and experimentally matched interventions, doses and times.",
     "Same-cell multimodal perturbation measurement and joint features are existing work."),
]


def compile_citations() -> None:
    records = []
    for key, source, kind, year, status, claim, limit, implication, boundary in SPECS:
        path = HERE / source
        if kind == "crossref":
            data = json.loads(path.read_text(encoding="utf-8"))["message"]
            title = data["title"][0]
            authors = [" ".join(filter(None, [x.get("given"), x.get("family")])) for x in data.get("author", [])]
            doi = data.get("DOI")
            venue = (data.get("container-title") or [""])[0]
            date = (data.get("published", {}).get("date-parts") or [[year]])[0]
            arxiv_id = None
        else:
            data = html_metadata(path)
            title = data["citation_title"][0]
            authors = data.get("citation_author", [])
            doi = (data.get("citation_doi") or [None])[0]
            venue = (data.get("citation_journal_title") or data.get("citation_conference_title") or ["arXiv"])[0]
            date = (data.get("citation_publication_date") or data.get("citation_date") or [str(year)])[0]
            arxiv_id = (data.get("citation_arxiv_id") or [None])[0]
        url = "https://doi.org/" + doi if doi else "https://arxiv.org/abs/" + arxiv_id if arxiv_id else {
            "roohani2025biodiscovery": "https://proceedings.iclr.cc/paper_files/paper/2025/hash/4252dc94531833029000f85dc5fac792-Abstract-Conference.html",
            "wenteler2025perteval": "https://proceedings.mlr.press/v267/wenteler25a.html",
        }[key]
        records.append({"id": key, "title": title, "authors": authors, "year": year, "publication_date": date,
                        "venue": venue, "doi": doi, "arxiv_id": arxiv_id, "publication_status": status,
                        "url": url, "verification": source_receipt(source), "claim_used": claim,
                        "does_not_establish": limit, "implication_for_maestro": implication, "novelty_boundary": boundary})
    payload = {"schema_version": 1, "review_date_client_timezone": "2026-10-11 Asia/Shanghai",
               "scope": "Targeted primary-source search, not an exhaustive systematic review. References and model outputs are never endpoint truth.",
               "citations": records}
    (HERE / "citations.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def compile_sources() -> None:
    records = []
    for filename in ["retrieval_log.json", "data_search_log.json", "followup_log.json", "second_followup_log.json",
                     "data_download_log.json", "verification_log.json", "final_sources_log.json"]:
        for entry in json.loads((HERE / filename).read_text(encoding="utf-8")):
            entry["log_file"] = filename
            entry.pop("candidates", None)
            entry.pop("headers", None)
            records.append(entry)
    # Initial ACL event-page fetch was explicitly capped; it is not used as citation evidence.
    for entry in records:
        if entry.get("key") == "acl_emnlp2025":
            entry["truncated_at_bytes"] = 8_000_000
            entry["used_for_claims"] = False
    for file in (HERE / "raw").iterdir():
        if file.is_file() and not any(str(x.get("path", "")).replace("\\", "/").endswith("raw/" + file.name) for x in records):
            records.append({"key": file.stem, "status": "LOCAL_SOURCE_WITHOUT_COMPLETE_RECEIPT", **source_receipt("raw/" + file.name)})
    (HERE / "source_catalog.json").write_text(json.dumps({"records": records, "failure_policy": "Failures are preserved; no invented citation or endpoint is substituted."}, ensure_ascii=False, indent=2), encoding="utf-8")


def compile_dataset_card() -> None:
    base = HERE / "datasets/cxcl9_2026"
    files = []
    for path in sorted(base.rglob("*")):
        if path.is_file():
            item = source_receipt(str(path.relative_to(HERE)).replace("\\", "/"))
            if path.suffix == ".csv":
                with path.open(encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    rows = list(reader)
                    item.update({"rows": len(rows), "columns": reader.fieldnames})
                if "MIDAS_" in path.name:
                    item["status"] = "MODEL_INPUT_NOT_MULTIMODAL_TRUTH"
                    item["constructed_time_grid"] = sorted({x["DA:ALL"] for x in rows}, key=float)
                elif "Raw_data_statistics" in path.name:
                    item["status"] = "AUTHOR_PROCESSED_MEASURED_CXCL9_SUMMARY"
                elif "00_Raw_Data_" in path.name:
                    item["status"] = "MEASURED_SINGLE_CELL_FACS_NO_INDEPENDENT_CELL_REPLICATION"
                else:
                    item["status"] = "EXPERIMENT_ANNOTATION_NOT_ENDPOINT_TRUTH"
            files.append(item)
    card = {"source_paper_id": "wang2026cxcl9", "source_repository": "https://github.com/SysBioOncology/ActiveLearning_MechanisticModels_CXCL9",
            "source_revision": "b654a45faf5a80cdb1b514188cc90af8c9565b85", "endpoint": "24-hour intracellular CXCL9 FACS fluorescence, author-normalized log mean response",
            "contexts": ["BxPC3", "AsPC1"], "measured_condition_summaries_per_context": 24,
            "downloaded_raw_context": "BxPC3 E3CA P12 and E3CB P14", "sample_unit": "Perturbation culture/plate/condition; cell events within a FACS sample are nested, not independent experiments.",
            "critical_exclusions": ["Do not treat six DA:ALL grid values in MIDAS files as six observed time points: repository assay metadata states one 24-hour assay.",
                                    "Do not treat DV:ERK, DV:AKT and related MIDAS state values as measured proteins; these are initialization/constraint inputs.",
                                    "Do not treat the prior-knowledge network or literature as verified mechanistic outcome labels.",
                                    "Do not call two backgrounds independent proof of broad biological generalization.",
                                    "Do not use all-condition min-max normalization as a deployment input before its relevant measurements; keep raw or externally fitted scaling for replay."],
            "eligible_use": "Small additional measured-endpoint replay or assay-contract example after a separate frozen protocol; no results or promotion are claimed by this data download.",
            "files": files, "total_downloaded_bytes": sum(x["bytes"] for x in files)}
    (HERE / "dataset_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    compile_citations()
    compile_sources()
    compile_dataset_card()
    print(json.dumps({"citations": len(SPECS), "dataset_files": len(json.loads((HERE / 'dataset_card.json').read_text())['files']), "output": str(HERE)}))

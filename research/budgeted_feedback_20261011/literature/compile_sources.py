"""Compile inspected primary records with explicit scope and claim limits."""
from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent

# This is a targeted evidence map, not an exhaustive novelty search.
RECORDS = [
    dict(id="feng2026map", key="user_doi_nature", domain="biological transfer / knowledge graph", year=2026,
         venue="Nature Machine Intelligence", doi="10.1038/s42256-026-01286-w",
         read_scope="Publisher HTML abstract, generalization protocols, knowledge ablations, limitations, and data/code availability inspected; supplements and code execution not reviewed.",
         claim="MAP aligns drug structures, protein sequences and mechanistic text using MAP-KG, then conditions a single-cell model. It tests unseen cell-drug pairs and drugs with no training profiles. The strict protocol also removes held-out drug entities, aliases and incident graph edges.",
         limit="Transcriptomic prediction and in silico pathway prioritization do not establish independently measured phenotype, causal mechanism, selection coverage or cost-adjusted adaptive benefit.",
         test="Compare context transfer alone against transfer plus frozen graph features, structure-only, no graph, and degree-preserving shuffled graph; remove held-out compound identities/aliases/edges for a strict inductive claim.",
         novelty_boundary="Knowledge-driven perturbation representations and their zero-shot use are existing methods."),
    dict(id="yoo2019loss", key="cv_learning_loss", domain="CV / active labeling", year=2019,
         venue="CVPR", read_scope="Official CVF abstract and citation metadata inspected.",
         claim="A small learned loss-prediction module selects annotations across image classification, detection and pose estimation.",
         limit="Predicted loss is an annotation heuristic; it is neither terminal biological utility nor a guarantee that expensive feedback will repay its cost.",
         test="Keep cheap residual/loss-based acquisition as a baseline; measure acquisition compute and endpoint value separately.",
         novelty_boundary="Learning a proxy for informative observations is established."),
    dict(id="kirsch2019batchbald", key="cv_batchbald", domain="CV / batch acquisition", year=2019,
         venue="arXiv primary author record; conference venue not independently verified here", arxiv_id="1906.08158",
         read_scope="arXiv abstract and metadata inspected; a candidate conference URL failed and is not used as evidence.",
         claim="BatchBALD approximates joint mutual information between a batch and model parameters, accounting for redundancy between selected points.",
         limit="Model information gain does not equal terminal decision gain. Its neural-classification acquisition is not directly a drop-in biological utility objective.",
         test="Compare one-shot diversity/covariance-aware batches and a small number of larger batches with greedy single-point acquisition under a shared turnaround tariff.",
         novelty_boundary="Joint information-aware batching is established."),
    dict(id="ash2019badge", key="cv_badge", domain="CV / batch acquisition", year=2019,
         venue="arXiv primary author record; fetched OpenReview page was a browser challenge", arxiv_id="1906.03671",
         read_scope="arXiv abstract and metadata inspected; OpenReview HTTP 200 did not provide paper content.",
         claim="BADGE combines uncertainty and diversity using gradient embeddings to choose batches.",
         limit="Gradient embeddings presuppose a suitable differentiable prediction task. A feature-space diversity baseline should be labeled an adaptation, not an exact BADGE reproduction.",
         test="Tune a fixed diversity batch on development data and freeze it before comparing adaptive policies.",
         novelty_boundary="Combining uncertainty and diversity in acquisition is established."),
    dict(id="oquab2023dinov2", key="cv_dinov2", domain="CV / scarce labels", year=2023,
         venue="arXiv primary author record", arxiv_id="2304.07193",
         read_scope="arXiv abstract and metadata inspected.",
         claim="Self-supervised pretraining on curated diverse images produces reusable representations and distilled smaller models.",
         limit="Cheap labels do not imply cheap pretraining. Natural-image features are not evidence of calibrated cell phenotype or cross-platform microscopy transfer.",
         test="For a future image assay, compare frozen representations plus a small measured endpoint head against morphology baselines; split by plate/site before tuning.",
         novelty_boundary="Unlabeled representation learning and frozen-feature transfer are established."),
    dict(id="eindor2020bert", key="nlp_bert_al", domain="NLP / scarce labels", year=2020,
         venue="EMNLP", doi="10.18653/v1/2020.emnlp-main.638",
         read_scope="ACL Anthology abstract and citation metadata inspected.",
         claim="A study of BERT active learning under small labeling budgets and class imbalance reports benefits, particularly from a biased keyword-selected initial sample.",
         limit="Benefits depend on initialization, class imbalance and task; the abstract does not support universal superiority of sequential acquisition over tuned batches.",
         test="Stratify replay by active-compound prevalence and prior bias; retain random and uncertainty sampling with identical initial observations.",
         novelty_boundary="Pretraining plus active annotation in low-data settings is established."),
    dict(id="liu2022wanli", key="nlp_wanli_acl", domain="NLP / inexpensive generated proposals", year=2022,
         venue="Findings of EMNLP", doi="10.18653/v1/2022.findings-emnlp.508",
         read_scope="ACL Anthology abstract/metadata and independent arXiv abstract inspected.",
         claim="WANLI identifies challenging existing examples, generates new examples with GPT-3, filters them and has humans revise and label the retained examples.",
         limit="Human-verifiable text labels differ from unobserved biological endpoints. Synthetic expression or LLM-generated viability must not become measured response truth.",
         test="Use LLMs to propose assay conditions or extract provenance-bearing graph edges; compare human/assay-verified acquisition against automated suggestions and account for review cost.",
         novelty_boundary="Generation followed by filtering and human verification is established."),
    dict(id="ren2023knowno", key="robot_knowno", domain="robotics / reliable help requests", year=2023,
         venue="CoRL, PMLR 229", arxiv_id="2307.01928",
         read_scope="PMLR abstract/metadata and arXiv HTML sections on conformal calibration, multi-step calibration and discussion inspected.",
         claim="KnowNo calibrates language-planner confidence and asks for help when needed; its multi-step construction calibrates complete sequences.",
         limit="Its task/scenario distribution, candidate actions and assistance assumptions are part of the guarantee. The result does not automatically transfer to selected drugs, a changed planner or arbitrary biological feedback.",
         test="Freeze a planner and calibrate/replay complete episodes; compare no-help, fixed-help, uncertainty-triggered help and decision-value-triggered observations under the same cost model.",
         novelty_boundary="Calibrated uncertainty-triggered assistance and multi-step LLM planning coverage are existing work."),
    dict(id="openx2023", key="robot_openx", domain="robotics / transfer from existing datasets", year=2023,
         venue="arXiv primary author record", arxiv_id="2310.08864",
         read_scope="arXiv abstract and metadata inspected.",
         claim="Open X-Embodiment standardizes datasets across 22 robots and reports positive transfer by pooling experience from different platforms.",
         limit="Standardized schemas do not make action spaces, observation distributions or biological cell contexts equivalent. Positive transfer must be tested and negative transfer retained in reporting.",
         test="Treat cell background and assay metadata as explicit context; compare target-only, pooled, nearest-context transfer and transferred residual correction on a held-out context.",
         novelty_boundary="Cross-domain data pooling and adaptation are established."),
    dict(id="chebotar2018sim2real", key="robot_sim2real_arxiv", domain="robotics / sparse real feedback", year=2018,
         venue="arXiv primary author record", arxiv_id="1810.05687",
         read_scope="arXiv abstract and metadata inspected; the initial guessed PMLR URL returned 404.",
         claim="The simulation-parameter distribution is updated using a few real-world rollouts interleaved with policy training, improving transfer in two robot tasks.",
         limit="Matching simulator behavior in these tasks does not establish that simulated cells capture unmeasured biology or that any number of feedback rounds is cost-effective.",
         test="Update a low-dimensional context/assay residual using sparse real measurements; ablate zero, one, two and many updates, real versus permuted feedback, and transferred versus target-only priors.",
         novelty_boundary="Few real observations used to adapt a simulator are established."),
    dict(id="kandasamy2017boca", key="bo_multifidelity", domain="multi-fidelity optimization", year=2017,
         venue="ICML, PMLR 70", read_scope="PMLR abstract and citation metadata inspected.",
         claim="BOCA selects among continuous cheap approximations and expensive objective evaluations, with regret results under its model assumptions.",
         limit="RNA, morphology, viability, and knowledge-graph evidence are not automatically ordered fidelities of one function. A paired, context-matched bridge is required before using a cheap modality as an endpoint approximation.",
         test="Compare endpoint-only, cheap-readout-only and mixed purchases at equal total cost; disable cross-assay updates when the held-out bridge is unreliable.",
         novelty_boundary="Cost-aware acquisition across fidelities is established."),
    dict(id="bao2024selective", key="selective_crossref", domain="selection-aware uncertainty", year=2024,
         venue="Biometrika", doi="10.1093/biomet/asae010",
         read_scope="Crossref publisher-deposited abstract/metadata inspected; publisher full-text request returned 403.",
         claim="Selective conditional conformal prediction applies selection to calibration and test samples and controls false coverage-statement rate for exchangeable selection; nonexchangeable cases require additional assumptions/bounds.",
         limit="FCR is not per-drug conditional coverage, simultaneous coverage of all selections, or worst-subgroup coverage. An empirical top-k residual quantile does not inherit this theorem without the specified construction and assumptions.",
         test="Report selected-set and active-subgroup coverage with sample counts/uncertainty and complete-episode error; separate empirical diagnostics from any theorem-backed statement.",
         novelty_boundary="Adjusting prediction intervals for selection and multiplicity is established."),
    dict(id="balandat2019botorch", key="bo_botorch", domain="efficient Bayesian optimization", year=2019,
         venue="arXiv primary author record", arxiv_id="1910.06403",
         read_scope="arXiv abstract and metadata inspected.",
         claim="BoTorch implements Monte Carlo acquisition with sample-average approximation, variance reduction and a one-shot Knowledge Gradient formulation.",
         limit="A faster acquisition implementation does not demonstrate scientific value or novel acquisition theory. Comparators still need equal observations and endpoint access.",
         test="Keep correlated posterior acquisition as a strong comparator, cache shared posterior terms and record acquisition wall time with assay/turnaround costs.",
         novelty_boundary="Efficient Monte Carlo decision acquisition and one-shot Knowledge Gradient are established."),
]


def main() -> None:
    retrievals = []
    for path in [HERE / "retrieval_log.json", HERE / "followup_log.json", HERE / "second_followup_log.json"]:
        retrievals.extend(json.loads(path.read_text(encoding="utf-8")))
    catalog = {r["key"]: r for r in retrievals}
    compiled = []
    for rec in RECORDS:
        result = dict(rec)
        evidence = catalog[rec["key"]]
        assert evidence["status"] == 200
        content = (HERE / evidence["path"]).read_text(encoding="utf-8")
        if rec["key"] == "selective_crossref":
            payload = json.loads(content)["message"]
            title = payload["title"][0]
            authors = [a["given"] + " " + a["family"] for a in payload["author"]]
            abstract = BeautifulSoup(payload["abstract"], "html.parser").get_text(" ", strip=True)
        else:
            soup = BeautifulSoup(content, "html.parser")
            title = soup.find("meta", attrs={"name": "citation_title"})["content"]
            authors = [a["content"] for a in soup.find_all("meta", attrs={"name": "citation_author"})]
            if rec["key"] == "user_doi_nature":
                abstract = soup.find("meta", attrs={"name": "dc.description"})["content"]
            else:
                block = soup.select_one("blockquote.abstract, div.acl-abstract, div.abstract, div#abstract")
                assert block is not None, rec["key"]
                abstract = block.get_text(" ", strip=True)
        result.update(title=title, authors=authors, abstract_evidence=abstract,
                      url=evidence["url"], verification=evidence)
        compiled.append(result)
    (HERE / "sources.json").write_text(json.dumps({
        "schema_version": 1,
        "review_date_client_timezone": "2026-10-11 Asia/Shanghai",
        "scope": "Targeted primary-source evidence map supplementing the existing 16-paper MAESTRO review; not an exhaustive systematic review or novelty certification.",
        "sources": compiled,
        "additional_evidence_keys": ["user_doi_crossref", "map_github", "map_readme", "map_kg_hf", "knowno_arxiv_html"],
        "known_retrieval_limits": [
            "Crossref broad batch-acquisition and robot-transfer searches returned 429.",
            "Two candidate proceedings URLs returned 404 and are not citation evidence.",
            "The selective-conformal publisher URL returned 403; only deposited abstract/metadata are used.",
            "The BADGE OpenReview response was HTTP 200 but titled 'Verifying your browser'; no paper text was obtained there.",
            "The retrieved arXiv 2304.06158 is a distinct paper about selecting the miscoverage level, not Bao et al.'s selected-candidate FCR method; it is logged but not used as a substitute."
        ]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Compiled {len(compiled)} inspected primary-paper records.")


if __name__ == "__main__":
    main()

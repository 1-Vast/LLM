"""Worked examples: the decision-support answer on real held-out episodes, with what happened next.

File summary
- Path: research/maestro_vc_v1/examples.py
- Purpose: show the system's full answer on three real situations, each chosen by a rule stated here and
  not by how well it turned out, and then reveal, from the evaluator's side, what the real measurement
  read and how the system's update handled it.
- Core points:
  - Selection rules (fixed before looking at any example's outcome):
    1. `informative_prior`: SciPlex3 tier B, fold 0, the first episode in seeded order whose compound has a
       structural neighbour at or above the applicability floor and a retrieved prior of at least 0.65 for
       one hypothesis;
    2. `no_decisive_action`: L1000 tier LT, fold 0, the first episode in seeded order (that fold's validator
       cannot eliminate, so no legal action can decide);
    3. `misled_prior`: SciPlex3 tier B, the first episode whose nearest structural neighbour is of another
       class than the truth and whose prior favours that other class.
  - Each example writes the markdown answer, the JSON payload, and an evaluator-side note: the real
    reading of the recommended action, the probability the system had given it, and the state after
    `ingest`. The system never sees the evaluator-side fields.
  - The seeded order is the replay's own episode order; nothing is resampled.
- Run: python -m research.maestro_vc_v1.examples
- Interfaces: `build`, `RULES`
- Depends on: system.py, research/scientific_case_memory, research/protocol_v2
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/maestro_vc_v1/examples"
RULES = {"informative_prior": ("sciplex3", "B", 0), "no_decisive_action": ("l1000", "LT", 0), "misled_prior": ("sciplex3", "B", None)}


def _episodes(dataset, tier, fold):
    from research.scientific_case_memory import build_cases as BC
    from research.protocol_v2 import tasks_v21 as V

    inputs = BC.load_inputs(dataset, tier, fold)
    snap = BC.build_snapshot(inputs, created_at="2026-09-29")
    return inputs, snap, V.episode_list(inputs.ctx, fold)


def _run(name, inputs, snap, episode, out: Path, ds=None):
    from research.protocol_v2 import contracts as K
    from research.scientific_case_memory import case_store as CS

    from . import system as SY

    ds = ds or SY.DecisionSupport(inputs, snap)
    comp = inputs.data.compounds.drop_duplicates("compound").set_index("compound")
    c, truth, _decoy, h1, h2 = episode
    problem = SY.UserProblem(c, comp.smiles.get(c), (h1, h2), (), unit=inputs.unit_of.get(c))
    report = ds.answer(problem)
    text = ds.render(problem, report)
    note = [f"\n---\n\n## Evaluator side (never visible to the system): example `{name}`\n",
            f"- Truth (curated class annotation): **{truth}**; the retrieved prior favoured "
            f"**{max(report.precedents['hypothesis_prior'], key=report.precedents['hypothesis_prior'].get)}** "
            f"({max(report.precedents['hypothesis_prior'].values()):.2f})."]
    if report.recommendation:
        key = ds.keys[report.recommendation["action"]]
        result = inputs_execute(inputs, c, key, h1, h2)
        outcome = result["outcome"] if result["qc"] else "quality_failed"
        store = CS.CaseStore()
        after = ds.ingest(problem, report, key, outcome, agreement=result["agreement"], store=store)
        label = {"eliminate_b": f"profile matches '{h1}'", "eliminate_a": f"profile matches '{h2}'", "ambiguous": "unresolved",
                 "undetected": "no detectable response", "quality_failed": "QC failure"}[outcome]
        note += [f"- Real reading at the recommended condition ({report.recommendation['action']}): **{label}**.",
                 f"- Probability the system had given that reading: {after['probability_given_to_realised_reading']}.",
                 f"- Registered rules after the reading: candidates {after['candidates']}, resolved: {after['resolved']}; "
                 f"biological update allowed: {after['biological_update_allowed']}.",
                 f"- Case memory: `{after['case_id']}` version {after['case_version']} appended; append-only chain verified: "
                 f"{store.verify() == ()}."]
        if after["resolved"]:
            note.append(f"- The surviving hypothesis {'agrees' if after['candidates'][0] == truth else 'DISAGREES'} with the annotation.")
    else:
        note.append("- No action was recommended, so nothing was measured; the answer is the abstention above.")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.md").write_text(text + "\n".join(note) + "\n", encoding="utf-8")
    (out / f"{name}.json").write_text(json.dumps(report.payload(), indent=1, default=str), encoding="utf-8")
    return {"example": name, "compound": c, "truth": truth, "recommended": report.recommendation.get("action") if report.recommendation else None,
            "abstention": (report.abstention or {}).get("reasons")}


def inputs_execute(inputs, compound, key, h1, h2):
    from research.protocol_v2 import contracts as K
    return K.T.E.execute(inputs.ctx, compound, key, h1, h2)


def build(out: Path = OUT) -> list[dict]:
    from . import system as SY

    results = []
    # 1 informative prior, and 3 misled prior, both on SciPlex3 B
    inputs, snap, eps = _episodes("sciplex3", "B", 0)
    ds = SY.DecisionSupport(inputs, snap)
    comp = inputs.data.compounds.drop_duplicates("compound").set_index("compound")
    first_informative, first_misled = None, None
    for ep in eps:
        c, truth, _d, h1, h2 = ep
        prior = ds.world.hypothesis_prior(c, h1, h2, inputs.unit_of.get(c))
        sim = ds.world._neighbourhood(c, inputs.unit_of.get(c))[0]
        near = float(sim.max()) if len(sim) else 0.0
        if near >= 0.40 and max(prior.values()) >= 0.65 and first_informative is None and max(prior, key=prior.get) == truth:
            first_informative = ep
        if near >= 0.40 and max(prior.values()) >= 0.65 and max(prior, key=prior.get) != truth and first_misled is None:
            first_misled = ep
        if first_informative and first_misled:
            break
    for name, ep in (("informative_prior", first_informative), ("misled_prior", first_misled)):
        if ep is not None:
            results.append(_run(name, inputs, snap, ep, out, ds))
    inputs, snap, eps = _episodes("l1000", "LT", 0)
    results.append(_run("no_decisive_action", inputs, snap, eps[0], out))
    (out / "index.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    return results


if __name__ == "__main__":
    for r in build():
        print(r)

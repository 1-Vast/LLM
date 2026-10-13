"""Offline source-pin, action, information-boundary, budget and outcome verification."""
import json
import sqlite3
import numpy as np
from experiment import HERE, ROOT, digest, score_choices


def main():
    for filename in ("PROTOCOL_FREEZE.json", "PILOT_FREEZE.json"):
        for name, expected in json.loads((HERE / filename).read_text())["hashes"].items():
            assert digest(HERE / name) == expected, name
    audit = json.loads((HERE / "input_audit.json").read_text())
    for name, expected in audit["sources"].items():
        assert digest(ROOT / name) == expected, name
    z = np.load(HERE / "replay.npz")
    meta = json.loads((HERE / "metadata.json").read_text())
    keyrow = {r["key"]:i for i,r in enumerate(meta["compounds"])}
    assert len(keyrow)==702 and len(set(meta["pilot"]))==84
    summary = json.loads((HERE / "RESULTS.json").read_text())
    rows = json.loads((HERE / "policy_rows.json").read_text())
    for arm in summary["policies"]:
        selected = [r for r in rows if r["arm"]==arm]
        assert len(selected)==702
        for r in selected:
            i,s,t = keyrow[r["key"]],r["first"],r["second"]
            assert s!=t and z["grid"][i,s] and z["grid"][i,t]
            hit,margin = score_choices(z["ratio"][[i]],np.array([s]),np.array([t]))
            assert r["hit"]==int(hit[0]) and r["margin_hit"]==int(margin[0])
        assert sum(r["hit"] for r in selected)==summary["policies"][arm]["hits"]
    records = json.loads((HERE / "agent_results.json").read_text())["records"]
    assert len(records)==36
    with sqlite3.connect(HERE / "case_state.sqlite") as db:
        assert db.execute("select count(*) from cases where spent=14 and state='deferred'").fetchone()[0]==36
        assert db.execute("select count(*) from results").fetchone()[0]==504
    for r in records:
        ids,s,t = r["indices"],z["first"][r["indices"]],np.array(r["second"])
        assert (s!=t).all() and z["grid"][ids,t].all()
        hit,margin=score_choices(z["ratio"][ids],s,t)
        assert r["hits"]==hit.astype(int).tolist()
        assert r["margin_hits"]==margin.astype(int).tolist()
    cache=list((HERE / "llm_cache").glob("*.json"))
    for path in cache:
        c=json.loads(path.read_text())
        content=json.loads(c["messages"][-1]["content"])
        if "feedback" in content:
            for item in content["feedback"]:
                i=int(item["id"])
                s=int(z["first"][i])
                assert item["observed_line"]==meta["lines"][s]
                assert item["observed_norm_ratio"]==round(float(z["ratio"][i,s]),4)
                for candidate in item["candidates"]:
                    assert set(candidate)<= {"line","empirical_p_active","norm_neighbour_p_active",
                        "rkt_p_active","rkt_expected_cosine_if_active","rkt_specific_refusal"}
                    assert candidate["line"]!=meta["lines"][s]
    ledger=json.loads((HERE / "api_ledger.json").read_text())
    assert ledger["calls"]<=72 and ledger["total_usd"]<=1
    assert all(r["usage"].get("model")=="deepseek-flash" for r in ledger["entries"] if r["status"]=="ok")
    comparisons=json.loads((HERE / "comparisons.json").read_text())
    for arm in ("C_agent_only", "D_conventional", "E_integrated"):
        ar=[r for r in records if r["arm"]==arm]
        assert sum(sum(r["hits"]) for r in ar)==comparisons["pilot"][arm]["hits"]
        assert sum(sum(r["margin_hits"]) for r in ar)==comparisons["pilot"][arm]["margin_hits"]
    p=comparisons["pilot"]
    interaction=(p["E_integrated"]["rate"]-p["C_agent_only"]["rate"])-(p["rkt"]["rate"]-p["empirical"]["rate"])
    assert abs(interaction-comparisons["pilot_contrasts"]["interaction"]["mean"])<1e-12
    manifest=HERE / "ARTIFACTS.json"
    if manifest.exists():
        for name, expected in json.loads(manifest.read_text())["sha256"].items():
            assert digest(HERE/name)==expected, name
    print("VERIFIED: hashes, 4212 deterministic choices, 252 agent choices, 504 source receipts, masked prompts and API accounting")


if __name__ == "__main__":
    main()

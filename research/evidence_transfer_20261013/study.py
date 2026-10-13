"""GCP source acquisition; metadata never reads measured feature rows."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import re
import threading
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/external/gcp2020"
STUDY = Path(__file__).resolve().parent
LANDING = "https://panoramaweb.org/project/Panorama%20Public/2020/LINCS%20PCCSE%20GCP%202020/begin.view"
LINES = ("A375", "MCF7", "PC3", "YAPC")
EXPOSED_NAMES = {"semagacestat", "bms-906024", "bms906024"}
CONTROL_NAMES = {"dmso", "vorinostat", "staurosporine"}
_WRITE_LOCK = threading.Lock()


def _open(url):
    for attempt in range(3):
        try:
            return urllib.request.urlopen(url, timeout=40)
        except (OSError, TimeoutError):
            if attempt == 2:
                raise


def _urls():
    with _open(LANDING) as response:
        page = response.read().decode()
    return sorted(set(url for url in re.findall(r'href="([^"]+)"', page)
                      if "/GCT/" in url and url.endswith("_LVL4.gct")))


def _header(stream):
    if stream.readline().strip() != "#1.3":
        raise ValueError("Expected GCT 1.3")
    nr, nc, nra, nca = map(int, stream.readline().split())
    header = stream.readline().rstrip("\r\n").split("\t")
    metadata = {}
    for _ in range(nca):
        row = stream.readline().rstrip("\r\n").split("\t")
        metadata[row[0]] = row[nra + 1:]
        if len(metadata[row[0]]) != nc:
            raise ValueError("Malformed sample metadata")
    samples = [{key: values[i] for key, values in metadata.items()} for i in range(nc)]
    return (nr, nc, nra, nca), header, samples


def _metadata_plate(url):
    name = url.rsplit("/", 1)[1]
    path = CACHE / "metadata" / (name + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    with _open(url) as response:
        stream = io.TextIOWrapper(response, encoding="utf-8")
        dims, header, samples = _header(stream)
        # Close here: no outcome row is read or cached during metadata acquisition.
    result = {"url": url, "dimensions": dims, "row_annotation_fields": header[:dims[2]+1],
              "samples": samples}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _connectivity(smiles):
    from rdkit import Chem
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("Invalid or missing structure: cannot certify compound split")
    return Chem.MolToInchiKey(molecule).split("-")[0]


def acquire_metadata():
    plates = list(concurrent.futures.ThreadPoolExecutor(max_workers=3).map(_metadata_plate, _urls()))
    compounds = {}
    for plate in plates:
        for sample in plate["samples"]:
            if sample["pert_type"] != "trt_cp" or sample["cell_id"] not in LINES:
                continue
            if float(sample["pert_time"]) != 24 or sample["pert_time_unit"] != "h":
                raise ValueError("Unexpected GCP exposure duration")
            connectivity = _connectivity(sample["isomeric_smiles"])
            source_ident = sample["pert_id"]
            ident = source_ident if source_ident.startswith("BRD-") else "GCP-" + connectivity
            sample["source_pert_id"] = source_ident
            sample["pert_id"] = ident
            item = compounds.setdefault(ident, {"pert_id": ident, "name": sample["pert_iname"],
                "smiles": sample["isomeric_smiles"], "pubchem_cid": sample["pubchem_cid"],
                "connectivity": connectivity, "samples": []})
            if item["connectivity"] != connectivity:
                raise ValueError("Inconsistent compound identity")
            item["samples"].append({**sample, "source_url": plate["url"]})
    exposed_groups = {item["connectivity"] for item in compounds.values()
                      if item["name"].lower() in EXPOSED_NAMES}
    for item in compounds.values():
        digest = hashlib.sha256(("gcp-transfer-20261013:" + item["connectivity"]).encode()).hexdigest()
        fraction = int(digest[:16], 16) / 2**64
        split = "reference" if fraction < .6 else "development" if fraction < .8 else "test"
        if item["connectivity"] in exposed_groups and split == "test":
            split = "development"
        item["evaluation_eligible"] = item["name"].lower() not in CONTROL_NAMES
        if not item["evaluation_eligible"]:
            split = "reference"
        item["split"] = split
    result = {"source": LANDING, "lines": LINES, "plates": plates,
              "compounds": sorted(compounds.values(), key=lambda item: item["pert_id"]),
              "outcomes_opened": False, "split_key": "InChIKey connectivity block",
              "published_example_exclusions": sorted(exposed_groups)}
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "metadata.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def prepare():
    """Explicit outcome acquisition after the caller freezes its scientific protocol."""
    protocol = STUDY / "PROTOCOL.md"
    freeze = STUDY / "FREEZE.json"
    if not protocol.exists() or not freeze.exists():
        raise ValueError("Freeze PROTOCOL.md and FREEZE.json before outcome acquisition")
    receipt = json.loads(freeze.read_text(encoding="utf-8"))
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    if receipt.get("protocol_sha256") != digest:
        raise ValueError("Protocol hash does not match frozen protocol_sha256 receipt")
    manifest = json.loads((CACHE / "metadata.json").read_text(encoding="utf-8"))
    numeric_plates = []
    normalization = []
    for plate in manifest["plates"]:
        if not any(s["cell_id"] in LINES for s in plate["samples"]):
            continue
        url = plate["url"].replace("_LVL4.gct", "_LVL3.gct")
        path = CACHE / "matrices" / url.rsplit("/", 1)[1]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            from http.client import IncompleteRead
            for attempt in range(3):
                try:
                    with _open(url) as response:
                        payload = response.read()
                    path.write_bytes(payload)
                    break
                except (OSError, IncompleteRead):
                    if attempt == 2:
                        raise
        with path.open(encoding="utf-8") as stream:
            dims, header, samples = _header(stream)
            annotations, values = {}, {}
            for _ in range(dims[0]):
                row = stream.readline().rstrip("\r\n").split("\t")
                ident = row[0]
                if ident in values:
                    raise ValueError("Duplicate GCP probe identifier")
                annotations[ident] = dict(zip(header[:dims[2]+1], row[:dims[2]+1]))
                values[ident] = np.asarray(row[dims[2]+1:], dtype=float)
                if values[ident].shape != (dims[1],):
                    raise ValueError("Malformed GCP outcome row")
        retained = {(s["det_plate"], s["det_well"], s["det_filename"])
                    for s in plate["samples"]}
        selected = [i for i, s in enumerate(samples)
                    if (s["det_plate"], s["det_well"], s["det_filename"]) in retained]
        if len(selected) != len(retained):
            raise ValueError("LVL3 sample provenance does not match frozen LVL4 metadata")
        samples = [samples[i] for i in selected]
        values = {f: vector[selected] for f, vector in values.items()}
        controls = [i for i, s in enumerate(samples)
                    if s["pert_iname"].lower() == "dmso"
                    and s["pert_type"] in {"ctrl_vehicle", "ctl_vehicle", "trt_ctl", "trt_cp"}
                    and s["pert_dose"] in {"0", "0.0", "0.1pct", "0.1"}
                    and s["pert_vehicle"].lower() == "dmso"]
        if len(controls) < 2:
            raise ValueError("No replicated, same-plate DMSO vehicle controls")
        contexts = {(s["cell_id"], s["det_plate"], s["pert_time"], s["pert_time_unit"])
                    for s in samples}
        if len(contexts) != 1:
            raise ValueError("Source plate mixes cell or exposure contexts")
        counts = {}
        for feature, vector in values.items():
            finite = vector[controls][np.isfinite(vector[controls])]
            counts[feature] = len(finite)
            values[feature] = vector - np.median(finite) if len(finite) >= 2 else np.full_like(vector, np.nan)
        normalization.append({"source_url": url, "source_path": str(path),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "context": next(iter(contexts)),
            "vehicle_samples": [samples[i] for i in controls], "finite_vehicle_counts": counts,
            "method": "LVL3 minus same-plate per-probe DMSO median; no all-treatment median"})
        numeric_plates.append((samples, annotations, values))
    features = sorted(set.intersection(*(set(v) for _, _, v in numeric_plates)))
    if not features:
        raise ValueError("No common measured probes")
    grouped, provenance = {}, {}
    for samples, annotations, values in numeric_plates:
        for index, sample in enumerate(samples):
            if sample["pert_type"] != "trt_cp" or sample["cell_id"] not in LINES:
                continue
            if sample["pert_iname"].lower() in CONTROL_NAMES:
                continue
            if not sample["pert_id"].startswith("BRD-"):
                sample["source_pert_id"] = sample["pert_id"]
                sample["pert_id"] = "GCP-" + _connectivity(sample["isomeric_smiles"])
            key = (sample["pert_id"], sample["cell_id"], float(sample["pert_dose"]), float(sample["pert_time"]))
            vector = np.asarray([values[f][index] for f in features])
            grouped.setdefault(key, []).append(vector)
            provenance.setdefault(key, []).append(sample)
    grouped = {key: vectors for key, vectors in grouped.items()
               if len(vectors) >= 2}
    feature_annotations = numeric_plates[0][1]
    (CACHE / "feature_annotations.json").write_text(json.dumps(
        {f: feature_annotations[f] for f in features}, indent=2), encoding="utf-8")
    (CACHE / "normalization_provenance.json").write_text(json.dumps(
        normalization, indent=2), encoding="utf-8")
    compounds = {c["pert_id"]: c for c in manifest["compounds"]}
    for split in ("reference", "development", "test", "test_anchor"):
        source_split = "test" if split == "test_anchor" else split
        keys = sorted(k for k in grouped if compounds[k[0]]["split"] == source_split
                      and (split != "test_anchor" or k[1] == "A375"))
        replicas = [np.asarray(grouped[k]) for k in keys]
        # Missing values remain NaN, never zero; model fitting must qualify their support.
        means = np.asarray([np.nanmean(r, axis=0) for r in replicas])
        offsets = np.cumsum([0] + [len(r) for r in replicas])
        np.savez_compressed(CACHE / (split + ".npz"), features=np.asarray(features),
            pert_id=np.asarray([k[0] for k in keys]), line=np.asarray([k[1] for k in keys]),
            dose=np.asarray([k[2] for k in keys]), time=np.asarray([k[3] for k in keys]),
            mean=means, replicate_values=np.concatenate(replicas), replicate_offsets=offsets)
        (CACHE / (split + "_provenance.json")).write_text(json.dumps(
            [{"unit": k, "samples": provenance[k]} for k in keys], indent=2), encoding="utf-8")
    return {"prepared": True, "test_outcome_summary": "not computed"}


def acquire_pharmacology(compounds):
    """Retrieve PubChem descriptions only; retain immutable source receipts per CID."""
    from datetime import datetime, timezone
    import time
    receipts = {}
    folder = CACHE / "pharmacology"
    folder.mkdir(parents=True, exist_ok=True)
    for compound in compounds:
        cid = str(compound.get("pubchem_cid", "")).strip()
        ident = compound["pert_id"]
        if not cid.isdigit():
            receipts[ident] = {"cid": cid, "descriptions": [], "error": "missing_numeric_cid"}
            continue
        path = folder / (cid + ".json")
        if path.exists():
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt.get("payload") is not None:
                digest = hashlib.sha256(json.dumps(receipt["payload"], sort_keys=True).encode()).hexdigest()
                if digest != receipt["payload_sha256"]:
                    raise ValueError("Altered pharmacology receipt: " + cid)
        else:
            url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/" + cid + "/description/JSON"
            receipt = {"cid": cid, "url": url,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "descriptions": [], "payload": None, "error": None,
                "evidence_scope": "provider pharmacology description, not causal or assay truth"}
            try:
                with _open(url) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                receipt["payload"] = payload
                receipt["payload_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                for index, item in enumerate(payload.get("InformationList", {}).get("Information", [])):
                    text = item.get("Description", "")
                    if text:
                        receipt["descriptions"].append({
                            "source_id": "pubchem:" + cid + ":description:" + str(index),
                            "text": text, "source_name": item.get("DescriptionSource"),
                            "source_url": item.get("DescriptionURL"), "title": item.get("Title")})
            except (OSError, ValueError, TimeoutError) as exc:
                receipt["error"] = type(exc).__name__
            with path.open("x", encoding="utf-8") as stream:
                json.dump(receipt, stream, indent=2)
            time.sleep(.25)
        receipts[ident] = receipt
    return receipts


def run_donor_agent(messages, *, arm, query_id, donor_ids, source_ids, stage="qualify"):
    """Serial budgeted call; donor choices and citations are validated, never numeric overrides."""
    from dataclasses import replace
    from datetime import datetime, timezone
    from agent.llm import DeepSeekChatClient, MAESTROSettings, LLMError
    from tools.evaluation.costs import SpendLedger
    freeze = STUDY / "MODEL_FREEZE.json"
    if not freeze.is_file():
        raise ValueError("Freeze model and prompts in MODEL_FREEZE.json before LLM calls")
    settings = MAESTROSettings.from_workspace(ROOT)
    if settings.chat_model != "deepseek-flash":
        raise ValueError("UNAUTHORIZED_MODEL")
    if stage not in ("acquire", "qualify"):
        raise ValueError("Unknown donor evidence stage")
    if len(json.dumps(messages)) > 60000:
        raise ValueError("Prompt exceeds frozen 60000-character budget bound")
    settings = replace(settings, timeout_seconds=45, max_tokens=900,
                       log_directory=STUDY / "provider_logs")
    specification = {"messages": messages, "arm": arm, "query_id": query_id,
        "donor_ids": sorted(donor_ids), "source_ids": sorted(source_ids),
        "model": settings.chat_model, "max_tokens": 900, "stage": stage,
        "model_freeze_sha256": hashlib.sha256(freeze.read_bytes()).hexdigest()}
    key = hashlib.sha256(json.dumps(specification, sort_keys=True).encode()).hexdigest()
    folder = STUDY / "llm_cache"
    folder.mkdir(exist_ok=True)
    path = folder / (key + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    label = arm + ":" + query_id + ":" + stage + ":" + key
    reservation = .015
    ledger_path = STUDY / "api_ledger.json"
    with _WRITE_LOCK:
        ledger = SpendLedger.load(ledger_path, ceiling_usd=2.50)
        if ledger.ceiling_usd > 2.50:
            raise ValueError("Study API ceiling exceeds authorized USD 2.50")
        if any(entry.label == label for entry in ledger.entries):
            raise ValueError("Uncached prior call: inspect ledger/provider logs before retrying")
        ledger.reserve(label, reservation)
        ledger.charge(label, {"model": settings.chat_model}, status="pending",
            reserved_usd=reservation, note="Conservative Flash reservation, not an invoice; raw usage retained.")
        ledger.write()
    client = DeepSeekChatClient(settings)
    obj, error, response_payload = None, None, None
    started = datetime.now(timezone.utc).isoformat()
    try:
        obj, response = client.complete_json(messages, max_tokens=900)
        response_payload = {"content": response.content, "finish_reason": response.finish_reason,
                            "model": response.model, "usage": dict(response.usage)}
        if not isinstance(obj, dict):
            raise ValueError("Expected a JSON object response")
        choices = obj.get("requests") if stage == "acquire" else obj.get("donors")
        if not isinstance(choices, list) or len(choices) > 5:
            raise ValueError("Expected at most five donor requests or qualifications")
        seen = set()
        for choice in choices:
            if stage == "acquire":
                if choice not in donor_ids or choice in seen:
                    raise ValueError("Invalid or duplicate acquisition donor ID")
                seen.add(choice)
                continue
            if not isinstance(choice, dict) or choice.get("id") not in donor_ids or choice["id"] in seen:
                raise ValueError("Invalid or duplicate donor ID")
            seen.add(choice["id"])
            citations = choice.get("source_ids")
            if not isinstance(citations, list) or not citations or any(c not in source_ids for c in citations):
                raise ValueError("Missing or unknown donor source citation")
            if not isinstance(choice.get("reason"), str):
                raise ValueError("Missing donor qualification rationale")
    except (LLMError, ValueError, TypeError, AttributeError) as exc:
        error = getattr(exc, "code", type(exc).__name__)
    usage = {**client.provider_usage, "model": settings.chat_model}
    with _WRITE_LOCK:
        ledger = SpendLedger.load(ledger_path, ceiling_usd=2.50)
        matches = [i for i, item in enumerate(ledger.entries) if item.label == label]
        if len(matches) != 1:
            raise ValueError("Reserved provider ledger entry is missing or ambiguous")
        ledger.entries[matches[0]] = replace(ledger.entries[matches[0]],
            status="failed" if error else "ok", usage=usage)
        ledger.write()
    record = {"key": key, "specification": specification, "object": obj, "error": error,
              "usage": usage, "response": response_payload, "started_at": started,
              "finished_at": datetime.now(timezone.utc).isoformat()}
    with _WRITE_LOCK:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
    return record


def write_json(name, value):
    (STUDY / name).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def eligible_metadata():
    manifest = json.loads((CACHE / "metadata.json").read_text(encoding="utf-8"))
    result = []
    for compound in manifest["compounds"]:
        if not compound.get("evaluation_eligible", True):
            continue
        counts = {}
        for sample in compound["samples"]:
            key = (float(sample["pert_dose"]), sample["cell_id"])
            counts[key] = counts.get(key, 0) + 1
        doses = sorted({dose for dose, line in counts if all(counts.get((dose, c), 0) >= 2 for c in LINES)})
        if doses:
            result.append({**compound, "selected_dose": doses[0]})
    return result


def load_tensor(split, compounds, *, anchors_only=False):
    """The policy loads test_anchor, never test.npz. Only evaluate() opens test targets."""
    source = CACHE / (("test_anchor" if anchors_only else split) + ".npz")
    with np.load(source, allow_pickle=False) as z:
        features = z["features"].tolist()
        tensor = np.full((len(compounds), 4, len(features)), np.nan)
        replicates = {}
        lookup = {(str(c), str(line), float(dose)): i for i, (c, line, dose) in
                  enumerate(zip(z["pert_id"], z["line"], z["dose"]))}
        for i, compound in enumerate(compounds):
            for t, line in enumerate(LINES):
                key = (compound["pert_id"], line, compound["selected_dose"])
                if key in lookup:
                    index = lookup[key]
                    tensor[i, t] = z["mean"][index]
                    lo, hi = z["replicate_offsets"][index:index+2]
                    replicates[i, t] = z["replicate_values"][lo:hi]
    return tensor, replicates, features


def cosine(a, b):
    return np.sum(a*b, axis=-1) / np.maximum(np.linalg.norm(a, axis=-1)*np.linalg.norm(b, axis=-1), 1e-12)


def fingerprints(compounds):
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    return np.array([generator.GetFingerprintAsNumPy(Chem.MolFromSmiles(c["smiles"])) for c in compounds], bool)


def build_predictions(reference, queries, ref_y, anchors, receipts):
    from virtual_cell.knowledge_transfer import fit_ridge_map
    keep = np.isfinite(ref_y).all(axis=(0, 1))
    if keep.sum() < 5:
        raise ValueError("Insufficient complete reference features")
    y = ref_y[..., keep]
    scale = np.maximum(y.reshape(-1, y.shape[-1]).std(axis=0, ddof=1), .1)
    y = y / scale
    anchor = anchors[:, 0, keep] / scale
    # Reference-only means impute missing visible anchor probes; never hidden target probes.
    missing_anchor = (~np.isfinite(anchor)).sum(axis=1)
    anchor = np.where(np.isfinite(anchor), anchor, y[:, 0].mean(axis=0))
    ref_center = y[:, 0].mean(axis=0)
    sim = cosine(anchor[:, None]-ref_center, y[None, :, 0]-ref_center)
    qfp, rfp = fingerprints(queries), fingerprints(reference)
    intersection = qfp.astype(float) @ rfp.astype(float).T
    chemical = intersection / np.maximum(qfp.sum(1)[:, None]+rfp.sum(1)[None]-intersection, 1)
    stop = set("the a an and or of in to is as with for by from that this compound drug has it its was are on inhibitor activity".split())
    def tokens(c):
        text = " ".join(d["text"] for d in receipts.get(c["pert_id"], {}).get("descriptions", []))
        return set(re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())) - stop
    qt, rt = list(map(tokens, queries)), list(map(tokens, reference))
    lexical = np.array([[len(a & b)/max(len(a | b), 1) for b in rt] for a in qt])
    out = {"reference_mean": np.broadcast_to(y[:, 1:].mean(0), (len(queries), 3, len(scale))).copy(),
           "shifted_anchor": anchor[:, None]+(y[:, 1:]-y[:, :1]).mean(0)[None]}
    ridge, maps = [], []
    for t in range(1, 4):
        target_mean = y[:, t].mean(0)
        fitted = fit_ridge_map(y[:, 0]-ref_center, y[:, t]-target_mean, lams=(1., 10., 100., 1000.))
        ridge.append((anchor-ref_center) @ fitted.B+target_mean)
        maps.append({"target": LINES[t], "lambda": fitted.lam, "reference_loo_cosine": fitted.loo_cosine})
    out["ridge"] = np.stack(ridge, axis=1)
    for name, similarity in (("phenotype", sim), ("chemical", chemical), ("lexical", lexical)):
        predictions = []
        for i in range(len(queries)):
            order = np.argsort(-similarity[i], kind="stable")[:5]
            weights = np.maximum(similarity[i, order], 0)
            weights = weights/weights.sum() if weights.sum() else np.full(len(order), 1/len(order))
            predictions.append(anchor[i]+np.einsum("r,rtf->tf", weights, y[order, 1:]-y[order, :1]))
        out[name] = np.array(predictions)
    out["no_agent_model"] = .5*out["ridge"]+.5*out["phenotype"]
    context = {"keep": keep, "scale": scale, "reference_y": y, "anchor": anchor,
               "phenotype": sim, "chemical": chemical, "maps": maps,
               "missing_anchor": missing_anchor.tolist()}
    return out, context


def selected_actions(prediction):
    flat = prediction.reshape(len(prediction), -1)
    index = np.argmax(np.abs(flat), axis=1)
    return [{"target": int(j//prediction.shape[-1])+1, "feature": int(j % prediction.shape[-1]),
             "sign": 1 if flat[i, j] >= 0 else -1} for i, j in enumerate(index)]


def score(prediction, truth, replicates, keep, scale):
    actions = selected_actions(prediction)
    y = truth[..., keep]
    hits, effects = [], []
    original_features = np.flatnonzero(keep)
    for i, action in enumerate(actions):
        t, f, sign = action["target"], action["feature"], action["sign"]
        raw = replicates[i, t][:, original_features[f]]
        raw = raw[np.isfinite(raw)]
        effect = float(sign*y[i, t, f])
        effects.append(effect if np.isfinite(effect) else None)
        hits.append(int(len(raw) >= 2 and np.isfinite(effect) and effect > .5 and np.all(sign*raw > 0)))
    target = y[:, 1:]/scale
    center = target - np.nanmean(target, axis=-1, keepdims=True)
    pred_center = prediction-prediction.mean(axis=-1, keepdims=True)
    valid = np.isfinite(center).all(-1)
    c = cosine(pred_center, np.nan_to_num(center))
    per_compound = [float(c[i, valid[i]].mean()) if valid[i].any() else None for i in range(len(c))]
    return {"hits": hits, "hit_count": sum(hits), "n": len(hits), "signed_effects": effects,
            "cosine_per_compound": per_compound,
            "mean_cosine": float(np.mean([v for v in per_compound if v is not None])), "actions": actions}


def develop():
    compounds = eligible_metadata()
    ref = [c for c in compounds if c["split"] == "reference"]
    dev = [c for c in compounds if c["split"] == "development"]
    ry, _, features = load_tensor("reference", ref)
    dy, replicas, _ = load_tensor("development", dev)
    receipts = acquire_pharmacology(compounds)
    pred, context = build_predictions(ref, dev, ry, dy[:, :1], receipts)
    scored = {name: score(p, dy, replicas, context["keep"], context["scale"]) for name, p in pred.items()}
    best = max(scored, key=lambda name: (scored[name]["hit_count"], scored[name]["mean_cosine"]))
    result = {"reference_n": len(ref), "development_n": len(dev), "retained_features": int(context["keep"].sum()),
              "total_features": len(features), "best_deterministic": best, "maps": context["maps"], "results": scored}
    write_json("DEVELOPMENT.json", result)
    print(json.dumps({k:v for k,v in result.items() if k != "results"}), flush=True)


def source_cards(receipt, limit=1800):
    return [{"source_id": d["source_id"], "text": d["text"][:limit],
             "provider": d.get("source_name"), "url": d.get("source_url")}
            for d in receipt.get("descriptions", [])[:2]]


def agent_predictions(reference, queries, predictions, context, receipts, features):
    """Two-stage evidence acquisition; reference outcomes remain fixed numerical donor assets."""
    y, anchor = context["reference_y"], context["anchor"]
    kept_features = np.asarray(features)[context["keep"]]
    annotations = json.loads((CACHE / "feature_annotations.json").read_text())
    audit = []

    def run_arm(arm):
        donor_predictions, initial_predictions = [], []
        for i, query in enumerate(queries):
            ph = context["phenotype"][i]
            ch = context["chemical"][i]
            indices = sorted(set(np.argsort(-ph, kind="stable")[:8]) | set(np.argsort(-ch, kind="stable")[:8]))
            by_id = {reference[j]["pert_id"]: j for j in indices}
            menu = [{"id": reference[j]["pert_id"], "name": reference[j]["name"],
                     "dose_uM": reference[j]["selected_dose"], "anchor_similarity": round(float(ph[j]), 4),
                     "structure_similarity": round(float(ch[j]), 4)} for j in indices]
            top = np.argsort(-np.abs(anchor[i]))[:6]
            packet = {"query": {"id": query["pert_id"], "name": query["name"], "dose_uM": query["selected_dose"],
                      "exposure_hours": 24, "anchor_line": "A375",
                      "anchor_features": [{"id": str(kept_features[f]),
                         "histone_mark": annotations[str(kept_features[f])].get("pr_gcp_histone_mark"),
                         "standardized": round(float(anchor[i, f]), 4)} for f in top]},
                      "query_sources": source_cards(receipts.get(query["pert_id"], {})), "candidate_donors": menu}
            if arm != "agent_only":
                diagnostics = {}
                for name in ("ridge", "phenotype", "chemical"):
                    p = predictions[name][i:i+1]
                    a = selected_actions(p)[0]
                    diagnostics[name] = {"line": LINES[a["target"]], "feature": str(kept_features[a["feature"]]),
                                         "histone_mark": annotations[str(kept_features[a["feature"]])].get("pr_gcp_histone_mark"),
                                         "sign": a["sign"], "value": float(p[0, a["target"]-1, a["feature"]])}
                packet["model_diagnostics"] = diagnostics
            style = ("Form competing pharmacological explanations for model disagreement. Identify the missing evidence, retrieve relevant donor descriptions, and revise donor support using attributed evidence."
                     if arm == "integrated" else "Analyze the compound scientifically and use the available information and tools to identify relevant transfer donors.")
            system = ("You are a scientific agent. " + style +
                " You may select measured reference donors, never fabricate response values. Drug descriptions are pharmacology, not proof of context-specific response. "
                "The fixed external decoder transfers donor target-minus-A375 responses, then selects one target cell/feature/sign. "
                "Aim for a reproducible histone perturbation (>0.5 log2 vs vehicle). No viability or causal claim. Return JSON only.")
            packet["task"] = "Choose at most five donor IDs whose pharmacology descriptions should be retrieved. Return {requests:[id,...],donors:[{id:...}],hypotheses:[...],evidence_gap:string}. Initial donors are optional source-free choices; <=5."
            messages = [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(packet)}]
            first = run_donor_agent(messages, arm=arm+":acquire", query_id=query["pert_id"],
                                    donor_ids=list(by_id), source_ids=[], stage="acquire")
            obj = first.get("object") if not first.get("error") else None
            requested = obj.get("requests", []) if isinstance(obj, dict) else []
            requested = list(dict.fromkeys(j for j in requested if j in by_id))[:5]
            if not requested:
                requested = [reference[j]["pert_id"] for j in sorted(indices, key=lambda j: (-ph[j], j))[:5]]
            acquired = {ident: source_cards(receipts.get(ident, {})) for ident in requested}
            source_ids = [d["source_id"] for cards in acquired.values() for d in cards]
            source_ids += [d["source_id"] for d in packet["query_sources"]]
            messages += [{"role": "assistant", "content": json.dumps(obj or {"error": first.get("error")})},
                         {"role": "user", "content": json.dumps({"retrieved_sources": acquired,
                           "task": "Revise donor support. Choose <=5 donors ONLY from retrieved donor IDs; cite supplied source IDs and <=30-word reasons. Abstain with donors:[] if unsupported. Return {donors:[{id,source_ids:[...],reason}],revised_hypotheses:[...],unresolved:[...]}."})}]
            final = run_donor_agent(messages, arm=arm+":qualify", query_id=query["pert_id"],
                                    donor_ids=requested, source_ids=source_ids, stage="qualify")
            def decode(record, initial=False):
                obj = record.get("object") if not record.get("error") else None
                items = obj.get("donors", []) if isinstance(obj, dict) else []
                ids = list(dict.fromkeys(d.get("id") for d in items if isinstance(d, dict) and d.get("id") in by_id))[:5]
                if not initial:
                    # A query-only citation cannot qualify a reference donor.
                    ids = [ident for ident in ids if any(d.get("id") == ident and
                           set(d.get("source_ids", [])) & {s["source_id"] for s in acquired.get(ident, [])} for d in items)]
                if not ids:
                    return predictions["phenotype"][i], []
                idx = [by_id[ident] for ident in ids]
                return anchor[i]+(y[idx, 1:]-y[idx, :1]).mean(0), ids
            before, before_ids = decode(first, initial=True)
            after, after_ids = decode(final)
            donor_predictions.append(after)
            initial_predictions.append(before)
            with _WRITE_LOCK:
                audit.append({"arm": arm, "query": query["pert_id"], "requested": requested,
                              "initial_donors": before_ids, "final_donors": after_ids,
                              "initial_cache_key": first["key"], "final_cache_key": final["key"],
                              "fallback": not bool(after_ids), "errors": [first.get("error"), final.get("error")]})
                write_json("AGENT_AUDIT.json", audit)
            print(arm, query["name"], "sources", sum(bool(v) for v in acquired.values()), "donors", len(after_ids), flush=True)
        return arm, np.asarray(donor_predictions), np.asarray(initial_predictions)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = [future.result() for future in
                   [pool.submit(run_arm, arm) for arm in ("integrated", "conventional", "agent_only")]]
    outputs = {}
    for arm, donors, initial in results:
        outputs[arm] = donors if arm == "agent_only" else .5*predictions["ridge"]+.5*donors
        if arm == "integrated":
            outputs["source_free_initial"] = .5*predictions["ridge"]+.5*initial
            # Shuffle donor residuals, preserving each query's own observed anchor.
            residual = donors-anchor[:, None]
            outputs["shuffled_evidence"] = .5*predictions["ridge"]+.5*(anchor[:, None]+np.roll(residual, 1, axis=0))
    return outputs


def choose():
    if (STUDY / "RESULTS.json").exists():
        raise ValueError("Test already evaluated; do not regenerate choices")
    freeze = json.loads((STUDY / "MODEL_FREEZE.json").read_text())
    if freeze["driver_sha256"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError("Model/prompt driver changed after freeze")
    compounds = eligible_metadata()
    ref = [c for c in compounds if c["split"] == "reference"]
    query = [c for c in compounds if c["split"] == "test"]
    ry, _, features = load_tensor("reference", ref)
    anchors, _, _ = load_tensor("test", query, anchors_only=True)
    receipts = acquire_pharmacology(compounds)
    pred, context = build_predictions(ref, query, ry, anchors, receipts)
    pred.update(agent_predictions(ref, query, pred, context, receipts, features))
    np.savez_compressed(STUDY / "predictions.npz", **pred, keep=context["keep"], scale=context["scale"])
    choices = {"ids": [c["pert_id"] for c in query], "actions": {name: selected_actions(p) for name, p in pred.items()},
               "missing_anchor_features": context["missing_anchor"],
               "model_freeze_sha256": hashlib.sha256((STUDY / "MODEL_FREEZE.json").read_bytes()).hexdigest(),
               "predictions_sha256": hashlib.sha256((STUDY / "predictions.npz").read_bytes()).hexdigest()}
    write_json("CHOICES.json", choices)
    print("All target choices persisted; test target outcomes remain unopened by policy", flush=True)


def evaluate():
    from scipy.stats import binomtest
    if (STUDY / "RESULTS.json").exists():
        raise ValueError("Test evaluation is one-shot; use existing results")
    choices = json.loads((STUDY / "CHOICES.json").read_text())
    if choices["predictions_sha256"] != hashlib.sha256((STUDY / "predictions.npz").read_bytes()).hexdigest():
        raise ValueError("Prediction hash mismatch")
    compounds = [c for c in eligible_metadata() if c["split"] == "test"]
    if choices["ids"] != [c["pert_id"] for c in compounds]:
        raise ValueError("Test identity mismatch")
    truth, replicas, _ = load_tensor("test", compounds)
    with np.load(STUDY / "predictions.npz") as z:
        keep, scale = z["keep"], z["scale"]
        scores = {name: score(z[name], truth, replicas, keep, scale) for name in choices["actions"]}
        if any(scores[name]["actions"] != choices["actions"][name] for name in scores):
            raise ValueError("Scored actions differ from frozen choices")
    best = json.loads((STUDY / "DEVELOPMENT.json").read_text())["best_deterministic"]
    rng = np.random.default_rng(20261013)
    indices = rng.integers(len(compounds), size=(10000, len(compounds)))
    comparisons = {}
    for baseline in (best, "conventional", "no_agent_model", "agent_only", "source_free_initial", "shuffled_evidence"):
        a, b = np.array(scores["integrated"]["hits"]), np.array(scores[baseline]["hits"])
        difference = a-b
        wins, losses = int((difference > 0).sum()), int((difference < 0).sum())
        comparisons[baseline] = {"mean_hit_difference": float(difference.mean()),
            "bootstrap_95": np.quantile(difference[indices].mean(1), [.025, .975]).tolist(),
            "wins": wins, "losses": losses,
            "paired_p_two_sided": float(binomtest(wins, wins+losses).pvalue) if wins+losses else 1.}
    interaction = (np.array(scores["integrated"]["hits"])-np.array(scores["no_agent_model"]["hits"]))-(
                    np.array(scores["agent_only"]["hits"])-np.array(scores["shifted_anchor"]["hits"]))
    oracle = []
    for i in range(len(compounds)):
        attainable = False
        for t in range(1, 4):
            for f in np.flatnonzero(keep):
                raw = replicas[i, t][:, f]
                raw = raw[np.isfinite(raw)]
                if len(raw) >= 2 and abs(truth[i, t, f]) > .5 and (np.all(raw > 0) or np.all(raw < 0)):
                    attainable = True
        oracle.append(int(attainable))
    result = {"test_n": len(compounds), "results": scores, "comparisons": comparisons,
              "development_selected_baseline": best, "oracle_hits": sum(oracle),
              "interaction": {"mean": float(interaction.mean()), "bootstrap_95": np.quantile(interaction[indices].mean(1), [.025, .975]).tolist()},
              "synergy_supported": comparisons[best]["bootstrap_95"][0] > 0 and comparisons["conventional"]["bootstrap_95"][0] > 0}
    write_json("RESULTS.json", result)
    print(json.dumps({"hits": {name: s["hit_count"] for name, s in scores.items()}, "synergy_supported": result["synergy_supported"]}), flush=True)


def verify():
    """Scientific boundary checks and deterministic replay; never initiates an API call."""
    compounds = eligible_metadata()
    split_groups = {s: {c["connectivity"] for c in compounds if c["split"] == s}
                    for s in ("reference", "development", "test")}
    assert not split_groups["reference"] & split_groups["development"]
    assert not split_groups["reference"] & split_groups["test"]
    assert not split_groups["development"] & split_groups["test"]
    assert all(c["name"].lower() not in CONTROL_NAMES for c in compounds)
    assert all(c["name"].lower() not in EXPOSED_NAMES for c in compounds if c["split"] == "test")
    with np.load(CACHE / "test_anchor.npz") as z:
        assert set(z["line"]) == {"A375"}
    for item in json.loads((CACHE / "normalization_provenance.json").read_text()):
        assert "LVL3" in item["source_url"] and len(item["vehicle_samples"]) >= 2
        assert hashlib.sha256(Path(item["source_path"]).read_bytes()).hexdigest() == item["source_sha256"]
        assert all(s["pert_iname"].lower() == "dmso" for s in item["vehicle_samples"])
    freeze = json.loads((STUDY / "FREEZE.json").read_text())
    assert hashlib.sha256((STUDY / "PROTOCOL.md").read_bytes()).hexdigest() == freeze["protocol_sha256"]
    # Feature alignment, replicate sign inconsistency, missing target and threshold boundary.
    prediction = np.zeros((4, 3, 2))
    prediction[:, 1, 1] = 3
    truth = np.zeros((4, 4, 3))
    truth[:, 2, 2] = [.6, .6, np.nan, .5]
    replica = {(i, t): np.zeros((2, 3)) for i in range(4) for t in range(4)}
    for i in range(4):
        replica[i, 2][:, 2] = ([.6, .7] if i != 1 else [.7, -.1])
    scored = score(prediction, truth, replica, np.array([True, False, True]), np.ones(2))
    assert scored["hits"] == [1, 0, 0, 0]
    assert all(a == {"target": 2, "feature": 1, "sign": 1} for a in scored["actions"])
    if (STUDY / "MODEL_FREEZE.json").exists():
        model_freeze = json.loads((STUDY / "MODEL_FREEZE.json").read_text())
        assert model_freeze["driver_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    replayed = False
    if (STUDY / "RESULTS.json").exists():
        result = json.loads((STUDY / "RESULTS.json").read_text())
        choices = json.loads((STUDY / "CHOICES.json").read_text())
        assert hashlib.sha256((STUDY / "predictions.npz").read_bytes()).hexdigest() == choices["predictions_sha256"]
        queries = [c for c in compounds if c["split"] == "test"]
        truth, replicas, _ = load_tensor("test", queries)
        with np.load(STUDY / "predictions.npz") as z:
            for name, expected in result["results"].items():
                actual = score(z[name], truth, replicas, z["keep"], z["scale"])
                assert actual == expected, name
        replayed = True
    if (STUDY / "ARTIFACTS.json").exists():
        for relative, digest in json.loads((STUDY / "ARTIFACTS.json").read_text())["sha256"].items():
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    print(json.dumps({"verified": True, "split_counts": {k: len(v) for k, v in split_groups.items()},
                      "one_anchor_boundary": True, "normalization_sources": 16,
                      "feature_and_replicate_semantics": True, "results_replayed": replayed}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("metadata", "prepare", "develop", "choose", "evaluate", "verify"))
    args = parser.parse_args()
    if args.command == "metadata":
        manifest = acquire_metadata()
        print(json.dumps({"plates": len(manifest["plates"]), "compounds": len(manifest["compounds"]),
            "split_compounds": {s: sum(c["split"] == s for c in manifest["compounds"])
                                for s in ("reference", "development", "test")}, "outcomes_opened": False}))
    elif args.command == "prepare":
        print(json.dumps(prepare()))
    else:
        globals()[args.command]()


if __name__ == "__main__":
    main()

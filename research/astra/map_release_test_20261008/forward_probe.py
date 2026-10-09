"""Post-hoc input-sensitivity diagnosis; not a biological MAP evaluation.

Compare the released-code causal CLS readout with a disclosed runtime
bidirectional-mask intervention. Parameters and authentic basal fixture are fixed.
The old checkpoint-specific forward and output gene names remain unresolved.
"""
import json
import types

import numpy as np
import torch

from native import ASSETS, OUT, load, se_forward


def main():
    destination = OUT / "FORWARD_PROBE.json"
    if destination.exists():
        raise RuntimeError("Refuse to overwrite forward diagnosis")
    torch.set_num_threads(4)
    model, _ = load()
    model.cuda()
    for layer in model.se.transformer_encoder.layers:
        layer.dropout = 0.
    source = ASSETS / "official_source/MAP/data/minimal_dataset/minimal_dataset/preprocessed_se_inputs_memmap/CVCL_0023"
    shape = json.loads((source / "se_shape.json").read_text())
    dims = (shape["N"], shape["pad_length"])
    genes = torch.from_numpy(np.memmap(source / "se_gene_ids.npy", dtype="int32", mode="r", shape=dims)[:1].copy()).long().cuda()
    counts = torch.from_numpy(np.memmap(source / "se_expr.npy", dtype="float16", mode="r", shape=dims)[:1].copy()).float().cuda()
    records = json.loads((OUT / "IDENTITIES.json").read_text())["records"]
    smiles = sorted({r["smiles"] for r in records if r["smiles"]})
    drugs = [smiles[0], smiles[-1]]
    pert = model.pert_model
    with torch.inference_mode():
        state, cls, esm = se_forward(model.se, genes, counts)
        drug_vectors = pert.encode_drug(drugs)
        drug_gap = float((drug_vectors[0] - drug_vectors[1]).abs().max())
        assert drug_gap > 1e-6
        cell, gene = pert.encode_cells(cls), pert.encode_genes(state, esm)
        def sequence(i):
            return torch.cat([cell[:, None], drug_vectors[i:i+1, None], gene], dim=1)
        hidden0 = pert.transformer_backbone(inputs_embeds=sequence(0)).last_hidden_state
        hidden1 = pert.transformer_backbone(inputs_embeds=sequence(1)).last_hidden_state
        causal_cls_gap = float((hidden0[:, 0] - hidden1[:, 0]).abs().max())
        causal_drug_gap = float((hidden0[:, 1] - hidden1[:, 1]).abs().max())
        assert causal_cls_gap == 0 and causal_drug_gap > 1e-6
        del hidden0, hidden1
        original_mask = pert.transformer_backbone._prepare_decoder_attention_mask
        def bidirectional(self, attention_mask, input_shape, inputs_embeds, past_key_values_length):
            assert past_key_values_length == 0 and bool(attention_mask.all())
            batch, length = input_shape
            return torch.zeros((batch, 1, length, length), dtype=inputs_embeds.dtype,
                               device=inputs_embeds.device)
        pert.transformer_backbone._prepare_decoder_attention_mask = types.MethodType(bidirectional, pert.transformer_backbone)
        predictions = [pert(state, cls, esm, [drug], torch.tensor([.5], device="cuda"))[1]
                       for drug in drugs]
        changed_gap = float((predictions[0] - predictions[1]).abs().max())
        assert changed_gap > 1e-6
        pert.transformer_backbone._prepare_decoder_attention_mask = original_mask
    receipt = {"post_hoc": True, "drug_structures": drugs,
        "projected_drug_vector_max_gap": drug_gap,
        "causal_first_CLS_hidden_max_gap": causal_cls_gap,
        "causal_second_drug_hidden_max_gap": causal_drug_gap,
        "runtime_bidirectional_output_max_gap": changed_gap,
        "diagnosis": "Current public Llama backbone uses causal masking but public PerturbationEncoder reads position0 [CLS|Drug|Genes]; CLS cannot attend the drug or gene tokens. Verified for the checkpoint-compatible bridge, not authenticated old PrimeKG_ver1 forward.",
        "intervention": "Runtime bidirectional mask only; restored afterward. No parameter change, retraining or claim that changing mask restores the trained model's biological validity.",
        "blocked": "Missing authenticated original forward/HVG gene order; no native candidate outcome comparison or production promotion",
        "peak_gpu_bytes": torch.cuda.max_memory_allocated()}
    destination.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

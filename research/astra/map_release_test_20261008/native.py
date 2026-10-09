"""Checkpoint-compatible component forward audit on the official basal fixture.

The released checkpoint predates the published MAP-KG module hierarchy. This
bridge uses its actual molecular tower and drug projector, with current public
component forwards. Strict tensor loading does not authenticate the old forward
semantics. No endpoint inference is licensed without its 2000-output gene order.
"""
import json
import pickle
import sys
import time
import types
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf
from safetensors import safe_open

from encoder import ASSETS, checkpoint, load_encoder

OUT = Path(__file__).resolve().parents[3] / "outputs/paper_01286/released_test"


def modules():
    sys.path[:0] = [str(ASSETS / "compat"), str(ASSETS / "official_source/MAP"),
                   str(ASSETS / "official_source/MAP/model")]
    package = types.ModuleType("model")
    package.__path__ = [str(ASSETS / "official_source/MAP/model")]
    sys.modules["model"] = package
    from model.se import StateEmbeddingModel
    from model.pert import PerturbationEncoder
    from model.components import CellProjector, ResidualProjector, ProjectOut
    from model.gene_decoders import LatentToGeneDecoder
    from model.transformer_encoder import get_transformer_backbone, ST_small_transformer_backbone_kwargs
    return (StateEmbeddingModel, PerturbationEncoder, CellProjector, ResidualProjector,
            ProjectOut, LatentToGeneDecoder, get_transformer_backbone, ST_small_transformer_backbone_kwargs)


def load():
    State, Pert, Cell, Residual, Out, Decoder, backbone, defaults = modules()
    cfg = OmegaConf.load(ASSETS / "official_source/MAP/configs/se600m.yaml")
    state = checkpoint(ASSETS / "epoch_3.pt")
    with torch.device("meta"):
        model = torch.nn.Module()
        model.se = State(token_dim=5120, d_model=2048, nhead=16, d_hid=2048,
                         nlayers=16, output_dim=2048, dropout=.1, cfg=cfg)
        model.se.pe_embedding = torch.nn.Embedding(*state["se.pe_embedding.weight"].shape)
        class CheckpointPert(Pert):
            def encode_drug(self, smiles):
                # Compatible with all released tensor names/shapes; the old
                # PrimeKG_ver1 forward is absent from public Git history.
                return self.drug_projector(self.smiles_encoder(smiles))

        pert = CheckpointPert.__new__(CheckpointPert)
        torch.nn.Module.__init__(pert)
        pert.smile_encoder = "PrimeKG_ver1_checkpoint_bridge"
        pert.cell_projector = Cell(n_layers=4, d_cell=2048, d_out=1024, dropout=.1)
        pert.smiles_encoder = load_encoder().smiles_encoder
        pert.drug_projector = Residual(256, 1024, 512)
        pert.gene_tokens_projector = Residual(2048 + 5120, 1024, 2048)
        kwargs = dict(defaults, max_position_embeddings=2049, hidden_size=1024)
        pert.transformer_backbone, _ = backbone("llama", kwargs)
        pert.project_out = Out(1024, 2048, .1)
        pert.gene_decoder = Decoder(2048, 2000, [512, 1024], .1)
        model.pert_model = pert
    expected = model.state_dict()
    missing = sorted(set(expected) - set(state))
    extra = sorted(set(state) - set(expected))
    assert not missing and not extra, (missing[:8], extra[:8], len(missing), len(extra))
    assert all(expected[k].shape == state[k].shape for k in expected)
    model.load_state_dict(state, strict=True, assign=True)
    # Nonpersistent rotary caches are deterministic functions of loaded inv_freq,
    # not trained/missing parameters. Rebuild those meta-device constructor caches.
    for layer in model.pert_model.transformer_backbone.layers:
        rotary = layer.self_attn.rotary_emb
        t = torch.arange(rotary.max_seq_len_cached, device=rotary.inv_freq.device,
                         dtype=rotary.inv_freq.dtype)
        frequencies = torch.outer(t, rotary.inv_freq)
        angles = torch.cat((frequencies, frequencies), dim=-1)
        rotary.cos_cached = angles.cos()[None, None]
        rotary.sin_cached = angles.sin()[None, None]
    assert not any(t.is_meta for t in model.buffers())
    return model.eval(), cfg


def se_forward(se, genes, expressions):
    src = se.pe_embedding(genes)
    esm = src[:, 1:, :].clone()
    src = torch.nn.functional.normalize(src, dim=2)
    src = torch.cat([se.cls_token.expand(src.shape[0], 1, -1), src[:, 1:]], dim=1)
    if se.dataset_token is not None:
        src = torch.cat([src, se.dataset_token.expand(src.shape[0], 1, -1)], dim=1)
    output, embedding, _ = se(src=src, counts=expressions, dataset_nums=None)
    return output[:, 1:-1], embedding, esm


def main():
    if (OUT / "NATIVE_AUDIT.json").exists():
        raise RuntimeError("Refuse to overwrite native audit")
    started = time.perf_counter()
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    model, cfg = load()
    model.cuda()
    fixture = ASSETS / "official_source/MAP/data/minimal_dataset/minimal_dataset"
    # Extract only the public tiny fixture, preserving its original bytes.
    if not fixture.exists():
        import zipfile
        with zipfile.ZipFile(ASSETS / "official_source/MAP/data/minimal_dataset.zip") as archive:
            archive.extractall(fixture.parent)
    source = fixture / "preprocessed_se_inputs_memmap/CVCL_0023"
    shape = json.loads((source / "se_shape.json").read_text())
    meta = pickle.load((fixture / "preprocessed/CVCL_0023/CVCL_0023_meta.pkl").open("rb"))
    controls = json.loads((fixture / "preprocessed/CVCL_0023/control_indices.json").read_text())
    index = next(i for i, value in enumerate(meta["ds_level_index"]) if value in controls)
    dims = (shape["N"], shape["pad_length"])
    genes = torch.from_numpy(np.memmap(source / "se_gene_ids.npy", dtype="int32", mode="r", shape=dims)[index:index+1].copy()).long().cuda()
    expressions = torch.from_numpy(np.memmap(source / "se_expr.npy", dtype="float16", mode="r", shape=dims)[index:index+1].copy()).float().cuda()
    with torch.inference_mode():
        torch.manual_seed(1)
        native1 = se_forward(model.se, genes, expressions)
        torch.manual_seed(2)
        native2 = se_forward(model.se, genes, expressions)
        native_gap = float((native1[1] - native2[1]).abs().max())
        # Official SDPA passes dropout=.1 in eval. Set the runtime field to0,
        # without editing released files or any pretrained parameter.
        for layer in model.se.transformer_encoder.layers:
            layer.dropout = 0.
        fixed1 = se_forward(model.se, genes, expressions)
        fixed2 = se_forward(model.se, genes, expressions)
        for a, b in zip(fixed1, fixed2):
            torch.testing.assert_close(a, b, atol=0, rtol=0)
        records = json.loads((OUT / "IDENTITIES.json").read_text())["records"]
        smiles = sorted({r["smiles"] for r in records if r["smiles"]})[:2]
        predictions = []
        for drug in smiles:
            for dose in (.5, 5.):
                embedding, hvg = model.pert_model(*fixed1, [drug], torch.tensor([dose], device="cuda"))
                assert torch.isfinite(hvg).all() and torch.isfinite(embedding).all()
                predictions.append(hvg.cpu().numpy())
    np.save(OUT / "NATIVE_HVG.npy", np.array(predictions))
    with safe_open(ASSETS / "se600m.safetensors", framework="pt") as released:
        checked = [k for k in model.se.state_dict() if k in released.keys()]
        mismatch = [k for k in checked if not torch.equal(model.se.state_dict()[k].cpu(), released.get_tensor(k))]
    receipt = {"strict_checkpoint_loading": True, "loaded_tensor_keys": len(model.state_dict()),
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "checkpoint_code_compatibility": "Released checkpoint uses PrimeKG_ver1/raw smiles_encoder plus drug_projector; current public code expects kg_smiles_encoder. No old forward found in public pert.py history.",
        "bridge": "Actual checkpoint molecular tower256 -> checkpoint drug_projector1024; remaining current official component forwards. Strict all-key loading, no random/missing tensors. Old forward semantics unverified; not exact MAP reproduction.",
        "se_public_checked_tensors": len(checked), "se_public_different_tensors": mismatch,
        "fixture": {"cell_line": "CVCL_0023", "control_row": index, "cells": 1, "tokens": shape["pad_length"]},
        "native_eval_seed_gap": native_gap,
        "eval_correction": "Runtime SDPA dropout field0; every pretrained parameter unchanged; repeated SE outputs exactly equal",
        "output_shape": list(np.array(predictions).shape),
        "dose_pair_max_difference": [float(np.max(np.abs(predictions[i] - predictions[i+1]))) for i in (0, 2)],
        "different_drug_max_difference": float(np.max(np.abs(predictions[0] - predictions[2]))),
        "dose_limitation": "Current public PerturbationEncoder.forward, used in this bridge, ignores concs. Dose invariance is measured for this bridge; original PrimeKG_ver1 forward is unavailable.",
        "output_gene_order": "Not published in fixture or weight keys; blocked from treating index as authenticated gene",
        "scope": "Actual checkpoint-backed compatible component forward and STATE-SE audit on public fixture; not authenticated original MAP forward or response/decision-value evaluation",
        "seconds": time.perf_counter() - started,
        "peak_gpu_bytes": torch.cuda.max_memory_allocated()}
    (OUT / "NATIVE_AUDIT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

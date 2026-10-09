"""Strict-load the released molecular tower/projector using pinned official code."""
import sys
from pathlib import Path

import numpy as np
import torch

ASSETS = Path(__file__).resolve().parents[3] / "data/external/map_release_20261008"


def checkpoint(path):
    # The public checkpoint includes NumPy scalar training metadata.
    globals_ = [(np._core.multiarray.scalar, "numpy.core.multiarray.scalar"),
                np.dtype, np.dtypes.Float64DType, np.dtypes.Float32DType]
    with torch.serialization.safe_globals(globals_):
        value = torch.load(path, map_location="cpu", weights_only=True, mmap=True)
    return value.get("model_state_dict", value)


def load_encoder():
    sys.path.insert(0, str(ASSETS / "official_source/MAP"))
    from model.mega_molbart.STMencoder_ddp import MolSTM_Extractor
    from model.mega_molbart.tokenizer import MolEncTokenizer
    from model.mega_molbart.util import REGEX, DEFAULT_CHEM_TOKEN_START
    from model.mega_molbart.decoder import DecodeSampler
    from model.mega_molbart.megatron_bart import MegatronBART
    from model.smiles_kg_encoder_v3 import KGSmilesEncoder_v3, ResidualProjector
    state = checkpoint(ASSETS / "mapkg_encoder_v3.pt")
    molecule = {k.removeprefix("smiles_encoder._model."): v for k, v in state.items()
                if k.startswith("smiles_encoder._model.")}
    tokenizer = MolEncTokenizer.from_vocab_file(ASSETS / "bart_vocab.txt", REGEX,
                                                DEFAULT_CHEM_TOKEN_START)
    assert len(tokenizer) == molecule["emb.weight"].shape[0]
    width = molecule["emb.weight"].shape[1]
    layers = max(int(k.split(".")[2]) for k in molecule if k.startswith("encoder.layers.")) + 1
    length = molecule["pos_emb"].shape[0]
    # Bypass only the constructor's unavailable hardcoded molecule_model.pth.
    # Every inference class/forward remains the official implementation.
    extractor = MolSTM_Extractor.__new__(MolSTM_Extractor)
    torch.nn.Module.__init__(extractor)
    extractor.tokenizer, extractor.max_seq_len = tokenizer, length
    extractor.dim_model = width
    with torch.device("meta"):
        extractor._model = MegatronBART(DecodeSampler(tokenizer, max_seq_len=length),
            pad_token_idx=tokenizer.vocab[tokenizer.pad_token], vocab_size=len(tokenizer),
            d_model=width, num_layers=layers, num_heads=8,
            d_feedforward=molecule["encoder.layers.0.fc1.weight"].shape[0],
            max_seq_len=length, dropout=.1)
        projector = ResidualProjector(width, state["smiles_projector.residual_proj.weight"].shape[0], 512)
    extractor._model.load_state_dict(molecule, strict=True, assign=True)
    projector.load_state_dict({k.removeprefix("smiles_projector."): v for k, v in state.items()
                               if k.startswith("smiles_projector.")}, strict=True, assign=True)
    encoder = KGSmilesEncoder_v3.__new__(KGSmilesEncoder_v3)
    torch.nn.Module.__init__(encoder)
    encoder.smiles_encoder, encoder.smiles_projector = extractor, projector
    return encoder.eval()


def encode(encoder, smiles):
    from rdkit import Chem
    canonical = []
    for s in smiles:
        molecule = Chem.MolFromSmiles(s)
        if molecule is None:
            raise ValueError("Refuse invalid SMILES; never replace a drug with methane")
        canonical.append(Chem.MolToSmiles(molecule, isomericSmiles=True))
    with torch.inference_mode():
        structure = encoder.smiles_encoder(canonical)
        knowledge = encoder.smiles_projector(structure)
    return structure, knowledge


if __name__ == "__main__":
    encoder = load_encoder().cuda()
    a, b = encode(encoder, ["CCO", "CC(=O)O"])
    print("Official encoder forward", list(a.shape), list(b.shape),
          bool(torch.isfinite(b).all()))

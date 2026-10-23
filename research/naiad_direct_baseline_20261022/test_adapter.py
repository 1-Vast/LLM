"""Check source-derived dimension schedule and explicit symmetric inference."""
import torch
from benchmark import author, dimension, predict

assert [dimension(b, 103) for b in [128, 512, 2048]] == [2, 4, 16]
assert dimension(206, 103) == 2 and dimension(412, 103) == 2
torch.manual_seed(0)
model = author.EmbedPhenoModel(3, d_embed=2, d_pheno_hid=256, model_type='both')
ids = torch.tensor([[0, 1], [1, 2]])
scalar = torch.tensor([[.1, -.5], [.2, .4]])
pred = predict(model, ids, scalar)
reverse = predict(model, ids.flip(1), scalar.flip(1))
assert torch.allclose(pred, reverse, atol=1e-7)
assert torch.isfinite(pred).all()
print('PASS exact strict schedule and symmetrized author-model inference')

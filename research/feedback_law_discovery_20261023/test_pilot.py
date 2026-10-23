"""Pre-data checks of independent-context gradients and the meta-training graph."""
import json
import torch
from pilot_accounted import Updater, SetPredictor, OUT


def main():
    torch.set_num_threads(2)
    torch.manual_seed(7)
    indices = torch.tensor([list(range(8)), list(range(8, 16))])
    values = torch.tensor([[0., 1., 2., 0., 1., 2., 0., 1.], [2., 0., 1., 2., 0., 1., 2., 0.]])
    model = Updater(20)
    batch = model.view(indices, values, 'AB', True)
    separate = torch.cat([model.view(indices[i:i+1], values[i:i+1], 'AB', True) for i in range(2)])
    assert torch.allclose(batch, separate, atol=1e-7), 'Contexts must not rescale each other gradients'
    meta_loss = batch[:, 16:].square().mean()
    gradients = torch.autograd.grad(meta_loss, tuple(model.parameters()))
    assert all(torch.isfinite(g).all() and g.abs().sum() > 0 for g in gradients), 'Outer parameters need actual second-order query gradients'
    set_model = SetPredictor(20)
    permutation = torch.tensor([7, 2, 5, 1, 6, 0, 4, 3])
    left = set_model(indices, values)
    right = set_model(indices[:, permutation], values[:, permutation])
    assert torch.allclose(left, right, atol=1e-6), 'Set sentinel must preserve the record package'
    changed = model.view(indices[:1], values[:1], 'AB', False)
    assert torch.allclose(changed, batch[:1].detach(), atol=1e-7), 'Evaluation must match the actual fast update'
    OUT.mkdir(parents=True, exist_ok=True)
    result = dict(status='PASS', independent_context_fast_gradients=True,
                  nonzero_finite_outer_gradients=True, set_permutation_consistency=True,
                  train_eval_update_agreement=True, biological_values_read=0)
    (OUT/'SYNTHETIC_CHECKS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

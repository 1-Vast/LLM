"""Experimental validation-only transcript fitting, not production inference."""
import copy
import numpy as np
import torch
from virtual_cell.learned_response import DoseAnchoredNetwork, ResponseFit


def fit_response(train_x, train_gate, train_y, validation_x, validation_gate, validation_y,
                 *, seed: int, epochs: int = 150, patience: int = 20, device: str = "cpu") -> ResponseFit:
    """Use validation only for early stopping; this function accepts no test labels."""
    arrays = [np.asarray(a, dtype=np.float32) for a in
              (train_x, train_gate, train_y, validation_x, validation_gate, validation_y)]
    if any(not np.isfinite(a).all() for a in arrays) or len(train_x) == 0 or len(validation_x) == 0:
        raise ValueError("invalid_training_data")
    if np.any(arrays[1] < 0) or np.any(arrays[4] < 0):
        raise ValueError("negative_dose_gate")
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(4)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = DoseAnchoredNetwork(arrays[0].shape[1], arrays[2].shape[1]).to(device)
    x, gate, y, vx, vg, vy = [torch.as_tensor(a, device=device) for a in arrays]
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    best, chosen, stale, history, state = float("inf"), 0, 0, [], None
    for epoch in range(1, epochs + 1):
        model.train()
        order = torch.randperm(len(x), device=device)
        for batch in order.split(256):
            optimizer.zero_grad(set_to_none=True)
            loss = (model(x[batch], gate[batch]) - y[batch]).square().mean()
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            train_loss = float((model(x, gate) - y).square().mean())
            value = float((model(vx, vg) - vy).square().mean())
        history.append({"epoch": epoch, "train_mse": train_loss, "validation_mse": value})
        if value < best:
            best, chosen, stale, state = value, epoch, 0, copy.deepcopy(model.state_dict())
        else:
            stale += 1
        if stale >= patience:
            break
    model.load_state_dict(state)
    return ResponseFit(model, history, chosen, seed)

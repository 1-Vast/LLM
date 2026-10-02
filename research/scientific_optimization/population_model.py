"""Experimental conditional population model and validation-only fitting."""
import copy
from dataclasses import dataclass
import numpy as np
import torch
from torch import nn
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist


def _population(value):
    value = np.asarray(value, dtype=np.float32)
    if value.ndim != 2 or min(value.shape) < 1 or not np.isfinite(value).all():
        raise ValueError("invalid_cell_population")
    return value


def population_mmd(predicted, observed, bandwidth: float) -> float:
    """Biased Gaussian MMD²; supports unequal set sizes and no cell pairing.

    Bandwidth must be fixed from training data, not selected on test outcomes.
    This descriptive distance is not an uncertainty or significance estimate.
    """
    x, y = _population(predicted), _population(observed)
    if x.shape[1] != y.shape[1] or not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("invalid_distribution_coordinates_or_bandwidth")
    kernel = lambda a, b: np.exp(-cdist(a, b, "sqeuclidean") / (2 * bandwidth ** 2))
    return float(max(0., kernel(x, x).mean() + kernel(y, y).mean() - 2 * kernel(x, y).mean()))


@dataclass(frozen=True)
class PopulationPair:
    """One matched experimental context, with independently sampled populations.

    group is the outer split unit (e.g. chemical connectivity identity), not a
    cell ID. condition contains only inference-available intervention/context
    covariates. dose_gate is a dimensionless nonnegative dose transform.
    """
    control: np.ndarray
    treated: np.ndarray
    condition: np.ndarray
    dose_gate: float
    group: str

    def validate(self):
        x, y = _population(self.control), _population(self.treated)
        c = np.asarray(self.condition)
        if (x.shape[1] != y.shape[1] or c.ndim != 1 or not len(c)
                or not np.isfinite(c).all() or not np.isfinite(self.dose_gate)
                or self.dose_gate < 0 or not self.group.strip()):
            raise ValueError("invalid_population_condition")


class ConditionalPopulationFlow(nn.Module):
    """Small control-set-conditioned vector field with a structural vehicle anchor.

    Mean and standard deviation provide permutation-invariant population context.
    This is a modest set encoder, not a reproduction of State/STACK attention.
    """
    def __init__(self, dimensions: int, condition_size: int):
        super().__init__()
        self.dimensions, self.condition_size = dimensions, condition_size
        self.velocity = nn.Sequential(nn.Linear(3 * dimensions + condition_size + 1, 64),
                                      nn.SiLU(), nn.Linear(64, 64), nn.SiLU(),
                                      nn.Linear(64, dimensions))

    def forward(self, cells, time, condition, context, dose_gate):
        features = torch.cat((cells, time, condition.expand(len(cells), -1),
                              context.expand(len(cells), -1)), dim=1)
        return self.velocity(features) * dose_gate

    def predict_population(self, control, condition, dose_gate: float, *, steps: int = 16):
        control = _population(control)
        condition = np.asarray(condition, dtype=np.float32)
        if (control.shape[1] != self.dimensions or condition.shape != (self.condition_size,)
                or not np.isfinite(condition).all() or not np.isfinite(dose_gate)
                or dose_gate < 0 or not isinstance(steps, int) or steps < 1):
            raise ValueError("invalid_population_query")
        if dose_gate == 0:
            return control.copy()
        device = next(self.parameters()).device
        x = torch.as_tensor(control, device=device)
        context = torch.cat((x.mean(0), x.std(0, unbiased=False)))
        c = torch.as_tensor(condition, device=device)
        self.eval()
        with torch.no_grad():
            for i in range(steps):
                # Midpoint integration in numerical flow time, not hours.
                t = torch.full((len(x), 1), i / steps, device=device)
                v = self(x, t, c, context, dose_gate)
                x = x + self(x + v / (2 * steps), t + 0.5 / steps, c, context, dose_gate) / steps
        result = x.cpu().numpy()
        if not np.isfinite(result).all():
            raise ValueError("nonfinite_population_prediction")
        return result


def fit_population_flow(training, validation, *, bandwidth: float, seed: int = 0,
                        epochs: int = 80, batch_cells: int = 32):
    """Equal-condition minibatch OT flow matching, selected by validation MMD.

    No test population is accepted. Validate chemical/study split identities;
    preprocessing, metadata provenance and pretraining overlap remain caller duties.
    """
    if not training or not validation or epochs < 1 or batch_cells < 2:
        raise ValueError("invalid_population_training_config")
    for pair in (*training, *validation):
        pair.validate()
    if {p.group for p in training} & {p.group for p in validation}:
        raise ValueError("population_split_group_overlap")
    d, c = training[0].control.shape[1], len(training[0].condition)
    if any(p.control.shape[1] != d or len(p.condition) != c for p in (*training, *validation)):
        raise ValueError("population_training_coordinates_mismatch")
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("invalid_population_bandwidth")
    rng = np.random.default_rng(seed)
    # Keep this experiment's seed from modifying the agent's torch RNG state.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = ConditionalPopulationFlow(d, c)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    training_contexts = []
    for pair in training:
        control = torch.as_tensor(pair.control, dtype=torch.float32)
        training_contexts.append((torch.cat((control.mean(0), control.std(0, unbiased=False))),
                                  torch.as_tensor(pair.condition, dtype=torch.float32)))
    best, state, history = float("inf"), None, []
    for epoch in range(1, epochs + 1):
        model.train()
        losses = []
        for index in rng.permutation(len(training)):
            p = training[index]
            x = p.control[rng.choice(len(p.control), batch_cells, replace=len(p.control) < batch_cells)]
            y = p.treated[rng.choice(len(p.treated), batch_cells, replace=len(p.treated) < batch_cells)]
            # Equal-mass minibatch OT; not inferred cell identity.
            rows, cols = linear_sum_assignment(cdist(x, y, "sqeuclidean"))
            x, y = torch.as_tensor(x[rows], dtype=torch.float32), torch.as_tensor(y[cols], dtype=torch.float32)
            t = torch.as_tensor(rng.uniform(size=(batch_cells, 1)), dtype=torch.float32)
            context, c_tensor = training_contexts[index]
            prediction = model((1 - t) * x + t * y, t, c_tensor, context, p.dose_gate)
            loss = (prediction - (y - x)).square().mean()
            if not torch.isfinite(loss):
                raise ValueError("nonfinite_population_training_loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        score = float(np.mean([population_mmd(model.predict_population(p.control, p.condition, p.dose_gate),
                                             p.treated, bandwidth) for p in validation]))
        history.append({"epoch": epoch, "flow_loss": float(np.mean(losses)), "validation_mmd": score})
        if score < best:
            best, state = score, copy.deepcopy(model.state_dict())
    model.load_state_dict(state)
    model.eval()
    return model, history

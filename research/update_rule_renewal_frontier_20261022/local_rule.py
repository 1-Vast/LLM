"""Candidate local target rule and its same-operation synthetic-gradient foil.

No source files, data, weights or biological observations are loaded here.
The teaching matrix P and initialization must be fitted on independent source
tasks with identical outer losses/budgets in both implementations.
"""
import numpy as np


def local_target_update(A, b, key, outcome, P, rate_a, rate_b):
    pre = A @ key
    hidden = np.tanh(pre)
    error = outcome - b @ hidden
    # Context-dependent teaching direction; no derivative through this target.
    direction = np.tanh(P @ np.concatenate((key, pre, b)))
    target = pre + direction * error
    next_A = A + rate_a * np.outer(target - pre, key)
    next_b = b + rate_b * error * hidden
    return next_A, next_b


def synthetic_gradient_update(A, b, key, outcome, P, rate_a, rate_b):
    pre = A @ key
    hidden = np.tanh(pre)
    error = outcome - b @ hidden
    feedback = np.tanh(P @ np.concatenate((key, pre, b)))
    gradient_at_pre = -feedback * error
    return A - rate_a * np.outer(gradient_at_pre, key), b + rate_b * error * hidden

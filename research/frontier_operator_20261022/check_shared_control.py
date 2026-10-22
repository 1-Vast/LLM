"""Exact synthetic boundary check for reused controls across bundles."""
from fractions import Fraction as F
from pathlib import Path
import json

# theta, shared-control error, and two independent assay errors all have variance1.
# y1=y2=1. Joint observation noise R=[[2,1],[1,2]].
joint_precision = 1 + F(2, 3)
joint_variance = 1 / joint_precision
joint_mean = joint_variance * F(2, 3)
# Mistakenly treating two control errors as fresh independent noise gives R=2I.
independent_precision = 1 + F(1, 2) + F(1, 2)
independent_variance = 1 / independent_precision
independent_mean = independent_variance
assert (joint_mean, joint_variance) == (F(2, 5), F(3, 5))
assert (independent_mean, independent_variance) == (F(1, 2), F(1, 2))
assert independent_variance < joint_variance
result = dict(evidence='exact synthetic Gaussian conditioning only',
              correct_shared_control=dict(mean=str(joint_mean), variance=str(joint_variance)),
              incorrect_fresh_control=dict(mean=str(independent_mean), variance=str(independent_variance)),
              assertions=3,
              conclusion='Per-bundle covariance is insufficient when the same physical control is reused.')
path = Path('D:/MAESTRO/log/20261022/operator_renewal/frontier/SHARED_CONTROL_RESULT.json')
if path.exists():
    raise FileExistsError(path)
path.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))

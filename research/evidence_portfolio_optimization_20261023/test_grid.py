"""An empty numerical bet grid must not silently select an invalid fallback."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'certified_discovery_gates_20261023'))
from evalues import clip_bets


def test_empty_grid_refuses_bet():
    with pytest.raises(ValueError, match='No grid-compliant bets'):
        clip_bets(np.array([1.0]), 1.0, np.array([0.5, 1.0]), np.array([False, False]))

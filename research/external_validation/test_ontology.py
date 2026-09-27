"""Contracts for the development-frozen, truth-free external episode builder."""
from __future__ import annotations

import pytest

from .ontology import build_episode_manifest, build_truth_free_episodes, load


def test_frozen_ontology_matches_development_pools():
    ontology = load()
    assert len(ontology.pool("A")) == 9
    assert len(ontology.pool("B")) == 17
    assert ontology.pool("A") == tuple(sorted(ontology.pool("A")))
    assert ontology.sha256
    with pytest.raises(TypeError):
        ontology.pools["A"] = ("hidden",)


def test_external_episodes_are_built_without_labels():
    ontology = load()
    episodes = build_truth_free_episodes(
        dataset="toy", tier="A", fold=2,
        compounds=({"compound": "x", "unit": "group-x"}, "y"), ontology=ontology)
    assert len(episodes) == 2 * (9 * 8 // 2)
    assert all(not hasattr(episode, "truth") for episode in episodes)
    assert all({episode.h1, episode.h2} <= set(ontology.pool("A")) for episode in episodes)


def test_external_metadata_cannot_smuggle_hidden_labels():
    with pytest.raises(ValueError, match="evaluator-only"):
        build_truth_free_episodes(dataset="toy", tier="A", fold=0,
                                  compounds=({"compound": "x", "klass": "secret"},))


def test_episode_manifest_has_no_truth_field():
    ontology = load()
    manifest = build_episode_manifest(
        dataset="toy", tier="A", fold=0, compounds=("x",), ontology=ontology,
        setting={"menu": ["assay"], "budget_days": 1.0, "max_measurements": 1,
                 "qc_rule": "continue", "fixed_order": ["assay"]},
    )
    assert "truth" not in manifest
    assert all("truth" not in episode for episode in manifest["episodes"])

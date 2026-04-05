"""Shared fixtures: a minimal Pakunoda results directory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def results_dir(tmp_path: Path) -> Path:
    """Create a minimal Pakunoda-style results directory."""
    root = tmp_path / "results" / "demo"
    root.mkdir(parents=True)

    # config.yaml (in parent, as Pakunoda places it)
    config = {
        "project": {"id": "demo", "description": "test project"},
        "blocks": [
            {
                "id": "expression",
                "file": "data/expression.tsv",
                "format": "tsv",
                "modes": ["genes", "samples"],
            },
            {
                "id": "methylation",
                "file": "data/methylation.tsv",
                "format": "tsv",
                "modes": ["cpg_sites", "samples"],
            },
        ],
        "relations": [
            {
                "type": "exact",
                "between": [
                    ["expression", "samples"],
                    ["methylation", "samples"],
                ],
            }
        ],
        "solver": {"family": "CoupledMWCA"},
        "search": {"enabled": True},
    }
    (root.parent / "config.yaml").write_text(yaml.dump(config))

    # graph/relation_graph.json
    (root / "graph").mkdir()
    graph = {
        "nodes": [
            {"id": "expression:genes", "block": "expression", "mode": "genes", "dimension": 100},
            {"id": "expression:samples", "block": "expression", "mode": "samples", "dimension": 20},
            {"id": "methylation:cpg_sites", "block": "methylation", "mode": "cpg_sites", "dimension": 500},
            {"id": "methylation:samples", "block": "methylation", "mode": "samples", "dimension": 20},
        ],
        "edges": [
            {"source": "expression:samples", "target": "methylation:samples", "type": "exact"}
        ],
        "adjacency": {
            "expression:samples": ["methylation:samples"],
            "methylation:samples": ["expression:samples"],
        },
    }
    (root / "graph" / "relation_graph.json").write_text(json.dumps(graph))

    # validate/report.json
    (root / "validate").mkdir()
    (root / "validate" / "report.json").write_text(
        json.dumps({"valid": True, "errors": [], "blocks_checked": ["expression", "methylation"], "relations_checked": 1})
    )

    # candidates/candidates.json
    (root / "candidates").mkdir()
    candidates = {
        "project_id": "demo",
        "num_candidates": 1,
        "constraints": {},
        "candidates": [
            {
                "id": "c0_expression_methylation",
                "blocks": ["expression", "methylation"],
                "mode_assignments": [
                    {"block": "expression", "mode": "genes", "status": "decompose", "sharing": "specific"},
                    {"block": "expression", "mode": "samples", "status": "decompose", "sharing": "common"},
                    {"block": "methylation", "mode": "cpg_sites", "status": "decompose", "sharing": "specific"},
                    {"block": "methylation", "mode": "samples", "status": "decompose", "sharing": "common"},
                ],
                "couplings": [
                    {
                        "group_id": 0,
                        "type": "exact",
                        "members": [
                            {"block": "expression", "mode": "samples"},
                            {"block": "methylation", "mode": "samples"},
                        ],
                    }
                ],
                "rank": None,
                "solver_family": "CoupledMWCA",
            }
        ],
    }
    (root / "candidates" / "candidates.json").write_text(json.dumps(candidates))

    # summary.json
    summary = {
        "total_candidates": 1,
        "succeeded": 1,
        "failed": 0,
        "ranking": [
            {
                "rank_position": 1,
                "candidate_id": "c0_expression_methylation",
                "reconstruction_error": 0.042,
                "runtime_seconds": 3.5,
                "total_params": 2400,
                "num_blocks": 2,
            }
        ],
        "failed_candidates": [],
    }
    (root / "summary.json").write_text(json.dumps(summary))

    # search/
    search_dir = root / "search"
    search_dir.mkdir()

    recommendation = {
        "best_by_error": {
            "candidate_id": "c0_expression_methylation",
            "trial": {"trial_number": 3, "value": 0.035, "rank": 5, "init_policy": "svd"},
        },
        "best_by_balanced": {
            "candidate_id": "c0_expression_methylation",
            "trial": {"trial_number": 2, "value": 0.040, "rank": 3, "init_policy": "svd"},
        },
        "top_n": [
            {
                "position": 1,
                "candidate_id": "c0_expression_methylation",
                "imputation_rmse": 0.035,
                "rank": 5,
                "init_policy": "svd",
                "total_params": 3000,
                "runtime_seconds": 4.1,
                "num_trials": 5,
            }
        ],
        "explanation": "Best model uses rank 5 with SVD initialization.",
        "total_candidates_searched": 1,
        "total_trials": 5,
    }
    (search_dir / "recommendation.yaml").write_text(yaml.dump(recommendation))

    best = {
        "project_id": "demo",
        "overall_best": {
            "candidate_id": "c0_expression_methylation",
            "best_trial": {"trial_number": 3, "value": 0.035, "rank": 5, "init_policy": "svd"},
            "num_trials": 5,
        },
        "by_candidate": [
            {
                "candidate_id": "c0_expression_methylation",
                "best_trial": {"trial_number": 3, "value": 0.035, "rank": 5, "init_policy": "svd"},
                "num_trials": 5,
            }
        ],
    }
    (search_dir / "best.json").write_text(json.dumps(best))

    trials_tsv = "candidate_id\ttrial_number\tstate\timputation_rmse\trank\tinit_policy\truntime_seconds\ttotal_params\tsuccess\n"
    trials_tsv += "c0_expression_methylation\t3\tCOMPLETE\t0.035\t5\tsvd\t4.1\t3000\tTrue\n"
    (search_dir / "trials.tsv").write_text(trials_tsv)

    return root

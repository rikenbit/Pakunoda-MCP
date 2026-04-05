"""Tests for pakunoda_mcp.reader."""

from __future__ import annotations

from pathlib import Path

import pytest

from pakunoda_mcp.reader import ProjectReader


def test_config(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    cfg = reader.config()
    assert cfg["project"]["id"] == "demo"
    assert len(cfg["blocks"]) == 2


def test_relation_graph(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    graph = reader.relation_graph()
    assert len(graph["nodes"]) == 4
    assert len(graph["edges"]) == 1
    assert graph["edges"][0]["type"] == "exact"


def test_candidates(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    data = reader.candidates()
    assert data["num_candidates"] == 1
    c = data["candidates"][0]
    assert c["id"] == "c0_expression_methylation"
    assert c["blocks"] == ["expression", "methylation"]


def test_validation_report(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    report = reader.validation_report()
    assert report["valid"] is True


def test_summary(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    s = reader.summary()
    assert s["succeeded"] == 1
    assert s["ranking"][0]["reconstruction_error"] == pytest.approx(0.042)


def test_search_recommendation(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    rec = reader.search_recommendation()
    assert rec["best_by_error"]["candidate_id"] == "c0_expression_methylation"
    assert rec["explanation"]


def test_search_best(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    best = reader.search_best()
    assert best["overall_best"]["best_trial"]["value"] == pytest.approx(0.035)


def test_search_trials(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    trials = reader.search_trials()
    assert len(trials) == 1
    assert trials[0]["candidate_id"] == "c0_expression_methylation"
    assert trials[0]["rank"] == "5"  # TSV reads as strings


def test_project_id(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    assert reader.project_id() == "demo"


def test_project_id_missing(tmp_path: Path) -> None:
    root = tmp_path / "no_config"
    root.mkdir()
    reader = ProjectReader(root)
    assert reader.project_id() is None


def test_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ProjectReader(tmp_path / "nonexistent")


def test_missing_file(results_dir: Path) -> None:
    reader = ProjectReader(results_dir)
    with pytest.raises(FileNotFoundError):
        reader.candidate_problem("no_such_candidate")

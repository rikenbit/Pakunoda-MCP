"""Tests for the adapter layer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from pakunoda_mcp.adapters import CandidatesAdapter, ProjectAdapter, SearchAdapter
from pakunoda_mcp.reader import ProjectReader


# ── ProjectAdapter ──


def test_project_config(results_dir: Path) -> None:
    adapter = ProjectAdapter(ProjectReader(results_dir))
    cfg = adapter.config()
    assert cfg["project"]["id"] == "demo"
    assert len(cfg["blocks"]) == 2


def test_project_graph(results_dir: Path) -> None:
    adapter = ProjectAdapter(ProjectReader(results_dir))
    graph = adapter.relation_graph()
    assert len(graph["nodes"]) == 4
    assert graph["edges"][0]["type"] == "exact"


def test_project_file_status_all_present(results_dir: Path) -> None:
    adapter = ProjectAdapter(ProjectReader(results_dir))
    status = adapter.file_status()
    assert status["config"] == "ok"
    assert status["relation_graph"] == "ok"
    assert status["candidates"] == "ok"
    assert status["search/recommendation"] == "ok"
    assert status["search/best"] == "ok"
    assert status["search/trials"] == "ok"


def test_project_file_status_partial(tmp_path: Path) -> None:
    """Only config exists — everything else should be 'missing'."""
    root = tmp_path / "sparse"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: sparse}")
    adapter = ProjectAdapter(ProjectReader(root))
    status = adapter.file_status()
    assert status["config"] == "ok"
    assert status["relation_graph"] == "missing"
    assert status["candidates"] == "missing"
    assert status["search/recommendation"] == "missing"


def test_project_file_status_malformed_json(results_dir: Path) -> None:
    """Malformed JSON should report 'error: ...'."""
    (results_dir / "graph" / "relation_graph.json").write_text("{bad json")
    adapter = ProjectAdapter(ProjectReader(results_dir))
    status = adapter.file_status()
    assert status["relation_graph"].startswith("error:")


# ── CandidatesAdapter ──


def test_candidates_list_all(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    data = adapter.list_all()
    assert data["num_candidates"] == 1
    c = data["candidates"][0]
    assert "mode_assignments" in c  # full detail preserved


def test_candidates_summarize(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    summary = adapter.summarize()
    assert summary["project_id"] == "demo"
    assert summary["num_candidates"] == 1
    c = summary["candidates"][0]
    assert c["id"] == "c0_expression_methylation"
    assert c["blocks"] == ["expression", "methylation"]
    assert c["num_couplings"] == 1
    assert c["solver_family"] == "CoupledMWCA"
    # summarize should NOT include full mode_assignments
    assert "mode_assignments" not in c


def test_candidates_get_details(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    detail = adapter.get_details("c0_expression_methylation")
    assert detail["id"] == "c0_expression_methylation"
    assert "mode_assignments" in detail
    assert detail["blocks"] == ["expression", "methylation"]


def test_candidates_get_details_missing(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    with pytest.raises(KeyError, match="no_such"):
        adapter.get_details("no_such")


def test_candidates_get_result(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    result = adapter.get_result("c0_expression_methylation")
    assert result["candidate_id"] == "c0_expression_methylation"
    assert result["status"] == "success"


def test_candidates_get_result_bad_id(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    with pytest.raises(KeyError, match="no_such"):
        adapter.get_result("no_such")


def test_candidates_get_result_no_file(results_dir: Path) -> None:
    """Valid candidate_id but result file does not exist."""
    # Remove the result file
    (results_dir / "runs" / "c0_expression_methylation" / "result.json").unlink()
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    with pytest.raises(FileNotFoundError):
        adapter.get_result("c0_expression_methylation")


def test_candidates_get_score(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    score = adapter.get_score("c0_expression_methylation")
    assert score["imputation_rmse"] == pytest.approx(0.035)


def test_candidates_get_score_bad_id(results_dir: Path) -> None:
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    with pytest.raises(KeyError, match="no_such"):
        adapter.get_score("no_such")


def test_candidates_get_score_no_file(results_dir: Path) -> None:
    (results_dir / "scores" / "c0_expression_methylation.score.json").unlink()
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    with pytest.raises(FileNotFoundError):
        adapter.get_score("c0_expression_methylation")


def test_candidates_missing(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: empty}")
    adapter = CandidatesAdapter(ProjectReader(root))
    with pytest.raises(FileNotFoundError):
        adapter.list_all()


def test_candidates_malformed(results_dir: Path) -> None:
    (results_dir / "candidates" / "candidates.json").write_text("not json")
    adapter = CandidatesAdapter(ProjectReader(results_dir))
    with pytest.raises(json.JSONDecodeError):
        adapter.list_all()


# ── SearchAdapter ──


def test_search_trials(results_dir: Path) -> None:
    adapter = SearchAdapter(ProjectReader(results_dir))
    trials = adapter.trials()
    assert len(trials) == 1
    assert trials[0]["candidate_id"] == "c0_expression_methylation"


def test_search_trials_missing(tmp_path: Path) -> None:
    root = tmp_path / "no_trials"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: x}")
    adapter = SearchAdapter(ProjectReader(root))
    with pytest.raises(FileNotFoundError):
        adapter.trials()


def test_search_combined_summary(results_dir: Path) -> None:
    adapter = SearchAdapter(ProjectReader(results_dir))
    combined = adapter.combined_summary()
    assert combined["recommendation"] is not None
    assert combined["recommendation"]["explanation"]
    assert combined["best"] is not None
    assert combined["best"]["overall_best"]["candidate_id"] == "c0_expression_methylation"


def test_search_combined_summary_missing(tmp_path: Path) -> None:
    root = tmp_path / "no_search"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: x}")
    adapter = SearchAdapter(ProjectReader(root))
    combined = adapter.combined_summary()
    assert combined["recommendation"] is None
    assert combined["best"] is None


def test_search_best_per_candidate(results_dir: Path) -> None:
    adapter = SearchAdapter(ProjectReader(results_dir))
    result = adapter.best_per_candidate()
    assert result["overall_best"]["candidate_id"] == "c0_expression_methylation"
    by_cand = result["by_candidate"]
    assert len(by_cand) == 1
    assert by_cand[0]["best_rmse"] == pytest.approx(0.035)
    assert by_cand[0]["best_rank"] == 5
    assert by_cand[0]["best_init_policy"] == "svd"
    assert by_cand[0]["num_trials"] == 5


def test_search_best_per_candidate_missing(tmp_path: Path) -> None:
    root = tmp_path / "no_search2"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: x}")
    adapter = SearchAdapter(ProjectReader(root))
    with pytest.raises(FileNotFoundError):
        adapter.best_per_candidate()


def test_search_recommendation(results_dir: Path) -> None:
    adapter = SearchAdapter(ProjectReader(results_dir))
    rec = adapter.recommendation()
    assert rec["best_by_error"]["candidate_id"] == "c0_expression_methylation"
    assert rec["total_trials"] == 5


def test_search_recommendation_missing(tmp_path: Path) -> None:
    root = tmp_path / "no_search3"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: x}")
    adapter = SearchAdapter(ProjectReader(root))
    with pytest.raises(FileNotFoundError):
        adapter.recommendation()


def test_search_recommendation_malformed(results_dir: Path) -> None:
    (results_dir / "search" / "recommendation.yaml").write_text(": : bad yaml\n\t:")
    adapter = SearchAdapter(ProjectReader(results_dir))
    with pytest.raises(Exception):
        adapter.recommendation()


# ── SearchAdapter.run_search ──


def _mock_snakemake_success(*args, **kwargs):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")


def _mock_snakemake_failure(*args, **kwargs):
    return subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="rule failed"
    )


def test_run_search_success(
    results_dir: Path, pakunoda_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(pakunoda_repo))
    config_path = results_dir.parent / "config.yaml"
    adapter = SearchAdapter(ProjectReader(results_dir))
    with patch("pakunoda_mcp.runner.subprocess.run", _mock_snakemake_success):
        result = adapter.run_search(config_path=config_path)
    assert result["accepted"] is True
    assert "search_outputs" in result
    assert result["search_outputs"]["recommendation"] == "ok"


def test_run_search_failure(
    results_dir: Path, pakunoda_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(pakunoda_repo))
    config_path = results_dir.parent / "config.yaml"
    adapter = SearchAdapter(ProjectReader(results_dir))
    with patch("pakunoda_mcp.runner.subprocess.run", _mock_snakemake_failure):
        result = adapter.run_search(config_path=config_path)
    assert result["accepted"] is False
    assert "detail" in result
    assert result["detail"]["returncode"] == 1


def test_run_search_unsupported_goal(results_dir: Path) -> None:
    # goal validation happens before runner is called — no repo needed
    config_path = results_dir.parent / "config.yaml"
    adapter = SearchAdapter(ProjectReader(results_dir))
    result = adapter.run_search(config_path=config_path, goal="clustering")
    assert result["accepted"] is False
    assert "Unsupported goal" in result["message"]


def test_run_search_invalid_max_trials(results_dir: Path) -> None:
    # max_trials validation happens before runner is called — no repo needed
    config_path = results_dir.parent / "config.yaml"
    adapter = SearchAdapter(ProjectReader(results_dir))
    result = adapter.run_search(config_path=config_path, max_trials=0)
    assert result["accepted"] is False
    assert "max_trials" in result["message"]


def test_run_search_max_trials_forwarded(
    results_dir: Path, pakunoda_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(pakunoda_repo))
    config_path = results_dir.parent / "config.yaml"
    adapter = SearchAdapter(ProjectReader(results_dir))
    with patch("pakunoda_mcp.runner.subprocess.run") as mock:
        mock.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        adapter.run_search(config_path=config_path, max_trials=50)
    cmd = mock.call_args[0][0]
    # Should contain --config with max_trials override
    assert "--config" in cmd
    config_idx = cmd.index("--config")
    assert "max_trials: 50" in cmd[config_idx + 1]


def test_run_search_uses_absolute_snakefile(
    results_dir: Path, pakunoda_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify the runner uses an absolute Snakefile path and cwd=repo_dir."""
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(pakunoda_repo))
    config_path = results_dir.parent / "config.yaml"
    adapter = SearchAdapter(ProjectReader(results_dir))
    with patch("pakunoda_mcp.runner.subprocess.run") as mock:
        mock.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        adapter.run_search(config_path=config_path)
    cmd = mock.call_args[0][0]
    snakefile_arg = cmd[cmd.index("--snakefile") + 1]
    assert snakefile_arg == str(pakunoda_repo / "Snakefile")
    assert mock.call_args[1]["cwd"] == str(pakunoda_repo)


# ── ProjectAdapter.refresh ──


def test_refresh_all_present(results_dir: Path) -> None:
    adapter = ProjectAdapter(ProjectReader(results_dir))
    snapshot = adapter.refresh()
    assert snapshot["config"]["project"]["id"] == "demo"
    assert snapshot["relation_graph"] is not None
    assert snapshot["candidates"] is not None
    assert snapshot["summary"] is not None
    assert snapshot["search_recommendation"] is not None


def test_refresh_partial(tmp_path: Path) -> None:
    root = tmp_path / "partial"
    root.mkdir()
    (root / "config.yaml").write_text("project: {id: partial}")
    adapter = ProjectAdapter(ProjectReader(root))
    snapshot = adapter.refresh()
    assert snapshot["config"]["project"]["id"] == "partial"
    assert snapshot["relation_graph"] is None
    assert snapshot["candidates"] is None
    assert snapshot["search_recommendation"] is None

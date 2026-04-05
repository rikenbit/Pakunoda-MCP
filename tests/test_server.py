"""Tests for pakunoda_mcp.server tools and resources."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from pakunoda_mcp import server


@pytest.fixture(autouse=True)
def _set_results_dir(results_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAKUNODA_RESULTS_DIR", str(results_dir))


# ── Resources ──

def test_resource_config() -> None:
    raw = server.resource_config()
    data = json.loads(raw)
    assert data["project"]["id"] == "demo"


def test_resource_graph() -> None:
    raw = server.resource_graph()
    data = json.loads(raw)
    assert "nodes" in data
    assert "edges" in data


def test_resource_candidates() -> None:
    raw = server.resource_candidates()
    data = json.loads(raw)
    assert data["num_candidates"] == 1


def test_resource_summary() -> None:
    raw = server.resource_summary()
    data = json.loads(raw)
    assert data["succeeded"] == 1
    assert data["ranking"][0]["candidate_id"] == "c0_expression_methylation"


def test_resource_search_trials() -> None:
    raw = server.resource_search_trials()
    data = json.loads(raw)
    assert len(data) == 1
    assert data[0]["candidate_id"] == "c0_expression_methylation"


def test_resource_search_trials_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bare = tmp_path / "bare_trials"
    bare.mkdir()
    (bare.parent / "config.yaml").write_text("project: {id: bare}")
    monkeypatch.setenv("PAKUNODA_RESULTS_DIR", str(bare))
    raw = server.resource_search_trials()
    data = json.loads(raw)
    assert data == []


def test_resource_search_summary() -> None:
    raw = server.resource_search_summary()
    data = json.loads(raw)
    assert data["recommendation"] is not None
    assert data["best"] is not None


def test_resource_search_summary_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A results dir with no search outputs
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare.parent / "config.yaml").write_text("project: {id: bare}")
    monkeypatch.setenv("PAKUNODA_RESULTS_DIR", str(bare))
    raw = server.resource_search_summary()
    data = json.loads(raw)
    assert data["recommendation"] is None
    assert data["best"] is None


# ── Tools ──

def test_tool_validate_project() -> None:
    raw = server.tool_validate_project()
    data = json.loads(raw)
    assert data["files"]["config"] == "ok"
    assert data["files"]["candidates"] == "ok"
    assert data["files"]["relation_graph"] == "ok"


def test_tool_enumerate_candidates() -> None:
    raw = server.tool_enumerate_candidates()
    data = json.loads(raw)
    assert data["num_candidates"] == 1
    assert data["candidates"][0]["id"] == "c0_expression_methylation"


def test_tool_summarize_search() -> None:
    raw = server.tool_summarize_search()
    data = json.loads(raw)
    assert data["overall_best"]["candidate_id"] == "c0_expression_methylation"
    assert len(data["by_candidate"]) == 1


def test_tool_recommend_model() -> None:
    raw = server.tool_recommend_model()
    data = json.loads(raw)
    assert "best_by_error" in data
    assert "explanation" in data


def test_tool_recommend_model_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare.parent / "config.yaml").write_text("project: {id: bare}")
    monkeypatch.setenv("PAKUNODA_RESULTS_DIR", str(bare))
    raw = server.tool_recommend_model()
    data = json.loads(raw)
    assert "error" in data


def test_resource_candidate_problem() -> None:
    raw = server.resource_candidate_problem("c0_expression_methylation")
    data = json.loads(raw)
    assert data["candidate_id"] == "c0_expression_methylation"
    assert data["blocks"] == ["expression", "methylation"]


def test_resource_candidate_problem_bad_id() -> None:
    raw = server.resource_candidate_problem("no_such")
    data = json.loads(raw)
    assert "error" in data


def test_tool_get_candidate_problem() -> None:
    raw = server.tool_get_candidate_problem("c0_expression_methylation")
    data = json.loads(raw)
    assert data["candidate_id"] == "c0_expression_methylation"


def test_tool_get_candidate_problem_bad_id() -> None:
    raw = server.tool_get_candidate_problem("no_such")
    data = json.loads(raw)
    assert "error" in data


def test_tool_get_candidate_problem_no_file(
    results_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (results_dir / "candidates" / "c0_expression_methylation.problem.json").unlink()
    raw = server.tool_get_candidate_problem("c0_expression_methylation")
    data = json.loads(raw)
    assert "error" in data
    assert "Problem file not found" in data["error"]


def test_tool_get_candidate_details() -> None:
    raw = server.tool_get_candidate_details("c0_expression_methylation")
    data = json.loads(raw)
    assert data["id"] == "c0_expression_methylation"
    assert "mode_assignments" in data


def test_tool_get_candidate_details_missing() -> None:
    raw = server.tool_get_candidate_details("no_such")
    data = json.loads(raw)
    assert "error" in data


def test_tool_get_candidate_result() -> None:
    raw = server.tool_get_candidate_result("c0_expression_methylation")
    data = json.loads(raw)
    assert data["candidate_id"] == "c0_expression_methylation"
    assert data["status"] == "success"


def test_tool_get_candidate_result_missing() -> None:
    raw = server.tool_get_candidate_result("no_such")
    data = json.loads(raw)
    assert "error" in data


def test_tool_get_candidate_score() -> None:
    raw = server.tool_get_candidate_score("c0_expression_methylation")
    data = json.loads(raw)
    assert data["imputation_rmse"] == pytest.approx(0.035)


def test_tool_get_candidate_score_missing() -> None:
    raw = server.tool_get_candidate_score("no_such")
    data = json.loads(raw)
    assert "error" in data


def test_env_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PAKUNODA_RESULTS_DIR", raising=False)
    with pytest.raises(RuntimeError, match="PAKUNODA_RESULTS_DIR"):
        server.tool_validate_project()


# ── Write tools ──


def test_tool_run_search_success(
    results_dir: Path, pakunoda_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(pakunoda_repo))
    config_path = str(results_dir.parent / "config.yaml")
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake):
        raw = server.tool_run_search(project_path=config_path)
    data = json.loads(raw)
    assert data["accepted"] is True
    assert data["search_outputs"]["recommendation"] == "ok"


def test_tool_run_search_failure(
    results_dir: Path, pakunoda_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(pakunoda_repo))
    config_path = str(results_dir.parent / "config.yaml")
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="failed"
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake):
        raw = server.tool_run_search(project_path=config_path)
    data = json.loads(raw)
    assert data["accepted"] is False
    assert data["detail"]["returncode"] == 1


def test_tool_run_search_bad_goal(results_dir: Path) -> None:
    # goal validation before runner — no repo needed
    raw = server.tool_run_search(project_path="/any", goal="clustering")
    data = json.loads(raw)
    assert data["accepted"] is False
    assert "Unsupported goal" in data["message"]


def test_tool_refresh_project_state(results_dir: Path) -> None:
    raw = server.tool_refresh_project_state()
    data = json.loads(raw)
    assert data["config"]["project"]["id"] == "demo"
    assert data["relation_graph"] is not None
    assert data["candidates"] is not None
    assert data["search_recommendation"] is not None

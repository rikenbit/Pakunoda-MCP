"""Tests for pakunoda_mcp.runner."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from pakunoda_mcp.runner import ALLOWED_TARGETS, RunResult, run_snakemake


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text("project: {id: test}")
    return p


@pytest.fixture()
def repo_dir(tmp_path: Path) -> Path:
    """Fake Pakunoda repo with a Snakefile."""
    d = tmp_path / "pakunoda_repo"
    d.mkdir()
    (d / "Snakefile").write_text("# fake")
    return d


def test_disallowed_target(config_file: Path, repo_dir: Path) -> None:
    with pytest.raises(ValueError, match="not allowed"):
        run_snakemake(
            config_path=config_file, target="dangerous_thing", repo_dir=repo_dir
        )


def test_missing_config(tmp_path: Path, repo_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Config not found"):
        run_snakemake(
            config_path=tmp_path / "nope.yaml", target="search", repo_dir=repo_dir
        )


def test_missing_repo_dir(config_file: Path, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="repo directory not found"):
        run_snakemake(
            config_path=config_file,
            target="search",
            repo_dir=tmp_path / "nonexistent",
        )


def test_missing_snakefile(config_file: Path, tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="Snakefile not found"):
        run_snakemake(
            config_path=config_file, target="search", repo_dir=empty_dir
        )


def test_env_not_set(config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PAKUNODA_REPO_DIR", raising=False)
    with pytest.raises(RuntimeError, match="PAKUNODA_REPO_DIR"):
        run_snakemake(config_path=config_file, target="search")


def test_env_fallback(
    config_file: Path, repo_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PAKUNODA_REPO_DIR", str(repo_dir))
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="ok", stderr=""
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        result = run_snakemake(config_path=config_file, target="search")

    assert result.success is True
    # Should use the Snakefile from the env-provided repo dir
    cmd = mock.call_args[0][0]
    assert str(repo_dir / "Snakefile") in cmd


def test_success(config_file: Path, repo_dir: Path) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done\n", stderr=""
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        result = run_snakemake(
            config_path=config_file, target="search", repo_dir=repo_dir
        )

    assert result.success is True
    assert result.target == "search"
    assert result.returncode == 0
    assert result.stdout == "done\n"

    cmd = mock.call_args[0][0]
    assert "--until" in cmd
    assert cmd[cmd.index("--until") + 1] == ALLOWED_TARGETS["search"]
    assert "--configfile" in cmd
    # Snakefile must be an absolute path inside repo_dir
    snakefile_arg = cmd[cmd.index("--snakefile") + 1]
    assert snakefile_arg == str(repo_dir / "Snakefile")


def test_cwd_is_repo_dir(config_file: Path, repo_dir: Path) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        run_snakemake(
            config_path=config_file, target="search", repo_dir=repo_dir
        )

    kwargs = mock.call_args[1]
    assert kwargs["cwd"] == str(repo_dir)


def test_failure(config_file: Path, repo_dir: Path) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="Error: rule failed\n"
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake):
        result = run_snakemake(
            config_path=config_file, target="search", repo_dir=repo_dir
        )

    assert result.success is False
    assert result.returncode == 1
    assert "Error" in result.stderr


def test_extra_args_forwarded(config_file: Path, repo_dir: Path) -> None:
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        run_snakemake(
            config_path=config_file,
            target="search",
            extra_args=["--config", "search={max_trials: 10}"],
            repo_dir=repo_dir,
        )

    cmd = mock.call_args[0][0]
    assert "--config" in cmd
    assert "search={max_trials: 10}" in cmd


def test_cores_passed(config_file: Path, repo_dir: Path) -> None:
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        run_snakemake(
            config_path=config_file, target="search", cores=4, repo_dir=repo_dir
        )

    cmd = mock.call_args[0][0]
    idx = cmd.index("--cores")
    assert cmd[idx + 1] == "4"

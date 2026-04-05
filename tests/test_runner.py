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


def test_disallowed_target(config_file: Path) -> None:
    with pytest.raises(ValueError, match="not allowed"):
        run_snakemake(config_path=config_file, target="dangerous_thing")


def test_missing_config(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Config not found"):
        run_snakemake(config_path=tmp_path / "nope.yaml", target="search")


def test_success(config_file: Path) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="done\n", stderr=""
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        result = run_snakemake(config_path=config_file, target="search")

    assert result.success is True
    assert result.target == "search"
    assert result.returncode == 0
    assert result.stdout == "done\n"

    cmd = mock.call_args[0][0]
    assert "--until" in cmd
    assert cmd[cmd.index("--until") + 1] == ALLOWED_TARGETS["search"]
    assert "--configfile" in cmd


def test_failure(config_file: Path) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="Error: rule failed\n"
    )
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake):
        result = run_snakemake(config_path=config_file, target="search")

    assert result.success is False
    assert result.returncode == 1
    assert "Error" in result.stderr


def test_extra_args_forwarded(config_file: Path) -> None:
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        run_snakemake(
            config_path=config_file,
            target="search",
            extra_args=["--config", "search={max_trials: 10}"],
        )

    cmd = mock.call_args[0][0]
    assert "--config" in cmd
    assert "search={max_trials: 10}" in cmd


def test_cores_passed(config_file: Path) -> None:
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("pakunoda_mcp.runner.subprocess.run", return_value=fake) as mock:
        run_snakemake(config_path=config_file, target="search", cores=4)

    cmd = mock.call_args[0][0]
    idx = cmd.index("--cores")
    assert cmd[idx + 1] == "4"

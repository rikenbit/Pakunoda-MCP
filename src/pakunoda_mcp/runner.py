"""Subprocess runner for Pakunoda's Snakemake pipeline.

This module is the ONLY place that invokes external processes.
It wraps ``snakemake`` CLI calls with a fixed allow-list of targets,
preventing arbitrary shell execution.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

# Snakemake targets that Pakunoda-MCP is allowed to request.
# Keys are logical names used by adapters; values are the Snakemake
# rule-output patterns that can be passed via ``--until``.
ALLOWED_TARGETS: dict[str, str] = {
    "search": "recommend",
}


@dataclass
class RunResult:
    """Outcome of a Snakemake invocation."""

    success: bool
    target: str
    returncode: int
    stdout: str
    stderr: str
    command: list[str] = field(repr=False)


def run_snakemake(
    *,
    config_path: str | Path,
    target: str,
    cores: int = 1,
    snakemake_bin: str = "snakemake",
    extra_args: Sequence[str] = (),
) -> RunResult:
    """Invoke Snakemake for a known target.

    Parameters
    ----------
    config_path:
        Absolute path to the project's ``config.yaml``.
    target:
        Logical target name (must be a key in ``ALLOWED_TARGETS``).
    cores:
        Number of cores to pass to Snakemake.
    snakemake_bin:
        Path or name of the ``snakemake`` executable.
    extra_args:
        Additional CLI flags forwarded verbatim.

    Returns
    -------
    RunResult with captured stdout/stderr and return code.

    Raises
    ------
    ValueError
        If *target* is not in the allow-list.
    FileNotFoundError
        If *config_path* does not exist.
    """
    if target not in ALLOWED_TARGETS:
        raise ValueError(
            f"Target {target!r} is not allowed. "
            f"Allowed targets: {sorted(ALLOWED_TARGETS)}"
        )

    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    snakemake_rule = ALLOWED_TARGETS[target]
    cmd: list[str] = [
        snakemake_bin,
        "--snakefile", "Snakefile",
        "--configfile", str(config_path),
        "--cores", str(cores),
        "--until", snakemake_rule,
        *extra_args,
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=3600,
    )

    return RunResult(
        success=proc.returncode == 0,
        target=target,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        command=cmd,
    )

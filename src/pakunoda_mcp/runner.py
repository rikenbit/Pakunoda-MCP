"""Subprocess runner for Pakunoda's Snakemake pipeline.

This module is the ONLY place that invokes external processes.
It wraps ``snakemake`` CLI calls with a fixed allow-list of targets,
preventing arbitrary shell execution.

Execution context is pinned via ``PAKUNODA_REPO_DIR`` (the Pakunoda
checkout that contains the Snakefile).  This eliminates cwd-dependence.
"""

from __future__ import annotations

import os
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


def _resolve_repo_dir(repo_dir: str | Path | None = None) -> Path:
    """Return the validated Pakunoda repo directory.

    Resolution order:
      1. Explicit *repo_dir* argument
      2. ``PAKUNODA_REPO_DIR`` environment variable

    Raises
    ------
    RuntimeError
        If neither source provides a value.
    FileNotFoundError
        If the directory or its ``Snakefile`` does not exist.
    """
    if repo_dir is not None:
        resolved = Path(repo_dir).resolve()
    else:
        env = os.environ.get("PAKUNODA_REPO_DIR", "")
        if not env:
            raise RuntimeError(
                "Set PAKUNODA_REPO_DIR to the Pakunoda repository root "
                "(the directory containing Snakefile)."
            )
        resolved = Path(env).resolve()

    if not resolved.is_dir():
        raise FileNotFoundError(f"Pakunoda repo directory not found: {resolved}")

    snakefile = resolved / "Snakefile"
    if not snakefile.exists():
        raise FileNotFoundError(
            f"Snakefile not found in repo directory: {snakefile}"
        )

    return resolved


def run_snakemake(
    *,
    config_path: str | Path,
    target: str,
    cores: int = 1,
    snakemake_bin: str = "snakemake",
    extra_args: Sequence[str] = (),
    repo_dir: str | Path | None = None,
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
    repo_dir:
        Pakunoda repository root.  Falls back to ``PAKUNODA_REPO_DIR``.

    Returns
    -------
    RunResult with captured stdout/stderr and return code.

    Raises
    ------
    ValueError
        If *target* is not in the allow-list.
    FileNotFoundError
        If *config_path* or *repo_dir* / Snakefile does not exist.
    RuntimeError
        If *repo_dir* is ``None`` and ``PAKUNODA_REPO_DIR`` is unset.
    """
    if target not in ALLOWED_TARGETS:
        raise ValueError(
            f"Target {target!r} is not allowed. "
            f"Allowed targets: {sorted(ALLOWED_TARGETS)}"
        )

    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    resolved_repo = _resolve_repo_dir(repo_dir)
    snakefile = resolved_repo / "Snakefile"

    snakemake_rule = ALLOWED_TARGETS[target]
    cmd: list[str] = [
        snakemake_bin,
        "--snakefile", str(snakefile),
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
        cwd=str(resolved_repo),
    )

    return RunResult(
        success=proc.returncode == 0,
        target=target,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        command=cmd,
    )

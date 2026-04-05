"""Read Pakunoda results directory (read-only).

This module reads output files produced by Pakunoda's Snakemake workflow.
It depends only on the stable output contract documented in
Pakunoda/docs/handoff_to_pakunoda_mcp.md §8.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


class ProjectReader:
    """Read-only access to a single Pakunoda project's results."""

    def __init__(self, results_dir: str | Path) -> None:
        self.root = Path(results_dir)
        if not self.root.is_dir():
            raise FileNotFoundError(f"Results directory not found: {self.root}")

    # --- helpers ---

    def _read_json(self, rel: str) -> Any:
        path = self.root / rel
        if not path.exists():
            raise FileNotFoundError(f"Not found: {path}")
        return json.loads(path.read_text())

    def _read_yaml(self, rel: str) -> Any:
        path = self.root / rel
        if not path.exists():
            raise FileNotFoundError(f"Not found: {path}")
        return yaml.safe_load(path.read_text())

    def _read_tsv(self, rel: str) -> list[dict[str, str]]:
        path = self.root / rel
        if not path.exists():
            raise FileNotFoundError(f"Not found: {path}")
        with open(path, newline="") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    # --- stable resources ---

    def config(self) -> dict[str, Any]:
        """Read config.yaml from the project root's parent (config_dir)."""
        # config.yaml lives alongside the results dir, not inside it.
        # But the caller may also place it inside results for convenience.
        for candidate in [
            self.root / "config.yaml",
            self.root.parent / "config.yaml",
        ]:
            if candidate.exists():
                return yaml.safe_load(candidate.read_text())
        raise FileNotFoundError(
            f"config.yaml not found in {self.root} or {self.root.parent}"
        )

    def relation_graph(self) -> dict[str, Any]:
        return self._read_json("graph/relation_graph.json")

    def candidates(self) -> dict[str, Any]:
        return self._read_json("candidates/candidates.json")

    def validation_report(self) -> dict[str, Any]:
        return self._read_json("validate/report.json")

    def summary(self) -> dict[str, Any]:
        return self._read_json("summary.json")

    # --- search outputs (may not exist) ---

    def search_recommendation(self) -> dict[str, Any]:
        return self._read_yaml("search/recommendation.yaml")

    def search_best(self) -> dict[str, Any]:
        return self._read_json("search/best.json")

    def search_trials(self) -> list[dict[str, str]]:
        return self._read_tsv("search/trials.tsv")

    # --- per-candidate ---

    def candidate_problem(self, candidate_id: str) -> dict[str, Any]:
        return self._read_json(f"candidates/{candidate_id}.problem.json")

    def candidate_result(self, candidate_id: str) -> dict[str, Any]:
        return self._read_json(f"runs/{candidate_id}/result.json")

    def candidate_score(self, candidate_id: str) -> dict[str, Any]:
        return self._read_json(f"scores/{candidate_id}.score.json")

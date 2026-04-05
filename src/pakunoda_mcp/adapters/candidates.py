"""Candidates adapter: enumerate and summarize decomposition candidates."""

from __future__ import annotations

from typing import Any

from pakunoda_mcp.reader import ProjectReader


class CandidatesAdapter:
    """Read and summarize decomposition candidates."""

    def __init__(self, reader: ProjectReader) -> None:
        self._reader = reader

    def list_all(self) -> dict[str, Any]:
        """Return the full candidates structure."""
        return self._reader.candidates()

    def summarize(self) -> dict[str, Any]:
        """Return a compact summary of all candidates.

        Each candidate is reduced to id, blocks, num_couplings, rank,
        and solver_family — enough for listing without full detail.
        """
        data = self._reader.candidates()
        summaries = [
            {
                "id": c["id"],
                "blocks": c["blocks"],
                "num_couplings": len(c.get("couplings", [])),
                "rank": c.get("rank"),
                "solver_family": c.get("solver_family"),
            }
            for c in data.get("candidates", [])
        ]
        return {
            "project_id": data.get("project_id"),
            "num_candidates": len(summaries),
            "candidates": summaries,
        }

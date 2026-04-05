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

    def _find_candidate(self, candidate_id: str) -> dict[str, Any]:
        """Find a candidate by id in candidates.json.

        Raises KeyError if the candidate_id is not found.
        """
        data = self._reader.candidates()
        for c in data.get("candidates", []):
            if c["id"] == candidate_id:
                return c
        known = [c["id"] for c in data.get("candidates", [])]
        raise KeyError(
            f"Candidate {candidate_id!r} not found. "
            f"Known candidates: {known}"
        )

    def get_details(self, candidate_id: str) -> dict[str, Any]:
        """Return full detail for a single candidate (from candidates.json).

        Raises KeyError if candidate_id is not found.
        """
        return self._find_candidate(candidate_id)

    def get_problem(self, candidate_id: str) -> dict[str, Any]:
        """Return the compiled problem for a candidate.

        Raises KeyError if the candidate_id is not in candidates.json.
        Raises FileNotFoundError if the problem file does not exist.
        """
        self._find_candidate(candidate_id)  # validate id exists
        return self._reader.candidate_problem(candidate_id)

    def get_result(self, candidate_id: str) -> dict[str, Any]:
        """Return the run result for a candidate.

        Raises KeyError if the candidate_id is not in candidates.json.
        Raises FileNotFoundError if the result file does not exist.
        """
        self._find_candidate(candidate_id)  # validate id exists
        return self._reader.candidate_result(candidate_id)

    def get_score(self, candidate_id: str) -> dict[str, Any]:
        """Return the score for a candidate.

        Raises KeyError if the candidate_id is not in candidates.json.
        Raises FileNotFoundError if the score file does not exist.
        """
        self._find_candidate(candidate_id)  # validate id exists
        return self._reader.candidate_score(candidate_id)

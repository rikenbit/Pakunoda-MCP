"""Search adapter: search summaries, best trials, and recommendations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pakunoda_mcp.reader import ProjectReader
from pakunoda_mcp.runner import RunResult, run_snakemake


class SearchAdapter:
    """Read and run hyperparameter search."""

    def __init__(self, reader: ProjectReader) -> None:
        self._reader = reader

    def combined_summary(self) -> dict[str, Any]:
        """Return recommendation + best trials, tolerating missing files.

        Returns {"recommendation": ... | None, "best": ... | None}.
        """
        result: dict[str, Any] = {}
        try:
            result["recommendation"] = self._reader.search_recommendation()
        except FileNotFoundError:
            result["recommendation"] = None
        try:
            result["best"] = self._reader.search_best()
        except FileNotFoundError:
            result["best"] = None
        return result

    def best_per_candidate(self) -> dict[str, Any]:
        """Return a compact summary of best trials per candidate.

        Raises FileNotFoundError if search/best.json is missing.
        """
        best = self._reader.search_best()
        return {
            "overall_best": best.get("overall_best"),
            "by_candidate": [
                {
                    "candidate_id": c["candidate_id"],
                    "best_rmse": c["best_trial"].get("value"),
                    "best_rank": c["best_trial"].get("rank"),
                    "best_init_policy": c["best_trial"].get("init_policy"),
                    "num_trials": c.get("num_trials"),
                }
                for c in best.get("by_candidate", [])
            ],
        }

    def recommendation(self) -> dict[str, Any]:
        """Return the search recommendation.

        Raises FileNotFoundError if search/recommendation.yaml is missing.
        """
        return self._reader.search_recommendation()

    def run_search(
        self,
        *,
        config_path: str | Path,
        max_trials: int | None = None,
        goal: str = "imputation",
        cores: int = 1,
    ) -> dict[str, Any]:
        """Launch the Pakunoda search pipeline via Snakemake.

        Parameters
        ----------
        config_path:
            Path to the project's config.yaml.
        max_trials:
            If given, override ``search.max_trials`` via Snakemake
            ``--config`` flag.
        goal:
            Search objective. Currently only "imputation" is supported.
        cores:
            Number of cores for Snakemake.

        Returns
        -------
        Dict with ``accepted`` (bool), ``message`` (str),
        ``search_outputs`` (dict of file statuses after run), and
        ``detail`` (RunResult fields) on failure.
        """
        if goal != "imputation":
            return {
                "accepted": False,
                "message": f"Unsupported goal {goal!r}. Only 'imputation' is supported.",
            }

        extra_args: list[str] = []
        if max_trials is not None:
            if max_trials < 1:
                return {
                    "accepted": False,
                    "message": "max_trials must be >= 1.",
                }
            extra_args += ["--config", f"search={{max_trials: {max_trials}}}"]

        result: RunResult = run_snakemake(
            config_path=config_path,
            target="search",
            cores=cores,
            extra_args=extra_args,
        )

        if result.success:
            # Re-read outputs after successful run.
            search_status: dict[str, str] = {}
            for name, fn in [
                ("recommendation", self._reader.search_recommendation),
                ("best", self._reader.search_best),
                ("trials", self._reader.search_trials),
            ]:
                try:
                    fn()
                    search_status[name] = "ok"
                except FileNotFoundError:
                    search_status[name] = "missing"
            return {
                "accepted": True,
                "message": "Search pipeline completed successfully.",
                "search_outputs": search_status,
            }
        else:
            return {
                "accepted": False,
                "message": "Search pipeline failed.",
                "detail": {
                    "returncode": result.returncode,
                    "stderr": result.stderr[-2000:] if result.stderr else "",
                },
            }

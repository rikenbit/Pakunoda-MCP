"""Pakunoda-MCP server — MCP interface to Pakunoda results.

Exposes Pakunoda project state (config, graph, candidates, search)
as MCP resources and tools over stdio transport.

The server delegates all data access to the adapter layer, which in turn
uses the reader for file I/O. The server itself has no knowledge of
Pakunoda's file layout.
"""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from pakunoda_mcp.adapters import CandidatesAdapter, ProjectAdapter, SearchAdapter
from pakunoda_mcp.reader import ProjectReader

mcp = FastMCP(
    "Pakunoda-MCP",
    instructions=(
        "This server provides access to Pakunoda factorization project "
        "results. Use resources to browse project state, read-only tools "
        "to get structured summaries, and write tools to run searches "
        "or refresh state."
    ),
)


def _get_reader() -> ProjectReader:
    results_dir = os.environ.get("PAKUNODA_RESULTS_DIR", "")
    if not results_dir:
        raise RuntimeError(
            "Set PAKUNODA_RESULTS_DIR to the Pakunoda results directory "
            "(e.g. results/my_project)"
        )
    return ProjectReader(results_dir)


# ── Resources ────────────────────────────────────────────────────────

@mcp.resource(
    "pakunoda://project/config",
    name="project_config",
    description="Project configuration (config.yaml)",
    mime_type="application/json",
)
def resource_config() -> str:
    adapter = ProjectAdapter(_get_reader())
    return json.dumps(adapter.config(), indent=2)


@mcp.resource(
    "pakunoda://project/graph",
    name="relation_graph",
    description="Block-mode relation graph",
    mime_type="application/json",
)
def resource_graph() -> str:
    adapter = ProjectAdapter(_get_reader())
    return json.dumps(adapter.relation_graph(), indent=2)


@mcp.resource(
    "pakunoda://project/candidates",
    name="candidates",
    description="All enumerated decomposition candidates",
    mime_type="application/json",
)
def resource_candidates() -> str:
    adapter = CandidatesAdapter(_get_reader())
    return json.dumps(adapter.list_all(), indent=2)


@mcp.resource(
    "pakunoda://project/summary",
    name="project_summary",
    description="Project summary with candidate ranking",
    mime_type="application/json",
)
def resource_summary() -> str:
    adapter = ProjectAdapter(_get_reader())
    return json.dumps(adapter.summary(), indent=2)


@mcp.resource(
    "pakunoda://search/summary",
    name="search_summary",
    description="Search recommendation and best trials",
    mime_type="application/json",
)
def resource_search_summary() -> str:
    adapter = SearchAdapter(_get_reader())
    return json.dumps(adapter.combined_summary(), indent=2)


@mcp.resource(
    "pakunoda://search/trials",
    name="search_trials",
    description="All hyperparameter search trial records",
    mime_type="application/json",
)
def resource_search_trials() -> str:
    adapter = SearchAdapter(_get_reader())
    try:
        return json.dumps(adapter.trials(), indent=2)
    except FileNotFoundError:
        return json.dumps([])


@mcp.resource(
    "pakunoda://candidate/{candidate_id}/problem",
    name="candidate_problem",
    description="Compiled problem JSON for a specific candidate",
    mime_type="application/json",
)
def resource_candidate_problem(candidate_id: str) -> str:
    adapter = CandidatesAdapter(_get_reader())
    try:
        return json.dumps(adapter.get_problem(candidate_id), indent=2)
    except KeyError as e:
        return json.dumps({"error": str(e)})
    except FileNotFoundError:
        return json.dumps({
            "error": f"Problem file not found for candidate {candidate_id!r}. "
                     "Has candidate enumeration been run?"
        })


# ── Tools ────────────────────────────────────────────────────────────

@mcp.tool(
    name="validate_project",
    description=(
        "Check whether the Pakunoda results directory is valid and readable. "
        "Returns which output files are present."
    ),
)
def tool_validate_project() -> str:
    reader = _get_reader()
    adapter = ProjectAdapter(reader)
    return json.dumps(
        {"results_dir": str(reader.root), "files": adapter.file_status()},
        indent=2,
    )


@mcp.tool(
    name="enumerate_candidates",
    description=(
        "List all decomposition candidates with their blocks, couplings, "
        "and mode assignments."
    ),
)
def tool_enumerate_candidates() -> str:
    adapter = CandidatesAdapter(_get_reader())
    return json.dumps(adapter.summarize(), indent=2)


@mcp.tool(
    name="summarize_search",
    description=(
        "Summarize hyperparameter search results: best trials per candidate, "
        "total trials, and overall best."
    ),
)
def tool_summarize_search() -> str:
    adapter = SearchAdapter(_get_reader())
    try:
        return json.dumps(adapter.best_per_candidate(), indent=2)
    except FileNotFoundError:
        return json.dumps(
            {"error": "Search results not found. Has search been run?"}
        )


@mcp.tool(
    name="recommend_model",
    description=(
        "Return the search recommendation: best model by error, "
        "best balanced model, top-N ranking, and explanation."
    ),
)
def tool_recommend_model() -> str:
    adapter = SearchAdapter(_get_reader())
    try:
        return json.dumps(adapter.recommendation(), indent=2, default=str)
    except FileNotFoundError:
        return json.dumps({
            "error": (
                "recommendation.yaml not found. "
                "Run Pakunoda search first (search.enabled: true)."
            )
        })


@mcp.tool(
    name="get_candidate_problem",
    description=(
        "Return the compiled problem for a candidate: the concrete tensor "
        "decomposition problem derived from the candidate definition. "
        "Use enumerate_candidates first to get IDs."
    ),
)
def tool_get_candidate_problem(candidate_id: str) -> str:
    adapter = CandidatesAdapter(_get_reader())
    try:
        return json.dumps(adapter.get_problem(candidate_id), indent=2)
    except KeyError as e:
        return json.dumps({"error": str(e)})
    except FileNotFoundError:
        return json.dumps({
            "error": f"Problem file not found for candidate {candidate_id!r}. "
                     "Has candidate enumeration been run?"
        })


@mcp.tool(
    name="get_candidate_details",
    description=(
        "Return full detail for a single candidate: blocks, mode assignments, "
        "couplings, and solver family. Use enumerate_candidates first to get IDs."
    ),
)
def tool_get_candidate_details(candidate_id: str) -> str:
    adapter = CandidatesAdapter(_get_reader())
    try:
        return json.dumps(adapter.get_details(candidate_id), indent=2)
    except KeyError as e:
        return json.dumps({"error": str(e)})


@mcp.tool(
    name="get_candidate_result",
    description=(
        "Return the run result for a candidate (reconstruction output). "
        "Use enumerate_candidates first to get IDs."
    ),
)
def tool_get_candidate_result(candidate_id: str) -> str:
    adapter = CandidatesAdapter(_get_reader())
    try:
        return json.dumps(adapter.get_result(candidate_id), indent=2)
    except KeyError as e:
        return json.dumps({"error": str(e)})
    except FileNotFoundError:
        return json.dumps({
            "error": f"Result file not found for candidate {candidate_id!r}. "
                     "Has the pipeline been run?"
        })


@mcp.tool(
    name="get_candidate_score",
    description=(
        "Return the score for a candidate (e.g. reconstruction error). "
        "Use enumerate_candidates first to get IDs."
    ),
)
def tool_get_candidate_score(candidate_id: str) -> str:
    adapter = CandidatesAdapter(_get_reader())
    try:
        return json.dumps(adapter.get_score(candidate_id), indent=2)
    except KeyError as e:
        return json.dumps({"error": str(e)})
    except FileNotFoundError:
        return json.dumps({
            "error": f"Score file not found for candidate {candidate_id!r}. "
                     "Has the pipeline been run?"
        })


# ── Write tools ──────────────────────────────────────────────────────

@mcp.tool(
    name="run_search",
    description=(
        "Launch Pakunoda's hyperparameter search pipeline. "
        "Accepts a high-level goal and max_trials count. "
        "Returns a job summary with search output status."
    ),
)
def tool_run_search(
    project_path: str,
    goal: str = "imputation",
    max_trials: int | None = None,
    cores: int = 1,
) -> str:
    adapter = SearchAdapter(_get_reader())
    result = adapter.run_search(
        config_path=project_path,
        max_trials=max_trials,
        goal=goal,
        cores=cores,
    )
    return json.dumps(result, indent=2)


@mcp.tool(
    name="refresh_project_state",
    description=(
        "Re-read all project outputs (config, graph, candidates, "
        "summary, search recommendation) and return a snapshot of "
        "current state. Use after running a pipeline or search."
    ),
)
def tool_refresh_project_state() -> str:
    adapter = ProjectAdapter(_get_reader())
    return json.dumps(adapter.refresh(), indent=2, default=str)


# ── Entry point ──────────────────────────────────────────────────────

def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

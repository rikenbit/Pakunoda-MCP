# Pakunoda-MCP v0.1.0

MCP server that exposes [Pakunoda](https://github.com/rikenbit/Pakunoda) multi-block tensor decomposition results to AI agents. Read project state, inspect candidates, review search results, and trigger hyperparameter searches — all through a structured MCP interface over stdio.

**Highlights**: 7 resources, 10 tools (8 read / 2 write), 2 prompts, project identity safety check, 101 tests.

## Resources (7)

| URI | Description |
|---|---|
| `pakunoda://project/config` | Project configuration |
| `pakunoda://project/graph` | Block-mode relation graph |
| `pakunoda://project/candidates` | All enumerated candidates |
| `pakunoda://project/summary` | Project summary with ranking |
| `pakunoda://candidate/{candidate_id}/problem` | Compiled problem (template) |
| `pakunoda://search/summary` | Search recommendation + best trials |
| `pakunoda://search/trials` | All search trial records |

## Tools (10)

**Read-only (8)**: `validate_project`, `enumerate_candidates`, `get_candidate_details`, `get_candidate_problem`, `get_candidate_result`, `get_candidate_score`, `summarize_search`, `recommend_model`

**Write (2)**: `run_search`, `refresh_project_state`

## Prompts (2)

- **`inspect_project`** — guided project health check (validate → enumerate → search → recommend)
- **`compare_candidates`** — side-by-side comparison of two candidates across definition / problem / result / score

## Safety

- **Allow-list runner**: only the `search` Snakemake target is permitted
- **Project identity check**: `run_search` rejects config/results `project.id` mismatch
- **Pinned execution context**: absolute `--snakefile` path + `cwd=PAKUNODA_REPO_DIR`

## Environment variables

| Variable | Required for | Description |
|---|---|---|
| `PAKUNODA_RESULTS_DIR` | All operations | Path to Pakunoda results directory |
| `PAKUNODA_REPO_DIR` | Write tools only | Path to Pakunoda repository root |

## Install

```bash
pip install -e .
pakunoda-mcp
```

## Current limitations

- Single project per server instance
- stdio transport only (no HTTP/SSE)
- No auth (local use)
- Not published to PyPI

Full API reference: [docs/api.md](api.md)

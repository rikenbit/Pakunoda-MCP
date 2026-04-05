# Pakunoda-MCP v0.1.0

Initial release of the MCP server for [Pakunoda](https://github.com/rikenbit/Pakunoda) project state.

## What is Pakunoda-MCP?

An [MCP](https://modelcontextprotocol.io/) server that exposes Pakunoda's
multi-block tensor decomposition results to AI agents over stdio transport.
Agents can browse project state, inspect candidates, review search results,
and trigger hyperparameter searches — all through a structured MCP interface.

## Resources (7)

| URI | Description |
|---|---|
| `pakunoda://project/config` | Project configuration (config.yaml) |
| `pakunoda://project/graph` | Block-mode relation graph |
| `pakunoda://project/candidates` | All enumerated candidates |
| `pakunoda://project/summary` | Project summary with candidate ranking |
| `pakunoda://candidate/{candidate_id}/problem` | Compiled problem for a specific candidate |
| `pakunoda://search/summary` | Search recommendation + best trials |
| `pakunoda://search/trials` | All search trial records |

## Tools (10)

### Read-only (8)

| Tool | Description |
|---|---|
| `validate_project` | Check project identity and output file status |
| `enumerate_candidates` | List all candidates (compact summary) |
| `get_candidate_details` | Full candidate definition (blocks, modes, couplings) |
| `get_candidate_problem` | Compiled tensor decomposition problem |
| `get_candidate_result` | Run result (reconstruction output, runtime) |
| `get_candidate_score` | Score (imputation RMSE, reconstruction error) |
| `summarize_search` | Best trials per candidate |
| `recommend_model` | Search recommendation with explanation |

### Write (2)

| Tool | Description |
|---|---|
| `run_search` | Launch Pakunoda search pipeline via Snakemake |
| `refresh_project_state` | Re-read all project outputs |

## Prompts (2)

| Prompt | Description |
|---|---|
| `inspect_project` | Guided project health check: validate → enumerate → search → recommend |
| `compare_candidates` | Side-by-side comparison of two candidates across all four stages |

## Safety

- **Allow-list runner**: only the `search` target (mapped to Snakemake rule `recommend`) is permitted — no arbitrary command execution
- **Project identity check**: `run_search` compares `project.id` between the results directory and the target config, rejecting mismatches before any subprocess runs
- **Pinned execution context**: Snakemake runs with absolute `--snakefile` path and `cwd=PAKUNODA_REPO_DIR`, independent of where the MCP server was started

## Environment variables

| Variable | Required for | Description |
|---|---|---|
| `PAKUNODA_RESULTS_DIR` | All operations | Path to a Pakunoda results directory |
| `PAKUNODA_REPO_DIR` | Write tools only | Path to the Pakunoda repository root |

## Installation

```bash
pip install -e .
```

Or with Docker:

```bash
docker build -t pakunoda-mcp .
docker run --rm -v /path/to/results:/data:ro -e PAKUNODA_RESULTS_DIR=/data/my_project -i pakunoda-mcp
```

## Current limitations

- **Minimal write**: only `run_search` — no config generation or freeze/release
- **Single project**: one results directory per server instance
- **stdio only**: no HTTP/SSE transport
- **No auth**: intended for local use
- **No PyPI publish**: install from source

## Test coverage

101 tests across 5 test modules:
- `test_reader.py` (12) — file I/O layer
- `test_adapters.py` (41) — domain adapter layer
- `test_runner.py` (11) — subprocess runner
- `test_server.py` (31) — MCP server tools/resources/prompts
- `test_smoke.py` (6) — registration completeness guard

# Pakunoda-MCP

[MCP](https://modelcontextprotocol.io/) server that exposes
[Pakunoda](https://github.com/rikenbit/Pakunoda) project state to AI agents.

> **v0.1.0** — 7 resources, 10 tools (8 read / 2 write), 2 prompts.
> No arbitrary shell execution, no direct solver parameter control.
> See [release notes](docs/release_notes_v0.1.0.md).

## Responsibility split

| Concern | Owner |
|---|---|
| Data ingestion, validation, candidate enumeration, compilation | **Pakunoda** |
| Solver execution (mwTensor) | **Pakunoda** (via R bridge) |
| Hyperparameter search (Optuna) | **Pakunoda** |
| Workflow orchestration (Snakemake) | **Pakunoda** |
| Exposing results to AI agents (MCP resources + tools) | **Pakunoda-MCP** |
| Triggering search pipeline (high-level, via Snakemake CLI) | **Pakunoda-MCP** |

Pakunoda-MCP reads the results directory that Pakunoda produces.
Write tools invoke Snakemake as a subprocess with an allow-listed target —
they do not import Pakunoda internals or execute arbitrary commands.

## MCP interface

| Category | Count | Examples |
|---|---|---|
| Resources | 7 | `pakunoda://project/config`, `pakunoda://search/trials`, ... |
| Tools (read) | 8 | `validate_project`, `enumerate_candidates`, `get_candidate_score`, ... |
| Tools (write) | 2 | `run_search`, `refresh_project_state` |
| Prompts | 2 | `inspect_project`, `compare_candidates` |

Read-only tools follow a **list → detail** pattern:
`enumerate_candidates` → `get_candidate_details` / `get_candidate_problem` / `get_candidate_result` / `get_candidate_score`

Write tool `run_search` verifies that `project.id` in the target config matches
the current results directory, rejecting mismatches before any subprocess runs.

For full parameter and return value details, see [docs/api.md](docs/api.md).

## Environment variables

Pakunoda-MCP uses two environment variables to separate read and write concerns:

| Variable | Purpose | Required for |
|---|---|---|
| `PAKUNODA_RESULTS_DIR` | Path to a Pakunoda results directory (e.g. `results/my_project`). Used by **all** resources and read-only tools. | All operations |
| `PAKUNODA_REPO_DIR` | Path to the Pakunoda repository root (the directory containing `Snakefile`). Used by `run_search` to pin the execution context. | Write tools only |

**Why two variables?** The results directory and the Pakunoda repo may live
in different locations. Read-only operations need only the results.
Write tools need the repo to locate the Snakefile — they run Snakemake
with `cwd=PAKUNODA_REPO_DIR` and an absolute `--snakefile` path, so the
server's own working directory is irrelevant.

## Quick start

```bash
pip install -e .

# Required: results directory produced by Pakunoda
export PAKUNODA_RESULTS_DIR=/path/to/results/my_project

# Optional: Pakunoda repo root (only needed for run_search)
export PAKUNODA_REPO_DIR=/path/to/Pakunoda

pakunoda-mcp
```

### Claude Code

Add to `~/.claude/settings.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "pakunoda": {
      "command": "pakunoda-mcp",
      "env": {
        "PAKUNODA_RESULTS_DIR": "/path/to/results/my_project"
      }
    }
  }
}
```

If you also want write tools (`run_search`), add `PAKUNODA_REPO_DIR`:

```json
{
  "mcpServers": {
    "pakunoda": {
      "command": "pakunoda-mcp",
      "env": {
        "PAKUNODA_RESULTS_DIR": "/path/to/results/my_project",
        "PAKUNODA_REPO_DIR": "/path/to/Pakunoda"
      }
    }
  }
}
```

### Docker

```bash
docker build -t pakunoda-mcp .

# Read-only (no PAKUNODA_REPO_DIR needed)
docker run --rm \
  -v /path/to/results:/data:ro \
  -e PAKUNODA_RESULTS_DIR=/data/my_project \
  -i pakunoda-mcp

# With write tools
docker run --rm \
  -v /path/to/results:/data \
  -v /path/to/Pakunoda:/repo:ro \
  -e PAKUNODA_RESULTS_DIR=/data/my_project \
  -e PAKUNODA_REPO_DIR=/repo \
  -i pakunoda-mcp
```

## Usage examples

### Read-only: inspect a project

Use the `inspect_project` prompt to walk through a standard check:

```
> Use the inspect_project prompt
(Agent calls validate_project → enumerate_candidates → summarize_search → recommend_model)
```

Or call tools directly:

```
> What candidates does this project have?
(Agent calls enumerate_candidates)

> Show me the score for c0_expression_methylation
(Agent calls get_candidate_score("c0_expression_methylation"))
```

### Read-only: compare two candidates

```
> Use the compare_candidates prompt with c0_alpha and c1_beta
(Agent calls get_candidate_details / get_candidate_problem /
 get_candidate_result / get_candidate_score for each, then summarizes)
```

### Write: run a search

```
> Run a hyperparameter search with 50 trials
(Agent calls run_search(project_path="/path/to/config.yaml", max_trials=50))
(Agent calls refresh_project_state to see updated results)
```

`run_search` checks that `project.id` in the target config matches the
current results directory. A mismatch is rejected before any subprocess runs.

## Development

```bash
pip install -e .
pytest
```

## Current limitations

- **Minimal write**: only `run_search` (via Snakemake subprocess) — no config generation, no freeze/release
- **No arbitrary execution**: runner has a fixed allow-list of Snakemake targets
- **Single project**: one results directory per server instance
- **stdio only**: no HTTP/SSE transport
- **No auth**: intended for local use

## License

MIT

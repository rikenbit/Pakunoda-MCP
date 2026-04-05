# Pakunoda-MCP

[MCP](https://modelcontextprotocol.io/) server that exposes
[Pakunoda](https://github.com/rikenbit/Pakunoda) project state to AI agents.

> **Status: Minimal MVP.** Read-only resources plus two write tools
> (`run_search`, `refresh_project_state`). No arbitrary shell execution,
> no direct solver parameter control.

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

## Resources (read-only)

| URI | Description |
|---|---|
| `pakunoda://project/config` | Project configuration (config.yaml) |
| `pakunoda://project/graph` | Block-mode relation graph |
| `pakunoda://project/candidates` | All enumerated candidates |
| `pakunoda://search/summary` | Search recommendation + best trials |

## Tools

### Read-only

| Tool | Description |
|---|---|
| `validate_project` | Check which output files are present |
| `enumerate_candidates` | List candidates with blocks and couplings |
| `summarize_search` | Summarize hyperparameter search results |
| `recommend_model` | Return search recommendation |

### Write

| Tool | Description |
|---|---|
| `run_search` | Launch Pakunoda search pipeline (goal, max_trials, project_path) |
| `refresh_project_state` | Re-read all project outputs after a pipeline run |

`run_search` accepts high-level parameters only:

| Parameter | Description | Default |
|---|---|---|
| `project_path` | Path to config.yaml | (required) |
| `goal` | Search objective | `"imputation"` |
| `max_trials` | Max trials per candidate | Pakunoda default (20) |
| `cores` | Snakemake cores | 1 |

Low-level Optuna API, solver parameters, and init policies are NOT directly
exposed — they are controlled via Pakunoda's config.yaml.

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
# Install
pip install -e .

# Read side: point to a Pakunoda results directory
export PAKUNODA_RESULTS_DIR=/path/to/results/my_project

# Write side: point to the Pakunoda repository (needed for run_search)
export PAKUNODA_REPO_DIR=/path/to/Pakunoda

# Run the MCP server (stdio transport)
pakunoda-mcp
```

### Claude Code / Claude Desktop

Add to your MCP config:

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
docker run --rm \
  -v /path/to/results:/data \
  -v /path/to/Pakunoda:/repo:ro \
  -e PAKUNODA_RESULTS_DIR=/data/my_project \
  -e PAKUNODA_REPO_DIR=/repo \
  -i pakunoda-mcp
```

## Development

```bash
pip install -e .
pytest
```

## Current limitations

- **Minimal write**: only `run_search` (via Snakemake subprocess) — no config generation, no freeze/release
- **No arbitrary execution**: runner has a fixed allow-list of Snakemake targets
- **Single project**: one results directory per server instance
- **No prompts yet**: MCP prompt templates are not implemented
- **stdio only**: no HTTP/SSE transport
- **No auth**: intended for local use

## License

MIT

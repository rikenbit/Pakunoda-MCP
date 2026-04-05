# Pakunoda-MCP API Reference

Complete reference for all MCP resources, tools, and prompts in v0.1.0.

All responses are JSON (`application/json`). Tools return a JSON string.
Resources return raw JSON content.

## Environment variables

| Variable | Required for | Description |
|---|---|---|
| `PAKUNODA_RESULTS_DIR` | All operations | Path to a Pakunoda results directory (e.g. `results/my_project`) |
| `PAKUNODA_REPO_DIR` | Write tools only | Path to the Pakunoda repository root (directory containing `Snakefile`) |

---

## Resources (6 static + 1 template)

Resources are read-only data endpoints. They do not accept parameters
(except templates, which accept URI parameters).

### `pakunoda://project/config`

Project configuration from `config.yaml`.

- **Returns**: Full config object (blocks, relations, solver, search settings)

### `pakunoda://project/graph`

Block-mode relation graph.

- **Returns**: `{nodes: [...], edges: [...], adjacency: {...}}`

### `pakunoda://project/candidates`

All enumerated decomposition candidates.

- **Returns**: `{project_id, num_candidates, candidates: [...]}`

### `pakunoda://project/summary`

Project summary with candidate ranking.

- **Returns**: `{total_candidates, succeeded, failed, ranking: [...], failed_candidates: [...]}`

### `pakunoda://search/summary`

Search recommendation and best trials (tolerates missing files).

- **Returns**: `{recommendation: ... | null, best: ... | null}`

### `pakunoda://search/trials`

All hyperparameter search trial records.

- **Returns**: `[{candidate_id, trial_number, state, imputation_rmse, rank, ...}, ...]`
- **If missing**: returns `[]`

### `pakunoda://candidate/{candidate_id}/problem` (template)

Compiled problem JSON for a specific candidate.

- **URI parameter**: `candidate_id` (string)
- **Returns**: compiled problem object
- **If unknown ID**: `{error: "..."}`
- **If file missing**: `{error: "Problem file not found ..."}`

---

## Tools — Read-only (8)

### `validate_project`

Check project identity and which output files are present.

- **Parameters**: none
- **Returns**: `{results_dir, project_id, files: {config: "ok"|"missing"|"error: ...", ...}}`

### `enumerate_candidates`

List all candidates in compact form.

- **Parameters**: none
- **Returns**: `{project_id, num_candidates, candidates: [{id, blocks, num_couplings, rank, solver_family}, ...]}`

### `get_candidate_details`

Full detail for a single candidate from `candidates.json`.

- **Parameters**: `candidate_id` (string, required)
- **Returns**: full candidate object (blocks, mode_assignments, couplings, rank, solver_family)
- **If unknown ID**: `{error: "..."}`

### `get_candidate_problem`

Compiled tensor decomposition problem.

- **Parameters**: `candidate_id` (string, required)
- **Returns**: compiled problem object (blocks, modes, shapes, rank, solver_family)
- **If unknown ID**: `{error: "..."}`
- **If file missing**: `{error: "Problem file not found ..."}`

### `get_candidate_result`

Run result for a candidate (reconstruction output).

- **Parameters**: `candidate_id` (string, required)
- **Returns**: `{candidate_id, status, reconstruction_error, runtime_seconds, rank, init_policy}`
- **If unknown ID**: `{error: "..."}`
- **If file missing**: `{error: "Result file not found ..."}`

### `get_candidate_score`

Score for a candidate.

- **Parameters**: `candidate_id` (string, required)
- **Returns**: `{candidate_id, imputation_rmse, reconstruction_error, rank}`
- **If unknown ID**: `{error: "..."}`
- **If file missing**: `{error: "Score file not found ..."}`

### `summarize_search`

Best trials per candidate with overall best.

- **Parameters**: none
- **Returns**: `{overall_best: {...}, by_candidate: [{candidate_id, best_rmse, best_rank, best_init_policy, num_trials}, ...]}`
- **If search not run**: `{error: "Search results not found. ..."}`

### `recommend_model`

Search recommendation with explanation.

- **Parameters**: none
- **Returns**: `{best_by_error, best_by_balanced, top_n, explanation, total_candidates_searched, total_trials}`
- **If not available**: `{error: "recommendation.yaml not found. ..."}`

---

## Tools — Write (2)

### `run_search`

Launch Pakunoda's hyperparameter search pipeline via Snakemake.

- **Parameters**:

  | Name | Type | Required | Default | Description |
  |---|---|---|---|---|
  | `project_path` | string | yes | — | Path to config.yaml |
  | `goal` | string | no | `"imputation"` | Search objective (only `"imputation"` supported) |
  | `max_trials` | integer | no | Pakunoda default | Max trials per candidate (must be >= 1) |
  | `cores` | integer | no | `1` | Snakemake cores |

- **Returns (success)**: `{accepted: true, message, search_outputs: {recommendation, best, trials}}`
- **Returns (failure)**: `{accepted: false, message, detail: {returncode, stderr}}`
- **Returns (rejected)**: `{accepted: false, message: "..."}`

- **Safety**:
  - Rejects unsupported `goal` values
  - Rejects `max_trials < 1`
  - Rejects project mismatch (results dir project_id != config project_id)
  - Only the `search` Snakemake target is allowed (allow-list)
  - Requires `PAKUNODA_REPO_DIR` environment variable

### `refresh_project_state`

Re-read all project outputs and return a snapshot.

- **Parameters**: none
- **Returns**: `{project_id, config, relation_graph, candidates, summary, search_recommendation}` — each value is the full object, `null` if missing, or `"error: ..."` on parse failure

---

## Prompts (2)

Prompts are instruction templates that guide AI agents through multi-step
workflows using the tools above. They return a `list[Message]` to be
sent as the conversation start.

### `inspect_project`

Guided project health check.

- **Parameters**: none
- **Steps**: `validate_project` → `enumerate_candidates` → `summarize_search` → `recommend_model`
- **Handles missing state**: instructs agent to report unavailable search/recommendation

### `compare_candidates`

Side-by-side comparison of two candidates across all four stages.

- **Parameters**:

  | Name | Type | Description |
  |---|---|---|
  | `candidate_a` | string | First candidate ID |
  | `candidate_b` | string | Second candidate ID |

- **Steps**: `get_candidate_details` → `get_candidate_problem` → `get_candidate_result` → `get_candidate_score` (for each candidate)
- **Handles missing state**: instructs agent to mark unavailable stages per candidate

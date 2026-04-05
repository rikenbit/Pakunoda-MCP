# Changelog

## 0.1.0 — 2026-04-05

Initial release.

### Resources
- `pakunoda://project/config` — project configuration
- `pakunoda://project/graph` — block-mode relation graph
- `pakunoda://project/candidates` — all enumerated candidates
- `pakunoda://project/summary` — project summary with ranking
- `pakunoda://candidate/{candidate_id}/problem` — compiled problem (template)
- `pakunoda://search/summary` — search recommendation + best trials
- `pakunoda://search/trials` — all search trial records

### Tools
- `validate_project` — check project identity and file status
- `enumerate_candidates` — list candidates (compact)
- `get_candidate_details` / `get_candidate_problem` / `get_candidate_result` / `get_candidate_score` — per-candidate drill-down
- `summarize_search` — best trials per candidate
- `recommend_model` — search recommendation
- `run_search` — launch Pakunoda search pipeline (write)
- `refresh_project_state` — re-read all outputs (write)

### Prompts
- `inspect_project` — guided project inspection workflow
- `compare_candidates` — side-by-side candidate comparison

### Safety
- Allow-list runner: only `search` → `recommend` Snakemake target
- Project identity check: `run_search` rejects config/results mismatch
- Pinned execution context via `PAKUNODA_REPO_DIR`

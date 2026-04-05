# Release Checklist — v0.1.0

## Pre-release

- [ ] `pyproject.toml` version is `0.1.0`
- [ ] `CHANGELOG.md` has `0.1.0` entry with correct date
- [ ] `README.md` status line says `v0.1.0`
- [ ] `docs/api.md` header says `v0.1.0`
- [ ] `docs/release_notes_v0.1.0.md` is finalized

## Consistency

- [ ] Resource count: 7 (6 static + 1 template) — matches across README / api.md / release notes / smoke test
- [ ] Tool count: 10 (8 read + 2 write) — matches across all docs and smoke test
- [ ] Prompt count: 2 — matches across all docs and smoke test
- [ ] Environment variables: `PAKUNODA_RESULTS_DIR`, `PAKUNODA_REPO_DIR` — consistent in README / api.md / release notes / server.py
- [ ] Entrypoint: `pakunoda-mcp` — consistent in pyproject.toml / README / Dockerfile

## CI

- [ ] `pytest` passes locally (101 tests)
- [ ] CI workflow (`.github/workflows/ci.yml`) passes on push to main
- [ ] Docker image builds: `docker build -t pakunoda-mcp .`

## Release

- [ ] All changes committed and pushed to `main`
- [ ] Create tag: `git tag v0.1.0`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] GitHub Release created (automated via `.github/workflows/release.yml` or manual)
- [ ] Release body uses `docs/release_notes_v0.1.0.md`

## Post-release

- [ ] Verify GitHub Release page looks correct
- [ ] Verify release tag points to correct commit

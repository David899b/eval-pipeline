# eval-pipeline

**One CI pipeline that runs two independent evaluation gates in sequence and produces a single roll-up, so a release decision is backed by both the quality/safety/cost/latency/governance signal and the adversarial (red-team) ASR signal.**

[![pipeline](https://github.com/David899b/eval-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/David899b/eval-pipeline/actions/workflows/pipeline.yml)
[![python 3.12](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

```
                ┌───────────────────────────┐
                │        eval-pipeline       │
                │      (this repository)     │
                └──────────────┬────────────┘
                               │ checkout (public)
          ┌────────────────────┴────────────────────┐
          ▼                                          ▼
┌───────────────────────┐                 ┌────────────────────────┐
│  eval-quality-gate    │                 │   eval-redteam-suite    │
│  5 dimensions + band  │                 │  OWASP LLM Top 10 ASR   │
│  demo -> REVIEW       │                 │  demo -> NO_GO          │
└──────────┬────────────┘                 └───────────┬────────────┘
           │ report.json                              │ report.json
           └──────────────────┬───────────────────────┘
                              ▼
                   scripts/summarize.py
                   pipeline-summary.{md,json}
```

## What it does

1. Checks out both gate repositories (both public).
2. Installs both gates (`pip install -e`).
3. Runs **Gate 1 — quality**: expects `REVIEW` (exit `0`).
4. Runs **Gate 2 — red-team**: the sample target is intentionally vulnerable, so
   the gate returns `NO_GO` (exit `1`); the step asserts exactly that exit code,
   proving the gate blocks the merge as designed.
5. Builds a combined `pipeline-summary.md` + `.json`, prints it to the job page,
   and uploads all evidence as an artifact.

## Run locally

The orchestrator is stdlib only and expects the gates' JSON reports to already
exist under `reports/`:

```bash
python scripts/summarize.py
```

## CI behaviour

- **`selftest` job** runs the orchestrator against the checked-in fixtures
  (stdlib only).
- **`gates` job** checks out both public gate repositories, runs **Gate 1 —
   quality** (expects `REVIEW`, exit `0`) and **Gate 2 — red-team** (the sample
   target is intentionally vulnerable, so the gate returns `NO_GO`, exit `1`;
   the step asserts exactly that exit code), then rolls up the evidence.

## Evidence produced

- `reports/quality/report.{md,json}` — 5-dimension decision + confidence band.
- `reports/redteam/report.{md,json}` — ASR by OWASP category + breaches.
- `pipeline-summary.{md,json}` — the roll-up.

See `guion-pipeline.md` for the narration, the numbers behind each figure, and
the open decisions.

## Companion repositories

- [`eval-quality-gate`](https://github.com/David899b/eval-quality-gate) — quality / safety / cost / latency / governance gate.
- [`eval-redteam-suite`](https://github.com/David899b/eval-redteam-suite) — OWASP-aligned red-team ASR gate.

# eval-pipeline

One CI pipeline that runs **two independent evaluation gates** in sequence and
produces a single roll-up, so a release decision is backed by both the
**quality/safety/cost/latency/governance** signal and the **adversarial
(red-team) ASR** signal.

```
                ┌───────────────────────────┐
                │        eval-pipeline       │
                │      (this repository)     │
                └──────────────┬────────────┘
                               │ checkout (CROSS_REPO_TOKEN)
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

1. Checks out both gate repositories (both private) using a scoped token.
2. Installs both gates (`pip install -e`).
3. Runs **Gate 1 — quality**: expects `REVIEW` (exit `0`).
4. Runs **Gate 2 — red-team**: the sample target is intentionally vulnerable, so
   the gate returns `NO_GO` (exit `1`); the step asserts exactly that exit code,
   proving the gate blocks the merge as designed.
5. Builds a combined `pipeline-summary.md` + `.json`, prints it to the job page,
   and uploads all evidence as an artifact.

## Setup (one time)

Create a **`CROSS_REPO_TOKEN`** secret in this repository with read access to the
two private gate repositories:

- Fine-grained PAT: enable **Contents: Read-only** on `eval-quality-gate` and
  `eval-redteam-suite`.
- Classic PAT: scope `repo`.

Then add it under *Settings → Secrets and variables → Actions → New repository
secret* named exactly `CROSS_REPO_TOKEN`.

## Troubleshooting the token

The `gates` job runs a **Token preflight** step first. If the checkout of a
private repo fails, read that step:

- `Bad credentials (401)` — the secret value is not a valid token (wrong paste
  or truncated).
- `Not Found (get-a-repository)` — the token authenticates but **cannot see the
  repo**. Almost always one of:
  - the token was created under a **different account** than `David899b`
    (resource owner must be `David899b`);
  - it is a fine-grained token and the two repos are **not in its allowed
    repository list**;
  - it lacks **Contents: Read-only**.
- Fix: regenerate the PAT under the `David899b` account with **Contents:
  Read-only** on `eval-quality-gate` and `eval-redteam-suite`, then update the
  `CROSS_REPO_TOKEN` secret.

## Setup (one time)

The orchestrator is stdlib only and expects the gates' JSON reports to already
exist under `reports/`:

```bash
python scripts/summarize.py
```

## CI behaviour

- **`selftest` job** always runs: it exercises `scripts/summarize.py` against the
  checked-in fixtures (stdlib only), so the orchestrator is verified even before
  the token exists.
- **`gates` job** runs only when `CROSS_REPO_TOKEN` is set; until then it is
  skipped and the workflow stays green.

## Evidence produced

- `reports/quality/report.{md,json}` — 5-dimension decision + confidence band.
- `reports/redteam/report.{md,json}` — ASR by OWASP category + breaches.
- `pipeline-summary.{md,json}` — the roll-up.

See `guion-pipeline.md` for the narration, the numbers behind each figure, and
the open decisions.

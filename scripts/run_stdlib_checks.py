"""Stdlib self-tests for the pipeline roll-up. No dependencies, no network.

Runs the same ``build_summary`` / ``render_markdown`` used in CI against the
checked-in fixtures, so the orchestrator is verified even before the
cross-repo token is configured.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import summarize  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
QUALITY = FIXTURES / "quality-report.json"
REDTEAM = FIXTURES / "redteam-report.json"

_checks = 0
_failures: list[str] = []


def check(condition: bool, label: str) -> None:
    global _checks
    _checks += 1
    if condition:
        print(f"  [PASS] {label}")
    else:
        _failures.append(label)
        print(f"  [FAIL] {label}")


def main() -> int:
    quality = json.loads(QUALITY.read_text(encoding="utf-8"))
    redteam = json.loads(REDTEAM.read_text(encoding="utf-8"))

    summary = summarize.build_summary(quality, redteam)
    q = summary["quality_gate"]
    r = summary["redteam_gate"]

    check(q["decision"] == "REVIEW", "quality decision folded in")
    check(0.0 < q["base"] <= 1.0, "quality base is a probability-like score")
    check(
        set(q["dimensions"]) >= {"quality", "safety", "cost", "latency", "governance"},
        "all five dimensions present",
    )
    check(r["decision"] == "NO_GO", "red-team decision folded in")
    check(0.0 <= r["overall_asr"] <= 1.0, "ASR bounded")
    check(isinstance(r["breaches"], list), "breaches is a list")

    markdown = summarize.render_markdown(summary)
    check(markdown.startswith("# Pipeline roll-up"), "markdown has a title")
    check("quality" in markdown and "red-team" in markdown, "markdown has both gates")
    check("REVIEW" in markdown and "NO_GO" in markdown, "markdown shows both decisions")

    original_q, original_r = summarize.QUALITY, summarize.REDTEAM
    summarize.QUALITY = ROOT / "does-not-exist-quality.json"
    summarize.REDTEAM = ROOT / "does-not-exist-redteam.json"
    missing_code = summarize.main()
    summarize.QUALITY, summarize.REDTEAM = original_q, original_r
    check(missing_code == 2, "main() returns 2 when reports are missing")

    print(f"\n{_checks - len(_failures)}/{_checks} checks passed")
    return 1 if _failures else 0


if __name__ == "__main__":
    sys.exit(main())

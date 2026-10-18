"""Combine the quality-gate and red-team reports into one roll-up summary.

Stdlib only. It reads the two JSON artifacts emitted by the upstream gates and
writes pipeline-summary.{md,json}. Exit 0 when both reports are present and
parseable, 2 otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
QUALITY = ROOT / "reports" / "quality" / "report.json"
REDTEAM = ROOT / "reports" / "redteam" / "report.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary(quality: dict[str, Any], redteam: dict[str, Any]) -> dict[str, Any]:
    decision = quality["decision"]
    return {
        "quality_gate": {
            "decision": decision["status"],
            "pessimistic": decision["scenario"]["pessimistic"],
            "base": decision["scenario"]["base"],
            "optimistic": decision["scenario"]["optimistic"],
            "dimensions": {d["dimension"]: d["status"] for d in decision["dimensions"]},
        },
        "redteam_gate": {
            "decision": redteam["status"],
            "overall_asr": redteam["overall_asr"],
            "ci": redteam["ci"],
            "breaches": [f["id"] for f in redteam["failures"]],
        },
    }


def render_markdown(summary: dict[str, Any]) -> str:
    q = summary["quality_gate"]
    r = summary["redteam_gate"]
    lines = [
        "# Pipeline roll-up",
        "",
        "| gate | decision | headline |",
        "|---|---|---|",
        f"| quality | `{q['decision']}` | base {q['base']:.3f} "
        f"(pessimistic {q['pessimistic']:.3f}, optimistic {q['optimistic']:.3f}) |",
        f"| red-team | `{r['decision']}` | overall ASR {r['overall_asr']:.3f} "
        f"(95% CI {r['ci'][0]:.3f}-{r['ci'][1]:.3f}) |",
        "",
        "## Quality dimensions",
        "",
        "| dimension | status |",
        "|---|---|",
    ]
    lines += [f"| {name} | {status} |" for name, status in q["dimensions"].items()]
    lines += ["", "## Red-team breaches", ""]
    breaches = [f"- `{b}`" for b in r["breaches"]]
    lines += breaches or ["_No attack succeeded._"]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not QUALITY.exists() or not REDTEAM.exists():
        print("missing upstream reports; run the gates first", file=sys.stderr)
        return 2
    summary = build_summary(_load(QUALITY), _load(REDTEAM))
    (ROOT / "pipeline-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (ROOT / "pipeline-summary.md").write_text(render_markdown(summary), encoding="utf-8")
    q = summary["quality_gate"]
    r = summary["redteam_gate"]
    print(
        f"quality={q['decision']} base={q['base']:.3f} "
        f"| red-team={r['decision']} asr={r['overall_asr']:.3f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

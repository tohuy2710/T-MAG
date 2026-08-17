#!/usr/bin/env python3
"""Focused parameter miner for the CMF/Williams absolute-gap alpha family.

Anchor:
    group_neutralize(
        ts_rank(abs(short_term_price_change_2 - short_term_price_change), 9)
        * (1 - ts_rank(returns, 15)), industry)

This script intentionally changes only the parameter/operator neighbourhood of
that anchor.  It does not mix in unrelated A/B templates.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_cmf_williams_campaign import (  # noqa: E402
    GROUP,
    REQUESTED_SETTINGS,
    A,
    B,
    EPS,
)


OUT_DIR = Path(__file__).resolve().parent / "output" / "cmf_williams_campaign" / "abs_gap_focus"
TEMPLATE_PATH = ROOT / "templates" / "abs_gap_parameter_mining.json"
CANDIDATES_PATH = OUT_DIR / "candidates.json"
EXPRESSIONS_PATH = OUT_DIR / "expressions.txt"
REPORT_PATH = OUT_DIR / "parameter_report.md"

FIELD_WINDOWS = tuple(range(2, 11))
RETURN_WINDOWS = (10, 15, 20, 25, 30)
GAP = f"abs({A} - {B})"


def template_specs() -> list[dict[str, str]]:
    return [
        {
            "variant": "base_ts_rank",
            "description": "Anchor structure; only ts_rank windows change",
            "signal": "ts_rank({gap}, {field_window}) * (1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "ranked_gap_dual_rank",
            "description": "Rank both the gap signal and reversal leg",
            "signal": "rank(ts_rank({gap}, {field_window})) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "zscore_gap",
            "description": "Replace inner ts_rank(gap) with rolling ts_zscore(gap)",
            "signal": "ts_zscore({gap}, {field_window}) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "rolling_zscore_gap",
            "description": "Rolling demean/std normalization of the gap",
            "signal": "(({gap} - ts_mean({gap}, {field_window})) / (ts_std_dev({gap}, {field_window}) + {epsilon})) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "mean_gap",
            "description": "Mean gap inside the same reversal interaction",
            "signal": "ts_mean({gap}, {field_window}) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "delayed_gap",
            "description": "One additional signal delay; platform delay remains 1",
            "signal": "ts_rank(ts_delay({gap}, 1), {field_window}) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "delta_gap",
            "description": "One-day change in the absolute gap",
            "signal": "ts_rank(ts_delta({gap}, 1), {field_window}) * rank(1 - ts_rank(returns, {return_window}))",
        },
    ]


def candidate_id(variant: str, field_window: int, return_window: int) -> str:
    return f"abs_gap__{variant}__f{field_window}__r{return_window}"


def generate_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for spec in template_specs():
        for field_window in FIELD_WINDOWS:
            for return_window in RETURN_WINDOWS:
                signal = spec["signal"].format(
                    gap=GAP,
                    field_window=field_window,
                    return_window=return_window,
                    epsilon=EPS,
                )
                expression = f"group_neutralize({signal}, {GROUP})"
                candidates.append(
                    {
                        "candidate_id": candidate_id(spec["variant"], field_window, return_window),
                        "family": "absolute_gap",
                        "variant": spec["variant"],
                        "description": spec["description"],
                        "field_window": field_window,
                        "return_window": return_window,
                        "expression": expression,
                        "settings": dict(REQUESTED_SETTINGS),
                    }
                )
    return candidates


def write_outputs(candidates: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH.write_text(
        json.dumps(
            {
                "name": "cmf_williams_absolute_gap_parameter_mining",
                "anchor": f"group_neutralize(ts_rank({GAP}, 9) * (1 - ts_rank(returns, 15)), industry)",
                "parameter_grid": {
                    "field_window": list(FIELD_WINDOWS),
                    "return_window": list(RETURN_WINDOWS),
                },
                "variants": template_specs(),
                "settings": REQUESTED_SETTINGS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    CANDIDATES_PATH.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    EXPRESSIONS_PATH.write_text(
        "\n\n".join(
            f"[{c['candidate_id']}] {c['variant']} | field_window={c['field_window']} | return_window={c['return_window']}\n{c['expression']}"
            for c in candidates
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Absolute-gap parameter mining",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Anchor: `group_neutralize(ts_rank({GAP}, 9) * (1 - ts_rank(returns, 15)), {GROUP})`, with the reference windows field=9 and returns=15.",
        "",
        f"- Variants: **{len(template_specs())}**",
        f"- Field windows: **{list(FIELD_WINDOWS)}**",
        f"- Return windows: **{list(RETURN_WINDOWS)}**",
        f"- Total expressions: **{len(candidates)}** (45 direct parameter replacements + 270 focused operator variants when the full set is kept)",
        "",
        "## Priority order",
        "",
        "1. `base_ts_rank`: direct sensitivity map around the supplied expression.",
        "2. `ranked_gap_dual_rank`: preserves the anchor while testing rank normalization.",
        "3. `zscore_gap` and `rolling_zscore_gap`: test normalization without changing the factor family.",
        "4. `mean_gap`, `delayed_gap`, `delta_gap`: operator-neighbourhood extensions.",
        "",
        "All candidates keep the campaign settings: GLB / TOPDIV3000 / Delay 1 / Market / Decay 20 / Truncation 0.08 / Pasteurization ON / Unit Verify / NaN ON / Max Trade OFF / Max Position OFF.",
        "",
        "No performance metrics are fabricated here; submit this focused set to BRAIN when simulation quota/rate-limit permits.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Keep only the first N expressions; 0 keeps all 315")
    args = parser.parse_args()
    candidates = generate_candidates()
    if args.limit > 0:
        candidates = candidates[: args.limit]
    write_outputs(candidates)
    print(f"generated={len(candidates)}")
    print(f"template={TEMPLATE_PATH}")
    print(f"expressions={EXPRESSIONS_PATH}")
    print(f"report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

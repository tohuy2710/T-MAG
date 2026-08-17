#!/usr/bin/env python3
"""Focused development campaign for alpha WjAv9LeG.

Anchor:
  group_neutralize(ts_rank(sign(A - B), 7) * (1 - ts_rank(returns, 10)), industry)

Only A, B and returns are used.  No volume, fundamentals, analyst or other
non-price data are introduced.  The script generates the parameter/operator
grid and matches already completed local BRAIN results without submitting new
simulations.
"""

from __future__ import annotations

import json
import math
import sys
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_cmf_williams_campaign import (  # noqa: E402
    A,
    B,
    EPS,
    GROUP,
    REQUESTED_SETTINGS,
    flatten_result,
    make_target,
)
from brain_api import BrainClient  # noqa: E402


OUT_DIR = Path(__file__).resolve().parent / "output" / "cmf_williams_campaign" / "wjav9leg_focus"
TEMPLATE_PATH = ROOT / "templates" / "wjav9leg_focused_parameter_mining.json"
CANDIDATES_PATH = OUT_DIR / "candidates.json"
REPORT_PATH = OUT_DIR / "report.md"
EXPRESSIONS_PATH = OUT_DIR / "expressions.txt"
RESULTS_PATH = Path(__file__).resolve().parent / "output" / "cmf_williams_campaign" / "results.json"
FOCUSED_RESULTS_PATH = OUT_DIR / "simulation_results.json"

FIELD_WINDOWS = tuple(range(2, 11))
RETURN_WINDOWS = (10, 15, 20, 25, 30)
GAP = f"sign({A} - {B})"


def variants() -> list[dict[str, str]]:
    return [
        {
            "variant": "base_ts_rank",
            "description": "Direct parameter replacement around WjAv9LeG",
            "signal": "ts_rank({gap}, {field_window}) * (1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "rank_signal",
            "description": "Rank the signal after ts_rank; reversal leg unchanged",
            "signal": "rank(ts_rank({gap}, {field_window})) * (1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "dual_rank",
            "description": "Rank both signal and reversal legs",
            "signal": "rank(ts_rank({gap}, {field_window})) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "one_day_delayed_signal",
            "description": "One additional delay on the price-derived gap",
            "signal": "ts_rank(ts_delay({gap}, 1), {field_window}) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "delta_signal",
            "description": "One-day delta of the price-derived gap",
            "signal": "rank(ts_rank(ts_delta({gap}, 1), {field_window})) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "zscore_signal",
            "description": "Rolling z-score of the price-derived gap",
            "signal": "ts_zscore({gap}, {field_window}) * rank(1 - ts_rank(returns, {return_window}))",
        },
        {
            "variant": "rolling_zscore_signal",
            "description": "Rolling demean/std normalization of the price-derived gap",
            "signal": "(({gap} - ts_mean({gap}, {field_window})) / (ts_std_dev({gap}, {field_window}) + {epsilon})) * rank(1 - ts_rank(returns, {return_window}))",
        },
    ]


def make_candidates() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for spec in variants():
        for field_window in FIELD_WINDOWS:
            for return_window in RETURN_WINDOWS:
                signal = spec["signal"].format(
                    gap=GAP,
                    field_window=field_window,
                    return_window=return_window,
                    epsilon=EPS,
                )
                result.append(
                    {
                        "candidate_id": f"wjav9leg__{spec['variant']}__f{field_window}__r{return_window}",
                        "stage": "parameter_sweep" if spec["variant"] == "base_ts_rank" else "operator_nesting",
                        "family": "wjav9leg_signed_price_gap",
                        "variant": spec["variant"],
                        "description": spec["description"],
                        "field_window": field_window,
                        "return_window": return_window,
                        "template": GAP,
                        "expression": f"group_neutralize({signal}, {GROUP})",
                        "settings": dict(REQUESTED_SETTINGS),
                    }
                )
    return result


def load_results() -> list[dict[str, Any]]:
    if not RESULTS_PATH.exists():
        return []
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("results", [])


def load_focused_results(reset: bool = False) -> list[dict[str, Any]]:
    if reset or not FOCUSED_RESULTS_PATH.exists():
        return []
    data = json.loads(FOCUSED_RESULTS_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("results", [])


def save_focused_results(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FOCUSED_RESULTS_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def simulate_candidates(
    candidates: list[dict[str, Any]],
    max_concurrent: int = 3,
    batch_size: int = 15,
    max_retries: int = 1,
    reset: bool = False,
) -> list[dict[str, Any]]:
    """Submit focused candidates to BRAIN with resumable checkpoints."""
    existing = load_focused_results(reset=reset)
    by_id = {row.get("candidate_id"): row for row in existing if row.get("candidate_id")}
    pending = [
        candidate
        for candidate in candidates
        if candidate["candidate_id"] not in by_id
        or by_id[candidate["candidate_id"]].get("status") != "COMPLETE"
    ]
    print(f"[simulate] total={len(candidates)} pending={len(pending)} concurrency={max_concurrent}", flush=True)
    if not pending:
        return list(by_id.values())

    client = BrainClient(max_concurrent=max_concurrent, target=make_target())
    client.connect()
    for start in range(0, len(pending), batch_size):
        batch = pending[start : start + batch_size]
        print(f"[simulate] batch {start // batch_size + 1} size={len(batch)}", flush=True)
        for streamed in client.batch_simulate_stream(
            batch,
            max_concurrent=max_concurrent,
            max_retries=max_retries,
        ):
            candidate = {
                key: value
                for key, value in streamed.items()
                if key not in {"sim_result", "batch_idx"}
            }
            row = flatten_result(candidate, streamed.get("sim_result", {}))
            by_id[row["candidate_id"]] = row
            save_focused_results(list(by_id.values()))
            metrics = row.get("metrics") or {}
            print(
                f"[simulate] {row.get('status')} {row.get('candidate_id')} "
                f"alpha={row.get('alpha_id')} sharpe={metrics.get('sharpe')} "
                f"turnover={metrics.get('turnover')}",
                flush=True,
            )
    return list(by_id.values())


def metric(row: dict[str, Any], key: str) -> float | None:
    value = (row.get("metrics") or {}).get(key)
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def match_completed(candidates: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_expression = {
        row.get("expression"): row
        for row in rows
        if row.get("status") == "COMPLETE" and row.get("expression")
    }
    matched = []
    for candidate in candidates:
        row = by_expression.get(candidate["expression"])
        if row:
            matched.append({**candidate, "alpha_id": row.get("alpha_id"), "metrics": row.get("metrics", {}), "effective_settings": row.get("effective_settings", {})})
    return matched


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    keys = ("sharpe", "fitness", "turnover")
    pools = {key: sorted([metric(row, key) or 0.0 for row in rows]) for key in keys}

    def pct(pool: list[float], value: float | None) -> float:
        if not pool or value is None:
            return 0.0
        return sum(v <= value for v in pool) / len(pool)

    for row in rows:
        row["focused_score"] = round(
            0.45 * pct(pools["sharpe"], metric(row, "sharpe"))
            + 0.25 * pct(pools["fitness"], metric(row, "fitness"))
            + 0.30 * pct(pools["turnover"], metric(row, "turnover")),
            6,
        )
    return sorted(rows, key=lambda row: (row["focused_score"], metric(row, "sharpe") or -999), reverse=True)


def write_outputs(candidates: list[dict[str, Any]], matched: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ranked = rank_candidates(matched)
    TEMPLATE_PATH.write_text(
        json.dumps(
            {
                "name": "wjav9leg_focused_parameter_mining",
                "source_alpha": "WjAv9LeG",
                "anchor": f"group_neutralize(ts_rank({GAP}, 7) * (1 - ts_rank(returns, 10)), {GROUP})",
                "parameter_grid": {"field_window": list(FIELD_WINDOWS), "return_window": list(RETURN_WINDOWS)},
                "variants": variants(),
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
            f"[{row['candidate_id']}] {row['stage']} | {row['variant']} | field_window={row['field_window']} | return_window={row['return_window']}\n{row['expression']}"
            for row in candidates
        )
        + "\n",
        encoding="utf-8",
    )

    base = [row for row in matched if row["variant"] == "base_ts_rank"]
    best_base = sorted(base, key=lambda row: (metric(row, "sharpe") or -999, metric(row, "fitness") or -999), reverse=True)
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matched:
        by_variant[row["variant"]].append(row)

    lines = [
        "# WjAv9LeG focused alpha development",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Source alpha",
        "",
        f"`WjAv9LeG`: `group_neutralize(ts_rank({GAP}, 7) * (1 - ts_rank(returns, 10)), industry)`",
        "",
        "Interpretation: signed price-gap direction between the two supplied short-term price fields, ranked over time and interacted with short-term reversal in returns.",
        "",
        "## Scope",
        "",
        f"- Generated: **{len(candidates)}** candidates = 45 parameter replacements + 270 operator nests.",
        f"- Matched completed local BRAIN results: **{len(matched)}**.",
        f"- Base parameter results matched: **{len(base)}**.",
        "- Allowed inputs: `short_term_price_change_2`, `short_term_price_change`, `returns`; `industry` is used only as the reference grouping key.",
        "- No volume, fundamentals, analyst, capitalization or other external data were added.",
        "",
        "## Settings",
        "",
        "All candidates retain the source settings: GLB / TOPDIV3000 / Delay 1 / Market / Decay 20 / Truncation 0.08 / Pasteurization ON / Unit Verify / NaN ON / Max Trade OFF / Max Position OFF.",
        "",
        "## Best direct parameter replacements",
        "",
        "| Alpha | Field window | Returns window | Sharpe | Fitness | Turnover | Returns | Expression |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in best_base[:10]:
        m = row["metrics"]
        lines.append(
            f"| `{row.get('alpha_id')}` | {row['field_window']} | {row['return_window']} | {m.get('sharpe')} | {m.get('fitness')} | {m.get('turnover')} | {m.get('returns')} | `{row['expression']}` |"
        )

    lines += ["", "## Best operator nests", "", "| Variant | Alpha | Field window | Returns window | Sharpe | Fitness | Turnover |", "|---|---|---:|---:|---:|---:|---:|"]
    for variant, rows in sorted(by_variant.items()):
        if variant == "base_ts_rank":
            continue
        best = sorted(rows, key=lambda row: (metric(row, "sharpe") or -999, metric(row, "fitness") or -999), reverse=True)[:3]
        for row in best:
            m = row["metrics"]
            lines.append(f"| `{variant}` | `{row.get('alpha_id')}` | {row['field_window']} | {row['return_window']} | {m.get('sharpe')} | {m.get('fitness')} | {m.get('turnover')} |")

    lines += ["", "## Development conclusion", ""]
    if best_base:
        top = best_base[0]
        lines.append(f"The strongest direct replacement in the matched sample is `{top.get('alpha_id')}` with field window={top['field_window']} and returns window={top['return_window']}.")
    lines.append("Prioritize short returns windows 10–15 for turnover, then compare field windows 4, 7, 9 and 10; validate each operator nest separately because z-score/rolling normalization can materially change the signal distribution.")
    lines.append("IC is not included in the local BRAIN response schema; Sharpe, fitness, turnover and returns are reported without fabricating IC.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    candidates = make_candidates()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="Submit focused candidates to BRAIN")
    parser.add_argument("--limit", type=int, default=0, help="Only use the first N candidates; 0 uses all 315")
    parser.add_argument("--max-concurrent", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--reset", action="store_true", help="Ignore focused simulation checkpoint")
    args = parser.parse_args()

    if args.limit > 0:
        candidates = candidates[: args.limit]

    if args.simulate:
        simulated = simulate_candidates(
            candidates,
            max_concurrent=args.max_concurrent,
            batch_size=args.batch_size,
            max_retries=args.max_retries,
            reset=args.reset,
        )
        matched = [row for row in simulated if row.get("status") == "COMPLETE"]
    else:
        matched = match_completed(candidates, load_results())
    write_outputs(candidates, matched)
    print(f"generated={len(candidates)} matched_completed={len(matched)}")
    if args.simulate:
        print(f"simulation_results={FOCUSED_RESULTS_PATH}")
    print(f"template={TEMPLATE_PATH}")
    print(f"report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

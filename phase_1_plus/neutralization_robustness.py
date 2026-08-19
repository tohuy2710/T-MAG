#!/usr/bin/env python3
"""Simulate a two-layer neutralization robustness grid for the signed price gap.

It distinguishes the portfolio-level BRAIN setting from the group argument in
the formula. Every cell is GLB/TOPDIV3000/Delay 1, so its aggregate benchmark
and APAC, EMEA and AMER benchmark blocks are directly comparable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from research_target import ResearchTarget  # noqa: E402


OUT_DIR = Path(__file__).resolve().parent / "output" / "neutralization_robustness"
CANDIDATES_PATH = OUT_DIR / "candidates.json"
RESULTS_PATH = OUT_DIR / "results.json"
BENCHMARK_PATH = OUT_DIR / "benchmark_matrix.csv"
REPORT_PATH = OUT_DIR / "report.md"

# Four matched hierarchy levels form a compact 4 x 4 factorial experiment.
PLATFORM_NEUTRALIZATIONS = ("MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY")
FORMULA_GROUPS = ("market", "sector", "industry", "subindustry")
REGIONS = {"overall": None, "APAC": "glbApac", "EMEA": "glbEmea", "AMER": "glbAmer"}
METRICS = ("sharpe", "fitness", "turnover", "returns", "drawdown", "margin")
BASE_SETTINGS: dict[str, Any] = {
    "instrumentType": "EQUITY",
    "region": "GLB",
    "universe": "TOPDIV3000",
    "delay": 1,
    "decay": 20,
    "truncation": 0.08,
    "pasteurization": "ON",
    "unitHandling": "VERIFY",
    "nanHandling": "ON",
    "maxTrade": "OFF",
    "maxPosition": "OFF",
    "language": "FASTEXPR",
    "visualization": False,
}


def target() -> ResearchTarget:
    return ResearchTarget(
        name="neutralization-robustness-glb-topdiv3000-delay1",
        instrument_type="EQUITY",
        region="GLB",
        universe="TOPDIV3000",
        delay=1,
        neutralizations=PLATFORM_NEUTRALIZATIONS,
        excluded_dataset_ids=frozenset(),
        fields_path=ROOT / "references" / "wq_glb_topdiv3000_delay1_data_fields.json",
    )


def formula(group: str) -> str:
    return (
        "rank(group_neutralize(rank(ts_rank("
        "sign(short_term_price_change_2 - short_term_price_change), 2)) "
        f"* (1 - ts_rank(returns, 10)), {group}))"
    )


def make_candidates() -> list[dict[str, Any]]:
    rows = []
    for platform in PLATFORM_NEUTRALIZATIONS:
        for group in FORMULA_GROUPS:
            settings = {**BASE_SETTINGS, "neutralization": platform}
            digest = hashlib.sha1(f"neutralization-robustness|{platform}|{group}".encode()).hexdigest()[:12]
            rows.append(
                {
                    "candidate_id": digest,
                    "platform_neutralization": platform,
                    "formula_group": group,
                    "expression": formula(group),
                    "settings": settings,
                }
            )
    return rows


def read_results() -> list[dict[str, Any]]:
    if not RESULTS_PATH.exists():
        return []
    try:
        payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("results", []) if isinstance(payload, dict) else payload
    return rows if isinstance(rows, list) else []


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_results(rows: list[dict[str, Any]]) -> None:
    order_platform = {value: index for index, value in enumerate(PLATFORM_NEUTRALIZATIONS)}
    order_group = {value: index for index, value in enumerate(FORMULA_GROUPS)}
    rows.sort(key=lambda row: (order_platform.get(row.get("platform_neutralization"), 99), order_group.get(row.get("formula_group"), 99)))
    write_json(
        RESULTS_PATH,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "matrix": {"platform_neutralizations": PLATFORM_NEUTRALIZATIONS, "formula_groups": FORMULA_GROUPS},
            "results": rows,
        },
    )


def numeric(value: Any) -> float | None:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    return output if math.isfinite(output) else None


def metrics(block: Any) -> dict[str, float | None]:
    return {key: numeric(block.get(key)) if isinstance(block, dict) else None for key in METRICS}


def benchmarks(sim_data: Any) -> dict[str, dict[str, float | None]]:
    is_data = sim_data.get("is", {}) if isinstance(sim_data, dict) else {}
    return {
        label: metrics(is_data if source is None else is_data.get(source, {}))
        for label, source in REGIONS.items()
    }


def flatten(candidate: dict[str, Any], sim_result: dict[str, Any]) -> dict[str, Any]:
    sim_data = sim_result.get("sim_data", {}) if isinstance(sim_result, dict) else {}
    return {
        **candidate,
        "status": sim_result.get("status", "ERROR"),
        "alpha_id": sim_result.get("alpha_id"),
        "attempts": sim_result.get("attempts"),
        "error": sim_result.get("error"),
        "effective_settings": sim_data.get("settings", {}) if isinstance(sim_data, dict) else {},
        "benchmarks": benchmarks(sim_data),
        "sim_data": sim_data if isinstance(sim_data, dict) else {},
        "simulated_at": datetime.now(timezone.utc).isoformat(),
    }


def simulate(candidates: list[dict[str, Any]], rows: list[dict[str, Any]], max_concurrent: int, retry_noncomplete: bool) -> list[dict[str, Any]]:
    # Keep --dry-run usable in a lightweight Python environment. The shared
    # client imports numpy only when a real BRAIN submission is requested.
    from brain_api import BrainClient

    by_id = {row.get("candidate_id"): row for row in rows if row.get("candidate_id")}
    pending = [
        candidate for candidate in candidates
        if candidate["candidate_id"] not in by_id
        or (retry_noncomplete and by_id[candidate["candidate_id"]].get("status") != "COMPLETE")
    ]
    print(f"[robustness] total={len(candidates)} existing={len(by_id)} pending={len(pending)} concurrency={max_concurrent}", flush=True)
    if not pending:
        return list(by_id.values())

    client = BrainClient(max_concurrent=max_concurrent, target=target())
    client.connect()
    for streamed in client.batch_simulate_stream(pending, max_concurrent=max_concurrent, max_retries=1):
        candidate = {key: value for key, value in streamed.items() if key not in {"sim_result", "batch_idx"}}
        row = flatten(candidate, streamed.get("sim_result", {}))
        by_id[row["candidate_id"]] = row
        saved = list(by_id.values())
        save_results(saved)
        bench = row["benchmarks"]
        print(
            f"[robustness] {row['status']} platform={row['platform_neutralization']} group={row['formula_group']} "
            f"alpha={row.get('alpha_id')} GLB_S={bench['overall']['sharpe']} APAC_S={bench['APAC']['sharpe']} "
            f"EMEA_S={bench['EMEA']['sharpe']} AMER_S={bench['AMER']['sharpe']}",
            flush=True,
        )
    return list(by_id.values())


def value(row: dict[str, Any], region: str, metric: str) -> float | None:
    return numeric((row.get("benchmarks") or {}).get(region, {}).get(metric))


def regional_stats(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    sharpes = [value(row, region, "sharpe") for region in ("APAC", "EMEA", "AMER")]
    if any(item is None for item in sharpes):
        return None, None, None
    present = [item for item in sharpes if item is not None]
    return min(present), sum(present) / len(present), max(present) - min(present)


def robustness_sort(row: dict[str, Any]) -> tuple[float, float, float]:
    minimum, average, _ = regional_stats(row)
    return (minimum if minimum is not None else -math.inf, average if average is not None else -math.inf, value(row, "overall", "sharpe") or -math.inf)


def fnum(item: float | None) -> str:
    return "—" if item is None else f"{item:.4f}"


def write_benchmark_csv(rows: list[dict[str, Any]]) -> None:
    headers = ["candidate_id", "alpha_id", "status", "platform_neutralization", "formula_group", "expression"]
    headers += [f"{region.lower()}_{metric}" for region in REGIONS for metric in METRICS]
    headers += ["min_regional_sharpe", "mean_regional_sharpe", "regional_sharpe_spread", "error"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with BENCHMARK_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in sorted(rows, key=robustness_sort, reverse=True):
            output = {key: row.get(key, "") for key in headers[:6]}
            for region in REGIONS:
                for metric in METRICS:
                    output[f"{region.lower()}_{metric}"] = value(row, region, metric)
            output["min_regional_sharpe"], output["mean_regional_sharpe"], output["regional_sharpe_spread"] = regional_stats(row)
            output["error"] = row.get("error", "")
            writer.writerow(output)


def write_report(candidates: list[dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    complete = sorted((row for row in rows if row.get("status") == "COMPLETE"), key=robustness_sort, reverse=True)
    lines = [
        "# Neutralization robustness — signed price-gap alpha",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Design",
        "",
        "```text",
        "rank(group_neutralize(rank(ts_rank(sign(short_term_price_change_2 - short_term_price_change), 2)) * (1 - ts_rank(returns, 10)), <group>))",
        "```",
        "",
        f"- Factorial matrix: **{len(PLATFORM_NEUTRALIZATIONS)} × {len(FORMULA_GROUPS)} = {len(candidates)}** combinations.",
        f"- BRAIN setting `NEUTRALIZATION`: {', '.join(f'`{item}`' for item in PLATFORM_NEUTRALIZATIONS)}.",
        f"- Formula grouping: {', '.join(f'`{item}`' for item in FORMULA_GROUPS)}.",
        "- Fixed controls: GLB / TOPDIV3000 / Delay 1 / Decay 20 / Truncation 0.08 / Pasteurization ON / Unit Verify / NaN ON.",
        "- APAC, EMEA and AMER are the `glbApac`, `glbEmea` and `glbAmer` benchmark blocks from each GLB simulation, not separate universe simulations.",
        "",
        "## Completion and ranking",
        "",
        f"- Completed: **{len(complete)}/{len(candidates)}**.",
        "- Rows are ordered by minimum regional Sharpe, then mean regional Sharpe, then GLB Sharpe. This prevents a strong aggregate result from concealing a weak region.",
        "",
        "## Benchmark matrix",
        "",
        "`S` = Sharpe; `F` = Fitness; `R` = Returns; `TO` = Turnover. The CSV also includes drawdown and margin.",
        "",
        "| System NEUTRALIZATION | Formula group | Alpha | GLB S/F/R/TO | APAC S/F/R/TO | EMEA S/F/R/TO | AMER S/F/R/TO | Min regional S | S spread |",
        "|---|---|---|---|---|---|---|---:|---:|",
    ]
    for row in complete:
        cells = [
            " / ".join(fnum(value(row, region, metric)) for metric in ("sharpe", "fitness", "returns", "turnover"))
            for region in REGIONS
        ]
        minimum, _, spread = regional_stats(row)
        lines.append(
            f"| `{row['platform_neutralization']}` | `{row['formula_group']}` | `{row.get('alpha_id')}` | "
            f"{cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {fnum(minimum)} | {fnum(spread)} |"
        )
    if not complete:
        lines += ["| — | — | — | — | — | — | — | — | — |", "", "No completed simulations yet. Run with `--simulate` to populate the matrix."]
    lines += [
        "",
        "## Robustness rule",
        "",
        "Use `min_regional_sharpe` as the primary robustness filter and `regional_sharpe_spread` to reject geographically uneven candidates. The report records observations only; no acceptance threshold is assumed.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="Submit all missing matrix cells to BRAIN.")
    parser.add_argument("--dry-run", action="store_true", help="Generate the matrix and report without BRAIN calls.")
    parser.add_argument("--max-concurrent", type=int, default=3)
    parser.add_argument("--retry-noncomplete", action="store_true", help="Also resubmit cells with a prior non-complete result.")
    args = parser.parse_args()
    if args.simulate and args.dry_run:
        parser.error("Choose either --simulate or --dry-run.")
    if args.max_concurrent < 1:
        parser.error("--max-concurrent must be at least 1.")

    candidates = make_candidates()
    write_json(CANDIDATES_PATH, candidates)
    rows = read_results()
    if args.simulate:
        rows = simulate(candidates, rows, args.max_concurrent, args.retry_noncomplete)
    save_results(rows)
    write_benchmark_csv(rows)
    write_report(candidates, rows)
    print(f"[robustness] candidates={len(candidates)} completed={sum(row.get('status') == 'COMPLETE' for row in rows)}")
    print(f"[robustness] results={RESULTS_PATH}")
    print(f"[robustness] benchmarks={BENCHMARK_PATH}")
    print(f"[robustness] report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

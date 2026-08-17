#!/usr/bin/env python3
"""Generate and evaluate CMF/Williams %R alpha candidates.

The campaign is deliberately separate from the older phase_1_plus simulator:
that simulator uses a different neutralization/decay/NaN configuration.  This
module enforces the settings requested for this experiment at the BRAIN API
boundary and leaves the existing results untouched.

The BRAIN regular-alpha response exposes strategy metrics (Sharpe, fitness,
turnover, returns, drawdown), but normally does not expose cross-sectional IC.
The report therefore records IC as unavailable unless it is present in the API
response; it never estimates IC from cumulative PnL.
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
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from brain_api import BrainClient  # noqa: E402
from research_target import ResearchTarget  # noqa: E402


OUT_DIR = Path(__file__).resolve().parent / "output" / "cmf_williams_campaign"
CANDIDATES_PATH = OUT_DIR / "candidates.json"
RESULTS_PATH = OUT_DIR / "results.json"
REPORT_PATH = OUT_DIR / "report.md"
TOP10_PATH = OUT_DIR / "top10.csv"
EXPR_PATH = OUT_DIR / "evaluated_expressions.txt"

A = "short_term_price_change_2"
B = "short_term_price_change"
# Fast Expression accepts decimal literals but rejects scientific notation.
EPS = "0.000001"
GROUP = "industry"
RETURN_WINDOWS = (10, 15, 20, 25, 30)
FIELD_WINDOWS = tuple(range(2, 11))

# This is the exact requested runtime configuration.  No startDate/endDate is
# sent: in BRAIN, omitting those fields means use the platform's available
# history, which corresponds to TEST PERIOD = 0 YEARS 0 MONTHS here.
REQUESTED_SETTINGS: dict[str, Any] = {
    "instrumentType": "EQUITY",
    "region": "GLB",
    "universe": "TOPDIV3000",
    "delay": 1,
    "neutralization": "MARKET",
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


def make_target() -> ResearchTarget:
    """Build a local target that permits the requested MARKET setting."""
    return ResearchTarget(
        name="cmf-williams-glb-topdiv3000-delay1-market",
        instrument_type="EQUITY",
        region="GLB",
        universe="TOPDIV3000",
        delay=1,
        neutralizations=("MARKET",),
        excluded_dataset_ids=frozenset(),
        fields_path=ROOT / "references" / "wq_glb_topdiv3000_delay1_data_fields.json",
    )


def template_catalog() -> list[dict[str, str]]:
    """Return raw A/B templates, including single-field controls."""
    return [
        {"template_id": "A_plus_B", "template": f"({A} + {B})"},
        {"template_id": "A_minus_B", "template": f"({A} - {B})"},
        {"template_id": "B_minus_A", "template": f"({B} - {A})"},
        {"template_id": "A_times_B", "template": f"({A} * {B})"},
        {"template_id": "A_div_B_safe", "template": f"({A} / ({B} + {EPS}))"},
        {"template_id": "B_div_A_safe", "template": f"({B} / ({A} + {EPS}))"},
        {"template_id": "max_A_B", "template": f"max({A}, {B})"},
        {"template_id": "min_A_B", "template": f"min({A}, {B})"},
        {"template_id": "mean_A_B", "template": f"(({A} + {B}) / 2)"},
        {
            "template_id": "symmetric_gap",
            "template": f"(({A} - {B}) / (abs({A}) + abs({B}) + {EPS}))",
        },
        {"template_id": "absolute_gap", "template": f"abs({A} - {B})"},
        {"template_id": "signed_gap", "template": f"sign({A} - {B})"},
        {"template_id": "A_only", "template": A},
        {"template_id": "B_only", "template": B},
    ]


def _candidate_id(stage: str, template_id: str, field_window: int, return_window: int, variant: str) -> str:
    raw = f"{stage}|{template_id}|{field_window}|{return_window}|{variant}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _candidate(
    *,
    stage: str,
    template_id: str,
    template: str,
    field_window: int,
    return_window: int,
    variant: str,
    expression: str,
) -> dict[str, Any]:
    return {
        "candidate_id": _candidate_id(stage, template_id, field_window, return_window, variant),
        "stage": stage,
        "template_id": template_id,
        "template": template,
        "field_window": field_window,
        "return_window": return_window,
        "variant": variant,
        "expression": expression,
        "settings": dict(REQUESTED_SETTINGS),
    }


def generate_stage1() -> list[dict[str, Any]]:
    """Generate parameter replacements for all raw templates.

    The basic wrapper is intentionally not smoothed, because the objective is
    high turnover.  Group neutralization is retained from the reference alpha
    while the platform-level neutralization remains MARKET.
    """
    out: list[dict[str, Any]] = []
    for aw in FIELD_WINDOWS:
        for rw in RETURN_WINDOWS:
            for item in template_catalog():
                expr = (
                    f"group_neutralize(ts_rank({item['template']}, {aw}) * "
                    f"(1 - ts_rank(returns, {rw})), {GROUP})"
                )
                out.append(
                    _candidate(
                        stage="stage1_parameter_sweep",
                        template_id=item["template_id"],
                        template=item["template"],
                        field_window=aw,
                        return_window=rw,
                        variant="base_ts_rank",
                        expression=expr,
                    )
                )
    return out


def generate_stage2(seeds: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate consecutive-operator variants from selected stage-1 seeds."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for seed in seeds:
        t = seed["template"]
        aw = int(seed["field_window"])
        rw = int(seed["return_window"])
        wrappers = {
            "dual_rank": (
                f"group_neutralize(rank(ts_rank({t}, {aw})) * "
                f"rank(1 - ts_rank(returns, {rw})), {GROUP})"
            ),
            "rank_signal": (
                f"group_neutralize(rank(ts_rank({t}, {aw})) * "
                f"(1 - ts_rank(returns, {rw})), {GROUP})"
            ),
            "zscore_signal": (
                f"group_neutralize(ts_zscore({t}, {aw}) * "
                f"rank(1 - ts_rank(returns, {rw})), {GROUP})"
            ),
            "rolling_zscore_signal": (
                f"group_neutralize((({t} - ts_mean({t}, {aw})) / "
                f"(ts_std_dev({t}, {aw}) + {EPS})) * "
                f"rank(1 - ts_rank(returns, {rw})), {GROUP})"
            ),
            "one_day_delayed_signal": (
                f"group_neutralize(ts_rank(ts_delay({t}, 1), {aw}) * "
                f"rank(1 - ts_rank(returns, {rw})), {GROUP})"
            ),
            "delta_signal": (
                f"group_neutralize(rank(ts_delta({t}, 1)) * "
                f"rank(1 - ts_rank(returns, {rw})), {GROUP})"
            ),
            "mean_reversion_interaction": (
                f"group_neutralize(rank(ts_rank({t}, {aw})) * rank(ts_rank(returns, {rw})), {GROUP})"
            ),
        }
        for variant, expr in wrappers.items():
            item = _candidate(
                stage="stage2_operator_nesting",
                template_id=seed["template_id"],
                template=t,
                field_window=aw,
                return_window=rw,
                variant=variant,
                expression=expr,
            )
            if item["expression"] not in seen:
                seen.add(item["expression"])
                out.append(item)
    return out


def priority_key(candidate: dict[str, Any]) -> tuple[int, int, int, str]:
    """Prefer short windows and turnover-oriented templates deterministically."""
    template_order = {x["template_id"]: i for i, x in enumerate(template_catalog())}
    return (
        int(candidate.get("field_window", 99)),
        int(candidate.get("return_window", 99)),
        template_order.get(candidate.get("template_id", ""), 999),
        candidate.get("variant", ""),
    )


def select_balanced(candidates: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    """Keep a broad, deterministic slice when quota/latency requires a cap."""
    if not limit or len(candidates) <= limit:
        return candidates
    # Round-robin over (field_window, return_window) cells so the cap does not
    # accidentally test only the first template family.
    cells: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for item in candidates:
        cells.setdefault((item["field_window"], item["return_window"]), []).append(item)
    for cell in cells.values():
        cell.sort(key=lambda x: (x["template_id"], x["variant"]))
    selected: list[dict[str, Any]] = []
    ordered_cells = sorted(cells, key=lambda x: (x[0], x[1]))
    # First pass visits every parameter cell once; subsequent passes add
    # alternative templates to the same cells.  This guarantees that a cap
    # still covers every field/return window before spending budget on depth.
    max_cell_depth = max((len(cells[key]) for key in ordered_cells), default=0)
    for depth in range(max_cell_depth):
        for cell_index, cell_key in enumerate(ordered_cells):
            cell = cells[cell_key]
            if depth < len(cell):
                # Rotate template order by cell index so a small cap covers
                # the 14 template families instead of selecting the same
                # alphabetically-first family across every window cell.
                selected.append(cell[(depth + cell_index) % len(cell)])
                if len(selected) >= limit:
                    break
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        used = {x["candidate_id"] for x in selected}
        for item in sorted(candidates, key=priority_key):
            if item["candidate_id"] not in used:
                selected.append(item)
                if len(selected) >= limit:
                    break
    return selected[:limit]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def flatten_result(candidate: dict[str, Any], sim_result: dict[str, Any]) -> dict[str, Any]:
    data = sim_result.get("sim_data") or {}
    metrics = data.get("is") or {}
    effective = data.get("settings") or {}
    return {
        **candidate,
        "status": sim_result.get("status", "ERROR"),
        "alpha_id": sim_result.get("alpha_id"),
        "error": sim_result.get("error") or data.get("message"),
        "metrics": {
            "sharpe": metrics.get("sharpe"),
            "fitness": metrics.get("fitness"),
            "turnover": metrics.get("turnover"),
            "returns": metrics.get("returns"),
            "drawdown": metrics.get("drawdown"),
            "margin": metrics.get("margin"),
            "ic_mean": metrics.get("ic", metrics.get("informationCoefficient")),
            "ic_std": metrics.get("icStd", metrics.get("informationCoefficientStd")),
            "ic_ir": metrics.get("icIr", metrics.get("informationCoefficientIr")),
        },
        "effective_settings": effective,
        "sim_data": data,
        "simulated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_simulations(candidates: list[dict[str, Any]], existing: list[dict[str, Any]], max_concurrent: int) -> list[dict[str, Any]]:
    by_id = {r.get("candidate_id"): r for r in existing if r.get("candidate_id")}
    # A prior interrupted/rate-limited run may have stored an ERROR result;
    # retry those candidates on resume.  Completed simulations are immutable
    # checkpoints and are never re-submitted.
    pending = [
        c for c in candidates
        if c["candidate_id"] not in by_id or by_id[c["candidate_id"]].get("status") != "COMPLETE"
    ]
    if not pending:
        return list(by_id.values())

    print(f"[campaign] pending simulations: {len(pending)} | concurrency={max_concurrent}", flush=True)
    client = BrainClient(max_concurrent=max_concurrent, target=make_target())
    client.connect()
    for streamed in client.batch_simulate_stream(pending, max_concurrent=max_concurrent, max_retries=1):
        candidate = {k: v for k, v in streamed.items() if k not in {"sim_result", "batch_idx"}}
        result = flatten_result(candidate, streamed.get("sim_result", {}))
        by_id[result["candidate_id"]] = result
        save_json(RESULTS_PATH, list(by_id.values()))
        m = result["metrics"]
        print(
            f"[campaign] {result['status']} {result['candidate_id']} "
            f"sharpe={m.get('sharpe')} turnover={m.get('turnover')}",
            flush=True,
        )
    return list(by_id.values())


def _remote_expression(alpha: dict[str, Any]) -> str | None:
    regular = alpha.get("regular")
    if isinstance(regular, dict):
        code = regular.get("code")
        return str(code) if code else None
    if isinstance(regular, str):
        return regular
    return None


def recover_remote_matches(candidates: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recover completed exact-setting candidates from BRAIN after interruption.

    This is GET-only.  It is intentionally restricted to expressions in the
    current candidate set and verifies the key settings before accepting an
    alpha from the user's broader account.
    """
    by_expr = {c["expression"]: c for c in candidates}
    by_id = {r.get("candidate_id"): r for r in results if r.get("candidate_id")}
    client = BrainClient(max_concurrent=1, target=make_target())
    client.connect()
    # The endpoint rejects offsets beyond 1000 even when its count is larger;
    # recent campaign alphas are first, so fetch the supported recent window.
    remote: list[dict[str, Any]] = []
    for offset in range(0, 1100, 100):
        resp = client.get_with_retry(
            "https://api.worldquantbrain.com/users/self/alphas",
            params={"limit": 100, "offset": offset},
        )
        if resp.status_code != 200:
            print(f"[campaign] remote recovery stopped at offset={offset} status={resp.status_code}", flush=True)
            break
        payload = resp.json()
        batch = payload.get("results", payload.get("alphas", [])) if isinstance(payload, dict) else []
        if not isinstance(batch, list):
            break
        remote.extend(x for x in batch if isinstance(x, dict))
        if len(batch) < 100:
            break
    recovered = 0
    for alpha in remote:
        expr = _remote_expression(alpha)
        candidate = by_expr.get(expr or "")
        if not candidate:
            continue
        settings = alpha.get("settings") or {}
        if any(settings.get(k) != REQUESTED_SETTINGS[k] for k in ("region", "universe", "delay", "decay", "neutralization", "truncation", "pasteurization", "unitHandling", "nanHandling", "maxTrade", "maxPosition")):
            continue
        if candidate["candidate_id"] in by_id and by_id[candidate["candidate_id"]].get("status") == "COMPLETE":
            continue
        alpha_id = alpha.get("id")
        if not alpha_id:
            continue
        full = client.get_alpha(str(alpha_id)) or alpha
        recovered_result = flatten_result(
            candidate,
            {"status": "COMPLETE", "alpha_id": alpha_id, "sim_data": full},
        )
        by_id[candidate["candidate_id"]] = recovered_result
        recovered += 1
    print(f"[campaign] recovered remote exact-setting matches: {recovered}", flush=True)
    return list(by_id.values())


def numeric(result: dict[str, Any], key: str) -> float | None:
    value = (result.get("metrics") or {}).get(key)
    try:
        return float(value) if value is not None and math.isfinite(float(value)) else None
    except (TypeError, ValueError):
        return None


def percentile(values: list[float], value: float | None) -> float:
    if value is None or not values:
        return 0.0
    return float(sum(v <= value for v in values) / len(values))


def attach_pnl_correlations(results: list[dict[str, Any]], max_fetch: int = 30) -> None:
    complete = [r for r in results if r.get("status") == "COMPLETE" and r.get("alpha_id")]
    complete.sort(key=lambda r: numeric(r, "fitness") or -999, reverse=True)
    selected = complete[:max_fetch]
    if len(selected) < 2:
        return
    client = BrainClient(max_concurrent=1, target=make_target())
    client.connect()
    pnl: dict[str, np.ndarray] = {}
    for item in selected:
        values = client.fetch_pnl(str(item["alpha_id"]))
        if len(values) >= 3:
            # PnL recordsets are cumulative; correlate daily changes.
            pnl[item["candidate_id"]] = np.diff(np.asarray(values, dtype=float))
    for item in results:
        item["max_abs_pnl_corr"] = None
        item["pnl_correlations"] = {}
    for i, item in enumerate(selected):
        a = pnl.get(item["candidate_id"])
        if a is None:
            continue
        correlations: list[float] = []
        for other in selected[:i]:
            b = pnl.get(other["candidate_id"])
            if b is None:
                continue
            n = min(len(a), len(b))
            if n < 3 or np.std(a[-n:]) == 0 or np.std(b[-n:]) == 0:
                continue
            corr = abs(float(np.corrcoef(a[-n:], b[-n:])[0, 1]))
            correlations.append(corr)
            item["pnl_correlations"][other["candidate_id"]] = corr
            other.setdefault("pnl_correlations", {})[item["candidate_id"]] = corr
        item["max_abs_pnl_corr"] = max(correlations) if correlations else 0.0


def rank_results(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid = [r for r in results if r.get("status") == "COMPLETE" and numeric(r, "sharpe") is not None]
    sharpe_values = [numeric(r, "sharpe") or 0.0 for r in valid]
    fitness_values = [numeric(r, "fitness") or 0.0 for r in valid]
    turnover_values = [numeric(r, "turnover") or 0.0 for r in valid]
    for r in valid:
        r["ranking_score"] = round(
            0.45 * percentile(sharpe_values, numeric(r, "sharpe"))
            + 0.25 * percentile(fitness_values, numeric(r, "fitness"))
            + 0.30 * percentile(turnover_values, numeric(r, "turnover")),
            6,
        )
    ordered = sorted(valid, key=lambda r: (r.get("ranking_score", 0), numeric(r, "sharpe") or -999), reverse=True)
    diversified: list[dict[str, Any]] = []
    for item in ordered:
        pairwise = item.get("pnl_correlations") or {}
        if any(float(pairwise.get(other.get("candidate_id"), 0.0)) > 0.85 for other in diversified):
            continue
        diversified.append(item)
        if len(diversified) >= 10:
            break
    if len(diversified) < min(10, len(ordered)):
        for item in ordered:
            if item not in diversified:
                diversified.append(item)
            if len(diversified) >= 10:
                break
    return ordered, diversified


def write_top10(top10: list[dict[str, Any]]) -> None:
    fields = [
        "rank", "candidate_id", "stage", "template_id", "variant", "field_window",
        "return_window", "alpha_id", "sharpe", "fitness", "turnover", "returns",
        "drawdown", "ranking_score", "max_abs_pnl_corr", "expression",
    ]
    with TOP10_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rank, item in enumerate(top10, 1):
            row = {key: item.get(key, "") for key in fields}
            row["rank"] = rank
            metrics = item.get("metrics") or {}
            for key in ("sharpe", "fitness", "turnover", "returns", "drawdown"):
                row[key] = metrics.get(key)
            row["max_abs_pnl_corr"] = selected_max_corr(item, top10)
            writer.writerow(row)


def selected_max_corr(item: dict[str, Any], cohort: list[dict[str, Any]]) -> float:
    """Maximum absolute PnL correlation against the selected cohort only."""
    pairwise = item.get("pnl_correlations") or {}
    values = [
        float(pairwise[other["candidate_id"]])
        for other in cohort
        if other["candidate_id"] != item.get("candidate_id")
        and other["candidate_id"] in pairwise
    ]
    return max(values) if values else 0.0


def write_report(all_candidates: list[dict[str, Any]], results: list[dict[str, Any]], ordered: list[dict[str, Any]], top10: list[dict[str, Any]]) -> None:
    complete = [r for r in results if r.get("status") == "COMPLETE"]
    lines = [
        "# CMF + Williams %R alpha campaign",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Scope and settings",
        "",
        "The campaign uses the user-specified fields and exact runtime settings below:",
        "",
        "```text",
        json.dumps(REQUESTED_SETTINGS, ensure_ascii=False, indent=2),
        "TEST PERIOD = 0 YEARS 0 MONTHS (startDate/endDate omitted; platform history)",
        "```",
        "",
        "The expression-level `group_neutralize(..., industry)` is retained from the reference alpha; the platform-level setting remains `neutralization=MARKET`.",
        "The official operator spelling `ts_std_dev` is used for the requested rolling standard deviation transformation.",
        "",
        "## Experiment coverage",
        "",
        f"- Generated candidate definitions: **{len(all_candidates)}**",
        f"- Results recorded: **{len(results)}**",
        f"- Completed by BRAIN: **{len(complete)}**",
        f"- Non-completed: **{len(results) - len(complete)}**",
        "- Stage 1: 14 raw A/B templates (including A-only and B-only controls), field windows 2–10, return windows 10/15/20/25/30.",
        "- Stage 2: generator implemented for dual-rank, z-score, rolling-z-score, delay, delta and return-interaction nests; it was not submitted in this snapshot because BRAIN rate-limited new POSTs after the Stage 1 campaign.",
        "",
        "## Metric availability",
        "",
        "BRAIN returned strategy-level Sharpe, fitness, turnover, returns and drawdown. The API response did not expose cross-sectional daily IC in the observed schema, so `IC mean`, `IC std` and `IC IR` are reported as `N/A`; they must not be reconstructed from cumulative PnL.",
        "",
        "## Top 10 diversified candidates",
        "",
        "| # | Alpha | Sharpe | Fitness | Turnover | Returns | Max corr vs selected | Template / variant |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for i, item in enumerate(top10, 1):
        m = item.get("metrics") or {}
        lines.append(
            f"| {i} | `{item.get('alpha_id')}` | {m.get('sharpe')} | {m.get('fitness')} | "
            f"{m.get('turnover')} | {m.get('returns')} | {selected_max_corr(item, top10):.4f} | "
            f"`{item.get('template_id')}` / `{item.get('variant')}` |"
        )
    lines += ["", "## Evaluated expressions", "", "See `evaluated_expressions.txt` and `candidates.json` for every expression and parameter combination.", ""]
    if top10:
        lines += ["## Recommended 3–5 expressions", ""]
        for i, item in enumerate(top10[:5], 1):
            m = item.get("metrics") or {}
            lines += [
                f"### {i}. `{item.get('alpha_id')}`",
                "",
                f"`{item.get('expression')}`",
                "",
                f"Sharpe={m.get('sharpe')}, Fitness={m.get('fitness')}, Turnover={m.get('turnover')}, Returns={m.get('returns')}. "
                "Selected because the composite ranking gives 45% weight to Sharpe, 25% to fitness and 30% to turnover, with a correlation-diversification pass.",
                "",
            ]
    else:
        lines += ["## Recommended expressions", "", "No completed BRAIN simulations were available.", ""]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_expression_catalog(candidates: list[dict[str, Any]]) -> None:
    lines = []
    for item in candidates:
        lines.append(
            f"[{item['candidate_id']}] {item['stage']} | {item['template_id']} | "
            f"field_window={item['field_window']} | return_window={item['return_window']} | {item['variant']}\n"
            f"{item['expression']}"
        )
    EXPR_PATH.write_text("\n\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage1-limit", type=int, default=96)
    parser.add_argument("--stage2-limit", type=int, default=48)
    parser.add_argument("--max-concurrent", type=int, default=2)
    parser.add_argument("--no-stage2", action="store_true")
    parser.add_argument("--skip-pnl-correlation", action="store_true")
    parser.add_argument("--recover-only", action="store_true", help="Only recover matching completed remote alphas; never POST simulations")
    parser.add_argument("--report-only", action="store_true", help="Rebuild report from local candidates/results; no network calls")
    parser.add_argument("--reset", action="store_true", help="Ignore old campaign results; does not delete files")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stage1_all = generate_stage1()
    stage1 = select_balanced(stage1_all, args.stage1_limit)
    print(f"[campaign] stage1 generated={len(stage1_all)} selected={len(stage1)}", flush=True)

    if args.report_only:
        all_candidates = load_json(CANDIDATES_PATH, stage1)
        results = load_json(RESULTS_PATH, [])
        if not isinstance(all_candidates, list):
            all_candidates = stage1
        if not isinstance(results, list):
            results = []
        ordered, top10 = rank_results(results)
        write_expression_catalog(all_candidates)
        write_top10(top10)
        write_report(all_candidates, results, ordered, top10)
        print(f"[campaign] report-only complete={len([r for r in results if r.get('status') == 'COMPLETE'])}/{len(results)}", flush=True)
        print(f"[campaign] report={REPORT_PATH}", flush=True)
        return 0

    existing = [] if args.reset else load_json(RESULTS_PATH, [])
    if not isinstance(existing, list):
        existing = []
    stage1_results = existing if args.recover_only else run_simulations(stage1, existing, args.max_concurrent)
    stage1_results = recover_remote_matches(stage1, stage1_results)

    if args.recover_only:
        all_candidates = stage1
        results_by_id = {r.get("candidate_id"): r for r in stage1_results if r.get("candidate_id")}
        results = list(results_by_id.values())
        if not args.skip_pnl_correlation:
            attach_pnl_correlations(results)
        ordered, top10 = rank_results(results)
        save_json(CANDIDATES_PATH, all_candidates)
        save_json(RESULTS_PATH, results)
        write_expression_catalog(all_candidates)
        write_top10(top10)
        write_report(all_candidates, results, ordered, top10)
        print(f"[campaign] recover-only complete={len([r for r in results if r.get('status') == 'COMPLETE'])}/{len(results)}", flush=True)
        print(f"[campaign] report={REPORT_PATH}", flush=True)
        return 0

    stage2: list[dict[str, Any]] = []
    if not args.no_stage2:
        completed = [r for r in stage1_results if r.get("status") == "COMPLETE"]
        completed.sort(key=lambda r: (numeric(r, "fitness") or -999, numeric(r, "sharpe") or -999), reverse=True)
        seeds = completed[: max(1, min(12, len(completed)))]
        if not seeds:
            seeds = stage1[:12]
        stage2 = select_balanced(generate_stage2(seeds), args.stage2_limit)
        print(f"[campaign] stage2 generated={len(generate_stage2(seeds))} selected={len(stage2)}", flush=True)
        stage2_results = run_simulations(stage2, stage1_results, args.max_concurrent)
    else:
        stage2_results = stage1_results

    all_candidates = stage1 + stage2
    save_json(CANDIDATES_PATH, all_candidates)
    results_by_id = {r.get("candidate_id"): r for r in stage2_results if r.get("candidate_id")}
    results = list(results_by_id.values())
    if not args.skip_pnl_correlation:
        attach_pnl_correlations(results)
    ordered, top10 = rank_results(results)
    save_json(RESULTS_PATH, results)
    write_expression_catalog(all_candidates)
    write_top10(top10)
    write_report(all_candidates, results, ordered, top10)
    print(f"[campaign] complete={len([r for r in results if r.get('status') == 'COMPLETE'])}/{len(results)}", flush=True)
    print(f"[campaign] report={REPORT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

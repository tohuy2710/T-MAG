from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
import time
from pathlib import Path

import requests

from brain_api import create_session
from generate_candidates import FieldValidator
from research_target import ResearchTarget, load_target

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CREDENTIAL_PATH = SKILL_DIR / "credential.txt"
API_BASE = "https://api.worldquantbrain.com"

HEADERS = {
    "Accept": "application/json;version=2.0",
    "Content-Type": "application/json",
}

# ============================================================
# High-Turnover Alpha Pool — Aug 10-16 Power Pool Theme
# Theme: "High Turnover returns ratio test PASS" + datasets not in ['model110']
#
# Strategy:
#   - pv1 (close, returns, volume, open, vwap, etc.) is NOW allowed.
#   - target turnover 30–60% using short windows (5–21 days) on price/volume.
#   - BRAIN's HIGH_TURNOVER check triggers at ~25%+ TO; we need it to PASS
#     (i.e., returns justify the turnover). Keep Sharpe ≥ 1.25, Fitness ≥ 1.0.
#   - No neutralization restriction — all 5 neutralizations are valid.
#   - decay=0 or decay=2 to avoid decay collapsing the natural high-TO signal.
# ============================================================
ALPHAS = [
    # --- Short-term reversal (classic high-TO) ---
    {
        "name": "str_5d_reversal",
        "expression": "group_rank(-ts_sum(returns, 5), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "str_10d_reversal",
        "expression": "group_rank(-ts_sum(returns, 10), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "str_21d_reversal",
        "expression": "group_rank(-ts_sum(returns, 21), subindustry)",
        "decay": 2,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    # --- Idiosyncratic reversal (returns vs. market-relative) ---
    {
        "name": "idio_reversal_5d",
        "expression": "rank(-ts_sum(returns - ts_mean(returns, 63), 5))",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "idio_reversal_10d",
        "expression": "rank(-ts_sum(returns - ts_mean(returns, 63), 10))",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    # --- Volatility-adjusted reversal ---
    # Use ts_std_dev window=20 (not 63) — cheaper to compute on GLB TOPDIV3000,
    # avoids TIMEOUT while still capturing the vol-normalized reversal effect.
    {
        "name": "vol_adj_reversal_10d",
        "expression": "group_rank(-ts_sum(returns, 10) / (ts_std_dev(returns, 20) + 0.0001), industry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "INDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "vol_adj_reversal_5d",
        "expression": "group_rank(-ts_sum(returns, 5) / (ts_std_dev(returns, 20) + 0.0001), industry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "INDUSTRY",
        "nanHandling": "ON",
    },
    # --- Price momentum reversal ---
    {
        "name": "close_delta_reversal_5d",
        "expression": "group_rank(-ts_delta(close, 5) / close, subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "close_delta_reversal_10d",
        "expression": "group_rank(-ts_delta(close, 10) / close, subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    # --- Volume-price divergence (high TO signal) ---
    {
        "name": "vp_divergence_5d",
        "expression": "group_rank(-ts_corr(volume, close, 10), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "volume_surprise",
        "expression": "group_rank(-ts_delta(volume, 5) / (ts_std_dev(volume, 20) + 1), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    # --- Open-to-close intraday signal ---
    {
        "name": "intraday_reversal",
        "expression": "group_rank(-(close / open - 1), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "intraday_reversal_ma5",
        "expression": "group_rank(-ts_mean(close / open - 1, 5), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    # --- VWAP-based high turnover ---
    {
        "name": "vwap_reversal_5d",
        "expression": "group_rank(-(close / vwap - 1), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "vwap_momentum_5d",
        "expression": "group_rank(ts_sum(close / vwap - 1, 5), subindustry)",
        "decay": 0,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    # --- Mixed: fundamental anchor + technical reversal (high TO component drives theme) ---
    {
        "name": "reversal_quality_mix",
        "expression": "0.5 * group_rank(-ts_sum(returns, 10), subindustry) + 0.5 * group_rank(ts_rank(operating_income / equity, 63), subindustry)",
        "decay": 2,
        "truncation": 0.08,
        "neutralization": "SUBINDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "reversal_eps_mix",
        "expression": "0.6 * group_rank(-ts_sum(returns, 5), industry) + 0.4 * group_rank(ts_rank(est_eps / close, 126), industry)",
        "decay": 2,
        "truncation": 0.08,
        "neutralization": "INDUSTRY",
        "nanHandling": "ON",
    },
    {
        "name": "vol_reversal_profit_mix",
        "expression": "0.5 * rank(-ts_delta(close, 5) / close) + 0.5 * group_rank(ts_rank(ebitda / sales, 63), subindustry)",
        "decay": 2,
        "truncation": 0.08,
        "neutralization": "INDUSTRY",
        "nanHandling": "ON",
    },
]




def build_payload(alpha: dict, target: ResearchTarget, expression: str | None = None) -> dict:
    settings = target.settings_for(
        {
            "decay": alpha["decay"],
            "truncation": alpha["truncation"],
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": alpha.get("nanHandling", "ON"),
            "maxTrade": "OFF",
            "maxPosition": "OFF",
            "language": "FASTEXPR",
            "visualization": False,
        },
        neutralization=alpha["neutralization"],
    )
    return {
        "type": "REGULAR",
        "settings": settings,
        "regular": expression if expression is not None else alpha["expression"],
    }


def simulate_with_retry(
    session: requests.Session,
    alpha: dict,
    target: ResearchTarget,
    expression: str | None = None,
    max_retries: int = 10,
) -> dict:
    payload = build_payload(alpha, target, expression=expression)
    last_error = None

    for attempt in range(max_retries):
        try:
            resp = session.post(f"{API_BASE}/simulations", json=payload)
            if resp.status_code != 201:
                detail = resp.text[:300]
                if "CONCURRENT_SIMULATION_LIMIT_EXCEEDED" in detail or resp.status_code in (429, 500, 502, 503, 504):
                    last_error = f"{resp.status_code}: {detail}"
                    sleep_time = min(30, 8 * (attempt + 1))
                    time.sleep(sleep_time)
                    continue
                return {"error": f"simulate_failed: {resp.status_code}", "detail": detail}

            sim_id = resp.headers["Location"].rstrip("/").split("/")[-1]

            # Poll with extended timeout — GLB TOPDIV3000 simulations can take 20-30min
            start = time.time()
            while time.time() - start < 1800:  # 30 min per alpha
                data = session.get(f"{API_BASE}/simulations/{sim_id}").json()
                status = data.get("status", "UNKNOWN")
                if status == "COMPLETE":
                    alpha_id = data["alpha"]
                    return {"sim_id": sim_id, "alpha_id": alpha_id, "status": "COMPLETE"}
                if status in ("ERROR", "FAILED"):
                    return {"sim_id": sim_id, "status": "ERROR", "detail": str(data.get("message", ""))[:200]}
                time.sleep(8)
            return {"sim_id": sim_id, "status": "TIMEOUT"}

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
            last_error = str(e)
            time.sleep(5 * (attempt + 1))
            continue

    return {"error": f"all_retries_failed: {last_error}"}


def get_metrics(session: requests.Session, alpha_id: str) -> dict:
    try:
        resp = session.get(f"{API_BASE}/alphas/{alpha_id}")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def submit_alpha(session: requests.Session, alpha_id: str) -> dict:
    try:
        sub = session.post(f"{API_BASE}/alphas/{alpha_id}/submit")
        if sub.status_code not in (200, 201):
            return {"submitted": False, "status_code": sub.status_code}

        for _ in range(30):
            time.sleep(10)
            resp = session.get(f"{API_BASE}/alphas/{alpha_id}")
            if resp.status_code != 200:
                continue
            alpha = resp.json()
            status = alpha.get("status")
            if status == "ACTIVE":
                return {"submitted": True, "status": "ACTIVE", "alpha": alpha}
            checks = alpha.get("is", {}).get("checks", [])
            sc = next((c for c in checks if c.get("name") == "SELF_CORRELATION"), {})
            if sc.get("result") == "FAIL":
                return {"submitted": True, "status": status, "self_correlation": "FAIL"}
        return {"submitted": True, "status": "PENDING"}
    except Exception as e:
        return {"submitted": False, "error": str(e)}


def process_one_alpha(
    idx: int,
    total: int,
    alpha: dict,
    session: requests.Session,
    target: ResearchTarget,
    validator: FieldValidator,
) -> dict:
    name = alpha["name"]
    expr_short = alpha["expression"][:50]
    translated_expression = validator.translate_expression(alpha["expression"])

    if not validator.validate_expression(translated_expression):
        print(f"[{idx}/{total}] {name}: SKIP (uses missing or excluded field)", flush=True)
        return {
            "idx": idx,
            "name": name,
            "expression": alpha["expression"],
            "translated_expression": translated_expression,
            "neutralization": alpha["neutralization"],
            "sim": {"status": "SKIPPED_FIELD_VALIDATION"},
        }

    try:
        sim_result = simulate_with_retry(session, alpha, target, expression=translated_expression)
        if sim_result.get("status") != "COMPLETE":
            detail = sim_result.get("detail", "") or sim_result.get("error", "")
            print(f"[{idx}/{total}] {name}: SKIP ({sim_result.get('status')} {detail})", flush=True)
            return {
                "idx": idx,
                "name": name,
                "expression": alpha["expression"],
                "translated_expression": translated_expression,
                "sim": sim_result,
            }

        alpha_id = sim_result["alpha_id"]
        metrics = get_metrics(session, alpha_id)
        is_ = metrics.get("is", {})
        sharpe = is_.get("sharpe", 0) or 0
        fitness = is_.get("fitness", 0) or 0
        turnover = is_.get("turnover", 1) or 1
        returns_val = is_.get("returns", 0) or 0
        drawdown = is_.get("drawdown", 0) or 0

        checks = is_.get("checks", [])
        failed = [c["name"] for c in checks if c.get("result") == "FAIL"]

        entry = {
            "idx": idx,
            "name": name,
            "expression": alpha["expression"],
            "decay": alpha["decay"],
            "neutralization": alpha["neutralization"],
            "alpha_id": alpha_id,
            "sharpe": sharpe,
            "fitness": fitness,
            "turnover": turnover,
            "returns": returns_val,
            "drawdown": drawdown,
            "checks_failed": failed,
        }

        # High Turnover Pool theme gate:
        #   1. Basic metric bars: Sharpe >= 1.25, Fitness >= 1.0
        #   2. Turnover in the "high" range (>= 25%) so BRAIN triggers the check
        #   3. HIGH_TURNOVER check must NOT be in checks_failed
        #      (means returns justify the turnover — check triggered AND passed)
        high_to_check_passed = "HIGH_TURNOVER" not in failed
        is_high_turnover = turnover >= 0.25
        passes_theme = (
            fitness >= 1.0
            and sharpe >= 1.25
            and is_high_turnover
            and high_to_check_passed
        )
        if passes_theme:
            sub_result = submit_alpha(session, alpha_id)
            entry["submission"] = sub_result
            print(
                f"[{idx}/{total}] {name}: Sharpe={sharpe:.2f} Fitness={fitness:.2f} TO={turnover*100:.1f}% HIGH_TO=PASS -> SUBMITTED ({sub_result.get('status')})",
                flush=True,
            )
        else:
            reason = []
            if sharpe < 1.25: reason.append(f"Sharpe={sharpe:.2f}<1.25")
            if fitness < 1.0: reason.append(f"Fitness={fitness:.2f}<1.0")
            if not is_high_turnover: reason.append(f"TO={turnover*100:.1f}%<25%(not high)")
            if not high_to_check_passed: reason.append("HIGH_TURNOVER_check=FAIL")
            entry["submission"] = {"submitted": False, "reason": ", ".join(reason)}
            print(
                f"[{idx}/{total}] {name}: Sharpe={sharpe:.2f} Fitness={fitness:.2f} TO={turnover*100:.1f}% -> SKIP ({', '.join(reason)})",
                flush=True,
            )

        return entry

    except Exception as e:
        print(f"[{idx}/{total}] {name}: ERROR ({e})", flush=True)
        return {"idx": idx, "name": name, "expression": alpha["expression"], "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Run the Alpha101 v2 expressions for the configured research target")
    parser.add_argument(
        "--output",
        type=Path,
        default=SKILL_DIR / "alpha101_v2_glb_results.json",
        help="Result path (default preserves the historical USA result file)",
    )
    parser.add_argument("--target-config", type=Path, default=None)
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent workers (default: 2)")
    args = parser.parse_args()

    target = load_target(args.target_config)
    fields_path = target.require_fields_reference()
    validator = FieldValidator(fields_path, target.excluded_dataset_ids)
    print(f"Target: {target.describe()}")
    print(f"Running with concurrency={args.concurrency}")

    alphas = [
        {
            **alpha,
            "name": f"{alpha['name']}__{neutralization.lower()}",
            "neutralization": neutralization,
        }
        for alpha in ALPHAS
        for neutralization in target.neutralizations
    ]
    session = create_session()
    results = []

    total = len(alphas)
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(process_one_alpha, i, total, alpha, session, target, validator): i
            for i, alpha in enumerate(alphas, 1)
        }
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    results.sort(key=lambda r: r.get("idx", 0))

    # Save
    out_path = args.output
    if not out_path.is_absolute():
        out_path = SKILL_DIR / out_path
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"Results saved to: {out_path}")

    # Summary
    active = [r for r in results if r.get("submission", {}).get("status") == "ACTIVE"]
    submitted = [r for r in results if r.get("submission", {}).get("submitted") and r.get("submission", {}).get("status") != "ACTIVE"]
    good_metrics = [r for r in results if r.get("fitness", 0) >= 1.0 and r.get("sharpe", 0) >= 1.25]
    errors = [r for r in results if "error" in r or (r.get("sim", {}).get("status") in ("ERROR", "TIMEOUT"))]

    print(f"\n=== Summary ===")
    print(f"Total: {len(results)}")
    print(f"ACTIVE: {len(active)}")
    print(f"Submitted (not ACTIVE): {len(submitted)}")
    print(f"Passed metrics (not submitted): {len(good_metrics) - len(active)}")
    print(f"Errors/timeouts: {len(errors)}")

    if active:
        print("\n=== ACTIVE Alphas ===")
        for r in active:
            print(f"  {r['name']}: {r['alpha_id']} Sharpe={r['sharpe']:.2f} Fitness={r['fitness']:.2f} TO={r['turnover']*100:.1f}%")

    if good_metrics:
        print("\n=== Passed Metrics ===")
        for r in good_metrics:
            sub = r.get("submission", {})
            status = sub.get("status", "not_submitted")
            print(f"  {r['name']}: Sharpe={r['sharpe']:.2f} Fitness={r['fitness']:.2f} TO={r['turnover']*100:.1f}% -> {status}")


if __name__ == "__main__":
    main()

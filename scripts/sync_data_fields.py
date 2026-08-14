#!/usr/bin/env python3
"""Download the complete BRAIN field catalog for the configured target.

The catalog is intentionally stored unfiltered.  Candidate validation applies
``excluded_dataset_ids`` at runtime, while retaining the raw metadata makes the
exclusion auditable and easy to change later.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from brain_api import API_BASE, BrainClient
from research_target import ResearchTarget, load_target


def fetch_all_fields(client: BrainClient, target: ResearchTarget, page_size: int = 50) -> list[dict]:
    fields: list[dict] = []
    offset = 0
    while True:
        params = {
            "instrumentType": target.instrument_type,
            "region": target.region,
            "delay": target.delay,
            "universe": target.universe,
            "limit": page_size,
            "offset": offset,
        }
        response = client.get_with_retry(f"{API_BASE}/data-fields", params=params)
        if response.status_code != 200:
            raise RuntimeError(f"Field catalog request failed: HTTP {response.status_code} {response.text[:300]}")
        payload = response.json()
        batch = payload.get("results", [])
        if not isinstance(batch, list):
            raise RuntimeError("Field catalog response did not contain a results list")
        fields.extend(item for item in batch if isinstance(item, dict))
        total = payload.get("count")
        print(f"Fetched {len(fields)} field(s)" + (f" / {total}" if total is not None else ""), flush=True)
        if not batch or len(batch) < page_size or (isinstance(total, int) and len(fields) >= total):
            break
        offset += len(batch)
    return fields


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync BRAIN fields for the configured research target")
    parser.add_argument("--output", type=Path, default=None, help="Override the configured fields_reference path")
    args = parser.parse_args()

    target = load_target()
    output = args.output or target.fields_path
    if not output.is_absolute():
        output = Path.cwd() / output

    print(f"Target: {target.describe()}")
    client = BrainClient(target=target)
    client.connect()
    try:
        fields = fetch_all_fields(client, target)
    finally:
        if client.session:
            client.session.close()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(fields, indent=2, ensure_ascii=False), encoding="utf-8")
    datasets = Counter(
        str((field.get("dataset") or {}).get("id", "unknown")).lower() for field in fields
    )
    excluded = sum(datasets[dataset] for dataset in target.excluded_dataset_ids)
    print(f"Saved {len(fields)} fields to {output}")
    print(f"Validator will exclude {excluded} field(s) from datasets: {sorted(target.excluded_dataset_ids)}")


if __name__ == "__main__":
    main()

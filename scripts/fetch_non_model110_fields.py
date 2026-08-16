#!/usr/bin/env python3
"""Fetch BRAIN field catalog excluding model110 dataset.

Downloads all data fields for region=GLB, delay=1, universe=TOPDIV3000
and filters out any fields from the 'model110' dataset.
"""
from __future__ import annotations

import json
from pathlib import Path

from brain_api import API_BASE, BrainClient
from research_target import ResearchTarget


def fetch_fields_excluding_model110(
    client: BrainClient,
    region: str = "GLB",
    delay: int = 1,
    universe: str = "TOPDIV3000",
    instrument_type: str = "EQUITY",
    page_size: int = 50
) -> list[dict]:
    """Fetch all fields and filter out model110 dataset.
    
    Args:
        client: Authenticated BrainClient instance
        region: Market region (default: GLB)
        delay: Data delay (default: 1)
        universe: Stock universe (default: TOPDIV3000)
        instrument_type: Instrument type (default: EQUITY)
        page_size: Number of results per page (default: 50)
    
    Returns:
        List of field dictionaries excluding model110
    """
    all_fields: list[dict] = []
    offset = 0
    
    print(f"Fetching fields for region={region}, delay={delay}, universe={universe}...")
    print(f"Will exclude dataset: model110")
    
    while True:
        params = {
            "instrumentType": instrument_type,
            "region": region,
            "delay": delay,
            "universe": universe,
            "limit": page_size,
            "offset": offset,
        }
        
        response = client.get_with_retry(f"{API_BASE}/data-fields", params=params)
        
        if response.status_code != 200:
            raise RuntimeError(
                f"Field catalog request failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
        
        payload = response.json()
        batch = payload.get("results", [])
        
        if not isinstance(batch, list):
            raise RuntimeError("Field catalog response did not contain a results list")
        
        # Filter out model110 dataset
        filtered_batch = []
        for item in batch:
            if not isinstance(item, dict):
                continue
            
            dataset_id = (item.get("dataset") or {}).get("id", "")
            if dataset_id.lower() != "model110":
                filtered_batch.append(item)
        
        all_fields.extend(filtered_batch)
        
        total = payload.get("count")
        print(
            f"Fetched {len(all_fields)} field(s) (excluding model110)" +
            (f" / ~{total}" if total is not None else ""),
            flush=True
        )
        
        # Check if we're done
        if not batch or len(batch) < page_size:
            break
        # Don't stop based on total count - keep going until no more results
        
        offset += len(batch)
    
    return all_fields


def main() -> None:
    """Main entry point."""
    # Output path
    output_dir = Path(__file__).resolve().parent.parent / "references"
    output_path = output_dir / "wq_glb_topdiv3000_delay1_data_fields_no_model110.json"
    
    print("="*70)
    print("Fetching BRAIN Data Fields (Excluding model110)")
    print("="*70)
    print()
    
    # Create client
    print("Connecting to BRAIN...")
    client = BrainClient()
    client.connect()
    
    try:
        # Fetch fields
        fields = fetch_fields_excluding_model110(client)
        
        # Count datasets
        dataset_counts: dict[str, int] = {}
        for field in fields:
            dataset_id = (field.get("dataset") or {}).get("id", "unknown")
            dataset_counts[dataset_id] = dataset_counts.get(dataset_id, 0) + 1
        
        # Save to file
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(fields, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        print()
        print("="*70)
        print(f"✓ Saved {len(fields)} fields to:")
        print(f"  {output_path}")
        print()
        print("Dataset distribution:")
        for dataset, count in sorted(dataset_counts.items()):
            print(f"  - {dataset}: {count} fields")
        print("="*70)
        
    finally:
        if client.session:
            client.session.close()


if __name__ == "__main__":
    main()

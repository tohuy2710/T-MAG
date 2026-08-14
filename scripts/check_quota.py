#!/usr/bin/env python3
"""Check simulation quota and account info from BRAIN platform."""

import sys
import json
from pathlib import Path
from brain_api import BrainClient, logger
from research_target import load_target

def check_quota():
    """Fetch and display user quota info."""
    
    print("\n" + "=" * 70)
    print("  WorldQuant BRAIN — Quota & Account Info")
    print("=" * 70 + "\n")
    
    try:
        client = BrainClient()
        client.connect()
        print("✓ Connected to BRAIN API\n")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return 1
    
    # Fetch user profile
    try:
        print("[1] Fetching user profile...")
        resp = client.get_with_retry("https://api.worldquantbrain.com/users/self")
        if resp.status_code == 200:
            user = resp.json()
            print(f"    User ID: {user.get('id', 'unknown')}")
            print(f"    Email: {user.get('email', 'unknown')}")
            print(f"    Name: {user.get('name', 'unknown')}")
            print()
        else:
            print(f"    ✗ Status {resp.status_code}")
            print()
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
    
    # Fetch simulation quota
    try:
        print("[2] Fetching simulation quota...")
        resp = client.get_with_retry("https://api.worldquantbrain.com/users/self/simulationQuota")
        if resp.status_code == 200:
            quota = resp.json()
            print(f"    Daily limit: {quota.get('dailyLimit', 'unknown')}")
            print(f"    Used today: {quota.get('usedToday', 0)}")
            print(f"    Remaining today: {quota.get('remainingToday', 'unknown')}")
            print(f"    Total used: {quota.get('totalUsed', 'unknown')}")
            print()
        elif resp.status_code == 404:
            print(f"    Endpoint not found (try alternative)")
            print()
        else:
            print(f"    ✗ Status {resp.status_code}: {resp.text[:200]}")
            print()
    except Exception as e:
        logger.error(f"Error fetching quota: {e}")
    
    # Fetch user alphas count
    try:
        print("[3] Fetching user alphas...")
        resp = client.get_with_retry(
            "https://api.worldquantbrain.com/users/self/alphas",
            params={"limit": 1, "offset": 0}
        )
        if resp.status_code == 200:
            data = resp.json()
            # Try to get total count from headers or response
            total = data.get('totalCount', data.get('meta', {}).get('total', 'unknown'))
            print(f"    Total alphas: {total}")
            
            # Count by status if available
            if isinstance(data, dict) and 'alphas' in data:
                alphas = data['alphas']
            elif isinstance(data, list):
                alphas = data
            else:
                alphas = []
            
            if alphas:
                statuses = {}
                for a in alphas:
                    s = a.get('status', 'UNKNOWN')
                    statuses[s] = statuses.get(s, 0) + 1
                print(f"    Status breakdown: {statuses}")
            print()
        else:
            print(f"    ✗ Status {resp.status_code}")
            print()
    except Exception as e:
        logger.error(f"Error fetching alphas: {e}")
    
    # Fetch account info (catch-all endpoint)
    try:
        print("[4] Checking account endpoints...")
        endpoints = [
            "/users/self",
            "/users/self/account",
            "/users/self/quotas",
        ]
        
        for endpoint in endpoints:
            resp = client.get_with_retry(f"https://api.worldquantbrain.com{endpoint}")
            if resp.status_code == 200:
                print(f"    ✓ {endpoint}")
                data = resp.json()
                print(f"      {json.dumps(data, indent=8)[:500]}")
            elif resp.status_code != 404:
                print(f"    ✗ {endpoint}: {resp.status_code}")
        print()
    except Exception as e:
        logger.error(f"Error checking endpoints: {e}")
    
    print("=" * 70)
    print("\n💡 Tips:")
    print("  - Check daily simulation quota on BRAIN platform dashboard")
    print("  - View quota usage: https://platform.worldquantbrain.com/account/quota")
    print("  - Each simulation costs ~1 quota point")
    print("  - OBSERVE action = no quota cost (pre-filter)")
    print("  - SUBMIT action = costs quota (platform rejection)")
    print("\n")

if __name__ == "__main__":
    sys.exit(check_quota())

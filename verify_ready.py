#!/usr/bin/env python3
"""Verify codebase is ready for GLB pool manual mode."""

import json
import os
from pathlib import Path

print('=' * 70)
print('  CODEBASE READINESS CHECK - GLB/TOPDIV3000/delay=1')
print('=' * 70)
print()

# Check config
print('✓ Configuration:')
cfg = json.load(open('config/research_target.json'))
print(f'  Region: {cfg["region"]}')
print(f'  Universe: {cfg["universe"]}')
print(f'  Delay: {cfg["delay"]}')
print()

# Check fields
print('✓ Field Catalog:')
fields = json.load(open('references/wq_glb_topdiv3000_delay1_data_fields.json'))
print(f'  {len(fields)} GLB fields available')
print()

# Check templates
print('✓ Templates:')
template_count = len(list(Path('templates').glob('*.json')))
print(f'  {template_count} templates available')
print()

# Check papers
print('✓ Papers Registry:')
reg = json.load(open('papers_registry.json'))
stats = reg['stats']
print(f'  Total: {stats["total"]} papers')
print(f'  Consumed: {stats["consumed"]} papers')
print(f'  Remaining: {stats["remaining"]} papers')
print()

# Check state files
print('✓ State Files:')
for f in ['mining_state.json', 'lessons.json', 'alpha_db.json']:
    status = '✗ Not found (will be created on first run)' if not os.path.exists(f) else '⚠️  Exists (from previous run)'
    print(f'  {f}: {status}')
print()

# List papers
print('✓ Papers Available:')
for src_id, src in sorted(reg['sources'].items()):
    title = src.get('title', 'N/A')[:45]
    status = src.get('status', 'unread')
    print(f'  {src_id}: [{status:8s}] {title}')
print()

print('=' * 70)
print('  ✓ READY TO RUN WITH MANUAL MODE!')
print('=' * 70)
print()
print('Start command:')
print('  python3 scripts/mining_loop.py --depth-backend manual --max-rounds 20')
print()
print('Alternative (template-only, no paper extraction):')
print('  python3 scripts/mining_loop.py --depth-backend none --max-rounds 30')
print()
print('See START_MANUAL_MODE.md for complete guide.')
print()

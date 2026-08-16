#!/usr/bin/env python3
import sys
import logging
sys.path.insert(0, '../scripts')

# Set DEBUG level
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s [%(name)s] %(message)s')

from brain_api import BrainClient
from research_target import load_target

client = BrainClient()
client.connect()

target = load_target()

# Test expression từ bước 2
test_expr = 'ts_rank(short_term_price_change_2, 3) * (1 - ts_rank(returns, 5))'
settings = {'decay': 10}

print(f'\n=== Testing Expression ===')
print(f'Expression: {test_expr}')
print(f'Settings input: {settings}')

merged_settings = target.settings_for(settings)
print(f'\nMerged settings:')
for k, v in merged_settings.items():
    print(f'  {k}: {v}')

print(f'\n=== Submitting to BRAIN ===')
try:
    result = client.simulate(test_expr, settings)
    print(f'\nResult: {result.get("status")}')
    if result.get('status') == 'ERROR':
        print(f'Error: {result.get("error")}')
        print(f'Message: {result.get("message")}')
    else:
        print(f'Alpha ID: {result.get("alpha_id")}')
except Exception as e:
    print(f'\nException: {e}')
    import traceback
    traceback.print_exc()

# Quick Start - Per-Paper Mining (5 Minutes)

## TL;DR

Process each of 14 papers separately:
1. Generate extraction prompt
2. Copy → ChatGPT + Paper PDF → Get JSON
3. Feed JSON → Create templates
4. Run mining

---

## Commands (Copy-Paste Ready)

### Paper 1: alpha_101.pdf

```bash
# Terminal 1: Generate prompt
cd /Volumes/SSD-WDBlue/tohuy/y3s2/wq-modified
python3 scripts/generate_extraction_prompt.py src_001

# You'll get: _extraction_prompt_src_001.md
# File is filled and ready for LLM
```

Then:
1. Open https://chat.openai.com (or claude.ai)
2. Paste `_extraction_prompt_src_001.md` content
3. Upload or paste Paper 1 PDF
4. ChatGPT gives you JSON

Then:
```bash
# Terminal 1: Ingest the JSON
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001

# You'll get: ✓ All templates ingested successfully! (2 template(s) ready for mining)
```

Then:
```bash
# Terminal 1: Run mining loop
python3 scripts/mining_loop.py --max-rounds 10

# Breadth phase runs with new templates
# Takes ~1-2 hours
```

---

### Paper 2: A股市场的动量反转效应研究

```bash
# Same process:
python3 scripts/generate_extraction_prompt.py src_002

# Copy _extraction_prompt_src_002.md → ChatGPT (now has Paper 1's lessons!)
# Get JSON → Save

python3 scripts/ingest_extracted_templates.py extraction_output2.json --paper src_002

# Mining loop will use templates from BOTH papers
python3 scripts/mining_loop.py --max-rounds 10
```

---

## Repeat for Papers 3-14

Same 3 commands for each paper.

---

## Why This Works

| Before | After |
|--------|-------|
| 4h initial breadth (wasteful) | ✓ SKIP breadth (saves 4h) |
| All papers at once | ✓ Each paper isolated |
| Manual LLM prompts | ✓ Auto-generated prompts |
| Lessons at end only | ✓ Lessons accumulate between papers |

---

## Full Workflow Timeline

```
Paper 1:
  T+0m:   python3 scripts/generate_extraction_prompt.py src_001
  T+5m:   Copy → ChatGPT (with paper)
  T+15m:  Get JSON → Save
  T+20m:  python3 scripts/ingest_extracted_templates.py output.json --paper src_001
  T+25m:  python3 scripts/mining_loop.py --max-rounds 10
  T+85m:  ✓ Paper 1 done (2 ACTIVE alphas, lessons accumulated)

Paper 2:
  T+90m:  python3 scripts/generate_extraction_prompt.py src_002
          (prompt now includes lessons from Paper 1)
  T+95m:  Copy → ChatGPT
  T+105m: Get JSON
  T+110m: python3 scripts/ingest_extracted_templates.py output2.json --paper src_002
  T+115m: python3 scripts/mining_loop.py --max-rounds 10
  T+180m: ✓ Paper 2 done (3 ACTIVE alphas, lessons+ from Papers 1-2)

...continue for papers 3-14
```

**Total time for all 14 papers:** ~20-24 hours (running sequentially)

---

## Check Progress

```bash
# See papers status
python3 -c "
import json
reg = json.load(open('papers_registry.json'))
print(f'Consumed: {reg[\"stats\"][\"consumed\"]}/{reg[\"stats\"][\"total\"]}')
for src_id in sorted(reg['sources'].keys()):
    src = reg['sources'][src_id]
    print(f'  {src_id}: {src.get(\"status\")} → {len(src.get(\"templates_created\", []))} templates')
"

# See active alphas
python3 -c "
import json
db = json.load(open('alpha_db.json'))
active = [a for a in db.get('alphas', {}).values() if a.get('status') == 'ACTIVE']
print(f'Active alphas: {len(active)}')
for a in active[:5]:
    print(f'  {a[\"alpha_id\"]}: Sharpe={a.get(\"sharpe\", 0):.2f}')
"
```

---

## Files You'll Need

| What | Where |
|------|-------|
| Prompts (filled) | `_extraction_prompt_src_NNN.md` |
| Templates (created) | `templates/` (generated from JSON) |
| Registry (tracking) | `papers_registry.json` (updated) |
| Knowledge (accumulated) | `lessons.json` (grows with each paper) |

---

## If Something Goes Wrong

```bash
# Invalid JSON from ChatGPT?
python3 -m json.tool extraction_output.json
# Fix errors, retry

# Ingest failed?
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001 --validate
# Check error message, fix template, retry

# Mining loop stuck?
# Check papers_registry.json - are there unread papers?
# Press Ctrl+C, check logs, restart
```

---

## Alternative: Keep Initial Breadth (Optional)

If you want initial breadth phase (tests 31 existing templates first):

```bash
python3 scripts/mining_loop.py --keep-initial-breadth --max-rounds 30
# Round 1-3: Initial BREADTH (31 templates) ← 4 hours
# Round 4+:  Per-paper workflow
```

---

## Next: Full Guide

For complete documentation:
- **`START_MANUAL_MODE_PERCHUNK.md`** - Detailed step-by-step guide
- **`IMPLEMENTATION_SUMMARY_PERCHUNK.md`** - Technical overview
- **`PAPER_EXTRACTION_PROMPT.md`** - The master LLM prompt template

---

**Start now:**

```bash
python3 scripts/generate_extraction_prompt.py src_001
# Then copy _extraction_prompt_src_001.md to ChatGPT
```

🚀

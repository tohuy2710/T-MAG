# Per-Paper Mining Workflow

## Core Flow

Each of 14 papers = 1 independent mining chunk:

```
1. Generate extraction prompt
   python3 scripts/generate_extraction_prompt.py src_001
   → _extraction_prompt_src_001.md (filled)

2. [Manual] ChatGPT/Claude extraction
   Copy _extraction_prompt_src_001.md → ChatGPT + Paper PDF
   → Get JSON templates

3. Ingest templates
   python3 scripts/ingest_extracted_templates.py output.json --paper src_001
   → templates/alpha1_*.json

4. Run mining
   python3 scripts/mining_loop.py --max-rounds 10
   → BREADTH phase learns from templates

5. Repeat for papers 2-14
   (Each paper gets lessons from previous papers)
```

## Files

**Core:**
- `PAPER_EXTRACTION_PROMPT.md` - LLM template
- `scripts/generate_extraction_prompt.py` - Fill template
- `scripts/ingest_extracted_templates.py` - Process JSON
- `scripts/mining_loop.py` - Mining engine

**State:**
- `lessons.json` - Accumulated knowledge
- `alpha_db.json` - All alphas
- `papers_registry.json` - Paper tracking
- `mining_state.json` - Round state

**Reference:**
- `SKILL.md` - Domain knowledge
- `README.md` - Project overview
- `QUICK_START_PERCHUNK.md` - Quick reference
- `START_MANUAL_MODE_PERCHUNK.md` - Detailed guide

## Start

```bash
python3 scripts/generate_extraction_prompt.py src_001
```

See `QUICK_START_PERCHUNK.md` for details.

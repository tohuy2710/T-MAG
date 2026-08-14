# Setup Guide

## Installation

### 1. Clone/Setup Project

```bash
cd /Volumes/SSD-WDBlue/tohuy/y3s2/wq-modified
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Credentials

**Option A: Environment Variables (Recommended)**

```bash
export WQ_BRAIN_USERNAME="your_username"
export WQ_BRAIN_PASSWORD="your_password"
```

**Option B: Credential File**

Create `credential.txt` (git-ignored):
```json
["username", "password"]
```

### 5. Verify Installation

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Test imports
python3 -c "import PyPDF2, requests, pandas, numpy; print('✓ All dependencies installed')"

# Verify config
cat config/research_target.json
# Should show: GLB / TOPDIV3000 / delay=1
```

## Project Structure

```
repo/
├── REQUIREMENTS.md              # Detailed requirements (functional)
├── SETUP.md                     # This file
├── requirements.txt             # Python dependencies
├── WORKFLOW.md                  # Main workflow
├── QUICK_START_PERCHUNK.md     # 5-min quick start
├── START_MANUAL_MODE_PERCHUNK.md  # Detailed guide
├── SKILL.md                     # Domain knowledge
├── PAPER_EXTRACTION_PROMPT.md   # LLM template
│
├── config/
│   └── research_target.json     # Configuration: GLB/TOPDIV3000/delay=1
│
├── references/
│   └── wq_glb_topdiv3000_delay1_data_fields.json  # 10k fields
│
├── papers/
│   ├── alpha_101.pdf
│   ├── 1. A股市场的动量反转效应研究.pdf
│   └── ... (12 more papers)
│
├── templates/
│   ├── analyst_estimate_trend.json
│   ├── profitability_trend.json
│   └── ... (generated from papers)
│
├── scripts/
│   ├── mining_loop.py                    # Main engine
│   ├── generate_extraction_prompt.py     # Fill template
│   ├── ingest_extracted_templates.py     # Process JSON
│   ├── brain_api.py                      # BRAIN API wrapper
│   ├── generate_candidates.py            # Template expansion
│   ├── evolve_skill.py                   # Lessons update
│   └── ... (other utilities)
│
└── State Files (auto-generated):
    ├── lessons.json              # Accumulated knowledge
    ├── alpha_db.json             # All alphas
    ├── papers_registry.json      # Paper tracking
    └── mining_state.json         # Current round
```

## Running the System

### First Time: Per-Paper Mining

```bash
# Step 1: Generate extraction prompt for Paper 1
python3 scripts/generate_extraction_prompt.py src_001

# Step 2: [Manual] Extract with ChatGPT/Claude
# - Copy _extraction_prompt_src_001.md
# - Upload papers/alpha_101.pdf
# - Save JSON output

# Step 3: Ingest templates
python3 scripts/ingest_extracted_templates.py output.json --paper src_001

# Step 4: Run mining loop
python3 scripts/mining_loop.py --max-rounds 10

# Step 5: Repeat for papers 2-14
```

### Quick Commands

```bash
# Generate prompt for any paper
python3 scripts/generate_extraction_prompt.py src_NNN

# Validate JSON before ingesting
python3 -m json.tool extraction_output.json

# Ingest templates
python3 scripts/ingest_extracted_templates.py output.json --paper src_NNN

# Run mining
python3 scripts/mining_loop.py --max-rounds 20
python3 scripts/mining_loop.py --keep-initial-breadth  # With initial breadth

# Check status
python3 -c "import json; reg=json.load(open('papers_registry.json')); print(f'Remaining: {reg[\"stats\"][\"remaining\"]}')"
```

## Environment Variables (Optional)

```bash
# Logging
export WQ_LOG_LEVEL=INFO  # or DEBUG

# Mining parameters
export WQ_EXPLORE_EPSILON=0.15
export WQ_SKIP_REVIVAL_PROB=0.1
export WQ_GP_CHILDREN_PER_ROUND=30

# Target config
export WQ_TARGET_CONFIG=config/research_target.json
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'PyPDF2'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "credential.txt not found"

**Solution:** Use environment variables instead:
```bash
export WQ_BRAIN_USERNAME="your_username"
export WQ_BRAIN_PASSWORD="your_password"
```

### Issue: "JSON parsing error during ingestion"

**Solution:** Validate JSON first:
```bash
python3 -m json.tool extraction_output.json
# Fix errors, then retry
```

### Issue: "PDF text extraction failed"

**Cause:** PDF might be image-based (scanned)
**Solution:** Extract text manually or use OCR, then edit `_extraction_prompt_src_NNN.md` and paste text

## Next Steps

1. Read **QUICK_START_PERCHUNK.md** for 5-minute overview
2. Read **START_MANUAL_MODE_PERCHUNK.md** for detailed workflow
3. Start with Paper 1: `python3 scripts/generate_extraction_prompt.py src_001`

## Support

- **Configuration Issues**: Check `config/research_target.json`
- **Field Issues**: See `references/wq_glb_topdiv3000_delay1_data_fields.json`
- **Domain Questions**: See `SKILL.md`
- **Process Questions**: See `WORKFLOW.md` or `START_MANUAL_MODE_PERCHUNK.md`

---

Last Updated: August 13, 2026

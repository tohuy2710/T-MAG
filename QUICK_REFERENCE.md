# Per-Paper Mining Workflow - Quick Reference Card

## 🚀 Quick Start (Copy-Paste Ready)

### One Paper, Start to Finish
```bash
# 1. Generate prompt
python3 scripts/generate_extraction_prompt.py src_002

# 2. [Manual: Open _extraction_prompt_src_002.md in ChatGPT/Claude with PDF]
#    [Save JSON response to extraction.json]

# 3. Ingest and mine
python3 scripts/run_per_paper_workflow.py ingest src_002 extraction.json --mining-rounds 3
```

### Multiple Papers (Batch)
```bash
# Generate prompts
python3 scripts/run_per_paper_workflow.py batch --papers src_002,src_003,src_004,src_005,src_006

# [Manual: Extract all 5 papers with LLM in parallel]

# Ingest and mine all
for paper in src_002 src_003 src_004 src_005 src_006; do
    python3 scripts/run_per_paper_workflow.py ingest $paper extraction_${paper}.json --mining-rounds 2
done
```

### Interactive Menu
```bash
python3 scripts/run_per_paper_workflow.py interactive
```

---

## 📋 Command Cheat Sheet

| Task | Command |
|------|---------|
| Generate prompt | `python3 scripts/generate_extraction_prompt.py src_XXX` |
| Ingest + Mine | `python3 scripts/run_per_paper_workflow.py ingest src_XXX output.json --mining-rounds 3` |
| Full workflow | `python3 scripts/run_per_paper_workflow.py single src_XXX output.json --mining-rounds 3` |
| Batch prompts | `python3 scripts/run_per_paper_workflow.py batch --papers src_002,src_003,src_004` |
| Interactive | `python3 scripts/run_per_paper_workflow.py interactive` |
| Verify lessons | `python3 scripts/verify_lessons_update.py --rounds 1` |
| Mining only | `python3 scripts/mining_loop.py --max-rounds 5 --keep-initial-breadth` |
| Check status | `python3 -c "import json; print(json.loads(open('papers_registry.json').read())['sources'])"` |

---

## 📁 Key Files Overview

| File | Purpose | Format |
|------|---------|--------|
| `_extraction_prompt_src_NNN.md` | Filled prompt for LLM extraction | Markdown (20KB) |
| `templates/*.json` | Individual trading factor templates | JSON |
| `lessons.json` | Accumulated learning from mining | JSON (updated during mining) |
| `papers_registry.json` | Status of all papers | JSON |
| `mining_state.json` | Current mining loop state | JSON |
| `mining_report.json` | Results from last mining session | JSON |

---

## 🔄 Workflow Phases

```
Phase 1: Generate Prompt (5 min)
    ↓
Phase 2: Manual LLM Extraction (2-3 min)
    ↓
Phase 3: Ingest Templates (1 min)
    ↓
Phase 4: Mining Loop (30-90 min)
    ↓
Phase 5: Ready for Next Paper (or repeat)
```

---

## ✅ Verification Steps

### Before mining:
```bash
# 1. Check templates were ingested
ls templates/ | wc -l

# 2. Verify papers registry
python3 -c "import json; print(json.loads(open('papers_registry.json').read())['stats'])"

# 3. Check lessons.json state
python3 -c "import json; l=json.loads(open('lessons.json').read()); print(f'Patterns: {len(l[\"patterns\"])}, Experiments: {sum(p.get(\"tested\",0) for p in l[\"patterns\"].values())}')"
```

### After mining:
```bash
# 1. Check lessons were updated
python3 scripts/verify_lessons_update.py --compare-only

# 2. View mining report
python3 -c "import json; r=json.loads(open('mining_report.json').read()); print(f'Rounds: {r[\"total_rounds\"]}, Submitted: {r[\"total_submitted\"]}, Active: {len(r[\"active_alphas\"])}')"

# 3. Verify templates are ready for next paper
python3 -c "import json; print(f'Templates ready: {len([t for t in (json.loads(open(\"templates/\" + f).read()) for f in __import__(\"os\").listdir(\"templates\") if f.endswith(\".json\")) if isinstance(t, dict)])}')"
```

---

## 🐛 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "No module named 'PyPDF2'" | `pip install PyPDF2 requests pandas numpy python-dotenv` |
| "Paper not found" | Check paper ID format: `src_001` not `src_1` |
| Template validation failed | Check JSON format matches specification in guide |
| Mining timeout | Mining loop waits 30 min for depth response - may need to manually ingest next paper |
| lessons.json not updating | Normal if no active alphas produced - check mining report |
| Memory error | Reduce max candidates or max rounds |

---

## 📊 Monitoring

### Growth metrics:
```bash
# Patterns discovered
python3 -c "import json; print(f'Patterns: {len(json.loads(open(\"lessons.json\").read())[\"patterns\"])}')"

# Total experiments run
python3 -c "import json; l=json.loads(open('lessons.json').read()); print(f'Experiments: {sum(p.get(\"tested\",0) for p in l[\"patterns\"].values())}')"

# Active alphas
python3 -c "import json; print(f'Active: {sum(1 for a in json.loads(open(\"alpha_db.json\").read())[\"alphas\"].values() if a.get(\"status\")==\"ACTIVE\")}')"
```

### Papers status:
```bash
python3 -c "
import json
reg = json.loads(open('papers_registry.json').read())
for sid, entry in sorted(reg.get('sources', {}).items()):
    status = entry.get('status', 'pending')
    print(f'{sid:8} {status:20} {entry.get(\"title\", \"N/A\")[:40]}')
"
```

---

## ⚡ Optimization Tips

| Tip | Benefit |
|-----|---------|
| Batch generate prompts for 5 papers | Parallel LLM extraction |
| Use `--no-validate` after first successful ingest | Faster ingestion (if trusted source) |
| Reduce `max_candidates_per_round` for faster iterations | Faster mining rounds |
| Run verification script weekly | Monitor cumulative learning |
| Use different LLM for each extraction | Better template diversity |
| Extract templates while waiting for mining to complete | Maximize parallelism |

---

## 📈 Expected Results (Per Paper)

| Metric | Expected |
|--------|----------|
| Prompts generated | 1 |
| Templates extracted | 2-5 |
| Candidates per round | 60 |
| Mining rounds | 2-5 |
| Time to complete | 2-3 hours |
| New active alphas | 0-3 |
| Lessons updated | Yes |

---

## 🎯 Success Criteria

✅ Prompt generated successfully  
✅ LLM extraction returns valid JSON  
✅ All templates pass validation  
✅ Mining loop runs without errors  
✅ Lessons.json is updated after mining  
✅ No timeout errors during mining  
✅ Ready to proceed to next paper  

---

## 📚 Full Documentation

For complete details, see:
- `PER_PAPER_WORKFLOW_GUIDE.md` - Comprehensive 500+ line guide
- `IMPLEMENTATION_COMPLETE.md` - Implementation summary
- `QUICK_START_PERCHUNK.md` - 5-minute overview
- `START_MANUAL_MODE_PERCHUNK.md` - Vietnamese manual mode

---

## 🚨 When Things Go Wrong

### Mining loop waiting forever?
```bash
# Check if depth_request.json exists
ls -l depth_request.json

# Generate prompt for next paper to proceed
python3 scripts/generate_extraction_prompt.py src_007  # (next in line)

# Ingest that paper's templates to resume mining
python3 scripts/run_per_paper_workflow.py ingest src_007 extraction.json
```

### Lessons.json not updated?
```bash
# This may be normal if:
# 1. No candidates passed (all discarded)
# 2. Sharpe didn't improve
# 3. Mining produced no ACTIVE alphas

# To verify:
python3 scripts/verify_lessons_update.py --compare-only
python3 -c "import json; print(json.loads(open('mining_report.json').read())['total_submitted'])"
```

### Templates invalid?
```bash
# Re-ingest without validation (temporary fix)
python3 scripts/ingest_extracted_templates.py output.json --paper src_XXX --no-validate

# Or, fix JSON and re-ingest
# Common issues: missing fields, wrong field names, syntax errors
```

---

## 🎬 TL;DR (Super Quick)

1. `python3 scripts/generate_extraction_prompt.py src_XXX`
2. [Copy to ChatGPT + PDF, get JSON, save]
3. `python3 scripts/run_per_paper_workflow.py ingest src_XXX output.json --mining-rounds 3`
4. Wait for mining
5. Repeat for next paper

**Time per paper:** ~2-3 hours total  
**Total for 14 papers:** ~28-42 hours  
**Time saved vs old method:** 56 hours! 🎉

---

**Last Updated:** August 13, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅

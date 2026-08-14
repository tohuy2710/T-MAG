# Per-Paper Mining Workflow - Complete Guide

**Date:** August 13, 2026  
**Status:** ✅ FULLY IMPLEMENTED & TESTED  
**Language:** English (with Vietnamese where noted)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Detailed Workflow Steps](#detailed-workflow-steps)
5. [Scripts Reference](#scripts-reference)
6. [Verification & Monitoring](#verification--monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

---

## Overview

The per-paper mining workflow allows you to systematically extract trading factors from research papers and use them to discover new alpha factors. Instead of running one massive breadth phase followed by depth, this workflow:

1. **Generates** an extraction prompt for a specific paper
2. **Extracts** templates from the paper using an LLM (Claude/ChatGPT)
3. **Ingests** the extracted templates into the system
4. **Mines** using those templates, accumulating lessons for the next paper
5. **Repeats** for all papers, continuously improving the factor library

### Key Benefits

- ✅ **Saves ~4 hours** per paper (skips initial breadth phase)
- ✅ **Cumulative learning** - each paper builds on lessons from previous papers
- ✅ **Parallel extraction** - extract multiple papers simultaneously with LLM
- ✅ **Fine-grained control** - choose which papers to process and when
- ✅ **Complete traceability** - track which paper created which templates

---

## Architecture

### Data Flow

```
Paper PDF → Extract Prompt → LLM Extraction → JSON Templates
                                                      ↓
                                               Validation
                                                      ↓
                                            Template Files (JSON)
                                                      ↓
                                         Mining Loop (Breadth Phase)
                                                      ↓
                                           Lessons.json (Updated)
                                                      ↓
                                              Next Paper Prompt
                                                      ↓
                                         [Include lessons from prev paper]
```

### Key Files

| File | Purpose | Format |
|------|---------|--------|
| `PAPER_EXTRACTION_PROMPT.md` | Master template for LLM extraction | Markdown |
| `_extraction_prompt_src_NNN.md` | Filled prompt for specific paper | Markdown |
| `templates/*.json` | Individual template definitions | JSON |
| `lessons.json` | Accumulated learning from all mining | JSON |
| `papers_registry.json` | Status of all papers (pending/extracted/completed) | JSON |
| `mining_state.json` | Current mining loop state | JSON |
| `mining_report.json` | Report from last mining session | JSON |

### Scripts

| Script | Purpose | Language |
|--------|---------|----------|
| `generate_extraction_prompt.py` | Generate filled extraction prompt for paper | Python |
| `ingest_extracted_templates.py` | Validate and ingest templates from LLM JSON | Python |
| `mining_loop.py` (modified) | Run mining with per-paper support | Python |
| `run_per_paper_workflow.py` | Orchestrate entire workflow | Python |
| `verify_lessons_update.py` | Verify lessons.json updates | Python |

---

## Quick Start

### Prerequisites

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install PyPDF2 requests pandas numpy python-dotenv
```

### Minimal Workflow (One Paper)

```bash
# 1. Generate extraction prompt
python3 scripts/generate_extraction_prompt.py src_002

# 2. [MANUAL] Copy _extraction_prompt_src_002.md to ChatGPT/Claude
#    Paste with the paper PDF, get JSON response, save to extraction_src_002.json

# 3. Ingest and mine
python3 scripts/run_per_paper_workflow.py ingest src_002 extraction_src_002.json --mining-rounds 3
```

### Using Interactive Workflow

```bash
python3 scripts/run_per_paper_workflow.py interactive
# Menu-driven interface - follow prompts
```

---

## Detailed Workflow Steps

### Step 1: Generate Extraction Prompt

**Command:**
```bash
python3 scripts/generate_extraction_prompt.py src_001
```

**What it does:**
1. Loads the master `PAPER_EXTRACTION_PROMPT.md` template
2. Extracts first 10K characters from paper PDF
3. Summarizes top patterns from `lessons.json` (Vietnamese)
4. Lists available data fields from field catalog
5. Fills all placeholders and saves to `_extraction_prompt_src_NNN.md`

**Output:**
- `_extraction_prompt_src_001.md` (~20KB, ready for LLM)
- Log messages showing what was included

**Example:**
```
2026-08-13 16:06:36,460 INFO Generating extraction prompt for paper=src_001
2026-08-13 16:06:36,519 INFO Extracted PDF text chars=10000 pages=22
2026-08-13 16:06:36,560 INFO Generated extraction prompt path=.../_extraction_prompt_src_001.md
✓ Ready! Open this file and copy to ChatGPT:
   /path/to/_extraction_prompt_src_001.md
```

### Step 2: Extract Templates (Manual - LLM)

**Instructions:**

1. Open [ChatGPT](https://chat.openai.com) or [Claude](https://claude.ai)
2. Copy entire content of `_extraction_prompt_src_NNN.md`
3. Upload or paste the paper PDF
4. Send the prompt
5. Wait for LLM to generate JSON array of templates
6. Copy the JSON response and save to file (e.g., `extraction_output.json`)

**Expected JSON Format:**
```json
[
  {
    "template_id": "template_name",
    "description": "Brief description in Vietnamese",
    "skeleton": "expression with {placeholders}",
    "field_pairs": [
      {"price_field": "close"},
      {"price_field": "vwap"}
    ],
    "param_ranges": {
      "window": [5, 10, 20, 63]
    },
    "default_settings": {
      "decay": 2,
      "neutralization": "SUBINDUSTRY"
    }
  }
]
```

**Tips:**
- LLM usually generates 2-5 templates per paper
- Each template should have 5-10 variations for param_ranges
- Field names must match available fields from field catalog
- Typically takes 2-3 minutes for LLM to respond

### Step 3: Ingest Templates

**Command:**
```bash
python3 scripts/ingest_extracted_templates.py extraction_output.json --paper src_001
```

**What it does:**
1. Loads JSON array from LLM
2. Validates each template:
   - Checks required fields exist
   - Validates types and structure
   - Tests template expansion (generates 5 candidates)
   - Verifies candidates are valid
3. Saves each template to `templates/template_id.json`
4. Updates `papers_registry.json` with creation record

**Output:**
- Individual template JSON files in `templates/`
- Updated `papers_registry.json`
- Validation report with success/error count

**Example:**
```
70 templates ingested successfully
✓ All templates ingested successfully!
  36 template(s) ready for mining
```

**Validation Errors:**
- ✗ Missing required field (template_id, skeleton, etc.)
- ✗ field_pairs keys not in skeleton placeholders
- ✗ expand_template produced zero candidates
- ✗ Generated candidates have invalid syntax

### Step 4: Run Mining Loop

**Command:**
```bash
python3 scripts/mining_loop.py --max-rounds 5 --keep-initial-breadth
```

**What it does:**
1. Loads newly ingested templates
2. Generates candidates from templates
3. Runs breadth phase (submits to BRAIN API)
4. Observes results, updates lessons.json
5. When templates exhausted, triggers depth phase
6. Reads next paper → asks for extraction

**Key Options:**
- `--max-rounds N` - Run N mining rounds (default: 10)
- `--keep-initial-breadth` - Run breadth in round 1 (default: skip)
- `--dry-run` - Simulate without API calls
- `--reset-state` - Start fresh state file

**Output:**
- Logs showing candidates generated, submitted, observed
- Updated `lessons.json` with new experiment results
- `mining_report.json` with final statistics
- If templates exhausted: creates `depth_request.json` (waits for you)

**Example Log:**
```
[breadth] Building candidates (producer=template)...
[expand] template_1: 8 candidates (action=expand, max=8)
...
[breadth] Round 1 summary:
  Candidates: 60
  SUBMIT: 12 (new ACTIVE: 2)
  OBSERVE: 3
  DISCARD: 45
[lessons] Updated pattern 'template_1' (avg_sharpe: 0.82 → 0.91)
```

### Step 5: Prepare Next Paper

**The mining loop will:**
1. Continue with templates until pool is exhausted
2. Create `depth_request.json` asking for next paper extraction
3. Wait (up to 30 minutes) for `depth_response.json`
4. Resume mining with new templates

**You should:**
1. See the `depth_request.json` file
2. Generate prompt for next paper: `python3 scripts/generate_extraction_prompt.py src_002`
3. Extract templates using LLM (as in Step 2)
4. Ingest templates (as in Step 3)
5. Mining loop resumes automatically with new templates

---

## Scripts Reference

### generate_extraction_prompt.py

```bash
python3 scripts/generate_extraction_prompt.py PAPER_ID [--output PATH]

Arguments:
  PAPER_ID                Paper source ID (e.g., src_001, src_002)
  --output PATH          Output file path (default: _extraction_prompt_PAPER_ID.md)

Environment Variables:
  WQ_LOG_LEVEL           Logging level (DEBUG, INFO, WARNING, ERROR)
```

**Returns:** Path to generated prompt file

### ingest_extracted_templates.py

```bash
python3 scripts/ingest_extracted_templates.py JSON_FILE [--paper PAPER_ID] [--validate]

Arguments:
  JSON_FILE              Path to JSON array from LLM
  --paper PAPER_ID       Source paper ID for registry (e.g., src_001)
  --validate             Validate templates (default: enabled)
  --no-validate          Skip validation (not recommended)

Environment Variables:
  WQ_LOG_LEVEL           Logging level
```

**Returns:** Exit code 0 if all succeeded, 1 if errors

### mining_loop.py (Modified)

```bash
python3 scripts/mining_loop.py [OPTIONS]

Key Options:
  --max-rounds N         Maximum rounds (default: 10)
  --keep-initial-breadth Keep initial breadth phase (default: skip)
  --dry-run              Simulate without API calls
  --reset-state          Start fresh mining state
```

**New Feature:** `--keep-initial-breadth`
- Default: False (skips breadth in round 1, saves ~4 hours)
- True: Runs normal breadth phase (old behavior)

### run_per_paper_workflow.py

```bash
python3 scripts/run_per_paper_workflow.py COMMAND [OPTIONS]

Commands:
  interactive              Menu-driven workflow interface
  batch                    Generate prompts for multiple papers
  single PAPER_ID JSON     Full workflow for one paper
  ingest PAPER_ID JSON     Ingest + mine (templates already extracted)

Examples:
  # Interactive
  python3 scripts/run_per_paper_workflow.py interactive
  
  # Batch generate prompts
  python3 scripts/run_per_paper_workflow.py batch --papers src_001,src_002,src_003
  
  # Full workflow
  python3 scripts/run_per_paper_workflow.py single src_002 extraction.json --mining-rounds 5
  
  # Ingest only
  python3 scripts/run_per_paper_workflow.py ingest src_003 extraction.json --mining-rounds 3
```

### verify_lessons_update.py

```bash
python3 scripts/verify_lessons_update.py [--rounds N] [--timeout SEC] [--compare-only]

Options:
  --rounds N              Mining rounds to run (default: 2)
  --timeout SEC           Mining timeout in seconds (default: 3600)
  --compare-only          Only compare, don't run mining

Returns:
  Report showing:
  - New patterns added
  - Existing patterns improved
  - Sharpe ratio changes
  - Experiment count changes
```

---

## Verification & Monitoring

### Check Papers Registry Status

```bash
python3 -c "
import json
from pathlib import Path

reg = json.loads(Path('papers_registry.json').read_text())
for sid, entry in reg.get('sources', {}).items():
    status = entry.get('status', 'pending')
    title = entry.get('title', 'N/A')
    print(f'{sid}: {status:20} {title}')
"
```

### Monitor Lessons.json Growth

```bash
python3 -c "
import json
from pathlib import Path

lessons = json.loads(Path('lessons.json').read_text())
patterns = len(lessons.get('patterns', {}))
experiments = sum(p.get('tested', 0) for p in lessons.get('patterns', {}).values())
print(f'Patterns: {patterns}')
print(f'Experiments: {experiments}')
print(f'Avg experiments/pattern: {experiments/patterns:.1f}')
"
```

### Verify Lessons Updated

```bash
python3 scripts/verify_lessons_update.py --rounds 2 --compare-only
```

### Check Mining Report

```bash
python3 -c "
import json
from pathlib import Path

report = json.loads(Path('mining_report.json').read_text())
print(f\"Rounds:        {report.get('total_rounds', 0)}\")
print(f\"Submitted:     {report.get('total_submitted', 0)}\")
print(f\"Observed:      {report.get('total_observe', 0)}\")
print(f\"Active alphas: {len(report.get('active_alphas', {}))}\")
"
```

---

## Troubleshooting

### Issue: "No module named 'PyPDF2'"

**Solution:**
```bash
source venv/bin/activate
pip install PyPDF2 requests pandas numpy python-dotenv
```

### Issue: "Paper not found in registry"

**Solution:**
- Check paper ID is correct (e.g., src_001, not src_1)
- Verify papers_registry.json exists
- List available papers: grep "\"src_" papers_registry.json

### Issue: Template validation failed

**Common causes:**
1. Missing required fields in JSON (template_id, skeleton, param_ranges)
2. Field names in skeleton don't match field_pairs keys
3. Skeleton expression has invalid syntax
4. Field names don't exist in field catalog

**Solution:**
- Check LLM extraction output format
- Verify field names against reference fields
- Fix JSON and re-ingest: `--no-validate` to skip checks (temporary)

### Issue: Mining loop exits with "Pending handoff timeout"

**Cause:** You didn't provide depth response in time

**Solution:**
- Generate prompt for next paper
- Extract and ingest templates
- Mining loop will auto-resume within 30 minutes

### Issue: lessons.json not updating

**Cause:** Mining didn't produce active alphas (no new patterns to learn)

**Verification:**
```bash
python3 scripts/verify_lessons_update.py --compare-only
# Shows "No changes detected" if no learning occurred
```

**This is normal if:**
- Templates produced no ACTIVE alphas
- All candidates were discarded
- Sharpe ratios didn't improve

### Issue: Too many candidates, very slow mining round

**Solution:**
- Reduce max_candidates in mining_loop.py (around line 300)
- Reduce max_rounds and iterate faster
- Use --dry-run first to preview candidates

---

## Examples

### Example 1: Single Paper from Start to Finish

```bash
# 1. Generate prompt
python3 scripts/generate_extraction_prompt.py src_002

# 2. [Manual: Extract with LLM, save to extraction_src002.json]

# 3. Full workflow with mining
python3 scripts/run_per_paper_workflow.py single src_002 extraction_src002.json --mining-rounds 3
```

### Example 2: Batch Generate Prompts, Then Extract

```bash
# Generate prompts for 5 papers
python3 scripts/run_per_paper_workflow.py batch --papers src_002,src_003,src_004,src_005,src_006

# [Manual: Extract all in parallel using LLM]
# extraction_src002.json, extraction_src003.json, ...

# Ingest and mine each one
for i in 2 3 4 5 6; do
    python3 scripts/run_per_paper_workflow.py ingest src_00${i} extraction_src00${i}.json --mining-rounds 2
done
```

### Example 3: Verify Lessons Updated After Mining

```bash
# Before mining
python3 scripts/verify_lessons_update.py --compare-only

# Run mining
python3 scripts/mining_loop.py --max-rounds 2 --keep-initial-breadth

# After mining - see changes
python3 scripts/verify_lessons_update.py --rounds 0 --compare-only
```

### Example 4: Interactive Workflow

```bash
python3 scripts/run_per_paper_workflow.py interactive

# Menu appears:
# Options:
#   1. Generate extraction prompt for a paper
#   2. Ingest extracted templates from JSON
#   3. Run mining loop
#   4. Full workflow (1+2+3)
#   5. Check status
#   q. Quit

# [Follow prompts]
```

---

## Implementation Details

### How --keep-initial-breadth Works

**Default behavior (False):**
- Round 1 skips breadth phase entirely
- Sets `consecutive_no_active = 2` to trigger depth immediately
- **Result:** Saves ~4 hours, goes straight to "need more templates"

**With --keep-initial-breadth (True):**
- Round 1 runs normal breadth phase
- Explores existing templates before requesting depth
- **Result:** Normal behavior, but takes longer

**Decision logic (in mining_loop.py):**
```python
if not keep_initial_breadth and state.get("round", 0) == 0:
    state["consecutive_no_active"] = 2  # Skip breadth, go to depth
```

### How Lessons.json Accumulates

**During mining round:**
1. Candidates are generated from templates
2. Each candidate is submitted to BRAIN API
3. Results come back with sharpe, fitness, status
4. `brain_api.py` updates lessons.json:
   - Increments template's `tested` count
   - Updates `avg_sharpe`, `avg_fitness`
   - Tracks `best` alpha (highest sharpe)
   - Adjusts `action` (skip/deprioritize/expand)

**Lessons used for next paper:**
1. New extraction prompt loads lessons.json
2. `lessons_summary()` creates Vietnamese summary
3. Prompt highlights top patterns to look for
4. LLM uses this context when extracting new templates
5. Cycle repeats with better informed extraction

---

## Workflow Completion Checklist

- [x] generate_extraction_prompt.py implemented and tested
- [x] ingest_extracted_templates.py implemented and tested
- [x] mining_loop.py modified with --keep-initial-breadth flag
- [x] Template structure fixed (array → individual files)
- [x] run_per_paper_workflow.py created (4 workflow modes)
- [x] verify_lessons_update.py created (verification tool)
- [x] Documentation complete (this file)
- [x] End-to-end workflow tested and working

---

## Next Steps

1. **Generate prompts for all 14 papers:**
   ```bash
   python3 scripts/run_per_paper_workflow.py batch --papers src_001,src_002,src_003,...,src_014
   ```

2. **Extract templates in parallel** using multiple LLM instances (Claude.ai, ChatGPT, etc.)

3. **Ingest and mine systematically:**
   ```bash
   for i in 001 002 003 ... 014; do
       python3 scripts/run_per_paper_workflow.py ingest src_${i} extraction_src_${i}.json --mining-rounds 3
   done
   ```

4. **Monitor progress:**
   ```bash
   python3 verify_lessons_update.py --compare-only  # Check lessons growth
   python3 -c "..."  # Check registry status
   ```

5. **Iterate** - Each paper's lessons inform the next paper's extraction

---

## Support & Questions

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review relevant script documentation
3. Check log files in `*.log`
4. Examine error messages carefully

---

**Status:** ✅ All components implemented, tested, and documented  
**Ready for:** Per-paper mining at scale (14 papers)  
**Estimated time:** ~2 hours per paper (30 min extraction + 90 min mining)  
**Total capacity:** ~28 hours for full 14-paper workflow

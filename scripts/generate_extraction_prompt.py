#!/usr/bin/env python3
"""generate_extraction_prompt.py — Generate filled extraction prompt for a specific paper.

Usage:
  python3 scripts/generate_extraction_prompt.py src_001
  python3 scripts/generate_extraction_prompt.py src_002 --output custom_path.md

Outputs:
  _extraction_prompt_src_NNN.md — filled prompt ready for LLM

Flow:
  1. Load PAPER_EXTRACTION_PROMPT.md template
  2. Get paper content from papers_registry
  3. Extract text from PDF
  4. Summarize top patterns from lessons.json
  5. Build field catalog summary
  6. Fill all placeholders in template
  7. Save to _extraction_prompt_src_NNN.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import PyPDF2

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))

from research_target import load_target

# Paths
TEMPLATE_PATH = SKILL_DIR / "PAPER_EXTRACTION_PROMPT.md"
PAPERS_REGISTRY_PATH = SKILL_DIR / "papers_registry.json"
LESSONS_PATH = SKILL_DIR / "lessons.json"
FIELD_CATALOG_PATH = SKILL_DIR / "references" / "wq_glb_topdiv3000_delay1_data_fields.json"

LOG_LEVEL = os.getenv("WQ_LOG_LEVEL", "INFO").upper() if "os" in dir() else "INFO"
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger = logging.getLogger(__name__)

import os


def extract_pdf_text(pdf_path: Path, max_chars: int = 10000) -> str:
    """Extract text from PDF, up to max_chars."""
    if not pdf_path.exists():
        logger.warning("PDF not found path=%s", pdf_path)
        return ""
    
    try:
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                if len(text) >= max_chars:
                    break
                try:
                    page_text = page.extract_text()
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning("Failed to extract page page_num=%s error=%s", page_num, e)
                    continue
        
        # Truncate to max_chars
        text = text[:max_chars]
        logger.info("Extracted PDF text chars=%s pages=%s", len(text), len(reader.pages))
        return text
    except Exception as e:
        logger.error("Failed to extract PDF error=%s", e)
        return ""


def lessons_summary(lessons: dict, top_n: int = 5) -> str:
    """Create Vietnamese summary of top patterns from lessons.json."""
    patterns = lessons.get("patterns", {})
    
    # Filter viable patterns (not skipped)
    viable = [
        (tid, data) 
        for tid, data in patterns.items()
        if data.get("action") != "skip" and data.get("tested", 0) > 0
    ]
    
    if not viable:
        return "**Chưa có patterns nào thành công từ bài báo trước.**\n\n(Bây giờ là lần đầu tiên, hãy tạo templates từ bài báo này.)"
    
    # Sort by avg_fitness, then pass_rate, then avg_sharpe
    viable.sort(
        key=lambda x: (
            -x[1].get("avg_fitness", 0),
            -x[1].get("pass_rate", 0),
            -x[1].get("avg_sharpe", 0),
        )
    )
    
    top = viable[:top_n]
    
    summary_lines = [
        "### Những Template Thành Công (từ các bài báo trước)\n",
    ]
    
    for i, (tid, data) in enumerate(top, 1):
        tested = data.get("tested", 0)
        passed = data.get("passed", 0)
        pass_rate = data.get("pass_rate", 0)
        avg_sharpe = data.get("avg_sharpe", 0)
        avg_fitness = data.get("avg_fitness", 0)
        best_alpha = data.get("best", {})
        best_sharpe = best_alpha.get("sharpe", 0)
        
        summary_lines.append(f"\n**{i}. {tid}**")
        summary_lines.append(f"- Mô tả: {data.get('description', 'N/A')}")
        summary_lines.append(f"- Đã test: {tested} candidates")
        summary_lines.append(f"- Pass rate: {pass_rate:.1%} ({passed}/{tested})")
        summary_lines.append(f"- Avg Sharpe: {avg_sharpe:.3f}")
        summary_lines.append(f"- Avg Fitness: {avg_fitness:.3f}")
        if best_sharpe > 0:
            summary_lines.append(f"- Best Sharpe: {best_sharpe:.3f} (alpha_id: {best_alpha.get('alpha_id', 'N/A')})")
        summary_lines.append(f"- Hành động: {data.get('action', 'unknown').upper()}")
    
    summary_lines.append("\n")
    return "\n".join(summary_lines)


def field_catalog_summary(field_catalog: list, top_per_category: int = 10) -> str:
    """Create Vietnamese summary of field catalog."""
    # Group by category
    by_category = {}
    for field in field_catalog:
        cat_id = field.get("category", {}).get("id", "unknown")
        cat_name = field.get("category", {}).get("name", "Unknown")
        if cat_id not in by_category:
            by_category[cat_id] = {"name": cat_name, "fields": []}
        by_category[cat_id]["fields"].append(field)
    
    # Sort fields within each category by alphaCount (descending)
    for cat_data in by_category.values():
        cat_data["fields"].sort(
            key=lambda f: f.get("alphaCount", 0),
            reverse=True
        )
    
    summary_lines = [
        "### Danh Sách Trường Khả Dụng (Top theo alpha usage)\n",
    ]
    
    # Sort categories by total field count
    sorted_cats = sorted(
        by_category.items(),
        key=lambda x: len(x[1]["fields"]),
        reverse=True
    )
    
    for cat_id, cat_data in sorted_cats:
        cat_name = cat_data["name"]
        fields = cat_data["fields"][:top_per_category]
        
        summary_lines.append(f"\n#### {cat_name} ({len(cat_data['fields'])} total)")
        
        field_list = []
        for field in fields:
            field_id = field.get("id", "?")
            alpha_count = field.get("alphaCount", 0)
            coverage = field.get("coverage", 0)
            field_list.append(f"`{field_id}` (alphas: {alpha_count}, coverage: {coverage:.1%})")
        
        summary_lines.append(", ".join(field_list))
    
    summary_lines.append("\n")
    return "\n".join(summary_lines)


def load_template(template_path: Path) -> str:
    """Load template markdown."""
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def load_papers_registry(registry_path: Path) -> dict:
    """Load papers registry."""
    if not registry_path.exists():
        raise FileNotFoundError(f"Papers registry not found: {registry_path}")
    return json.loads(registry_path.read_text(encoding="utf-8"))


def load_lessons(lessons_path: Path) -> dict:
    """Load lessons.json."""
    if not lessons_path.exists():
        logger.warning("Lessons not found, using empty: %s", lessons_path)
        return {}
    return json.loads(lessons_path.read_text(encoding="utf-8"))


def load_field_catalog(catalog_path: Path) -> list:
    """Load field catalog."""
    if not catalog_path.exists():
        logger.warning("Field catalog not found: %s", catalog_path)
        return []
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def render_prompt(
    template: str,
    paper_title: str,
    paper_content: str,
    lessons_summary_text: str,
    field_catalog_text: str,
) -> str:
    """Fill placeholders in template."""
    result = template
    result = result.replace("{PAPER_TITLE}", paper_title or "Unknown")
    result = result.replace("{PAPER_CONTENT}", paper_content)
    result = result.replace("{LESSONS_TOP_PATTERNS}", lessons_summary_text)
    result = result.replace("{FIELD_CATALOG_SUMMARY}", field_catalog_text)
    return result


def generate_for_paper(paper_id: str, output_path: Path | None = None) -> Path:
    """Generate extraction prompt for a specific paper.
    
    Args:
        paper_id: Source ID, e.g., "src_001"
        output_path: Custom output path (default: _extraction_prompt_src_NNN.md)
    
    Returns:
        Path to generated prompt file
    """
    logger.info("Generating extraction prompt for paper=%s", paper_id)
    
    # Load registry
    registry = load_papers_registry(PAPERS_REGISTRY_PATH)
    if paper_id not in registry.get("sources", {}):
        raise ValueError(f"Paper not found in registry: {paper_id}")
    
    paper_entry = registry["sources"][paper_id]
    paper_locator = paper_entry.get("locator")
    paper_title = paper_entry.get("title", "Unknown")
    
    if not paper_locator:
        raise ValueError(f"Paper locator not found for {paper_id}")
    
    # Construct full paper path
    paper_path = SKILL_DIR / paper_locator
    logger.info("Loading paper path=%s", paper_path)
    
    # Extract paper content
    paper_content = extract_pdf_text(paper_path, max_chars=10000)
    if not paper_content:
        logger.warning("No content extracted from PDF, using placeholder")
        paper_content = f"[PDF content extraction failed for {paper_title}]"
    
    # Load template
    template = load_template(TEMPLATE_PATH)
    
    # Load lessons and create summary
    lessons = load_lessons(LESSONS_PATH)
    lessons_text = lessons_summary(lessons, top_n=5)
    
    # Load field catalog and create summary
    field_catalog = load_field_catalog(FIELD_CATALOG_PATH)
    catalog_text = field_catalog_summary(field_catalog, top_per_category=10)
    
    # Render prompt
    filled_prompt = render_prompt(
        template,
        paper_title,
        paper_content,
        lessons_text,
        catalog_text,
    )
    
    # Determine output path
    if output_path is None:
        output_path = SKILL_DIR / f"_extraction_prompt_{paper_id}.md"
    else:
        output_path = Path(output_path)
    
    # Write to file
    output_path.write_text(filled_prompt, encoding="utf-8")
    logger.info("Generated extraction prompt path=%s chars=%s", output_path, len(filled_prompt))
    
    print(f"✓ Extraction prompt generated: {output_path}")
    print(f"  Paper: {paper_title}")
    print(f"  Content: {len(paper_content)} characters")
    print(f"  File size: {len(filled_prompt)} characters")
    print(f"\n  Next step: Copy & paste this .md into ChatGPT/Claude with the paper PDF")
    print(f"  Then save the JSON output and use: ingest_extracted_templates.py")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate filled extraction prompt for a paper"
    )
    parser.add_argument(
        "paper_id",
        help="Paper source ID (e.g., src_001, src_002)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: _extraction_prompt_src_NNN.md)",
        default=None,
    )
    
    args = parser.parse_args()
    
    try:
        output_path = generate_for_paper(args.paper_id, args.output)
        print(f"\n✓ Ready! Open this file and copy to ChatGPT:\n   {output_path}")
    except Exception as e:
        logger.error("Failed to generate prompt: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

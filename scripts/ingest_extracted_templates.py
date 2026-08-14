#!/usr/bin/env python3
"""ingest_extracted_templates.py — Process JSON output from LLM extraction.

Usage:
  python3 scripts/ingest_extracted_templates.py output.json --paper src_001
  python3 scripts/ingest_extracted_templates.py output.json --paper src_002 --validate

Expects JSON format:
  [
    {
      "template_id": "...",
      "description": "...",
      "skeleton": "...",
      "field_pairs": [...],
      "param_ranges": {...},
      "default_settings": {...},
      ...
    }
  ]

Output:
  • Creates templates/template_id.json for each valid template
  • Updates papers_registry.json with template creation record
  • Prints validation report
  • Returns exit code 0 on success, 1 on errors
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))

from research_target import load_target
from generate_candidates import FieldValidator, expand_template
from data_discovery import DataDiscoveryEngine, FieldCatalog

# Paths
TEMPLATES_DIR = SKILL_DIR / "templates"
PAPERS_REGISTRY_PATH = SKILL_DIR / "papers_registry.json"
LESSONS_PATH = SKILL_DIR / "lessons.json"
DISCOVERY_CONFIG_PATH = SKILL_DIR / "config" / "discovery_config.json"

LOG_LEVEL = os.getenv("WQ_LOG_LEVEL", "INFO").upper()
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger = logging.getLogger(__name__)


def validate_template(template: dict, validator: FieldValidator, target) -> list[str]:
    """Validate a template JSON structure.
    
    Returns:
        List of error strings (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ["template_id", "description", "skeleton", "field_pairs", "param_ranges", "default_settings"]
    for field in required_fields:
        if field not in template:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return errors
    
    # Validate types
    if not isinstance(template.get("template_id"), str) or not template["template_id"].strip():
        errors.append("template_id must be non-empty string")
    
    if not isinstance(template.get("skeleton"), str) or not template["skeleton"].strip():
        errors.append("skeleton must be non-empty string")
    
    if not isinstance(template.get("field_pairs"), list) or not template["field_pairs"]:
        errors.append("field_pairs must be non-empty list")
    
    if not isinstance(template.get("param_ranges"), dict) or not template["param_ranges"]:
        errors.append("param_ranges must be non-empty dict")
    
    if not isinstance(template.get("default_settings"), dict):
        errors.append("default_settings must be dict")
    
    # Validate placeholders match field_pairs
    skeleton = template.get("skeleton", "")
    placeholders = set()
    import re
    for match in re.finditer(r'\{(\w+)\}', skeleton):
        placeholders.add(match.group(1))
    
    # Check that each placeholder has a field_pair entry
    for fp in template.get("field_pairs", []):
        if not isinstance(fp, dict):
            errors.append(f"field_pairs items must be dicts, got {type(fp)}")
            continue
        for placeholder_key in fp.keys():
            if placeholder_key not in placeholders:
                errors.append(f"field_pair key '{placeholder_key}' not found in skeleton placeholders")
    
    # Try to expand template and verify it produces valid candidates
    try:
        cands = expand_template(
            template,
            max_candidates=5,
            validator=validator,
            target=target,
        )
        if not cands:
            errors.append("expand_template produced zero candidates (check field_pairs and param_ranges)")
    except Exception as e:
        errors.append(f"expand_template raised error: {e}")
    
    return errors


def save_template(template: dict, output_dir: Path = TEMPLATES_DIR) -> Path:
    """Save template to templates/ directory.
    
    Args:
        template: Template dict
        output_dir: Output directory (default: templates/)
    
    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    template_id = template.get("template_id")
    output_path = output_dir / f"{template_id}.json"
    
    # Add metadata
    template_with_meta = dict(template)
    template_with_meta["_ingested_at"] = datetime.now(timezone.utc).isoformat()
    template_with_meta["_source"] = "llm_extraction"
    
    output_path.write_text(json.dumps(template_with_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved template path=%s", output_path)
    
    return output_path


def load_papers_registry(registry_path: Path) -> dict:
    """Load papers registry."""
    if not registry_path.exists():
        logger.warning("Papers registry not found, initializing: %s", registry_path)
        return {
            "version": 1,
            "sources": {},
            "stats": {"total": 0, "consumed": 0, "remaining": 0},
        }
    return json.loads(registry_path.read_text(encoding="utf-8"))


def save_papers_registry(registry: dict, registry_path: Path) -> None:
    """Save papers registry."""
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved papers registry path=%s", registry_path)


def ingest_templates(
    json_path: Path,
    paper_id: str | None = None,
    validate: bool = True,
    enable_discovery: bool = False,
    max_discovered_fields: int = 12,
) -> tuple[int, int, list]:
    """Ingest templates from JSON file.
    
    Args:
        json_path: Path to JSON file from LLM
        paper_id: Source paper ID (e.g., src_001) for registry tracking
        validate: Whether to validate templates
        enable_discovery: Whether to auto-discover field_pairs if missing (T-MAG v2.0)
        max_discovered_fields: Max fields to discover per template (default: 12)
    
    Returns:
        (success_count, error_count, error_messages, saved_templates)
    """
    logger.info(
        "Ingesting templates from json_path=%s paper_id=%s validate=%s discovery=%s",
        json_path, paper_id, validate, enable_discovery
    )
    
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    # Load JSON
    try:
        content = json_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    # Ensure it's a list
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")
    
    if not data:
        raise ValueError("JSON array is empty")
    
    logger.info("Loaded templates count=%s", len(data))
    
    # Load target and validator for validation
    target = load_target()
    validator = FieldValidator(
        target.require_fields_reference(),
        target.excluded_dataset_ids,
    )
    
    # Initialize discovery engine if enabled
    discovery_engine = None
    if enable_discovery:
        try:
            catalog = FieldCatalog.load(target.require_fields_reference())
            lessons_path = LESSONS_PATH if LESSONS_PATH.exists() else None
            config_path = DISCOVERY_CONFIG_PATH if DISCOVERY_CONFIG_PATH.exists() else None
            discovery_engine = DataDiscoveryEngine(
                catalog=catalog,
                lessons_path=lessons_path,
                config_path=config_path
            )
            logger.info("Discovery engine initialized (T-MAG v2.0 enabled)")
        except Exception as e:
            logger.warning("Failed to initialize discovery engine: %s", e)
            discovery_engine = None
    
    # Process each template
    success_count = 0
    error_count = 0
    error_messages = []
    saved_templates = []
    
    for i, template_data in enumerate(data):
        template_id = template_data.get("template_id", f"unknown_{i}")
        logger.info("Processing template[%d] template_id=%s", i, template_id)
        
        # Auto-discover field_pairs if enabled and missing
        if discovery_engine and (not template_data.get("field_pairs") or len(template_data.get("field_pairs", [])) == 0):
            skeleton = template_data.get("skeleton", "")
            if skeleton:
                logger.info(
                    "Auto-discovering field_pairs for template_id=%s (T-MAG v2.0)",
                    template_id
                )
                try:
                    discovered_field_pairs = discovery_engine.discover_fields(
                        skeleton=skeleton,
                        max_fields=max_discovered_fields,
                        per_placeholder=False
                    )
                    
                    if discovered_field_pairs:
                        # Remove metadata before storing
                        clean_field_pairs = [
                            {k: v for k, v in fp.items() if k != "_metadata"}
                            for fp in discovered_field_pairs
                        ]
                        template_data["field_pairs"] = clean_field_pairs
                        template_data["_discovery_enabled"] = True
                        
                        # Log pool distribution
                        pool_dist = discovery_engine.get_pool_distribution(discovered_field_pairs)
                        logger.info(
                            "Discovered %d field_pairs for template_id=%s: Pool A=%d, B=%d, C=%d",
                            len(clean_field_pairs),
                            template_id,
                            pool_dist.get("A", 0),
                            pool_dist.get("B", 0),
                            pool_dist.get("C", 0)
                        )
                    else:
                        logger.warning(
                            "Discovery produced no field_pairs for template_id=%s",
                            template_id
                        )
                except Exception as e:
                    logger.error(
                        "Discovery failed for template_id=%s: %s",
                        template_id,
                        e
                    )
        
        # Validate if requested
        if validate:
            errors = validate_template(template_data, validator, target)
            if errors:
                error_count += 1
                error_msg = f"Template[{i}] {template_id}: {'; '.join(errors)}"
                error_messages.append(error_msg)
                logger.warning(error_msg)
                continue
        
        try:
            # Save template
            saved_path = save_template(template_data)
            success_count += 1
            saved_templates.append(template_id)
            logger.info("Template saved template_id=%s path=%s", template_id, saved_path)
        except Exception as e:
            error_count += 1
            error_msg = f"Template[{i}] {template_id}: failed to save: {e}"
            error_messages.append(error_msg)
            logger.error(error_msg)
    
    # Update papers registry if paper_id provided
    if paper_id and saved_templates:
        try:
            registry = load_papers_registry(PAPERS_REGISTRY_PATH)
            if paper_id in registry.get("sources", {}):
                # Update the paper entry
                paper_entry = registry["sources"][paper_id]
                if "templates_created" not in paper_entry:
                    paper_entry["templates_created"] = []
                paper_entry["templates_created"].extend(saved_templates)
                paper_entry["extraction_completed_at"] = datetime.now(timezone.utc).isoformat()
                paper_entry["status"] = "templates_extracted"
                
                save_papers_registry(registry, PAPERS_REGISTRY_PATH)
                logger.info("Updated papers registry paper_id=%s templates=%s", paper_id, saved_templates)
        except Exception as e:
            logger.warning("Failed to update papers registry: %s", e)
    
    return success_count, error_count, error_messages, saved_templates


def print_report(success_count: int, error_count: int, error_messages: list, saved_templates: list):
    """Print ingestion report."""
    print("\n" + "=" * 70)
    print("INGEST REPORT")
    print("=" * 70)
    
    print(f"\n✓ Successful: {success_count}")
    for tid in saved_templates:
        print(f"  • {tid}")
    
    if error_count > 0:
        print(f"\n✗ Errors: {error_count}")
        for msg in error_messages:
            print(f"  • {msg}")
    
    print("\n" + "=" * 70)
    if error_count == 0:
        print("✓ All templates ingested successfully!")
        print(f"  {success_count} template(s) ready for mining")
    else:
        print(f"⚠  {success_count} succeeded, {error_count} failed")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest LLM-extracted templates into repository"
    )
    parser.add_argument(
        "json_file",
        type=Path,
        help="JSON file from LLM extraction (array of templates)",
    )
    parser.add_argument(
        "--paper",
        help="Source paper ID (e.g., src_001) for registry tracking",
        default=None,
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate templates before saving (default: True)",
        default=True,
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation (not recommended)",
        default=False,
    )
    parser.add_argument(
        "--enable-discovery",
        action="store_true",
        help="Enable T-MAG v2.0 auto field discovery (70-20-10 rule)",
        default=False,
    )
    parser.add_argument(
        "--max-discovered-fields",
        type=int,
        default=12,
        help="Max fields to discover per template (default: 12)",
    )
    
    args = parser.parse_args()
    
    validate = not args.no_validate
    
    try:
        success, errors, error_msgs, saved = ingest_templates(
            args.json_file,
            paper_id=args.paper,
            validate=validate,
            enable_discovery=args.enable_discovery,
            max_discovered_fields=args.max_discovered_fields,
        )
        
        print_report(success, errors, error_msgs, saved)
        
        if errors > 0 and success == 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

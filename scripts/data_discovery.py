#!/usr/bin/env python3
"""data_discovery.py — T-MAG v2.0 Data Discovery & Mutation Engine

Implements the 70-20-10 field selection rule for alpha factor discovery:
  - Pool A (70%): Exploitation - Semantic matching with high relevance
  - Pool B (20%): Cross-domain exploration - Related categories
  - Pool C (10%): Wildcard mutation - Type-safe random selection

This module transforms the system from a "theory copy machine" to a 
"true Quant researcher" capable of discovering Hidden Alphas.

Usage:
    from data_discovery import DataDiscoveryEngine, FieldCatalog
    
    catalog = FieldCatalog.load()
    engine = DataDiscoveryEngine(catalog, lessons_path="lessons.json")
    field_pairs = engine.discover_fields(
        skeleton="group_rank(ts_rank({profitability} / {scale}, {window}), {group})",
        max_fields=12
    )
"""
from __future__ import annotations

import json
import logging
import os
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Configuration & Constants
# --------------------------------------------------------------------------- #
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_FIELDS_PATH = SKILL_DIR / "references" / "wq_glb_topdiv3000_delay1_data_fields.json"
DEFAULT_CONFIG_PATH = SKILL_DIR / "config" / "discovery_config.json"

LOG_LEVEL = os.getenv("WQ_LOG_LEVEL", "INFO").upper()
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger = logging.getLogger(__name__)

# Default pool ratios (70-20-10 rule)
DEFAULT_POOL_RATIOS = {
    "exploitation": 0.7,   # Pool A: Theory-driven semantic matching
    "cross_domain": 0.2,   # Pool B: Related but different categories
    "wildcard": 0.1,       # Pool C: Type-safe random mutations
}

DEFAULT_COVERAGE_THRESHOLDS = {
    "pool_a": 0.8,  # High coverage for exploitation
    "pool_b": 0.7,  # Medium coverage for cross-domain
    "pool_c": 0.5,  # Lower coverage OK for wildcards
}

DEFAULT_SCORING_WEIGHTS = {
    "keyword_match": 0.5,   # How well keywords match description
    "coverage": 0.3,        # Data availability (0-1)
    "usage": 0.2,           # alphaCount/userCount popularity
}

# Cross-category exploration rules
# Maps primary category to related categories for cross-domain exploration
CROSS_CATEGORY_RULES = {
    "fundamental": ["analyst", "model"],          # Profits → Estimates
    "analyst": ["fundamental", "model"],          # Estimates → Actuals
    "technical": ["fundamental", "model"],        # Price → Value
    "model": ["fundamental", "analyst"],          # Models → Raw data
    "volume": ["sentiment", "options"],           # Trading → Interest
    "sentiment": ["volume", "fundamental"],       # Sentiment → Activity
    "options": ["volume", "technical"],           # Options → Price/Volume
}

# Known operators that require numerical data types
NUMERICAL_OPERATORS = {
    "rank", "group_rank", "ts_rank", "ts_mean", "ts_std_dev", "ts_delta",
    "ts_sum", "ts_corr", "ts_covariance", "abs", "log", "sqrt", "power",
    "zscore", "group_zscore", "normalize", "scale", "winsorize",
}

# Operators that can work with categorical or grouped data
CATEGORICAL_OPERATORS = {
    "group_rank", "group_mean", "group_neutralize", "group_zscore",
    "if_else", "trade_when",
}


# --------------------------------------------------------------------------- #
# Field Catalog - Index and query data fields
# --------------------------------------------------------------------------- #
class FieldCatalog:
    """Index and query the BRAIN data field catalog.
    
    Provides fast lookup by:
      - Field ID
      - Category (fundamental, analyst, technical, etc.)
      - Subcategory
      - Keywords in description
      - Coverage threshold
      - Data type (MATRIX for numerical)
    """
    
    def __init__(self, fields: list[dict[str, Any]]):
        """Initialize catalog from field list.
        
        Args:
            fields: List of field dictionaries from JSON catalog
        """
        self.fields = fields
        self.field_count = len(fields)
        
        # Build indexes for fast lookup
        self._build_indexes()
        
        logger.info(
            "FieldCatalog initialized fields=%d categories=%d",
            self.field_count,
            len(self.by_category)
        )
    
    def _build_indexes(self):
        """Build lookup indexes for efficient querying."""
        self.by_id = {f["id"]: f for f in self.fields if "id" in f}
        
        self.by_category = defaultdict(list)
        self.by_subcategory = defaultdict(list)
        self.by_dataset = defaultdict(list)
        
        for field in self.fields:
            # Category indexing
            category_id = (field.get("category") or {}).get("id")
            if category_id:
                self.by_category[category_id].append(field)
            
            # Subcategory indexing
            subcategory_id = (field.get("subcategory") or {}).get("id")
            if subcategory_id:
                self.by_subcategory[subcategory_id].append(field)
            
            # Dataset indexing
            dataset_id = (field.get("dataset") or {}).get("id")
            if dataset_id:
                self.by_dataset[dataset_id].append(field)
        
        # Build keyword index for semantic search
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build inverted index: keyword → [field_ids] for fast search."""
        self.keyword_index = defaultdict(list)
        
        for field in self.fields:
            field_id = field.get("id", "")
            description = field.get("description", "").lower()
            
            # Index field ID tokens
            for token in re.findall(r'[a-z_][a-z0-9_]+', field_id.lower()):
                if len(token) > 2:  # Skip very short tokens
                    self.keyword_index[token].append(field_id)
            
            # Index description tokens
            for token in re.findall(r'\b[a-z]{3,}\b', description):
                if len(token) > 3:  # Skip very short words
                    self.keyword_index[token].append(field_id)
        
        logger.debug(
            "Keyword index built with %d unique keywords",
            len(self.keyword_index)
        )
    
    @classmethod
    def load(cls, fields_path: Path | None = None) -> FieldCatalog:
        """Load catalog from JSON file.
        
        Args:
            fields_path: Path to field catalog JSON. If None, uses default.
        
        Returns:
            FieldCatalog instance
        """
        path = fields_path or DEFAULT_FIELDS_PATH
        
        if not path.exists():
            raise FileNotFoundError(f"Field catalog not found: {path}")
        
        data = json.loads(path.read_text(encoding="utf-8"))
        
        if isinstance(data, list):
            fields = data
        elif isinstance(data, dict) and "fields" in data:
            fields = data["fields"]
        else:
            raise ValueError(f"Invalid field catalog format in {path}")
        
        logger.info("Loaded field catalog from %s: %d fields", path, len(fields))
        return cls(fields)
    
    def get_field(self, field_id: str) -> dict[str, Any] | None:
        """Get field by ID.
        
        Args:
            field_id: Field identifier
        
        Returns:
            Field dict or None if not found
        """
        return self.by_id.get(field_id)
    
    def search_by_keywords(
        self, 
        keywords: list[str], 
        min_coverage: float = 0.0,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Search fields by keywords.
        
        Args:
            keywords: List of search keywords
            min_coverage: Minimum coverage threshold (0.0-1.0)
            limit: Maximum number of results
        
        Returns:
            List of matching fields, sorted by relevance
        """
        # Collect matching field IDs
        matching_field_ids = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Exact match
            if keyword_lower in self.keyword_index:
                matching_field_ids.update(self.keyword_index[keyword_lower])
            # Partial match (substring)
            for indexed_keyword, field_ids in self.keyword_index.items():
                if keyword_lower in indexed_keyword or indexed_keyword in keyword_lower:
                    matching_field_ids.update(field_ids)
        
        # Retrieve full field objects
        results = []
        for field_id in matching_field_ids:
            field = self.by_id.get(field_id)
            if field and field.get("coverage", 0) >= min_coverage:
                results.append(field)
        
        # Sort by coverage (prefer higher coverage)
        results.sort(key=lambda f: f.get("coverage", 0), reverse=True)
        
        return results[:limit]
    
    def get_by_category(
        self, 
        category_id: str, 
        min_coverage: float = 0.0
    ) -> list[dict[str, Any]]:
        """Get all fields in a category.
        
        Args:
            category_id: Category identifier (e.g., 'fundamental', 'analyst')
            min_coverage: Minimum coverage threshold
        
        Returns:
            List of fields in category
        """
        fields = self.by_category.get(category_id, [])
        if min_coverage > 0:
            fields = [f for f in fields if f.get("coverage", 0) >= min_coverage]
        return fields
    
    def get_numerical_fields(self, min_coverage: float = 0.5) -> list[dict[str, Any]]:
        """Get all numerical (MATRIX type) fields.
        
        Args:
            min_coverage: Minimum coverage threshold
        
        Returns:
            List of numerical fields
        """
        return [
            f for f in self.fields
            if f.get("type") == "MATRIX" and f.get("coverage", 0) >= min_coverage
        ]


# --------------------------------------------------------------------------- #
# Placeholder Analyzer - Extract and understand template placeholders
# --------------------------------------------------------------------------- #
class PlaceholderAnalyzer:
    """Analyze template skeleton to extract placeholders and infer semantic intent.
    
    Extracts placeholders like {profitability}, {scale}, {momentum} and infers:
      - Semantic keywords for field matching
      - Required data type based on operator context
      - Position in expression (numerator/denominator/argument)
    """
    
    def __init__(self, skeleton: str):
        """Initialize analyzer with template skeleton.
        
        Args:
            skeleton: Template expression with placeholders
        """
        self.skeleton = skeleton
        self.placeholders = self._extract_placeholders()
        self.semantic_keywords = self._infer_semantic_keywords()
        self.data_type_requirements = self._infer_data_types()
        
        logger.debug(
            "PlaceholderAnalyzer: found %d placeholders: %s",
            len(self.placeholders),
            list(self.placeholders)
        )
    
    def _extract_placeholders(self) -> set[str]:
        """Extract all {placeholder} names from skeleton.
        
        Returns:
            Set of placeholder names (without braces)
        """
        pattern = r'\{([^}]+)\}'
        placeholders = set(re.findall(pattern, self.skeleton))
        
        # Filter out param placeholders (these are filled differently)
        # Typical param names: window, group, decay, lag, etc.
        param_names = {
            "window", "group", "decay", "lag", "delay", "period", "days",
            "threshold", "alpha", "beta", "quantile", "percentile"
        }
        
        # Keep only field placeholders
        field_placeholders = {
            p for p in placeholders 
            if p not in param_names and not p.isdigit()
        }
        
        return field_placeholders
    
    def _infer_semantic_keywords(self) -> dict[str, list[str]]:
        """Infer semantic keywords from placeholder names.
        
        Extracts meaningful tokens from compound placeholder names.
        E.g., {profitability_metric} → ['profitability', 'metric']
        
        Returns:
            Dict mapping placeholder to list of keywords
        """
        keywords_map = {}
        
        for placeholder in self.placeholders:
            # Split by underscores and camelCase
            tokens = re.findall(r'[a-z]+', placeholder.lower())
            
            # Filter out common stopwords
            stopwords = {"the", "a", "an", "and", "or", "for", "to", "of", "in"}
            keywords = [t for t in tokens if t not in stopwords and len(t) > 2]
            
            # Add synonyms/related terms based on common patterns
            expanded_keywords = set(keywords)
            for keyword in keywords:
                expanded_keywords.update(self._get_synonyms(keyword))
            
            keywords_map[placeholder] = sorted(expanded_keywords)
        
        return keywords_map
    
    def _get_synonyms(self, keyword: str) -> set[str]:
        """Get synonyms and related terms for a keyword.
        
        Args:
            keyword: Single keyword
        
        Returns:
            Set of related terms
        """
        # Simple synonym mapping (can be extended)
        synonym_map = {
            "profitability": {"profit", "income", "earnings", "margin", "return"},
            "profit": {"profitability", "income", "earnings", "ebitda"},
            "income": {"profit", "earnings", "revenue", "sales"},
            "revenue": {"sales", "income", "turnover"},
            "sales": {"revenue", "income"},
            "momentum": {"trend", "change", "delta", "velocity", "acceleration"},
            "trend": {"momentum", "direction", "slope"},
            "volatility": {"variance", "stddev", "deviation", "risk"},
            "volume": {"turnover", "liquidity", "trading", "activity"},
            "liquidity": {"volume", "turnover", "depth"},
            "value": {"valuation", "price", "worth", "equity"},
            "scale": {"size", "magnitude", "normalization", "denominator"},
            "size": {"scale", "magnitude", "market_cap", "capitalization"},
            "quality": {"stability", "consistency", "reliability"},
            "growth": {"expansion", "increase", "acceleration"},
            "estimate": {"forecast", "prediction", "expectation", "consensus"},
            "forecast": {"estimate", "prediction", "projection"},
            "sentiment": {"opinion", "mood", "feeling", "attitude"},
        }
        
        return synonym_map.get(keyword, set())
    
    def _infer_data_types(self) -> dict[str, str]:
        """Infer required data type for each placeholder based on context.
        
        Analyzes operators around placeholder to determine if numerical
        data is required (e.g., inside ts_rank, math operations, etc.)
        
        Returns:
            Dict mapping placeholder to required type ('numerical' or 'any')
        """
        requirements = {}
        
        for placeholder in self.placeholders:
            # Find operators that use this placeholder
            pattern = rf'\b(\w+)\s*\([^)]*\{{{placeholder}\}}[^)]*\)'
            operators = re.findall(pattern, self.skeleton.lower())
            
            # Check if any operator requires numerical data
            requires_numerical = any(
                op in NUMERICAL_OPERATORS for op in operators
            )
            
            # Check position in expression
            # Denominators in divisions typically need numerical data
            is_denominator = self._is_denominator_position(placeholder)
            
            if requires_numerical or is_denominator:
                requirements[placeholder] = "numerical"
            else:
                requirements[placeholder] = "any"
        
        return requirements
    
    def _is_denominator_position(self, placeholder: str) -> bool:
        """Check if placeholder appears in denominator position.
        
        Args:
            placeholder: Placeholder name
        
        Returns:
            True if placeholder appears after division operator
        """
        # Look for patterns like "/ {placeholder}" or "/{placeholder}"
        pattern = rf'/\s*\{{{placeholder}\}}'
        return bool(re.search(pattern, self.skeleton))
    
    def get_keywords_for_placeholder(self, placeholder: str) -> list[str]:
        """Get semantic keywords for a specific placeholder.
        
        Args:
            placeholder: Placeholder name
        
        Returns:
            List of keywords for semantic search
        """
        return self.semantic_keywords.get(placeholder, [placeholder])
    
    def requires_numerical(self, placeholder: str) -> bool:
        """Check if placeholder requires numerical data type.
        
        Args:
            placeholder: Placeholder name
        
        Returns:
            True if numerical data required
        """
        return self.data_type_requirements.get(placeholder) == "numerical"


# --------------------------------------------------------------------------- #
# Configuration Manager
# --------------------------------------------------------------------------- #
class DiscoveryConfig:
    """Manage discovery configuration with defaults and overrides."""
    
    def __init__(self, config_path: Path | None = None):
        """Load configuration from file and environment variables.
        
        Args:
            config_path: Path to config JSON. If None, uses defaults.
        """
        # Start with defaults
        self.pool_ratios = DEFAULT_POOL_RATIOS.copy()
        self.coverage_thresholds = DEFAULT_COVERAGE_THRESHOLDS.copy()
        self.scoring_weights = DEFAULT_SCORING_WEIGHTS.copy()
        self.cross_category_rules = CROSS_CATEGORY_RULES.copy()
        
        # Load from file if exists
        if config_path and config_path.exists():
            self._load_from_file(config_path)
        
        # Override with environment variables
        self._load_from_env()
        
        # Validate configuration
        self._validate()
        
        logger.info(
            "DiscoveryConfig loaded: pool_ratios=%s",
            self.pool_ratios
        )
    
    def _load_from_file(self, config_path: Path):
        """Load configuration from JSON file."""
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            
            if "pool_ratios" in config:
                self.pool_ratios.update(config["pool_ratios"])
            if "coverage_thresholds" in config:
                self.coverage_thresholds.update(config["coverage_thresholds"])
            if "scoring_weights" in config:
                self.scoring_weights.update(config["scoring_weights"])
            if "cross_category_rules" in config:
                self.cross_category_rules.update(config["cross_category_rules"])
            
            logger.info("Loaded discovery config from %s", config_path)
        except Exception as e:
            logger.warning("Failed to load config from %s: %s", config_path, e)
    
    def _load_from_env(self):
        """Override config with environment variables."""
        # Pool ratios
        if ratio := os.getenv("WQ_DISCOVERY_POOL_A_RATIO"):
            self.pool_ratios["exploitation"] = float(ratio)
        if ratio := os.getenv("WQ_DISCOVERY_POOL_B_RATIO"):
            self.pool_ratios["cross_domain"] = float(ratio)
        if ratio := os.getenv("WQ_DISCOVERY_POOL_C_RATIO"):
            self.pool_ratios["wildcard"] = float(ratio)
        
        # Coverage thresholds
        if threshold := os.getenv("WQ_DISCOVERY_POOL_A_COVERAGE"):
            self.coverage_thresholds["pool_a"] = float(threshold)
    
    def _validate(self):
        """Validate configuration values."""
        # Check pool ratios sum to ~1.0
        total = sum(self.pool_ratios.values())
        if not (0.95 <= total <= 1.05):
            logger.warning(
                "Pool ratios sum to %.2f (expected ~1.0): %s",
                total,
                self.pool_ratios
            )
        
        # Check thresholds are in valid range
        for name, threshold in self.coverage_thresholds.items():
            if not (0.0 <= threshold <= 1.0):
                raise ValueError(
                    f"Invalid coverage threshold for {name}: {threshold} "
                    "(must be 0.0-1.0)"
                )
        
        # Check scoring weights sum to ~1.0
        total_weight = sum(self.scoring_weights.values())
        if not (0.95 <= total_weight <= 1.05):
            logger.warning(
                "Scoring weights sum to %.2f (expected ~1.0): %s",
                total_weight,
                self.scoring_weights
            )


# --------------------------------------------------------------------------- #
# Module Exports
# --------------------------------------------------------------------------- #
__all__ = [
    "FieldCatalog",
    "PlaceholderAnalyzer",
    "DiscoveryConfig",
    "DEFAULT_POOL_RATIOS",
    "DEFAULT_COVERAGE_THRESHOLDS",
    "DEFAULT_SCORING_WEIGHTS",
    "CROSS_CATEGORY_RULES",
]


# --------------------------------------------------------------------------- #
# Pool A: Semantic Field Matcher (Exploitation - 70%)
# --------------------------------------------------------------------------- #
class SemanticFieldMatcher:
    """Match fields based on semantic similarity using keyword scoring.
    
    Pool A (Exploitation): Selects fields with highest relevance to the
    placeholder's semantic intent. Uses hybrid keyword matching with
    coverage and usage scoring to find the most appropriate fields.
    
    Scoring Formula:
        score = 0.5 * keyword_match + 0.3 * coverage + 0.2 * usage
    
    Where:
        - keyword_match: How well field matches semantic keywords (0-1)
        - coverage: Data availability (dateCoverage field, 0-1)
        - usage: Popularity (normalized alphaCount, 0-1)
    """
    
    def __init__(
        self, 
        catalog: FieldCatalog, 
        config: DiscoveryConfig | None = None
    ):
        """Initialize semantic matcher.
        
        Args:
            catalog: Field catalog for searching
            config: Discovery configuration (uses defaults if None)
        """
        self.catalog = catalog
        self.config = config or DiscoveryConfig()
        
        # Extract scoring weights
        self.weights = self.config.scoring_weights
        
        # Precompute max values for normalization
        self._compute_normalization_factors()
        
        logger.debug("SemanticFieldMatcher initialized with weights=%s", self.weights)
    
    def _compute_normalization_factors(self):
        """Compute max values for normalizing usage scores."""
        max_alpha_count = max(
            (f.get("alphaCount", 0) for f in self.catalog.fields),
            default=1
        )
        max_user_count = max(
            (f.get("userCount", 0) for f in self.catalog.fields),
            default=1
        )
        
        self.max_alpha_count = max(max_alpha_count, 1)
        self.max_user_count = max(max_user_count, 1)
        
        logger.debug(
            "Normalization factors: max_alpha_count=%d, max_user_count=%d",
            self.max_alpha_count,
            self.max_user_count
        )
    
    def match_placeholder(
        self,
        keywords: list[str],
        pool_size: int,
        min_coverage: float | None = None,
        category_hint: str | None = None
    ) -> list[dict[str, Any]]:
        """Match fields to placeholder keywords using semantic scoring.
        
        Args:
            keywords: Semantic keywords from placeholder
            pool_size: Number of fields to return
            min_coverage: Minimum coverage threshold (uses config default if None)
            category_hint: Optional category to prioritize (e.g., 'fundamental')
        
        Returns:
            List of top matching fields, sorted by relevance score
        """
        if min_coverage is None:
            min_coverage = self.config.coverage_thresholds["pool_a"]
        
        # Search by keywords
        candidates = self.catalog.search_by_keywords(
            keywords=keywords,
            min_coverage=min_coverage,
            limit=500  # Get large pool for scoring
        )
        
        if not candidates:
            logger.warning(
                "No fields found matching keywords=%s with min_coverage=%.2f",
                keywords,
                min_coverage
            )
            return []
        
        # Score each candidate
        scored_fields = []
        for field in candidates:
            score = self._compute_relevance_score(
                field=field,
                keywords=keywords,
                category_hint=category_hint
            )
            scored_fields.append((score, field))
        
        # Sort by score (descending) and take top pool_size
        scored_fields.sort(key=lambda x: x[0], reverse=True)
        top_fields = [field for score, field in scored_fields[:pool_size]]
        
        logger.debug(
            "Matched %d fields for keywords=%s (min_coverage=%.2f, top_score=%.3f)",
            len(top_fields),
            keywords,
            min_coverage,
            scored_fields[0][0] if scored_fields else 0.0
        )
        
        return top_fields
    
    def _compute_relevance_score(
        self,
        field: dict[str, Any],
        keywords: list[str],
        category_hint: str | None = None
    ) -> float:
        """Compute relevance score for a field.
        
        Args:
            field: Field dictionary
            keywords: Search keywords
            category_hint: Optional category to boost
        
        Returns:
            Relevance score (0.0-1.0, higher is better)
        """
        # Component 1: Keyword match score
        keyword_score = self._keyword_match_score(field, keywords)
        
        # Component 2: Coverage score (data availability)
        coverage = field.get("coverage", 0.0)
        date_coverage = field.get("dateCoverage", coverage)
        coverage_score = (coverage + date_coverage) / 2.0
        
        # Component 3: Usage score (popularity)
        usage_score = self._usage_score(field)
        
        # Weighted combination
        score = (
            self.weights["keyword_match"] * keyword_score +
            self.weights["coverage"] * coverage_score +
            self.weights["usage"] * usage_score
        )
        
        # Boost if category matches hint
        if category_hint:
            field_category = (field.get("category") or {}).get("id", "")
            if field_category == category_hint:
                score *= 1.2  # 20% boost for category match
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _keyword_match_score(
        self, 
        field: dict[str, Any], 
        keywords: list[str]
    ) -> float:
        """Compute keyword match score.
        
        Checks how many keywords appear in field ID and description.
        
        Args:
            field: Field dictionary
            keywords: Search keywords
        
        Returns:
            Match score (0.0-1.0)
        """
        if not keywords:
            return 0.0
        
        field_id = field.get("id", "").lower()
        description = field.get("description", "").lower()
        combined_text = f"{field_id} {description}"
        
        # Count keyword matches
        matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Exact match in field ID (highest weight)
            if keyword_lower in field_id:
                matches += 2.0
            # Match in description
            elif keyword_lower in description:
                matches += 1.0
            # Partial match (substring)
            elif any(keyword_lower in token for token in combined_text.split()):
                matches += 0.5
        
        # Normalize by number of keywords
        max_possible = len(keywords) * 2.0  # Max score if all exact matches in ID
        score = matches / max_possible if max_possible > 0 else 0.0
        
        return min(score, 1.0)
    
    def _usage_score(self, field: dict[str, Any]) -> float:
        """Compute usage/popularity score.
        
        Based on alphaCount (how many alphas use this field) and
        userCount (how many users).
        
        Args:
            field: Field dictionary
        
        Returns:
            Usage score (0.0-1.0)
        """
        alpha_count = field.get("alphaCount", 0)
        user_count = field.get("userCount", 0)
        
        # Normalize and combine
        alpha_score = alpha_count / self.max_alpha_count
        user_score = user_count / self.max_user_count
        
        # Average of both metrics
        usage_score = (alpha_score + user_score) / 2.0
        
        return usage_score
    
    def get_category_distribution(self, fields: list[dict[str, Any]]) -> dict[str, int]:
        """Get distribution of categories in field list.
        
        Args:
            fields: List of field dictionaries
        
        Returns:
            Dict mapping category ID to count
        """
        distribution = defaultdict(int)
        for field in fields:
            category_id = (field.get("category") or {}).get("id", "unknown")
            distribution[category_id] += 1
        return dict(distribution)


# --------------------------------------------------------------------------- #
# Pool B: Cross-Domain Explorer (Exploration - 20%)
# --------------------------------------------------------------------------- #
class CrossDomainExplorer:
    """Explore fields from related but different categories.
    
    Pool B (Cross-domain): Selects fields from categories that are logically
    related but not directly matching the semantic keywords. This creates
    decorrelated alphas by combining different data types.
    
    Example: For 'profitability' (fundamental), also try analyst estimates
             or sentiment data to find hidden correlations.
    """
    
    def __init__(
        self, 
        catalog: FieldCatalog, 
        config: DiscoveryConfig | None = None
    ):
        """Initialize cross-domain explorer.
        
        Args:
            catalog: Field catalog
            config: Discovery configuration
        """
        self.catalog = catalog
        self.config = config or DiscoveryConfig()
        self.cross_rules = self.config.cross_category_rules
        
        logger.debug(
            "CrossDomainExplorer initialized with %d category mappings",
            len(self.cross_rules)
        )
    
    def explore(
        self,
        keywords: list[str],
        pool_size: int,
        primary_category: str | None = None,
        min_coverage: float | None = None
    ) -> list[dict[str, Any]]:
        """Explore fields from related categories.
        
        Args:
            keywords: Original semantic keywords
            pool_size: Number of fields to return
            primary_category: Primary category (auto-detected if None)
            min_coverage: Minimum coverage threshold
        
        Returns:
            List of fields from related categories
        """
        if min_coverage is None:
            min_coverage = self.config.coverage_thresholds["pool_b"]
        
        # Detect primary category if not provided
        if primary_category is None:
            primary_category = self._detect_primary_category(keywords)
        
        # Get related categories
        related_categories = self.cross_rules.get(primary_category, [])
        
        if not related_categories:
            logger.debug(
                "No cross-category rules for primary_category=%s, using all categories",
                primary_category
            )
            # Fall back to sampling from different categories
            related_categories = [
                cat for cat in self.catalog.by_category.keys()
                if cat != primary_category
            ]
        
        # Sample fields from related categories
        cross_domain_fields = []
        fields_per_category = max(1, pool_size // len(related_categories)) if related_categories else pool_size
        
        for category in related_categories:
            category_fields = self.catalog.get_by_category(
                category_id=category,
                min_coverage=min_coverage
            )
            
            if category_fields:
                # Sample with preference for higher coverage
                sampled = self._weighted_sample(
                    category_fields,
                    k=min(fields_per_category, len(category_fields))
                )
                cross_domain_fields.extend(sampled)
            
            if len(cross_domain_fields) >= pool_size:
                break
        
        # Ensure we return exactly pool_size fields (or less if not enough available)
        result = cross_domain_fields[:pool_size]
        
        logger.debug(
            "Explored %d cross-domain fields from categories=%s (primary=%s)",
            len(result),
            related_categories,
            primary_category
        )
        
        return result
    
    def _detect_primary_category(self, keywords: list[str]) -> str:
        """Detect primary category from keywords.
        
        Args:
            keywords: Semantic keywords
        
        Returns:
            Detected category ID
        """
        # Keyword to category mapping
        category_keywords = {
            "fundamental": {
                "profit", "income", "revenue", "sales", "earnings", "ebitda",
                "margin", "asset", "equity", "liability", "debt", "cash",
                "roe", "roa", "eps", "book", "value", "quality"
            },
            "analyst": {
                "estimate", "forecast", "consensus", "revision", "expectation",
                "prediction", "target", "recommendation", "rating"
            },
            "technical": {
                "price", "momentum", "trend", "volatility", "return", "moving",
                "oscillator", "rsi", "macd", "bollinger", "signal"
            },
            "volume": {
                "volume", "turnover", "liquidity", "trading", "activity",
                "depth", "spread", "bid", "ask"
            },
            "sentiment": {
                "sentiment", "news", "opinion", "mood", "buzz", "social",
                "twitter", "media", "feeling"
            },
            "options": {
                "option", "implied", "volatility", "put", "call", "strike",
                "skew", "greek", "delta", "gamma"
            },
        }
        
        # Count matches for each category
        category_scores = defaultdict(int)
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for category, cat_keywords in category_keywords.items():
                if keyword_lower in cat_keywords:
                    category_scores[category] += 1
        
        # Return category with most matches, default to fundamental
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        else:
            return "fundamental"  # Default
    
    def _weighted_sample(
        self, 
        fields: list[dict[str, Any]], 
        k: int
    ) -> list[dict[str, Any]]:
        """Sample fields with probability proportional to coverage.
        
        Args:
            fields: List of fields to sample from
            k: Number of samples
        
        Returns:
            Sampled fields
        """
        if not fields or k <= 0:
            return []
        
        if len(fields) <= k:
            return fields
        
        # Compute weights based on coverage
        weights = [f.get("coverage", 0.5) for f in fields]
        total_weight = sum(weights)
        
        if total_weight == 0:
            # Fallback to uniform sampling
            return random.sample(fields, k)
        
        # Weighted random sampling without replacement
        sampled = []
        remaining = list(fields)
        remaining_weights = list(weights)
        
        for _ in range(k):
            if not remaining:
                break
            
            # Normalize weights
            total = sum(remaining_weights)
            probabilities = [w / total for w in remaining_weights]
            
            # Sample one
            idx = random.choices(range(len(remaining)), weights=probabilities, k=1)[0]
            sampled.append(remaining[idx])
            
            # Remove sampled item
            remaining.pop(idx)
            remaining_weights.pop(idx)
        
        return sampled


# --------------------------------------------------------------------------- #
# Pool C: Wildcard Mutator (Random Mutation - 10%)
# --------------------------------------------------------------------------- #
class WildcardMutator:
    """Generate type-safe random field selections.
    
    Pool C (Wildcard): Randomly selects fields that match required data type
    but may have no semantic relation to the placeholder. This discovers
    market anomalies and hidden correlations that human intuition misses.
    
    Type Safety: Ensures random fields are compatible with operators
    (e.g., only numerical fields for math operations).
    """
    
    def __init__(
        self, 
        catalog: FieldCatalog, 
        config: DiscoveryConfig | None = None
    ):
        """Initialize wildcard mutator.
        
        Args:
            catalog: Field catalog
            config: Discovery configuration
        """
        self.catalog = catalog
        self.config = config or DiscoveryConfig()
        
        # Build pools of fields by type for fast sampling
        self._build_type_pools()
        
        # Track mutations for logging
        self.mutation_log = []
        
        logger.debug(
            "WildcardMutator initialized: %d numerical fields available",
            len(self._numerical_pool)
        )
    
    def _build_type_pools(self):
        """Build pre-filtered pools of fields by data type."""
        min_coverage = self.config.coverage_thresholds["pool_c"]
        
        # Numerical fields (MATRIX type)
        self._numerical_pool = [
            f for f in self.catalog.fields
            if f.get("type") == "MATRIX" 
            and f.get("coverage", 0) >= min_coverage
        ]
        
        # All fields (for categorical/any type)
        self._all_pool = [
            f for f in self.catalog.fields
            if f.get("coverage", 0) >= min_coverage
        ]
        
        logger.debug(
            "Type pools built: numerical=%d, all=%d (min_coverage=%.2f)",
            len(self._numerical_pool),
            len(self._all_pool),
            min_coverage
        )
    
    def sample_wildcard(
        self,
        data_type: str,
        exclude: set[str],
        count: int,
        seed: int | None = None
    ) -> list[dict[str, Any]]:
        """Sample random fields with type safety.
        
        Args:
            data_type: Required data type ('numerical' or 'any')
            exclude: Set of field IDs to exclude
            count: Number of fields to sample
            seed: Random seed for reproducibility (optional)
        
        Returns:
            List of randomly sampled fields
        """
        if seed is not None:
            random.seed(seed)
        
        # Select appropriate pool
        if data_type == "numerical":
            pool = self._numerical_pool
        else:
            pool = self._all_pool
        
        # Filter out excluded fields
        eligible = [f for f in pool if f["id"] not in exclude]
        
        if not eligible:
            logger.warning(
                "No eligible fields for wildcard sampling (type=%s, exclude=%d)",
                data_type,
                len(exclude)
            )
            return []
        
        # Sample randomly
        sample_size = min(count, len(eligible))
        sampled = random.sample(eligible, sample_size)
        
        # Log mutations
        for field in sampled:
            self.mutation_log.append({
                "field_id": field["id"],
                "data_type": data_type,
                "category": (field.get("category") or {}).get("id", "unknown"),
                "coverage": field.get("coverage", 0.0)
            })
        
        logger.debug(
            "Sampled %d wildcard fields (type=%s, eligible=%d)",
            len(sampled),
            data_type,
            len(eligible)
        )
        
        return sampled
    
    def get_mutation_log(self) -> list[dict[str, Any]]:
        """Get log of all mutations performed.
        
        Returns:
            List of mutation records
        """
        return self.mutation_log.copy()
    
    def clear_mutation_log(self):
        """Clear mutation log."""
        self.mutation_log.clear()


# --------------------------------------------------------------------------- #
# Module Exports (Updated)
# --------------------------------------------------------------------------- #
__all__ = [
    "FieldCatalog",
    "PlaceholderAnalyzer",
    "DiscoveryConfig",
    "SemanticFieldMatcher",
    "CrossDomainExplorer",
    "WildcardMutator",
    "DEFAULT_POOL_RATIOS",
    "DEFAULT_COVERAGE_THRESHOLDS",
    "DEFAULT_SCORING_WEIGHTS",
    "CROSS_CATEGORY_RULES",
]


# --------------------------------------------------------------------------- #
# Lessons-Driven Adjuster - Use historical performance to guide selection
# --------------------------------------------------------------------------- #
class LessonsDrivenAdjuster:
    """Adjust field selection based on historical performance from lessons.json.
    
    Uses accumulated knowledge to:
      - Boost fields that performed well in past patterns
      - Penalize fields that consistently failed
      - Promote wildcard discoveries that succeeded
      - Exclude fields from repeatedly failed patterns
    """
    
    def __init__(self, lessons_path: Path | None = None):
        """Initialize adjuster with lessons data.
        
        Args:
            lessons_path: Path to lessons.json (optional)
        """
        self.lessons_path = lessons_path
        self.field_performance = {}
        self.preferred_fields = set()
        self.excluded_fields = set()
        
        if lessons_path and lessons_path.exists():
            self._load_lessons()
        else:
            logger.debug("No lessons file provided, adjuster inactive")
    
    def _load_lessons(self):
        """Load and analyze lessons.json for field performance."""
        try:
            lessons = json.loads(self.lessons_path.read_text(encoding="utf-8"))
            
            # Analyze pattern performance
            patterns = lessons.get("patterns", {})
            self._analyze_pattern_fields(patterns)
            
            # Load field performance if exists (from Task 8)
            if "field_performance" in lessons:
                self._load_field_performance(lessons["field_performance"])
            
            logger.info(
                "Lessons loaded: %d field scores, %d preferred, %d excluded",
                len(self.field_performance),
                len(self.preferred_fields),
                len(self.excluded_fields)
            )
        except Exception as e:
            logger.warning("Failed to load lessons from %s: %s", self.lessons_path, e)
    
    def _analyze_pattern_fields(self, patterns: dict[str, Any]):
        """Extract field performance from pattern data.
        
        Args:
            patterns: Pattern dictionary from lessons.json
        """
        for pattern_id, data in patterns.items():
            action = data.get("action", "expand")
            avg_sharpe = data.get("avg_sharpe", 0.0)
            tested = data.get("tested", 0)
            
            if tested < 5:  # Need minimum sample size
                continue
            
            # Extract field names from pattern ID
            # Pattern IDs often contain field names, e.g., "profitability_trend"
            fields = self._extract_fields_from_pattern_id(pattern_id)
            
            for field_id in fields:
                if field_id not in self.field_performance:
                    self.field_performance[field_id] = {
                        "total_sharpe": 0.0,
                        "pattern_count": 0,
                        "success_count": 0,
                        "skip_count": 0
                    }
                
                perf = self.field_performance[field_id]
                perf["total_sharpe"] += avg_sharpe
                perf["pattern_count"] += 1
                
                if action == "expand":
                    perf["success_count"] += 1
                    self.preferred_fields.add(field_id)
                elif action == "skip":
                    perf["skip_count"] += 1
                    # Exclude if consistently failing
                    if perf["skip_count"] >= 3 and perf["success_count"] == 0:
                        self.excluded_fields.add(field_id)
    
    def _extract_fields_from_pattern_id(self, pattern_id: str) -> list[str]:
        """Extract potential field names from pattern ID.
        
        Pattern IDs like "operating_income_trend" might contain field names.
        
        Args:
            pattern_id: Pattern identifier
        
        Returns:
            List of potential field IDs
        """
        # Simple heuristic: split by underscore and check for known field patterns
        tokens = pattern_id.split("_")
        
        # Common field name patterns
        field_candidates = []
        for i in range(len(tokens)):
            # Single token fields
            if len(tokens[i]) > 3:
                field_candidates.append(tokens[i])
            
            # Two-token combinations
            if i < len(tokens) - 1:
                two_token = f"{tokens[i]}_{tokens[i+1]}"
                field_candidates.append(two_token)
            
            # Three-token combinations
            if i < len(tokens) - 2:
                three_token = f"{tokens[i]}_{tokens[i+1]}_{tokens[i+2]}"
                field_candidates.append(three_token)
        
        return field_candidates
    
    def _load_field_performance(self, field_perf_data: dict[str, Any]):
        """Load field performance data from lessons.json.
        
        Args:
            field_perf_data: Field performance section from lessons
        """
        for field_id, data in field_perf_data.items():
            # Update our tracking
            if field_id not in self.field_performance:
                self.field_performance[field_id] = {
                    "total_sharpe": 0.0,
                    "pattern_count": 0,
                    "success_count": 0,
                    "skip_count": 0
                }
            
            perf = self.field_performance[field_id]
            perf["total_sharpe"] += data.get("avg_sharpe", 0.0) * data.get("tested", 0)
            perf["pattern_count"] += data.get("tested", 0)
            
            # Check status
            if data.get("status") == "prefer":
                self.preferred_fields.add(field_id)
            elif data.get("submit_count", 0) == 0 and data.get("tested", 0) > 10:
                self.excluded_fields.add(field_id)
    
    def adjust_field_scores(
        self, 
        fields: list[tuple[float, dict[str, Any]]]
    ) -> list[tuple[float, dict[str, Any]]]:
        """Adjust field scores based on historical performance.
        
        Args:
            fields: List of (score, field) tuples
        
        Returns:
            Adjusted list of (score, field) tuples
        """
        if not self.field_performance:
            return fields  # No adjustments if no lessons
        
        adjusted = []
        for score, field in fields:
            field_id = field["id"]
            
            # Skip excluded fields
            if field_id in self.excluded_fields:
                logger.debug("Excluding field %s (consistently failed)", field_id)
                continue
            
            # Boost preferred fields
            if field_id in self.preferred_fields:
                score *= 1.2  # 20% boost
                logger.debug("Boosting field %s (preferred)", field_id)
            
            # Adjust based on performance history
            if field_id in self.field_performance:
                perf = self.field_performance[field_id]
                if perf["pattern_count"] > 0:
                    avg_sharpe = perf["total_sharpe"] / perf["pattern_count"]
                    
                    # Boost if high average sharpe
                    if avg_sharpe > 1.0:
                        boost_factor = 1.0 + (avg_sharpe - 1.0) * 0.1
                        score *= boost_factor
                        logger.debug(
                            "Boosting field %s by %.2fx (avg_sharpe=%.2f)",
                            field_id, boost_factor, avg_sharpe
                        )
                    # Penalize if low sharpe
                    elif avg_sharpe < 0.5:
                        penalty_factor = 0.8
                        score *= penalty_factor
                        logger.debug(
                            "Penalizing field %s by %.2fx (avg_sharpe=%.2f)",
                            field_id, penalty_factor, avg_sharpe
                        )
            
            adjusted.append((score, field))
        
        # Re-sort after adjustment
        adjusted.sort(key=lambda x: x[0], reverse=True)
        return adjusted
    
    def should_exclude_field(self, field_id: str) -> bool:
        """Check if field should be excluded from selection.
        
        Args:
            field_id: Field identifier
        
        Returns:
            True if field should be excluded
        """
        return field_id in self.excluded_fields
    
    def get_field_score(self, field_id: str) -> float:
        """Get performance score for a field.
        
        Args:
            field_id: Field identifier
        
        Returns:
            Average sharpe ratio (0.0 if no data)
        """
        if field_id not in self.field_performance:
            return 0.0
        
        perf = self.field_performance[field_id]
        if perf["pattern_count"] == 0:
            return 0.0
        
        return perf["total_sharpe"] / perf["pattern_count"]


# --------------------------------------------------------------------------- #
# Data Discovery Engine - Main orchestrator combining all pools
# --------------------------------------------------------------------------- #
class DataDiscoveryEngine:
    """Main engine orchestrating the 70-20-10 field discovery strategy.
    
    Combines:
      - Pool A (70%): Semantic matching for exploitation
      - Pool B (20%): Cross-domain exploration
      - Pool C (10%): Type-safe random wildcards
      - Lessons-driven adjustment for all pools
    
    Usage:
        engine = DataDiscoveryEngine(catalog, lessons_path="lessons.json")
        field_pairs = engine.discover_fields(
            skeleton="group_rank(ts_rank({profitability} / {scale}, {window}), {group})",
            max_fields=12
        )
    """
    
    def __init__(
        self,
        catalog: FieldCatalog,
        lessons_path: Path | None = None,
        config_path: Path | None = None
    ):
        """Initialize discovery engine.
        
        Args:
            catalog: Field catalog
            lessons_path: Path to lessons.json (optional)
            config_path: Path to discovery config (optional)
        """
        self.catalog = catalog
        self.config = DiscoveryConfig(config_path)
        
        # Initialize all components
        self.semantic_matcher = SemanticFieldMatcher(catalog, self.config)
        self.cross_explorer = CrossDomainExplorer(catalog, self.config)
        self.wildcard_mutator = WildcardMutator(catalog, self.config)
        self.adjuster = LessonsDrivenAdjuster(lessons_path) if lessons_path else None
        
        logger.info(
            "DataDiscoveryEngine initialized with pool_ratios=%s",
            self.config.pool_ratios
        )
    
    def discover_fields(
        self,
        skeleton: str,
        max_fields: int = 12,
        per_placeholder: bool = False
    ) -> list[dict[str, Any]]:
        """Discover field_pairs for a template skeleton.
        
        Args:
            skeleton: Template expression with {placeholders}
            max_fields: Total number of field_pairs to generate
            per_placeholder: If True, max_fields is per placeholder; 
                           if False, max_fields is total across all placeholders
        
        Returns:
            List of field_pair dicts ready for template expansion
        """
        # Analyze skeleton
        analyzer = PlaceholderAnalyzer(skeleton)
        
        if not analyzer.placeholders:
            logger.warning("No placeholders found in skeleton: %s", skeleton)
            return []
        
        # Determine fields per placeholder
        if per_placeholder:
            fields_per_placeholder = max_fields
        else:
            fields_per_placeholder = max(1, max_fields // len(analyzer.placeholders))
        
        # Discover fields for each placeholder
        all_field_pairs = []
        
        for placeholder in sorted(analyzer.placeholders):
            keywords = analyzer.get_keywords_for_placeholder(placeholder)
            requires_numerical = analyzer.requires_numerical(placeholder)
            
            logger.info(
                "Discovering fields for placeholder=%s keywords=%s numerical=%s",
                placeholder,
                keywords,
                requires_numerical
            )
            
            # Discover using 70-20-10 rule
            discovered_fields = self._discover_for_placeholder(
                placeholder=placeholder,
                keywords=keywords,
                requires_numerical=requires_numerical,
                target_count=fields_per_placeholder
            )
            
            # Convert to field_pairs format
            for field in discovered_fields:
                field_pair = {placeholder: field["id"]}
                
                # Add metadata for tracking
                field_pair["_metadata"] = {
                    "source_pool": field.get("_pool", "unknown"),
                    "category": (field.get("category") or {}).get("id", "unknown"),
                    "coverage": field.get("coverage", 0.0),
                    "description": field.get("description", "")
                }
                
                all_field_pairs.append(field_pair)
        
        # Limit to max_fields if needed
        if not per_placeholder and len(all_field_pairs) > max_fields:
            all_field_pairs = all_field_pairs[:max_fields]
        
        logger.info(
            "Discovered %d field_pairs for %d placeholders",
            len(all_field_pairs),
            len(analyzer.placeholders)
        )
        
        return all_field_pairs
    
    def _discover_for_placeholder(
        self,
        placeholder: str,
        keywords: list[str],
        requires_numerical: bool,
        target_count: int
    ) -> list[dict[str, Any]]:
        """Discover fields for a single placeholder using 70-20-10 rule.
        
        Args:
            placeholder: Placeholder name
            keywords: Semantic keywords
            requires_numerical: Whether numerical type is required
            target_count: Total number of fields to discover
        
        Returns:
            List of field dicts with _pool metadata
        """
        # Calculate pool sizes
        pool_a_size = int(target_count * self.config.pool_ratios["exploitation"])
        pool_b_size = int(target_count * self.config.pool_ratios["cross_domain"])
        pool_c_size = max(1, target_count - pool_a_size - pool_b_size)
        
        logger.debug(
            "Pool sizes for %s: A=%d, B=%d, C=%d (total=%d)",
            placeholder, pool_a_size, pool_b_size, pool_c_size, target_count
        )
        
        # Pool A: Semantic matching (exploitation)
        pool_a_fields = self.semantic_matcher.match_placeholder(
            keywords=keywords,
            pool_size=pool_a_size
        )
        for field in pool_a_fields:
            field["_pool"] = "A"
        
        # Pool B: Cross-domain exploration
        pool_b_fields = self.cross_explorer.explore(
            keywords=keywords,
            pool_size=pool_b_size
        )
        for field in pool_b_fields:
            field["_pool"] = "B"
        
        # Pool C: Wildcard mutation
        existing_ids = {f["id"] for f in pool_a_fields + pool_b_fields}
        data_type = "numerical" if requires_numerical else "any"
        
        pool_c_fields = self.wildcard_mutator.sample_wildcard(
            data_type=data_type,
            exclude=existing_ids,
            count=pool_c_size
        )
        for field in pool_c_fields:
            field["_pool"] = "C"
        
        # Combine all pools
        all_fields = pool_a_fields + pool_b_fields + pool_c_fields
        
        # Apply lessons-driven adjustment
        if self.adjuster:
            # Convert to (score, field) format for adjustment
            # Use simple coverage as base score for adjustment
            scored_fields = [(f.get("coverage", 0.5), f) for f in all_fields]
            adjusted_scored = self.adjuster.adjust_field_scores(scored_fields)
            all_fields = [field for score, field in adjusted_scored]
        
        logger.info(
            "Discovered %d fields for %s: Pool A=%d, B=%d, C=%d",
            len(all_fields),
            placeholder,
            len(pool_a_fields),
            len(pool_b_fields),
            len(pool_c_fields)
        )
        
        return all_fields
    
    def get_pool_distribution(
        self, 
        field_pairs: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Get distribution of fields across pools.
        
        Args:
            field_pairs: List of field_pair dicts
        
        Returns:
            Dict mapping pool ID to count
        """
        distribution = defaultdict(int)
        for fp in field_pairs:
            if "_metadata" in fp:
                pool = fp["_metadata"].get("source_pool", "unknown")
                distribution[pool] += 1
        return dict(distribution)
    
    def validate_field_pairs(
        self,
        field_pairs: list[dict[str, Any]]
    ) -> tuple[bool, list[str]]:
        """Validate discovered field_pairs.
        
        Args:
            field_pairs: List of field_pair dicts
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        if not field_pairs:
            errors.append("No field_pairs discovered")
            return False, errors
        
        # Check each field_pair
        for i, fp in enumerate(field_pairs):
            # Remove metadata for validation
            fp_clean = {k: v for k, v in fp.items() if k != "_metadata"}
            
            if not fp_clean:
                errors.append(f"Field_pair {i} is empty after removing metadata")
                continue
            
            # Validate field IDs exist in catalog
            for placeholder, field_id in fp_clean.items():
                if not self.catalog.get_field(field_id):
                    errors.append(
                        f"Field_pair {i}: field '{field_id}' not found in catalog"
                    )
        
        is_valid = len(errors) == 0
        return is_valid, errors


# --------------------------------------------------------------------------- #
# Module Exports (Final)
# --------------------------------------------------------------------------- #
__all__ = [
    "FieldCatalog",
    "PlaceholderAnalyzer",
    "DiscoveryConfig",
    "SemanticFieldMatcher",
    "CrossDomainExplorer",
    "WildcardMutator",
    "LessonsDrivenAdjuster",
    "DataDiscoveryEngine",
    "DEFAULT_POOL_RATIOS",
    "DEFAULT_COVERAGE_THRESHOLDS",
    "DEFAULT_SCORING_WEIGHTS",
    "CROSS_CATEGORY_RULES",
]

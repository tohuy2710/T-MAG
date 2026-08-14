"""Central runtime target for WorldQuant BRAIN research.

All templates and research is configured for GLB/TOPDIV3000/delay=1.
Templates are research ideas, not immutable simulation settings: every candidate is
normalised through :class:`ResearchTarget` immediately before it is validated
or sent to BRAIN.  This prevents an old template's ``default_settings`` from
quietly changing the configured market or neutralization.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONFIG_PATH = SKILL_DIR / "config" / "research_target.json"


class TargetConfigError(ValueError):
    """Raised when the runtime target configuration is incomplete or unsafe."""


def normalize_neutralization(value: str) -> str:
    """Return BRAIN's canonical upper-snake spelling for a neutralization."""
    normalized = re.sub(r"[\s-]+", "_", str(value).strip().upper())
    return re.sub(r"_+", "_", normalized)


@dataclass(frozen=True)
class ResearchTarget:
    """One coherent BRAIN market/data-field target."""

    name: str
    instrument_type: str
    region: str
    universe: str
    delay: int
    neutralizations: tuple[str, ...]
    excluded_dataset_ids: frozenset[str]
    fields_path: Path

    def base_settings(self) -> dict[str, Any]:
        """Non-negotiable simulation settings plus safe generic defaults."""
        return {
            "instrumentType": self.instrument_type,
            "region": self.region,
            "universe": self.universe,
            "delay": self.delay,
            "truncation": 0.08,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "OFF",
            "maxTrade": "OFF",
            "maxPosition": "OFF",
            "language": "FASTEXPR",
            "visualization": False,
        }

    def settings_for(
        self,
        settings: dict[str, Any] | None = None,
        neutralization: str | None = None,
    ) -> dict[str, Any]:
        """Merge optional tuning settings while enforcing this target.

        ``region``, ``universe`` and ``delay`` are always overwritten.  A
        candidate may only use one of this target's configured neutralizations;
        failing early is safer than accidentally simulating an old USA setting.
        """
        merged = dict(self.base_settings())
        supplied = dict(settings or {})

        # A few historic templates used snake_case keys.  Canonicalise them so
        # their intended non-target settings still survive the migration.
        aliases = {"unit_handling": "unitHandling", "nan_handling": "nanHandling"}
        for old, new in aliases.items():
            if old in supplied and new not in supplied:
                supplied[new] = supplied[old]
            supplied.pop(old, None)
        merged.update(supplied)

        selected = neutralization if neutralization is not None else merged.get("neutralization")
        if selected is None:
            selected = self.neutralizations[0]
        selected = normalize_neutralization(str(selected))
        if selected not in self.neutralizations:
            raise TargetConfigError(
                f"Neutralization {selected!r} is not enabled for target {self.name}; "
                f"choose one of {list(self.neutralizations)}"
            )

        # Target settings win over stale template/LLM settings.
        merged.update(
            {
                "instrumentType": self.instrument_type,
                "region": self.region,
                "universe": self.universe,
                "delay": self.delay,
                "neutralization": selected,
            }
        )
        return merged

    def require_fields_reference(self) -> Path:
        """Fail closed when the target's field catalog has not been synced."""
        if not self.fields_path.is_file():
            raise TargetConfigError(
                "GLB field reference is missing: "
                f"{self.fields_path}. Fetch it with "
                "`python3 scripts/sync_data_fields.py` before generating candidates."
            )
        return self.fields_path

    def describe(self) -> str:
        return (
            f"{self.region}/{self.universe}/delay={self.delay}; "
            f"neutralization={','.join(self.neutralizations)}; "
            f"excluded datasets={','.join(sorted(self.excluded_dataset_ids))}"
        )


def load_target(config_path: Path | str | None = None) -> ResearchTarget:
    """Load the configured target, optionally from ``WQ_TARGET_CONFIG``."""
    raw_path = config_path or os.getenv("WQ_TARGET_CONFIG") or DEFAULT_CONFIG_PATH
    path = Path(raw_path)
    if not path.is_absolute():
        path = SKILL_DIR / path
    if not path.is_file():
        raise TargetConfigError(f"Research target configuration not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("name", "instrument_type", "region", "universe", "delay", "neutralizations", "fields_reference")
    missing = [key for key in required if key not in data]
    if missing:
        raise TargetConfigError(f"Target config {path} missing required keys: {missing}")

    neutralizations = tuple(normalize_neutralization(value) for value in data["neutralizations"])
    if not neutralizations or len(set(neutralizations)) != len(neutralizations):
        raise TargetConfigError("neutralizations must be a non-empty list without duplicates")

    fields_path = Path(data["fields_reference"])
    if not fields_path.is_absolute():
        fields_path = SKILL_DIR / fields_path

    return ResearchTarget(
        name=str(data["name"]),
        instrument_type=str(data["instrument_type"]),
        region=str(data["region"]),
        universe=str(data["universe"]),
        delay=int(data["delay"]),
        neutralizations=neutralizations,
        excluded_dataset_ids=frozenset(
            str(dataset).lower() for dataset in data.get("excluded_dataset_ids", [])
        ),
        fields_path=fields_path,
    )

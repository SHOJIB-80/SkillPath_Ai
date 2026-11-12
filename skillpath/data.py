"""Loading and taxonomy-based filtering of processed occupation profiles."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from skillpath.config import DEFAULT_DATA_FILE, OCCUPATION_FILTERS
from skillpath.skills import normalize_skill


def is_technology_occupation(code: str) -> bool:
    """Use the documented O*NET-SOC 15-12 and 15-2051 code families."""
    normalized = (code or "").strip()
    return any(normalized.startswith(prefix) for prefix in OCCUPATION_FILTERS["technology"])


def _split_field(value: str | None) -> list[str]:
    if not value:
        return []
    return list(dict.fromkeys(
        normalized
        for part in value.split("|")
        if (normalized := normalize_skill(part))
    ))


def load_roles(
    path: Path = DEFAULT_DATA_FILE,
    filter_mode: str = "all",
) -> list[dict[str, Any]]:
    """Load profiles from processed O*NET or the legacy sample CSV.

    ``all`` preserves compatibility with the original sample CSV. Production
    interfaces explicitly request ``technology`` so occupation codes are used
    to keep the recommender within the intended technology/data scope.
    """
    if filter_mode not in OCCUPATION_FILTERS:
        raise ValueError(f"Unknown occupation filter: {filter_mode}")
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    roles: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        required = {"role", "skills"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV must contain columns: role, skills")
        for row_number, row in enumerate(reader, start=2):
            name = (row.get("role") or "").strip()
            code = (row.get("onet_soc_code") or row.get("O*NET-SOC Code") or "").strip()
            if filter_mode == "technology" and not is_technology_occupation(code):
                continue
            skills = _split_field(row.get("skills"))
            if not name or not skills:
                raise ValueError(f"Invalid role or skills on CSV row {row_number}")
            key = (code, name) if code else ("", name)
            if key in seen:
                continue
            seen.add(key)
            role: dict[str, Any] = {
                "role": name,
                "skills": skills,
                "description": (row.get("description") or "").strip(),
                "learning_path": (row.get("learning_path") or "").strip(),
                "onet_soc_code": code,
                "software_examples": _split_field(row.get("software_examples")),
                "hot_technologies": _split_field(row.get("hot_technologies")),
                "in_demand_technologies": _split_field(row.get("in_demand_technologies")),
                "source_release": (row.get("source_release") or "").strip(),
            }
            role["onet_url"] = (
                f"https://www.onetonline.org/link/summary/{code}" if code else ""
            )
            roles.append(role)
    if not roles:
        raise ValueError(
            "No occupation profiles remain after applying the selected filter. "
            "Run import_onet.py and verify the dataset's O*NET-SOC code column."
        )
    return roles


def vocabulary(roles: list[dict[str, Any]]) -> set[str]:
    """All normalized technology labels represented in the supplied profiles."""
    return {skill for role in roles for skill in role.get("skills", [])}

"""Reproducible preprocessing for the O*NET 31.0 Software Skills CSV."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from skillpath.config import DEFAULT_ONET_FILE, DEFAULT_DATA_FILE
from skillpath.skills import normalize_skill

SOURCE_URL = "https://www.onetcenter.org/dictionary/31.0/csv/software_skills.html"
REQUIRED_COLUMNS = {"O*NET-SOC Code", "Title", "Workplace Example"}


def _cell(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _split_sorted(values: set[str]) -> str:
    return "|".join(sorted(value for value in values if value))


def convert(source: Path = DEFAULT_ONET_FILE, destination: Path = DEFAULT_DATA_FILE) -> tuple[int, int]:
    """Aggregate official records into one profile per O*NET-SOC code/title.

    The original input is never edited. ``skills`` contains canonicalized
    workplace-example labels; the original example names and O*NET's optional
    hot/in-demand markers remain separately available in the output.
    """
    source = Path(source)
    destination = Path(destination)
    if not source.is_file():
        raise FileNotFoundError(f"Official O*NET CSV not found: {source}")
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different files.")

    grouped: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"skills": set(), "examples": set(), "hot": set(), "demand": set()}
    )
    seen_records: set[tuple[str, ...]] = set()
    rows_read = valid_rows = duplicate_rows = skipped_incomplete = 0

    with source.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
            raise ValueError(
                "Not the expected O*NET Software Skills CSV; missing columns: "
                + ", ".join(missing)
            )
        for row in reader:
            rows_read += 1
            code = _cell(row, "O*NET-SOC Code")
            title = _cell(row, "Title")
            example = _cell(row, "Workplace Example")
            if not (code and title and example):
                skipped_incomplete += 1
                continue
            valid_rows += 1
            record_key = tuple(_cell(row, field) for field in reader.fieldnames)
            if record_key in seen_records:
                duplicate_rows += 1
                continue
            seen_records.add(record_key)

            profile = grouped[(code, title)]
            profile["examples"].add(example)
            canonical = normalize_skill(example)
            if canonical:
                profile["skills"].add(canonical)
                if _cell(row, "Hot Technology").upper() == "Y":
                    profile["hot"].add(canonical)
                if _cell(row, "In Demand").upper() == "Y":
                    profile["demand"].add(canonical)

    if valid_rows < 100:
        raise ValueError(
            f"Only {valid_rows} usable rows found; check that you downloaded the full O*NET Software Skills CSV."
        )
    if not grouped:
        raise ValueError("No valid O*NET occupation profiles were found.")

    output_fields = [
        "onet_soc_code",
        "role",
        "skills",
        "software_examples",
        "hot_technologies",
        "in_demand_technologies",
        "description",
        "learning_path",
        "source_release",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = destination.with_suffix(destination.suffix + ".tmp")
    with tmp_output.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fields)
        writer.writeheader()
        for (code, title), profile in sorted(grouped.items()):
            writer.writerow({
                "onet_soc_code": code,
                "role": title,
                "skills": _split_sorted(profile["skills"]),
                "software_examples": _split_sorted({x.lower() for x in profile["examples"]}),
                "hot_technologies": _split_sorted(profile["hot"]),
                "in_demand_technologies": _split_sorted(profile["demand"]),
                "description": f"O*NET-SOC {code}; aggregated O*NET software workplace examples.",
                "learning_path": "Other profile technologies are potential exploration topics, not verified requirements.",
                "source_release": "O*NET 31.0",
            })
    tmp_output.replace(destination)

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = {
        "source_release": "O*NET 31.0",
        "source_url": SOURCE_URL,
        "source_file": source.name,
        "source_sha256": digest,
        "records_read": rows_read,
        "usable_records": valid_rows,
        "unique_complete_records_used": len(seen_records),
        "duplicate_records_skipped": duplicate_rows,
        "incomplete_records_skipped": skipped_incomplete,
        "occupation_profiles_written": len(grouped),
        "processed_file": destination.name,
        "processing_notes": [
            "Grouped by O*NET-SOC code and title.",
            "Exact duplicate source records and rows missing code/title/workplace example are omitted.",
            "Canonical aliases are project-derived labels; original workplace examples are retained separately.",
            "O*NET Hot Technology and In Demand examples are preserved as separate fields when supplied.",
        ],
    }
    manifest_path = destination.with_name("data_manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Keep the original convert() return contract: count usable source rows and profiles.
    return valid_rows, len(grouped)

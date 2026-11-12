"""Prepare the existing project's profiles from official O*NET 31.0 data."""
from __future__ import annotations

import argparse
from pathlib import Path

from skillpath.config import DEFAULT_DATA_FILE, DEFAULT_ONET_FILE
from skillpath.preprocessing import convert


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import O*NET 31.0 Software Skills into SkillPath AI profiles"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_ONET_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_DATA_FILE)
    args = parser.parse_args()
    try:
        records, occupations = convert(args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Import failed: {exc}\n")
    print(f"Processed {records:,} usable O*NET source rows into {occupations:,} occupation profiles.")
    print(f"Created: {args.output}")
    print(f"Manifest: {args.output.with_name('data_manifest.json')}")
    print("Run the dashboard with: python -m streamlit run app.py")


if __name__ == "__main__":
    main()

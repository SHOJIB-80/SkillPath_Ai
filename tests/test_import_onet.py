import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from import_onet import convert


class ImporterTests(unittest.TestCase):
    def test_convert_deduplicates_skips_missing_and_keeps_codes_and_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "software_skills.csv"
            out = Path(tmp) / "raw_skills.csv"
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "O*NET-SOC Code", "Title", "Workplace Example",
                    "Hot Technology", "In Demand",
                ])
                for i in range(120):
                    example = "Python" if i % 2 == 0 else "Amazon Web Services AWS Software"
                    writer.writerow(["15-1252.00", "Software Developers", example, "Y", "N"])
                writer.writerow(["15-1252.00", "Software Developers", "", "N", "N"])
            rows, jobs = convert(source, out)
            self.assertEqual((rows, jobs), (120, 1))
            with out.open(newline="", encoding="utf-8") as f:
                result = next(csv.DictReader(f))
            self.assertEqual(result["role"], "Software Developers")
            self.assertEqual(result["onet_soc_code"], "15-1252.00")
            self.assertEqual(set(result["skills"].split("|")), {"aws", "python"})
            manifest = json.loads((Path(tmp) / "data_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["duplicate_records_skipped"], 118)
            self.assertEqual(manifest["incomplete_records_skipped"], 1)
            self.assertEqual(manifest["occupation_profiles_written"], 1)

    def test_rejects_source_destination_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.csv"
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["O*NET-SOC Code", "Title", "Workplace Example"])
                for i in range(100):
                    writer.writerow(["15-1252.00", "Software Developers", f"tool {i}"])
            with self.assertRaises(ValueError):
                convert(source, source)

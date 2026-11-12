import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import parse_skills, load_roles, recommend
from skillpath.config import DEFAULT_DATA_FILE
from skillpath.data import is_technology_occupation, vocabulary


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecommenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_roles = load_roles(PROJECT_ROOT / "sample_skills.csv")
        cls.onet_roles = load_roles(DEFAULT_DATA_FILE, filter_mode="technology")
        cls.all_onet_roles = load_roles(DEFAULT_DATA_FILE, filter_mode="all")

    def test_normalize_and_deduplicate_input(self):
        self.assertEqual(
            parse_skills(" Python, Cloud Computing, python, Automation "),
            ["python", "cloud", "automation"],
        )

    def test_technology_aliases(self):
        self.assertEqual(
            parse_skills("AWS, Amazon Web Services, JS, JavaScript, Postgres, PostgreSQL, Node.js"),
            ["aws", "javascript", "postgresql", "nodejs"],
        )

    def test_three_recommendations_and_score_order(self):
        recs = recommend(parse_skills("Python, Cloud Computing, Automation"), self.sample_roles)
        self.assertEqual(len(recs), 3)
        self.assertTrue(all(0 < rec["score"] <= 1 for rec in recs))
        self.assertTrue(all(recs[i]["score"] >= recs[i + 1]["score"] for i in range(len(recs) - 1)))

    def test_no_overlap_and_unknown_skills_are_honest(self):
        self.assertEqual(recommend(["painting", "singing", "juggling"], self.sample_roles), [])
        self.assertEqual(recommend(["unknown one", "unknown two", "unknown three"], self.onet_roles), [])

    def test_unknown_terms_reduce_weighted_coverage(self):
        recs = recommend(parse_skills("Python, SQL, Machine Learning"), self.onet_roles)
        self.assertTrue(recs)
        self.assertTrue(all(rec["skill_coverage"] < 1.0 for rec in recs))
        self.assertTrue(all("machine learning" in rec["unmatched_skills"] for rec in recs))

    def test_minimum_input_after_alias_deduplication(self):
        with self.assertRaises(ValueError):
            recommend(["python", "py", "sql"], self.sample_roles)

    def test_skill_coverage_and_explanation(self):
        recs = recommend(parse_skills("machine learning, statistics, python"), self.sample_roles)
        self.assertTrue(recs)
        self.assertTrue(all(0 <= rec["skill_coverage"] <= 1 for rec in recs))
        self.assertTrue(all(rec["matched_skills"] for rec in recs))
        self.assertTrue(all(rec["unmatched_skills"] is not None for rec in recs))
        self.assertTrue(all("TF-IDF/cosine" in rec["explanation"] for rec in recs))

    def test_filter_uses_configured_occupation_identifiers(self):
        self.assertTrue(is_technology_occupation("15-1252.00"))
        self.assertTrue(is_technology_occupation("15-2051.00"))
        self.assertFalse(is_technology_occupation("13-2051.00"))
        self.assertFalse(is_technology_occupation("19-4031.00"))
        self.assertFalse(is_technology_occupation("15-1299.07"))
        self.assertTrue(all(is_technology_occupation(r["onet_soc_code"]) for r in self.onet_roles))
        self.assertIn("Blockchain Engineers", {r["role"] for r in self.all_onet_roles})

    def test_deterministic_ranking_and_top_three(self):
        skills = parse_skills("Python, SQL, AWS")
        first = recommend(skills, self.onet_roles, top_n=3)
        second = recommend(skills, self.onet_roles, top_n=3)
        self.assertEqual([r["onet_soc_code"] for r in first], [r["onet_soc_code"] for r in second])
        self.assertLessEqual(len(first), 3)

    def test_realistic_skill_scenarios_resolve_within_technology_scope(self):
        scenarios = [
            "Python, SQL, Machine Learning",
            "Docker, Kubernetes, AWS",
            "JavaScript, React, Node.js",
            "Linux, Networking, Cybersecurity",
        ]
        known = vocabulary(self.onet_roles)
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                skills = parse_skills(scenario)
                self.assertEqual(len(skills), 3)
                results = recommend(skills, self.onet_roles, top_n=3)
                # Evaluate scope, evidence, and score consistency rather than
                # prescribing a specific occupation title as the right answer.
                self.assertLessEqual(len(results), 3)
                self.assertTrue(all(is_technology_occupation(r["onet_soc_code"]) for r in results))
                if any(skill in known for skill in skills):
                    self.assertTrue(results)
                for result in results:
                    self.assertTrue(set(result["matched_skills"]).issubset(set(skills)))
                    self.assertGreater(result["score"], 0)

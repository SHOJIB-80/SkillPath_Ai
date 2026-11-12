"""Central configuration for SkillPath AI."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "raw_skills.csv"
DEFAULT_ONET_FILE = PROJECT_ROOT / "software_skills.csv"

# Default candidate scope uses actual O*NET-SOC occupation code families for
# computer systems, security, support, networks/databases, programming/web,
# and data scientists. The exact prefixes are deliberately listed so users can
# audit and change the scope; no recommendation is forced by title or input.
# Less directly comparable 15-1299 specializations (e.g. blockchain and digital
# forensics) remain in raw_skills.csv and are available in the all-data mode.
TECH_OCCUPATION_PREFIXES = (
    "15-1211",  # Computer Systems Analysts
    "15-1212",  # Information Security Analysts
    "15-1221",  # Computer and Information Research Scientists
    "15-1231",  # Computer Network Support Specialists
    "15-1232",  # Computer User Support Specialists
    "15-1241",  # Computer Network Architects and detailed occupation
    "15-1242",  # Database Administrators
    "15-1243",  # Database Architects and Data Warehousing Specialists
    "15-1244",  # Network and Computer Systems Administrators
    "15-1251",  # Computer Programmers
    "15-1252",  # Software Developers
    "15-1253",  # Software QA Analysts and Testers
    "15-1254",  # Web Developers
    "15-1255",  # Web and Digital Interface Designers and detailed occupation
    "15-1299.01",  # Web Administrators
    "15-1299.04",  # Penetration Testers
    "15-1299.05",  # Information Security Engineers
    "15-1299.08",  # Computer Systems Engineers/Architects
    "15-2051",  # Data Scientists and detailed occupations
)
OCCUPATION_FILTERS = {
    "technology": TECH_OCCUPATION_PREFIXES,
    "all": (),
}
FILTER_LABELS = {
    "technology": "Core software, infrastructure, security, and data occupations",
    "all": "All occupations in the O*NET file",
}

# Combined score = TF-IDF/cosine similarity * 0.65 + weighted skill coverage * 0.35.
TFIDF_WEIGHT = 0.65
COVERAGE_WEIGHT = 0.35

# Very broad office/web terms are still valid O*NET examples, but are less
# diagnostic than specific technologies. TF-IDF already applies IDF weighting;
# this extra, explicit factor prevents common software tags from dominating.
GENERIC_SKILL_PENALTY = 0.25
GENERIC_SKILLS = frozenset({
    "microsoft office software",
    "microsoft office",
    "microsoft word",
    "excel",
    "microsoft excel",
    "microsoft powerpoint",
    "cloud",
    "web browser",
    "email software",
    "spreadsheet software",
    "word processing software",
})

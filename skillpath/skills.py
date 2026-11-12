"""Skill normalization shared by the importer, CLI, tests, and dashboard."""
from __future__ import annotations

import re

ALIASES = {
    "py": "python",
    "js": "javascript",
    "node": "nodejs",
    "node.js": "nodejs",
    "node js": "nodejs",
    "react.js": "react",
    "cloud computing": "cloud",
    "amazon web services": "aws",
    "aws cloud": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "machine-learning": "machine learning",
    "machine learning software": "machine learning",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dev ops": "devops",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "power bi": "powerbi",
    "ci/cd": "cicd",
    "data structures and algorithms": "algorithms",
    "structured query language": "sql",
    "structured query language sql": "sql",
    "microsoft excel": "excel",
    "microsoft word": "microsoft word",
    "microsoft powerpoint": "microsoft powerpoint",
    "microsoft azure": "azure",
    "google cloud platform software": "gcp",
}

# Anchored patterns capture common O*NET workplace-example spellings without
# turning unrelated text that merely contains a substring into a technology.
EXAMPLE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(?:amazon web services(?: aws)?|aws)(?: software)?$"), "aws"),
    (re.compile(r"^(?:google cloud platform|google cloud)(?: software)?$"), "gcp"),
    (re.compile(r"^(?:microsoft azure|azure)(?: software)?$"), "azure"),
    (re.compile(r"^(?:postgres|postgresql)(?: database)?(?: software)?$"), "postgresql"),
    (re.compile(r"^(?:power\s*bi)(?: software)?$"), "powerbi"),
    (re.compile(r"^(?:javascript|java script)(?: software)?$"), "javascript"),
    (re.compile(r"^(?:node\.?js|node js)(?: software)?$"), "nodejs"),
    (re.compile(r"^(?:react\.?js)(?: software)?$"), "react"),
    (re.compile(r"^(?:structured query language(?: sql)?|sql)(?: software)?$"), "sql"),
    (re.compile(r"^(?:python)(?: software)?$"), "python"),
    (re.compile(r"^(?:microsoft excel|excel)(?: software)?$"), "excel"),
)


def _clean(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def normalize_skill(skill: str) -> str:
    """Return a stable canonical label; unknown labels remain searchable as entered."""
    cleaned = _clean(skill)
    if not cleaned:
        return ""
    for pattern, canonical in EXAMPLE_PATTERNS:
        if pattern.fullmatch(cleaned):
            return canonical
    return ALIASES.get(cleaned, cleaned)


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize and deduplicate while preserving the user's first-entry order."""
    result: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        name = normalize_skill(skill)
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def parse_skills(text: str) -> list[str]:
    """Parse a comma-separated skill string and remove blanks/duplicates."""
    return normalize_skills(text.split(","))

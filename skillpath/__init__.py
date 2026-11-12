"""SkillPath AI recommendation package."""

from skillpath.data import is_technology_occupation, load_roles, vocabulary
from skillpath.recommender import recommend
from skillpath.skills import normalize_skill, parse_skills

__all__ = [
    "is_technology_occupation",
    "load_roles",
    "normalize_skill",
    "parse_skills",
    "recommend",
    "vocabulary",
]

"""Explainable technology-career ranking using TF-IDF, cosine, and coverage."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from skillpath.config import (
    COVERAGE_WEIGHT,
    GENERIC_SKILLS,
    GENERIC_SKILL_PENALTY,
    TFIDF_WEIGHT,
)
from skillpath.skills import normalize_skills


def recommend(
    user_skills: list[str],
    roles: list[dict[str, Any]],
    top_n: int = 3,
    tfidf_weight: float = TFIDF_WEIGHT,
    coverage_weight: float = COVERAGE_WEIGHT,
) -> list[dict[str, Any]]:
    """Return nonzero matches ranked by a transparent combined score.

    TF-IDF statistics are learned only from the selected occupation profiles.
    Coverage is inverse-document-frequency weighted: matching a distinctive
    skill contributes more than matching a term repeated across profiles.
    Explicitly broad software tags receive an additional small penalty. User
    skills absent from the selected corpus are counted as unmatched in coverage
    using the mean known-input IDF as their denominator weight. They therefore
    cannot silently turn a partial profile match into 100% coverage.
    """
    cleaned = normalize_skills(user_skills)
    if len(cleaned) < 3:
        raise ValueError("Please provide at least three different skills.")
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    if tfidf_weight < 0 or coverage_weight < 0 or not np.isclose(tfidf_weight + coverage_weight, 1.0):
        raise ValueError("tfidf_weight and coverage_weight must be nonnegative and sum to 1.")
    if not roles:
        return []

    profiles: list[list[str]] = [
        normalize_skills(list(role.get("skills", []))) for role in roles
    ]
    if any(not skills for skills in profiles):
        raise ValueError("Every occupation profile must include at least one skill.")

    vectorizer = TfidfVectorizer(
        analyzer=lambda tokens: tokens,
        lowercase=False,
        norm="l2",
        smooth_idf=True,
    )
    role_vectors = vectorizer.fit_transform(profiles)
    user_vector = vectorizer.transform([cleaned])
    vocab = vectorizer.vocabulary_
    idf = vectorizer.idf_

    feature_weights = np.ones(len(vocab), dtype=float)
    for term, index in vocab.items():
        if term in GENERIC_SKILLS:
            feature_weights[index] = GENERIC_SKILL_PENALTY
    # Reweight both query and occupation vectors consistently, then renormalize.
    role_vectors = normalize(role_vectors.multiply(feature_weights), norm="l2")
    user_vector = normalize(user_vector.multiply(feature_weights), norm="l2")
    cosine_scores = cosine_similarity(user_vector, role_vectors).ravel()

    known_skills = [skill for skill in cleaned if skill in vocab]
    base_importance = {
        skill: float(idf[vocab[skill]]) * (
            GENERIC_SKILL_PENALTY if skill in GENERIC_SKILLS else 1.0
        )
        for skill in known_skills
    }
    unknown_weight = float(np.mean(list(base_importance.values()))) if base_importance else 1.0
    importance = {
        skill: base_importance.get(skill, unknown_weight)
        for skill in cleaned
    }
    denominator = sum(importance.values())

    ranked: list[dict[str, Any]] = []
    for index, cosine_score in enumerate(cosine_scores):
        role = roles[index]
        role_skills = set(profiles[index])
        matched = [skill for skill in cleaned if skill in role_skills]
        if cosine_score <= 0 or not matched:
            continue
        coverage_numerator = sum(importance[skill] for skill in matched)
        coverage_score = coverage_numerator / denominator if denominator else 0.0
        final_score = tfidf_weight * float(cosine_score) + coverage_weight * coverage_score
        unmatched = [skill for skill in cleaned if skill not in role_skills]

        suggested = list(dict.fromkeys(
            list(role.get("hot_technologies", []))
            + list(role.get("in_demand_technologies", []))
            + profiles[index]
        ))
        suggested = [skill for skill in suggested if skill not in set(cleaned)][:8]
        match_text = ", ".join(matched)
        explanation = (
            f"Matches {len(matched)} of {len(cleaned)} entered skills ({match_text}). "
            f"TF-IDF/cosine similarity is {cosine_score:.3f}; "
            f"inverse-frequency-weighted coverage is {coverage_score:.3f}."
        )
        ranked.append({
            **role,
            "skills": profiles[index],
            "score": float(final_score),
            "cosine_score": float(cosine_score),
            "skill_coverage": float(coverage_score),
            "matched_skills": matched,
            "unmatched_skills": unmatched,
            "additional_skills": suggested,
            "explanation": explanation,
        })

    # Stable tie-breaks make the result reproducible across runs/platforms.
    ranked.sort(key=lambda item: (
        -item["score"],
        -item["cosine_score"],
        -item["skill_coverage"],
        item.get("onet_soc_code", ""),
        item["role"].casefold(),
    ))
    return ranked[:top_n]

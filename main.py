"""SkillPath AI command-line interface (kept for backward compatibility)."""
from __future__ import annotations

from skillpath.config import DEFAULT_DATA_FILE
from skillpath.data import load_roles, vocabulary
from skillpath.recommender import recommend
from skillpath.skills import normalize_skill, parse_skills

TOP_N = 3
DATA_FILE = DEFAULT_DATA_FILE


def main() -> None:
    print("=" * 64)
    print("                 SkillPath AI | Career Recommender")
    print("=" * 64)
    print("Enter at least 3 different skills separated by commas.")
    print("Example: Python, SQL, AWS")
    print("Type 'exit' to quit. Similarity is not a probability of success.\n")

    try:
        roles = load_roles(DATA_FILE, filter_mode="technology")
    except (OSError, ValueError) as exc:
        print(f"Dataset error: {exc}")
        return
    known = vocabulary(roles)

    while True:
        try:
            raw = input("Your skills: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if raw.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        skills = parse_skills(raw)
        if len(skills) < 3:
            print("Please enter at least 3 different skills (comma-separated).\n")
            continue

        unknown = [skill for skill in skills if skill not in known]
        if unknown:
            print("Not present in the selected O*NET technology profiles: " + ", ".join(unknown))
        results = recommend(skills, roles, top_n=TOP_N)
        if not results:
            print("No positive skill overlap was found in the selected profiles. Try other skills.\n")
            continue
        print("\nTop career matches:")
        for rank, role in enumerate(results, start=1):
            print(f"\n{rank}. {role['role']} ({role.get('onet_soc_code') or 'O*NET code unavailable'})")
            print(f"   Combined similarity score: {role['score']:.1%} (not a success probability)")
            print(f"   Matched: {', '.join(role['matched_skills'])}")
            print(f"   Unmatched: {', '.join(role['unmatched_skills']) or 'none'}")
            print(f"   Why: {role['explanation']}")
            print(f"   Explore: {', '.join(role['additional_skills']) or 'no additional profile examples'}")
            if role.get("onet_url"):
                print(f"   O*NET: {role['onet_url']}")
        print()


if __name__ == "__main__":
    main()

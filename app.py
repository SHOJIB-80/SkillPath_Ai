"""Streamlit dashboard for SkillPath AI."""
from __future__ import annotations

import html

import streamlit as st

from skillpath.config import DEFAULT_DATA_FILE, FILTER_LABELS
from skillpath.data import load_roles, vocabulary
from skillpath.recommender import recommend
from skillpath.skills import normalize_skills, parse_skills

st.set_page_config(
    page_title="SkillPath AI",
    page_icon="SP",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #0b1220; color: #f4f7fb; }
    [data-testid="stHeader"] { background: rgba(11,18,32,.9); }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: #f6f8fc; letter-spacing: -.02em; }
    .eyebrow { color: #79aefc; font-size: .78rem; text-transform: uppercase; letter-spacing: .14em; font-weight: 700; }
    .subtle { color: #aab7ca; }
    .skill-chip { display:inline-block; margin: .12rem .28rem .12rem 0; padding:.28rem .62rem; border-radius:999px; background:#17243a; color:#d9e8ff; border:1px solid #2b4163; font-size:.84rem; }
    .score-label { color:#aab7ca; font-size:.88rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #24334b; background: #111c2e; border-radius: 14px; }
    div.stButton > button[kind="primaryFormSubmit"] { background:#3478e5; border-color:#3478e5; font-weight:700; }
    a { color:#8dbaff !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading O*NET occupation profiles…")
def get_roles(mode: str):
    return load_roles(DEFAULT_DATA_FILE, filter_mode=mode)


def chips(values: list[str]) -> str:
    if not values:
        return '<span class="subtle">None</span>'
    return " ".join(
        f'<span class="skill-chip">{html.escape(value)}</span>' for value in values
    )


st.markdown('<div class="eyebrow">DecodeLabs · Career exploration</div>', unsafe_allow_html=True)
st.title("SkillPath AI")
st.markdown(
    "Explore technology careers that overlap with your skills. Recommendations use "
    "O*NET workplace software examples; they are a starting point, not a hiring or "
    "career-success prediction."
)
st.caption("Occupation scope uses configurable O*NET-SOC identifiers. The all-occupations option is available for comparison.")

try:
    all_roles = get_roles("all")
    all_skills = sorted(vocabulary(all_roles))
except (OSError, ValueError) as exc:
    st.error(f"Could not load occupation profiles: {exc}")
    st.info("Keep software_skills.csv in the project folder, then run `python import_onet.py`.")
    st.stop()

filter_options = list(FILTER_LABELS)
with st.form("recommendation_form", clear_on_submit=False):
    scope = st.selectbox(
        "Occupation scope",
        options=filter_options,
        format_func=lambda value: FILTER_LABELS[value],
        index=0,
        help="The default scope uses configured O*NET-SOC prefixes for computer systems, network/database, programming/web, security, and data-science occupations. Review skillpath/config.py for the exact list.",
    )
    chosen_skills = st.multiselect(
        "Search and select technologies",
        options=all_skills,
        placeholder="Type to search, e.g. Python, SQL, AWS",
        help="Choose at least three different skills. Use the field below for labels not listed in the O*NET profile vocabulary.",
    )
    custom_text = st.text_input(
        "Add custom skills (comma-separated)",
        placeholder="For example: Terraform, Snowflake",
    )
    submitted = st.form_submit_button("Generate recommendations", type="primary", use_container_width=True)

if submitted:
    skills = normalize_skills(list(chosen_skills) + parse_skills(custom_text))
    if len(skills) < 3:
        st.session_state.pop("skillpath_result", None)
        st.error("Enter at least three different skills.")
    else:
        try:
            roles = get_roles(scope)
            st.session_state["skillpath_result"] = {
                "skills": skills,
                "scope": scope,
                "results": recommend(skills, roles, top_n=3),
                "known_vocabulary": vocabulary(roles),
                "role_count": len(roles),
            }
        except (OSError, ValueError) as exc:
            st.error(f"Could not generate recommendations: {exc}")

result = st.session_state.get("skillpath_result")
if result:
    st.divider()
    st.subheader("Your results")
    entered = result["skills"]
    known = result["known_vocabulary"]
    absent_from_scope = [skill for skill in entered if skill not in known]
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown("**Selected skills**")
        st.markdown(chips(entered), unsafe_allow_html=True)
    with col_b:
        st.metric("Profiles compared", f"{result['role_count']:,}")
    if absent_from_scope:
        st.warning(
            "These entries are not represented in the selected O*NET occupation profiles, "
            "so they cannot contribute to the similarity component and remain unmatched in coverage: "
            + ", ".join(absent_from_scope)
        )

    matches = result["results"]
    if not matches:
        st.info(
            "No positive skill overlap was found in this occupation scope. The application "
            "does not invent or force a recommendation; try different skills or compare "
            "with the all-occupations scope."
        )
    else:
        st.caption(
            "Combined score = 65% TF-IDF/cosine similarity + 35% inverse-frequency-weighted "
            "skill coverage. These percentages describe profile similarity only—not a probability "
            "of career success, eligibility, or hiring."
        )
        st.markdown("### Compare the top matches")
        chart_data = {
            "Occupation": [f"{rank}. {item['role']}" for rank, item in enumerate(matches, 1)],
            "Similarity score": [item["score"] for item in matches],
        }
        st.bar_chart(chart_data, x="Occupation", y="Similarity score", color="#5b9aff")

        st.markdown("### Career recommendations")
        for rank, role in enumerate(matches, start=1):
            with st.container(border=True):
                head_left, head_right = st.columns([4, 1])
                with head_left:
                    st.markdown(f"#### {rank}. {role['role']}")
                    code = role.get("onet_soc_code") or "O*NET code unavailable"
                    st.markdown(f'<span class="subtle">O*NET-SOC {html.escape(code)}</span>', unsafe_allow_html=True)
                with head_right:
                    st.metric("Similarity", f"{role['score']:.1%}")
                st.progress(min(max(float(role["score"]), 0.0), 1.0), text="Combined profile similarity")

                first, second = st.columns(2)
                with first:
                    st.markdown("**Matched skills**")
                    st.markdown(chips(role["matched_skills"]), unsafe_allow_html=True)
                with second:
                    st.markdown("**Unmatched skills**")
                    st.markdown(chips(role["unmatched_skills"]), unsafe_allow_html=True)

                raw_coverage = len(role["matched_skills"]) / len(entered)
                st.progress(raw_coverage, text=f"Exact entered-skill coverage: {len(role['matched_skills'])}/{len(entered)}")
                st.markdown("**Why this was recommended**")
                st.write(role["explanation"])
                st.markdown("**Other technologies in this O*NET profile**")
                st.caption("Potential exploration topics only; these are not verified mandatory requirements.")
                st.markdown(chips(role["additional_skills"]), unsafe_allow_html=True)
                if role.get("onet_url"):
                    st.link_button("Open official O*NET occupation reference", role["onet_url"])

st.divider()
st.caption(
    "Source: O*NET 31.0 Database, U.S. Department of Labor, Employment and Training Administration, "
    "used under CC BY 4.0. SkillPath AI derives canonical technology aliases and recommendation scores; "
    "those modifications are not endorsed by USDOL/ETA. O*NET software examples are not a complete "
    "inventory of job requirements."
)

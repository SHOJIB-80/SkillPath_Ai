# SkillPath AI

An explainable career-exploration recommender that compares user-entered technology skills with occupation software examples from the O*NET 31.0 Database.

## Overview

SkillPath AI helps users explore technology occupations whose O*NET software profiles overlap with their skills. It provides a Streamlit dashboard and a command-line interface, normalizes common technology aliases, and explains each match using the skills matched and a combined similarity score.

The recommendation score ranks profile similarity; it is not a prediction of job eligibility, hiring, career fit, or career success. O*NET workplace software examples are not a complete list of job skills or verified prerequisites.

## Features

- Streamlit dashboard with searchable O*NET skill selection and comma-separated custom skills.
- Command-line recommender for entering skills interactively.
- Minimum of three distinct skills after normalization and deduplication.
- Technology occupation scope based on configurable O*NET-SOC code prefixes, with an all-occupations comparison option in the dashboard.
- Explainable top-three recommendations showing matched and unmatched skills, profile similarity, weighted coverage, and additional profile technologies.
- Canonical aliases for common names such as `JS`/`JavaScript`, `AWS`/`Amazon Web Services`, and `Postgres`/`PostgreSQL`.
- Reproducible O*NET CSV importer that aggregates source records into occupation profiles and writes a source manifest.
- Unit tests for importer behavior, normalization, filtering, scoring, and recommendation scenarios.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Importer, recommendation logic, dashboard, CLI, and tests |
| Streamlit | Interactive web dashboard |
| scikit-learn | TF-IDF vectorization and cosine similarity |
| NumPy | Score calculation and vector operations |
| O*NET 31.0 Software Skills CSV | Occupation and workplace software-example source data |

## Recommendation Method

Recommendations are limited to profiles with positive skill overlap and are ordered by a combined score:

- **65% TF-IDF/cosine similarity**, with inverse document frequency learned from the selected occupation profiles.
- **35% inverse-frequency-weighted skill coverage**, where skills less common across profiles contribute more than broadly shared skills.
- Configured broad software labels, such as Microsoft Office, Excel, cloud, web browser, and email software, receive an additional weighting penalty.

Unknown skills remain visible as unmatched input and do not silently count as matched coverage. If no positive overlap exists, the recommender returns no recommendations rather than forcing a match. The dashboard's default technology scope is configured in `skillpath/config.py`; the all-occupations option is available for comparison.

## Project Structure

```text
.
├── app.py                     # Streamlit dashboard
├── main.py                    # Command-line recommender
├── import_onet.py             # O*NET source-data importer
├── software_skills.csv        # Original O*NET 31.0 source CSV
├── raw_skills.csv             # Generated occupation profiles
├── data_manifest.json         # Source fingerprint and preprocessing summary
├── sample_skills.csv          # Sample dataset used in tests
├── NOTICE.md                  # O*NET data attribution and modification notice
├── LICENSE                    # MIT license for the project software
├── requirements.txt           # Python dependencies
├── skillpath/
│   ├── config.py              # Paths, occupation filters, and scoring weights
│   ├── data.py                # Profile loading, filtering, and vocabulary
│   ├── preprocessing.py       # O*NET aggregation and manifest generation
│   ├── recommender.py         # Ranking and match explanations
│   └── skills.py              # Skill parsing, normalization, and aliases
└── tests/
    ├── test_import_onet.py    # Importer tests
    └── test_recommender.py    # Recommendation tests
```

## Installation

The project runs locally with Python and does not require a database or API credentials. Python 3.11 is used in the setup commands below.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Data Preparation

The repository includes the O*NET 31.0 Software Skills source file, `software_skills.csv`, and its generated profile data, `raw_skills.csv`. To regenerate the profiles and `data_manifest.json` from the bundled source, run from the project root:

```bash
python import_onet.py
```

The importer groups records by O*NET-SOC code and occupation title, normalizes software-example labels, retains original examples and O*NET hot/in-demand markers in separate fields, skips incomplete and exact duplicate records, and records the source SHA-256 and processing counts in the manifest.

If the source CSV is unavailable, obtain the O*NET 31.0 Software Skills CSV from the [official O*NET source](https://www.onetcenter.org/dictionary/31.0/csv/software_skills.html) and place it in the project root as `software_skills.csv` before running the importer.

## Running the Project

### Streamlit dashboard

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, typically `http://localhost:8501`. Select an occupation scope, choose skills from the searchable profile vocabulary, and enter any additional skills as comma-separated text. Submit at least three distinct skills to display up to three recommendations.

### Command-line interface

```bash
python main.py
```

Enter at least three comma-separated skills at the prompt. Type `exit` or `quit` to end the session.

## Application Workflow

1. The application loads generated occupation profiles from `raw_skills.csv`.
2. The selected O*NET-SOC scope filters the profiles used for comparison.
3. Input skills are normalized to canonical labels and duplicates are removed.
4. The recommender ranks profiles using the configured TF-IDF/cosine and weighted-coverage components.
5. The dashboard or CLI displays the top matches, matched and unmatched skills, an explanation, and additional technologies listed in each profile.

The additional profile technologies are exploration topics, not verified requirements for an occupation.

## Testing

Run the test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

The tests cover data import and manifest generation, duplicate and incomplete source rows, skill normalization, occupation filtering, deterministic ranking, score components, and realistic skill-input scenarios against the bundled profiles.

## Data Attribution and License

The project software is licensed under the [MIT License](LICENSE), with copyright attributed to **SHOJIB-80**. The license for the project software does not replace or change the terms applicable to bundled third-party data.

The included O*NET 31.0 Database information is made available under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Attribution: “This project includes information from the O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA).” SkillPath AI has modified some information through grouping, data cleaning, canonical technology aliases, and recommendation scores. These modifications are not approved, endorsed, or tested by USDOL/ETA. See [NOTICE.md](NOTICE.md) for the data notice and the [official O*NET source](https://www.onetcenter.org/database.html).

## Author

**SHOJIB-80** — [GitHub profile](https://github.com/SHOJIB-80)

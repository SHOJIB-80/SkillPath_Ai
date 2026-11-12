# SkillPath AI — DecodeLabs Project 3

SkillPath AI is an explainable career-exploration recommender built on the official O*NET 31.0 Software Skills data. The project retains the original downloaded CSV, reproducibly aggregates it by O*NET-SOC occupation code, and provides both a Streamlit dashboard and a backwards-compatible command-line interface.

## What changed and why

The earlier recommender compared skills against every occupation in the source. That allowed broad software examples shared by unrelated occupations to produce misleading top matches. The default recommender now uses a transparent list of O*NET-SOC prefixes in `skillpath/config.py`, covering core computer systems, network/database, programming/web, security, and data-science occupations. This is intentionally narrower than the entire `15-12` computer-occupation family; specialized `15-1299` roles not included in the configured list remain in the source and can be viewed with the dashboard's all-occupations comparison. The filter can be edited without changing the scoring logic. Original O*NET occupation titles and SOC codes are preserved, and no title is inserted or promoted because of a particular query. The code families follow O*NET's [2019 O*NET-SOC occupation taxonomy](https://www.onetcenter.org/taxonomy/2019/list.html).

Ranking combines two documented components:

- **65% TF-IDF/cosine similarity**, with inverse document frequency learned from the selected occupation profiles.
- **35% inverse-frequency-weighted skill coverage**, measuring how much of the user's vocabulary is represented by a role. More distinctive terms contribute more than terms common across profiles. Unknown terms remain unmatched and count against coverage instead of disappearing from the denominator.

A small, explicit penalty in `skillpath/config.py` further reduces the influence of broad office/web software tags. Equivalent labels such as `AWS`/`Amazon Web Services`, `JS`/`JavaScript`, `Postgres`/`PostgreSQL`, and `K8s`/`Kubernetes` are normalized in one place; `Node.js` is kept distinct from JavaScript. Only positive-overlap profiles are returned. Unknown skills are disclosed and do not create fabricated matches. Each result reports both score components, matched and unmatched user skills, and other technologies recorded for that occupation.

The combined score is **not** a probability of job eligibility, hiring, or career success.

## Dataset, attribution, and limitations

`software_skills.csv` is the original O*NET 31.0 Software Skills CSV included in this project. Its 31,821 source rows contain an O*NET-SOC code, occupation title, workplace software example, content-model element, and hot-technology/in-demand indicators. The official data dictionary and download are at [O*NET 31.0 Software Skills](https://www.onetcenter.org/dictionary/31.0/csv/software_skills.html); all O*NET 31.0 CSV files are listed at the [O*NET Database page](https://www.onetcenter.org/database.html).

`import_onet.py` creates `raw_skills.csv` and `data_manifest.json`. The manifest records the source-file SHA-256, rows read, skipped duplicates/incomplete rows, profile count, source version, and transformation notes. Preprocessing groups by O*NET-SOC code and title, retains original example names, and stores canonical technology labels and O*NET hot/in-demand examples in separate columns. Canonical aliases and scores are project-derived changes, not additional O*NET observations. The source CSV is never overwritten.

O*NET 31.0 Database data is made available under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). Attribution: “This project includes information from the O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), used under CC BY 4.0. SkillPath AI has modified some information through preprocessing and derived aliases; USDOL/ETA has not approved, endorsed, or tested these modifications. O*NET® is a trademark of USDOL/ETA.” See the [official license](https://www.onetcenter.org/license_db.html).

O*NET workplace software examples are not a complete list of job skills or verified prerequisites. The configured occupation scope is a career-exploration choice, not a qualification or career-fit assessment. O*NET is U.S.-oriented, software names may be product-specific, and profiles can omit technologies a worker uses. A missing match means the provided profile data did not support a recommendation, not that an occupation does not use a skill.

## Project layout

```text
.
├── app.py                     # Streamlit dashboard
├── main.py                    # command-line interface
├── import_onet.py             # reproducible importer entry point
├── software_skills.csv        # original O*NET 31.0 source data
├── raw_skills.csv             # generated occupation profiles
├── data_manifest.json         # source fingerprint and preprocessing summary
├── sample_skills.csv          # small legacy/sample fixture for tests
├── skillpath/
│   ├── config.py              # filters, scoring weights, and paths
│   ├── data.py                # loading and occupation filtering
│   ├── preprocessing.py       # O*NET conversion
│   ├── recommender.py         # ranking and explanations
│   └── skills.py              # skill aliases and input parsing
├── tests/                     # unit and real-data scenario tests
├── requirements.txt
└── .gitignore
```

## Run on Windows with VS Code

Open this project folder in VS Code. In **Terminal → New Terminal**, run these PowerShell commands:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python import_onet.py
python -m streamlit run app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. In VS Code, use **Python: Select Interpreter** and select `.venv\Scripts\python.exe`.

To use the CLI instead of the dashboard:

```powershell
python main.py
```

The provided `software_skills.csv` is the source file. If it is removed, download the O*NET 31.0 CSV from the official source above and save it beside `import_onet.py` as `software_skills.csv`, then run the importer. Do not rename the original O*NET file to `raw_skills.csv`; the importer generates that processed file.

## Test and reproduce

```powershell
python -m unittest discover -s tests -v
```

The suite covers the original sample recommender use cases and adds normalization, minimum-input validation, duplicate/missing source handling, SOC-code filtering, score components, unknown/zero-overlap inputs, deterministic ordering, top-three limits, and four realistic skill scenarios. Scenario tests evaluate whether recommendations are evidence-backed and remain within the selected occupation family; they do not require predetermined job titles. They are functional/relevance guardrails, not a benchmark against observed career outcomes.

The current processed CSV is reproducible from the bundled source. Run the commands above to refresh it and verify the dashboard locally. The only evidence used for matching is the processed O*NET Software Skills profile; no occupational requirements, user data, or success probabilities are invented or stored.

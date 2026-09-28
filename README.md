# Particle Contamination and IRR Analysis

An end-to-end manufacturing analytics project investigating particle contamination across three production stations and its association with IRR.

## Project contents

- `01_Particles_IRR.ipynb` — the complete analysis, including data validation, SQLite modeling, exploratory analysis, statistical tests, SQL examples, and conclusions.
- `particle_irr_enriched.csv` — the source dataset used by the notebook.
- `particles_irr_analysis.db` — the SQLite database consumed by the dashboard.
- `particles_irr_streamlit.py` — an interactive Streamlit dashboard for exploring the results.
- `requirements.txt` — Python dependencies.

## Analysis scope

The analysis compares SUB30, AOI20, and ICT40 across operators, shifts, product lines, particle types, particle sizes, particle metrics, and IRR. It combines descriptive summaries, hypothesis tests, an adjusted multi-factor model, and SQL queries.

The results are observational: statistical associations do not establish physical causation. The CSV does not contain real production timestamps. Any temporal sequence in the analysis is a clearly labeled synthetic proxy derived from sample order and is intended only to demonstrate SQL window functions, not to represent production history.

## Setup and run

Use Python 3.10 or later. From the project directory, install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Open `01_Particles_IRR.ipynb` in Jupyter or VS Code and run its cells from top to bottom. This loads the CSV and creates or refreshes `particles_irr_analysis.db`.

Then start the dashboard:

```bash
streamlit run particles_irr_streamlit.py
```

Keep the CSV, notebook, SQLite database, and Streamlit app in the same project directory.
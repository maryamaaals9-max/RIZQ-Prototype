# RIZQ — Climate Retrofit & Green Jobs Prototype

Interactive Streamlit demonstration for the INT305 Software Engineering project.

## Features
- Dashboard with simulated projects, funding and green-job metrics
- Building assessment and explainable 0–100 retrofit priority score
- Retrofit package recommendations and illustrative cost/energy/CO2 estimates
- Simulated sponsor funding, certified worker assignment and project lifecycle
- Evidence checklist, verifier approval and downloadable impact record
- Project portfolio, methodology and testing guide

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Create a GitHub repository, upload `app.py`, `requirements.txt`, and optionally `README.md`, then deploy from Streamlit Community Cloud. Set main file path to `app.py` and branch to `main`.

**Important:** All demo building records, funding, worker profiles, and performance estimates are synthetic. The priority engine is a transparent weighted scoring model, **not a trained machine-learning model**. Session changes reset when the app restarts; no real payments or certifications occur.

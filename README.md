# Made-in-America Sourcing Assistant

AI-powered matching + distance ranking to help small businesses discover nearby U.S. manufacturers and strengthen local supply chains.

## Live Demo
https://made-in-america-sourcing-assistant-lnetxc3ccaoccn6ok6w5jm.streamlit.app/

## Community Problem
Small businesses often source from distant or overseas suppliers because they lack visibility into nearby American manufacturers. This tool makes it easier to find local suppliers using keyword/fuzzy matching and distance ranking.

## What the App Does
- Takes a user “need” (example: machining, CNC turning, grinding)
- Matches against supplier capability/process/material tags
- Ranks results using:
  - Relevance score (fuzzy text match)
  - Distance score (approx. miles from buyer ZIP)
- Shows:
  - Top 5 table of matches
  - Interactive map with tooltips (supplier names)
  - Supplier “highlights” panel (short descriptions + contact info)

## AI / Matching Approach (MVP)
This MVP uses lightweight “AI-style” techniques:
- Fuzzy matching with RapidFuzz to handle messy real-world keyword searches (partial terms, different phrasing).
- Scoring + ranking to combine relevance with proximity for practical sourcing decisions.

## 📁 Project Structure
.
├── app.py
├── requirements.txt
├── westmoreland_seed_suppliers.csv
├── assets/
│ ├── trump.jpg
│ └── melania.png
└── .streamlit/
└── config.toml

## Run Locally
1) Install dependencies (Streamlit deploys using `requirements.txt`, and local runs should match that). :contentReference[oaicite:1]{index=1}  
```bash
pip install -r requirements.txt
2) Start the app:
streamlit run app.py

Data
- Supplier data lives in westmoreland_seed_suppliers.csv (example fields):
- supplier_name, city/state/zip
- capability_tags, process_tags, material_tags
- website, phone, email
- Short Description

Deployment
- Deployed on Streamlit Community Cloud from this GitHub repo.
- Streamlit Cloud installs dependencies from requirements.txt during build.

Notes
- No secrets/keys required.
- All data is local (CSV) for an easy-to-review competition MVP.

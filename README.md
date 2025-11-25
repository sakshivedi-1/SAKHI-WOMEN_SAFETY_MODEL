# SAKHI – Women Safety Risk & Navigation System

Sakhi is an AI-driven Women Safety Application that analyzes crime patterns,
identifies unsafe zones, and provides safe navigation routes inside Delhi.

### Key Features
- Crime-based risk scoring using weighted hybrid algorithm
- Safety heatmaps for all Delhi police station jurisdictions
- GPS-based manual location safety check
- Route generation to nearest safe zone using OSMnx or Mapbox
- Clean modular architecture (app + datasets + notebooks)
- Visual analytics dashboard built with Streamlit & Folium



### Project Structure
SAKHI_WOMEN_SAFETY_APP/

│
├── app/

│   ├── __pycache__/               # auto-created (ignored in .gitignore)

│   ├── app.py                     # MAIN Streamlit Application

│   ├── gps_utils.py               # Safety logic helpers

│   ├── navigation_route.py        # Routing logic (OSM / Mapbox)

│   ├── women_safety_heatmap.html  # Optional saved 

│   ├── women_safety_markermap.html# Optional saved map

│   └── cache/                     # Optional cache folder (ignored in git)

│
├── dataset/

│   ├── crime.csv

│   ├── delhi.geojson

│   ├── final_women_safety_data.csv

│   ├── map.geojson

│   └── preprocessed_data.csv

│
├── notebooks/

│   ├── data_preprocessing.ipynb

│   ├── feature_engineering.ipynb

│   └── visualizations.ipynb

│
├── .gitignore

├── LICENSE

├── README.md

└── requirements.txt

###  Tech Stack
- **Python**
- **Streamlit**
- **Folium / HeatMaps**
- **OSMnx + NetworkX** (offline routing)
- **Mapbox Directions API** (online routing)
- **Pandas / NumPy / Scikit-learn**

### Data Sources
- Delhi crime and GPS coordinates (collected manually)
- Delhi administrative boundaries from GeoJSON (public domain)

###  Risk Score Model
Risk score is computed using:
hybrid_score = Σ( feature_value * severity_weight * importance_weight )
## Installation
git clone "project_link"

pip install -r requirements.txt

streamlit run app/app.py



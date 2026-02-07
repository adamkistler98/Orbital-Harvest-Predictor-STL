# 🛰️ Orbital Harvest Predictor // St. Louis

![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![Python](https://img.shields.io/badge/Backend-Python-3776AB?style=for-the-badge&logo=python)
![Sentinel Hub](https://img.shields.io/badge/Data-Sentinel_Hub-009900?style=for-the-badge)
![GitLab CI](https://img.shields.io/badge/Pipeline-GitLab_CI-FC6D26?style=for-the-badge&logo=gitlab)

**Orbital Harvest** is a cloud-native geospatial dashboard designed to monitor and forecast agricultural health in the St. Louis region.

By ingesting multi-spectral imagery from the **European Space Agency's Sentinel-2 constellation**, this application calculates the **Normalized Difference Vegetation Index (NDVI)** to quantify biomass density. It then applies a linear regression model to 4 years of historical data to predict future crop yields.

---

## 📸 Dashboard Preview

*(Place a screenshot of your app here - `screenshots/dashboard_v1.png`)*

---

## 🧠 The Science: Spectral Analysis

This project relies on the fact that healthy vegetation reflects massive amounts of **Near-Infrared (NIR)** light, which is invisible to the human eye, while absorbing Red light for photosynthesis.



**The Formula:**
$$NDVI = \frac{(NIR - Red)}{(NIR + Red)}$$

* **High NDVI (0.6 - 0.9):** Dense, healthy canopy (Peak Summer).
* **Low NDVI (0.0 - 0.2):** Fallow soil or stressed crops (Winter).
* **Negative NDVI:** Water or Clouds.

---

## 🏗️ Architecture

This project demonstrates a **Platform Engineering** approach to data science:

1.  **Ingest Layer:** Connects to the Sentinel Hub API to fetch **L1C (Top-of-Atmosphere)** spectral bands.
2.  **Processing Layer:** Python-based `pandas` & `numpy` pipeline filters cloud cover and computes NDVI indices locally.
3.  **Analysis Layer:** `scikit-learn` Linear Regression model trains on 4+ years of time-series data to forecast yield trends.
4.  **Presentation Layer:** Streamlit dashboard provides interactive visualization and "Ground Truth" verification via True Color satellite imagery.

---

## 🚀 Local Installation & Setup

### Prerequisites
* Python 3.9+
* Sentinel Hub Account (Free Trial) for API Credentials

### 1. Clone the Repository
```bash
git clone [https://gitlab.com/your-username/orbital-harvest-predictor.git](https://gitlab.com/your-username/orbital-harvest-predictor.git)
cd orbital-harvest-predictor

pip install -r requirements.txt

Linux/Mac:
export SH_CLIENT_ID="your_client_id"
export SH_CLIENT_SECRET="your_client_secret"

Windows/Powershell:
$env:SH_CLIENT_ID="your_client_id"
$env:SH_CLIENT_SECRET="your_client_secret"

☁️ Deployment (Streamlit Cloud)
This project is configured for continuous deployment.

Push changes to main branch.

Streamlit Cloud detects the commit and re-builds the container.

Secrets are managed via the Streamlit Secrets Manager (not in code).

🛠️ Technology Stack
Frontend: Streamlit

Satellite API: SentinelHub-py

Data Processing: Pandas, NumPy

Machine Learning: Scikit-Learn (Linear Regression)

CI/CD: GitLab CI

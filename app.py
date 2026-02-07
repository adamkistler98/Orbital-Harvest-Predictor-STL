import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_visual_confirm
from src.forecaster import predict_health

# 1. PAGE CONFIG
st.set_page_config(page_title="ORBITAL HARVEST // OPS", page_icon="🛰️", layout="wide")

# 2. STEALTH MODE CSS (Fixed Sidebar)
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* SIDEBAR Background & Text - The Fix */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
        border-right: 1px solid #00ff41;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #00ff41 !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        color: #00ff41;
        background-color: #1c1f26;
        border: 1px solid #00ff41;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #00ff41 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. HEADER
st.title("🛰️ ORBITAL HARVEST // GLOBAL OPS")
st.markdown("`SYSTEM STATUS: ONLINE` | `SATELLITE LINK: SENTINEL-2` | `COVERAGE: UNITED STATES`")
st.markdown("---")

# 4. SIDEBAR CONTROLS
st.sidebar.header("📍 TARGET ACQUISITION")

targets = {
    "St. Louis, MO (Wheat/Corn)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Select Operation Zone", list(targets.keys()))

if target_name == "Custom Coordinates":
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("Enter BBox", str(default_coords))
else:
    coords_input = str(targets[target_name])
    st.sidebar.info(f"Locked on: {target_name}")

if st.sidebar.button("INITIATE ANALYSIS"):
    with st.spinner("ESTABLISHING UPLINK... DOWNLOADING TELEMETRY..."):
        try:
            bbox = eval(coords_input)
            end_d = date.today()
            start_d = end_d - timedelta(days=90)
            
            # 1. Get Data
            dates, ndvi_scores = get_sentinel_data(bbox, (start_d, end_d))
            
            if not dates:
                st.error("NO CLEAR DATA FOUND (CLOUD COVER OR BAD COORDS). RETRY.")
                st.stop()

            # 2. Get Visual
            last_valid_date = dates[-1]
            visual_image = get_visual_confirm(bbox, last_valid_date)

            # 3. Run Forecast (Now with Confidence!)
            future_days, predicted_ndvi, trend, confidence = predict_health(dates, ndvi_scores)

            # --- DASHBOARD UI ---
            
            # Row 1: Map & Visual
            col_img, col_map = st.columns([1, 1])
            with col_img:
                st.subheader("📸 VISUAL CONFIRMATION")
                if visual_image is not None:
                    st.image(visual_image, caption=f"Satellite Capture: {last_valid_date}", use_container_width=True)
                else:
                    st.warning("Visual feed unavailable.")
            with col_map:
                st.subheader("🗺️ GEOLOCATION")
                lat_center = (bbox[1] + bbox[3]) / 2
                lon_center = (bbox[0] + bbox[2]) / 2
                map_df = pd.DataFrame({'lat': [lat_center], 'lon': [lon_center]})
                st.map(map_df, zoom=12)

            st.markdown("---")
            
            # Row 2: Metrics
            st.subheader("📈 INTELLIGENCE REPORT")
            m1, m2, m3, m4 = st.columns(4)
            
            current_health = ndvi_scores[-1]
            
            m1.metric("CURRENT BIOMASS", f"{current_health:.2f}")
            m2.metric("DATA POINTS", f"{len(dates)}")
            
            # Trend Logic
            if trend > 0.001:
                m3.success("TREND: POSITIVE")
            elif trend < -0.001:
                m3.error("TREND: NEGATIVE")
            else:
                m3.warning("TREND: STABLE")
            
            # Confidence Logic
            conf_percent = confidence * 100
            if conf_percent > 70:
                m4.metric("CONFIDENCE", f"{conf_percent:.1f}%", delta="HIGH ACCURACY")
            elif conf_percent > 40:
                m4.metric("CONFIDENCE", f"{conf_percent:.1f}%", delta="MODERATE", delta_color="off")
            else:
                m4.metric("CONFIDENCE", f"{conf_percent:.1f}%", delta="LOW / NOISY DATA", delta_color="inverse")

            # Row 3: The Chart
            chart_data = pd.DataFrame({
                "Date": dates,
                "Actual Health": ndvi_scores
            }).set_index("Date")
            st.line_chart(chart_data)
                
        except Exception as e:
            st.error(f"SYSTEM FAILURE: {e}")

else:
    st.info("AWAITING OPERATOR INPUT. SELECT TARGET AND INITIATE.")

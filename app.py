import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_visual_confirm
from src.forecaster import predict_health

# 1. PAGE CONFIG (Must be first)
st.set_page_config(page_title="ORBITAL HARVEST // OPS", page_icon="🛰️", layout="wide")

# 2. STEALTH MODE CSS (Injecting "Hacker" visual styles)
st.markdown("""
    <style>
    /* Force dark background and monospace fonts */
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
        font-family: 'Courier New', Courier, monospace;
    }
    /* Customize input boxes */
    .stTextInput > div > div > input {
        color: #00ff41;
        background-color: #262730;
        border: 1px solid #00ff41;
    }
    /* Custom headers */
    h1, h2, h3 {
        color: #ffffff !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        color: #00ff41 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. HEADER
st.title("🛰️ ORBITAL HARVEST // GLOBAL OPS")
st.markdown("`SYSTEM STATUS: ONLINE` | `SATELLITE LINK: SENTINEL-2` | `COVERAGE: UNITED STATES`")
st.markdown("---")

# 4. SIDEBAR CONTROLS
st.sidebar.header("📍 TARGET ACQUISITION")

# Pre-set Targets for easy demoing
targets = {
    "St. Louis, MO (Wheat/Corn)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Select Operation Zone", list(targets.keys()))

if target_name == "Custom Coordinates":
    # Default to STL if they choose Custom
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("Enter BBox [min_lon, min_lat, max_lon, max_lat]", str(default_coords))
else:
    coords_input = str(targets[target_name])
    st.sidebar.info(f"Locked on: {target_name}")

if st.sidebar.button("INITIATE ANALYSIS"):
    with st.spinner("ESTABLISHING UPLINK... DOWNLOADING TELEMETRY..."):
        
        # A. PARSE INPUT
        try:
            bbox = eval(coords_input)
            
            # B. FETCH DATA (Last 90 days for better trend lines)
            end_d = date.today()
            start_d = end_d - timedelta(days=90)
            
            # 1. Get The Math (NDVI)
            dates, ndvi_scores = get_sentinel_data(bbox, (start_d, end_d))
            
            if not dates:
                st.error("NO CLEAR DATA FOUND (CLOUD COVER OR BAD COORDS). RETRY.")
                st.stop()

            # 2. Get The Picture (Visual Proof)
            # We try to fetch the image from the LAST successful data point
            last_valid_date = dates[-1]
            visual_image = get_visual_confirm(bbox, last_valid_date)

            # C. DISPLAY DASHBOARD
            
            # Row 1: The "Eyes" (Map & Satellite Image)
            col_img, col_map = st.columns([1, 1])
            
            with col_img:
                st.subheader("📸 VISUAL CONFIRMATION")
                if visual_image is not None:
                    st.image(visual_image, caption=f"Satellite Capture: {last_valid_date}", use_container_width=True)
                else:
                    st.warning("Visual feed unavailable for this date.")

            with col_map:
                st.subheader("🗺️ GEOLOCATION")
                # Calculate center point for the map pin
                lat_center = (bbox[1] + bbox[3]) / 2
                lon_center = (bbox[0] + bbox[2]) / 2
                map_df = pd.DataFrame({'lat': [lat_center], 'lon': [lon_center]})
                st.map(map_df, zoom=12)

            st.markdown("---")

            # Row 2: The "Brains" (Forecasting)
            future_days, predicted_ndvi, trend = predict_health(dates, ndvi_scores)
            
            st.subheader("📈 BIOMASS PREDICTION MODEL")
            
            # Create a slick chart
            chart_data = pd.DataFrame({
                "Date": dates,
                "Actual Health": ndvi_scores
            }).set_index("Date")
            
            st.line_chart(chart_data)
            
            # Row 3: Mission Report
            m1, m2, m3 = st.columns(3)
            current_health = ndvi_scores[-1]
            
            m1.metric("CURRENT BIOMASS (NDVI)", f"{current_health:.2f}")
            m2.metric("DATA POINTS ANALYZED", f"{len(dates)}")
            
            if trend > 0.001:
                m3.success("TREND: POSITIVE YIELD")
            elif trend < -0.001:
                m3.error("TREND: NEGATIVE YIELD")
            else:
                m3.warning("TREND: STABLE")
                
        except Exception as e:
            st.error(f"SYSTEM FAILURE: {e}")

else:
    st.info("AWAITING OPERATOR INPUT. SELECT TARGET AND INITIATE.")

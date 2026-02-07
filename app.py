import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_filmstrip
from src.forecaster import predict_health

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Orbital Harvest // Pro", 
    page_icon="🛰️", 
    layout="wide"
)

# 2. TITLE (Minimalist, No Images)
st.title("🛰️ Orbital Harvest // Command Center")
st.markdown("---")

# 3. SIDEBAR CONTROLS
st.sidebar.header("📍 Target Selector")

targets = {
    "St. Louis, MO (Grafton Farms)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Region:", list(targets.keys()))

if target_name == "Custom Coordinates":
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("BBox Coordinates:", str(default_coords))
else:
    coords_input = str(targets[target_name])

st.sidebar.markdown("---")
st.sidebar.header("🗓️ Analysis Window")

# MANUAL DATE PICKER (Default: 2 Years)
col_start, col_end = st.sidebar.columns(2)
start_d = col_start.date_input("Start", date.today() - timedelta(days=730))
end_d = col_end.date_input("End", date.today())

if st.sidebar.button("📡 Acquire Satellite Feed"):
    with st.spinner("Establishing Uplink... Downloading Raw Telemetry..."):
        try:
            bbox = eval(coords_input)
            
            # 1. FETCH DATA (Aggressive Mode)
            dates, ndvi_scores = get_sentinel_data(bbox, (start_d, end_d))
            
            # 2. ERROR HANDLING (Soft Fail)
            if not dates or len(dates) < 3:
                st.warning(f"Low Signal: Only found {len(dates)} clear data points. Try a larger date range or different location.")
                # We do NOT stop. We try to plot what we have.
            
            # 3. RUN FORECAST
            if len(dates) > 5:
                future_days, predicted_ndvi, trend, confidence = predict_health(dates, ndvi_scores)
            else:
                trend = 0
                confidence = 0

            # --- VISUAL FEED (THE FILMSTRIP) ---
            st.subheader("📸 Raw Satellite Feed (Visual Verification)")
            # Grab 4 actual images from the timeframe
            filmstrip = get_filmstrip(bbox, dates, limit=4)
            
            if filmstrip:
                cols = st.columns(len(filmstrip))
                for idx, (img_date, img_data) in enumerate(filmstrip):
                    with cols[idx]:
                        st.image(img_data, caption=f"Capture: {img_date}", use_container_width=True)
            else:
                st.warning("Visual feed unavailable for this sector.")
            
            st.markdown("---")

            # --- ANALYTICS ---
            col_chart, col_metrics = st.columns([3, 1])

            with col_metrics:
                st.subheader("Telemetry")
                current_health = ndvi_scores[-1] if ndvi_scores else 0
                
                st.metric("Current NDVI", f"{current_health:.2f}")
                st.metric("Passes Analyzed", f"{len(dates)}")
                
                if trend > 0.0001:
                    st.metric("Trend", "Positive", delta="Growing")
                elif trend < -0.0001:
                    st.metric("Trend", "Negative", delta="Declining")
                else:
                    st.metric("Trend", "Stable")
                
                st.metric("Model Confidence", f"{confidence*100:.1f}%")

            with col_chart:
                st.subheader("Biomass Trajectory")
                chart_data = pd.DataFrame({
                    "Date": dates,
                    "NDVI (Biomass)": ndvi_scores
                }).set_index("Date")
                st.line_chart(chart_data)

            # --- DATA EXPORT ---
            with st.expander("💾 Download Raw Mission Data"):
                df_export = pd.DataFrame({"Date": dates, "NDVI": ndvi_scores})
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button("Download .CSV", csv, "orbital_data.csv", "text/csv")

        except Exception as e:
            st.error(f"Critical System Failure: {e}")

else:
    st.info("System Ready. Select Parameters and Initiate Uplink.")

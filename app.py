import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_visual_confirm
from src.forecaster import predict_health

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Orbital Harvest // St. Louis", 
    page_icon="🌾", 
    layout="wide"
)

# 2. TITLE
st.title("🌾 Orbital Harvest Predictor")
st.markdown("Automated crop yield forecasting using Sentinel-2 satellite imagery.")
st.markdown("---")

# 3. SIDEBAR CONTROLS
st.sidebar.header("Configuration")

# Target Selector
targets = {
    "St. Louis, MO (Grafton Farms)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Select Location:", list(targets.keys()))

if target_name == "Custom Coordinates":
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("Enter BBox Coordinates:", str(default_coords))
else:
    coords_input = str(targets[target_name])

st.sidebar.markdown("---")

# Date Picker (Manual)
st.sidebar.header("Analysis Period")
# Default to 1 Year (365 days) - This is the safest default to ensure you find data
default_start = date.today() - timedelta(days=365)
start_d = st.sidebar.date_input("Start Date", default_start)
end_d = st.sidebar.date_input("End Date", date.today())

if st.sidebar.button("Run Analysis"):
    with st.spinner("Fetching satellite data..."):
        try:
            bbox = eval(coords_input)
            
            # 1. GET DATA
            dates, ndvi_scores = get_sentinel_data(bbox, (start_d, end_d))
            
            # Check if we got anything
            if not dates:
                st.error("No clear data found for this date range. Try expanding the range to 1 year.")
                st.stop()
                
            # 2. GET VISUAL (Just the latest valid one)
            last_date = dates[-1]
            visual_image = get_visual_confirm(bbox, last_date)
            
            # 3. RUN FORECAST
            future_days, predicted_ndvi, trend, confidence = predict_health(dates, ndvi_scores)

            # --- DASHBOARD ---
            
            # Row 1: Visuals
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Satellite Feed")
                if visual_image is not None:
                    st.image(visual_image, caption=f"Real Image: {last_date}", use_container_width=True)
                else:
                    st.warning("Visual preview unavailable.")
                    
            with col2:
                st.subheader("Crop Health Trends (NDVI)")
                chart_data = pd.DataFrame({
                    "Date": dates,
                    "Health Index": ndvi_scores
                }).set_index("Date")
                st.line_chart(chart_data)

            # Row 2: Metrics
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric("Current Health", f"{ndvi_scores[-1]:.2f}")
            m2.metric("Images Analyzed", len(dates))
            
            if trend > 0.0001:
                m3.metric("Trend", "Growing", delta="+Positive")
            elif trend < -0.0001:
                m3.metric("Trend", "Declining", delta="-Negative")
            else:
                m3.metric("Trend", "Stable", delta="Neutral")
                
            m4.metric("Confidence", f"{confidence*100:.1f}%")
            
            # Data Export
            with st.expander("View Raw Data"):
                df = pd.DataFrame({"Date": dates, "NDVI": ndvi_scores})
                st.dataframe(df)

        except Exception as e:
            st.error(f"Error: {e}")

else:
    st.info("Select a location and date range, then click 'Run Analysis'.")

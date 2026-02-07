import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_visual_confirm
from src.forecaster import predict_health

# 1. PAGE CONFIG
st.set_page_config(page_title="Orbital Harvest", page_icon="🌾", layout="wide")

# 2. HEADER
st.title("🌾 Orbital Harvest Predictor")
st.markdown("---")

# 3. SIDEBAR
st.sidebar.header("Configuration")

# Credential Check
if "SH_CLIENT_ID" in st.secrets:
    st.sidebar.success("🔑 Keys Loaded from Secrets")
else:
    st.sidebar.error("❌ Keys NOT Found! Check .streamlit/secrets.toml")

targets = {
    "St. Louis, MO (Grafton Farms)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Select Target:", list(targets.keys()))

if target_name == "Custom Coordinates":
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("Coordinates:", str(default_coords))
else:
    coords_input = str(targets[target_name])

st.sidebar.markdown("---")
st.sidebar.header("Timeframe")

# Use 2 Years to be safe
default_start = date.today() - timedelta(days=730)
start_d = st.sidebar.date_input("Start Date", default_start)
end_d = st.sidebar.date_input("End Date", date.today())

# CONNECTION TEST BUTTON
if st.sidebar.button("🛠️ Test Connection"):
    with st.sidebar.status("Testing API Link..."):
        try:
            # Try to fetch 1 day of data
            test_bbox = [-90.44, 38.97, -90.43, 38.98]
            d, s = get_sentinel_data(test_bbox, (date.today()-timedelta(days=10), date.today()))
            st.write(f"Response Length: {len(d)}")
            if len(d) == 0:
                st.error("API Connected but returned Empty Data.")
            else:
                st.success("API Operational!")
        except Exception as e:
            st.error(f"Connection Failed: {e}")

if st.button("Run Analysis"):
    with st.spinner("Analyzing Satellite Feed..."):
        try:
            bbox = eval(coords_input)
            
            # 1. FETCH
            dates, ndvi_scores = get_sentinel_data(bbox, (start_d, end_d))
            
            # Debug Message if empty
            if not dates:
                st.error(f"No Data Found. \n1. Check Coordinates: {bbox} \n2. Check Dates: {start_d} to {end_d} \n3. Verify your Sentinel Hub Account is Active.")
                st.stop()
            
            # 2. VISUAL
            last_date = dates[-1]
            visual_image = get_visual_confirm(bbox, last_date)
            
            # 3. FORECAST
            trend = 0
            confidence = 0
            if len(dates) > 10:
                future_days, predicted_ndvi, trend, confidence = predict_health(dates, ndvi_scores)

            # --- DISPLAY ---
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Satellite Feed")
                if visual_image is not None:
                    st.image(visual_image, caption=f"Capture Date: {last_date}", use_container_width=True)
                else:
                    st.warning("Visual unavailable.")

            with col2:
                st.subheader("Crop Health (NDVI)")
                chart_data = pd.DataFrame({
                    "Date": dates,
                    "Health Index": ndvi_scores
                }).set_index("Date")
                st.line_chart(chart_data)

            # METRICS
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric("Current Health", f"{ndvi_scores[-1]:.2f}")
            m2.metric("Images Processed", len(dates))
            
            if trend > 0:
                m3.metric("Trend", "Positive", delta="Growing")
            else:
                m3.metric("Trend", "Negative", delta="Declining")
                
            m4.metric("Confidence", f"{confidence*100:.1f}%")
            
            with st.expander("Raw Data"):
                df = pd.DataFrame({"Date": dates, "NDVI": ndvi_scores})
                st.dataframe(df)

        except Exception as e:
            st.error(f"Error: {e}")

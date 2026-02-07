import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_visual_confirm
from src.forecaster import predict_health

# 1. PAGE CONFIG (Standard White Theme)
st.set_page_config(
    page_title="Orbital Harvest Predictor", 
    page_icon="🌾", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. WELCOME HEADER
# We use a nice banner image
st.image("https://images.unsplash.com/photo-1625246333195-58197bd47d26?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
st.title("🌾 Orbital Harvest Predictor")
st.markdown("""
**Welcome to the St. Louis Regional Yield Forecast System.** This tool utilizes European Space Agency (Sentinel-2) satellite feeds to track biomass development 
and predict crop yields using linear regression modeling.
""")
st.markdown("---")

# 3. SIDEBAR CONTROLS
st.sidebar.header("📍 Region Selector")

targets = {
    "St. Louis, MO (Wheat/Corn)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Choose a Target Zone:", list(targets.keys()))

if target_name == "Custom Coordinates":
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("Enter BBox Coordinates:", str(default_coords))
else:
    coords_input = str(targets[target_name])
    st.sidebar.success(f"📍 Location Locked: {target_name}")

if st.sidebar.button("🚀 Run Analysis"):
    with st.spinner("Connecting to Sentinel-2 Satellite Network..."):
        try:
            bbox = eval(coords_input)
            end_d = date.today()
            
            # FIXED: Look back 365 days (1 Full Year) to ensure we find clear data
            start_d = end_d - timedelta(days=365)
            
            # 1. Get Data
            dates, ndvi_scores = get_sentinel_data(bbox, (start_d, end_d))
            
            if not dates:
                st.warning("⚠️ No clear satellite data found for this period. Try a different location or season.")
                st.stop()

            # 2. Get Visual & Forecast
            last_valid_date = dates[-1]
            visual_image = get_visual_confirm(bbox, last_valid_date)
            future_days, predicted_ndvi, trend, confidence = predict_health(dates, ndvi_scores)

            # --- TABS INTERFACE ---
            tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🛰️ Visual Confirmation", "💾 Raw Data"])

            with tab1:
                st.subheader("Crop Health Forecast")
                
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                current_health = ndvi_scores[-1]
                conf_percent = confidence * 100
                
                m1.metric("Current NDVI", f"{current_health:.2f}", delta="Live from Space")
                m2.metric("Data Points", f"{len(dates)}", help="Number of cloud-free images analyzed")
                
                if trend > 0.001:
                    m3.metric("Trend", "Growing", delta="Positive", delta_color="normal")
                elif trend < -0.001:
                    m3.metric("Trend", "Declining", delta="Negative", delta_color="inverse")
                else:
                    m3.metric("Trend", "Stable", delta="Neutral", delta_color="off")
                
                # Color code confidence
                if conf_percent > 70:
                    m4.metric("Model Confidence", f"{conf_percent:.1f}%", delta="High Accuracy")
                elif conf_percent > 40:
                    m4.metric("Model Confidence", f"{conf_percent:.1f}%", delta="Moderate", delta_color="off")
                else:
                    m4.metric("Model Confidence", f"{conf_percent:.1f}%", delta="Low / Noisy", delta_color="inverse")

                # The Main Chart
                chart_data = pd.DataFrame({
                    "Date": dates,
                    "Actual Health": ndvi_scores
                }).set_index("Date")
                st.line_chart(chart_data)
                
                st.info(f"ℹ️ Prediction Model based on {len(dates)} satellite passes over the last 365 days.")

            with tab2:
                st.subheader("Ground Truth Validation")
                col_img, col_map = st.columns(2)
                
                with col_img:
                    st.markdown("**Latest Satellite Pass (True Color)**")
                    if visual_image is not None:
                        st.image(visual_image, caption=f"Captured on {last_valid_date}", use_container_width=True)
                    else:
                        st.warning("Visual feed unavailable.")
                
                with col_map:
                    st.markdown("**Geolocation**")
                    lat_center = (bbox[1] + bbox[3]) / 2
                    lon_center = (bbox[0] + bbox[2]) / 2
                    map_df = pd.DataFrame({'lat': [lat_center], 'lon': [lon_center]})
                    st.map(map_df, zoom=13)

            with tab3:
                st.subheader("Export Data")
                st.markdown("Download the processed spectral data for your own analysis.")
                
                df_export = pd.DataFrame({
                    "Date": dates,
                    "NDVI_Score": ndvi_scores,
                    "Location": target_name
                })
                
                st.dataframe(df_export)
                
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "orbital_harvest_data.csv",
                    "text/csv",
                    key='download-csv'
                )
                
        except Exception as e:
            st.error(f"Analysis Failed: {e}")

else:
    st.info("👈 Select a region and click 'Run Analysis' to begin.")

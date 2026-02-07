import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data, get_visual_confirm
from src.forecaster import predict_health

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Orbital Harvest // 4-Year Analysis", 
    page_icon="🛰️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. HEADER
st.image("https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
st.title("🛰️ Orbital Harvest // Long-Range Predictor")
st.markdown("""
**Historical Satellite Intelligence System.** Analyzing 4 years of Sentinel-2 multispectral data to forecast crop yields in the St. Louis region.
""")
st.markdown("---")

# 3. SIDEBAR CONTROLS
st.sidebar.header("📍 Mission Control")

targets = {
    "St. Louis, MO (Grafton Farms)": [-90.44, 38.97, -90.43, 38.98],
    "Napa Valley, CA (Vineyards)": [-122.28, 38.42, -122.27, 38.43],
    "Des Moines, IA (Corn Belt)": [-93.62, 41.58, -93.61, 41.59],
    "Custom Coordinates": None
}

target_name = st.sidebar.selectbox("Select Target Zone:", list(targets.keys()))

if target_name == "Custom Coordinates":
    default_coords = [-90.44, 38.97, -90.43, 38.98]
    coords_input = st.sidebar.text_input("Enter BBox Coordinates:", str(default_coords))
else:
    coords_input = str(targets[target_name])
    st.sidebar.success(f"📍 Locked: {target_name}")

st.sidebar.markdown("---")
st.sidebar.header("🗓️ Time Horizon")

# DEFAULT: 4 Years back
default_start = date.today() - timedelta(days=1460)
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", date.today())

if st.sidebar.button("🚀 Initiate 4-Year Scan"):
    with st.spinner("Downloading 4 Years of Satellite Imagery... (This may take 10s)"):
        try:
            bbox = eval(coords_input)
            
            # 1. Get Data (The Force Fetch)
            dates, ndvi_scores = get_sentinel_data(bbox, (start_date, end_date))
            
            if not dates or len(dates) < 5:
                st.error("⚠️ Insufficient data found. Try expanding the date range further.")
                st.stop()

            # 2. Get Visuals (The "Seasonal Contrast")
            # We grab one image from Summer (High NDVI) and one from Winter (Low NDVI)
            df = pd.DataFrame({'date': dates, 'ndvi': ndvi_scores})
            
            # Find the "Best Day" (Max Green) and "Worst Day" (Winter)
            best_day = df.loc[df['ndvi'].idxmax()]['date']
            worst_day = df.loc[df['ndvi'].idxmin()]['date']
            
            img_summer = get_visual_confirm(bbox, best_day)
            img_winter = get_visual_confirm(bbox, worst_day)

            # 3. Run Forecast
            future_days, predicted_ndvi, trend, confidence = predict_health(dates, ndvi_scores)

            # --- TABS UI ---
            tab1, tab2, tab3 = st.tabs(["📊 Long-Range Dashboard", "📸 Real Satellite Imagery", "💾 Data Export"])

            with tab1:
                st.subheader("4-Year Crop Health Trends")
                
                m1, m2, m3, m4 = st.columns(4)
                current_health = ndvi_scores[-1]
                conf_percent = confidence * 100
                
                m1.metric("Current Health Index", f"{current_health:.2f}", delta="NDVI Score")
                m2.metric("Images Analyzed", f"{len(dates)}", help="Total cloud-free satellite passes")
                
                # Trend Logic
                if trend > 0.0001:
                    m3.metric("Long-Term Trend", "Improving", delta="Positive")
                elif trend < -0.0001:
                    m3.metric("Long-Term Trend", "Degrading", delta="Negative")
                else:
                    m3.metric("Long-Term Trend", "Stable", delta="Neutral")
                
                m4.metric("Model Confidence", f"{conf_percent:.1f}%")

                # The "Money Chart" - 4 Years of Data
                chart_data = df.set_index("date")
                st.line_chart(chart_data)
                st.caption(f"Visualizing crop biomass fluctuations from {start_date} to {end_date}.")

            with tab2:
                st.subheader("Seasonal Contrast (Visual Proof)")
                st.markdown("Comparing the field during **Peak Season** vs **Off-Season** to verify data integrity.")
                
                col_sum, col_win = st.columns(2)
                
                with col_sum:
                    st.markdown(f"**🟩 Peak Summer ({best_day})**")
                    if img_summer is not None:
                        st.image(img_summer, use_container_width=True)
                    else:
                        st.warning("Image unavailable.")
                
                with col_win:
                    st.markdown(f"**🟫 Deep Winter ({worst_day})**")
                    if img_winter is not None:
                        st.image(img_winter, use_container_width=True)
                    else:
                        st.warning("Image unavailable.")

            with tab3:
                st.subheader("Raw Spectral Data")
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Full History (CSV)",
                    csv,
                    "orbital_harvest_4year.csv",
                    "text/csv"
                )
                
        except Exception as e:
            st.error(f"System Error: {e}")

else:
    st.info("👈 Select a date range (up to 4 years) and click 'Initiate Scan'.")

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from src.satellite import get_sentinel_data # (Assume this exists from previous step)
from src.forecaster import predict_health

st.set_page_config(page_title="Orbital Harvest Predictor STL", page_icon="🌾")

st.title("🌾 Orbital Harvest Predictor STL")
st.markdown("**St. Louis Regional Yield Forecast System**")

# --- SIDEBAR CONFIG ---
st.sidebar.header("Configuration")
# Default: A farm near Grafton, IL (Just north of STL)
default_coords = [-90.44, 38.97, -90.43, 38.98]
coords = st.sidebar.text_input("Coordinates", str(default_coords))

if st.sidebar.button("Run Forecast Model"):
    with st.spinner("Acquiring Satellite Data & Training Model..."):
        
        # 1. Fetch Historical Data (Last 60 Days)
        # (Mocking data here for the example, in real life this calls src.satellite)
        # We simulate a "growing season" where health is improving
        dates = pd.date_range(end=date.today(), periods=10)
        ndvi_scores = np.linspace(0.2, 0.6, 10) + np.random.normal(0, 0.05, 10) # Adding noise
        
        # 2. Run the Prediction
        future_days, predicted_ndvi, trend = predict_health(dates, ndvi_scores)
        
        # 3. Display The "Verdict"
        st.subheader("Yield Forecast")
        col1, col2, col3 = st.columns(3)
        
        current_health = ndvi_scores[-1]
        predicted_health = predicted_ndvi[-1]
        
        col1.metric("Current Health (NDVI)", f"{current_health:.2f}")
        col2.metric("Predicted Health (14 Days)", f"{predicted_health:.2f}", 
                    delta=f"{(predicted_health - current_health):.2f}")
        
        with col3:
            if trend > 0.005:
                st.success("🚀 Trend: STRONG GROWTH")
            elif trend < -0.005:
                st.error("📉 Trend: CROP FAILURE LIKELY")
            else:
                st.warning("➡️ Trend: STAGNANT")

        # 4. The "Money Chart"
        # We combine Past (Actual) and Future (Predicted) into one graph
        st.subheader("Crop Health Trajectory")
        
        chart_data = pd.DataFrame({
            "Date": dates,
            "Actual Health": ndvi_scores,
            "Forecast": [None]*len(dates) # Placeholder
        })
        
        # Add future dates
        future_dates = [dates[-1] + timedelta(days=int(i)) for i in range(1, 15)]
        future_df = pd.DataFrame({
            "Date": future_dates,
            "Actual Health": [None]*14,
            "Forecast": predicted_ndvi
        })
        
        full_df = pd.concat([chart_data, future_df]).set_index("Date")
        
        st.line_chart(full_df)
        
        st.info("ℹ️ This model uses Linear Regression on Sentinel-2 Spectral Data to forecast biomass accumulation.")

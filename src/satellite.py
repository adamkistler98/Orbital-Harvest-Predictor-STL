import sentinelhub
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS
import numpy as np
import pandas as pd
from datetime import date, timedelta
import os
import streamlit as st

# 1. AUTHENTICATION
def get_config():
    config = SHConfig()
    if "SH_CLIENT_ID" in st.secrets:
        config.sh_client_id = st.secrets["SH_CLIENT_ID"]
        config.sh_client_secret = st.secrets["SH_CLIENT_SECRET"]
    else:
        config.sh_client_id = os.environ.get("SH_CLIENT_ID")
        config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET")
    
    if not config.sh_client_id:
        raise ValueError("Missing Sentinel Hub Credentials!")
    return config

# 2. DATA FETCHING (Aggressive Mode)
def get_sentinel_data(bbox_coords, time_interval):
    config = get_config()
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
    evalscript = """
    //VERSION=3
    function setup() {
      return {
        input: ["B04", "B08"],
        output: { bands: 1, sampleType: "FLOAT32" }
      };
    }
    function evaluatePixel(sample) {
      let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
      return [ndvi];
    }
    """
    
    # We allow 100% clouds (maxcc=1.0) to ensure we get a response
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=1.0 
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF),
            SentinelHubRequest.output_response("userdata", MimeType.JSON)
        ],
        bbox=bbox,
        config=config,
    )

    response_list = request.get_data()
    
    # Check if empty
    if not response_list or len(response_list) < 2:
        return [], []
    
    image_data = response_list[0]
    metadata = response_list[1]
    
    clean_dates = []
    ndvi_scores = []
    
    for i, img in enumerate(image_data):
        if i < len(metadata):
            ts_str = metadata[i]['timestamp']
            ts_date = pd.to_datetime(ts_str).date()
            avg_ndvi = np.mean(img)
            
            # Smart Filter: NDVI must be > 0.05 to be "Real" (Not cloud/water)
            if not np.isnan(avg_ndvi) and avg_ndvi > 0.05:
                clean_dates.append(ts_date)
                ndvi_scores.append(avg_ndvi)
            
    return clean_dates, ndvi_scores

# 3. VISUAL FILMSTRIP (New Feature)
def get_filmstrip(bbox_coords, dates_list, limit=4):
    """
    Fetches 3-4 True Color images evenly spaced across the timeframe
    to show the user the "Real Data."
    """
    config = get_config()
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
    # Select indices evenly spaced (e.g., Start, Middle, End)
    if len(dates_list) < limit:
        selected_dates = dates_list
    else:
        indices = np.linspace(0, len(dates_list) - 1, limit, dtype=int)
        selected_dates = [dates_list[i] for i in indices]
    
    images = []
    
    evalscript = """
    //VERSION=3
    function setup() {
      return {
        input: ["B02", "B03", "B04"],
        output: { bands: 3, sampleType: "AUTO" }
      };
    }
    function evaluatePixel(sample) {
      return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
    }
    """
    
    for d in selected_dates:
        d_str = d.strftime("%Y-%m-%d")
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(d_str, d_str),
                    maxcc=1.0
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
            bbox=bbox,
            config=config,
        )
        data = request.get_data()
        if len(data) > 0:
            images.append((d, data[0]))
            
    return images

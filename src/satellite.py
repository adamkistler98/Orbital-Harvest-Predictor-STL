# src/satellite.py
import sentinelhub
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS
import numpy as np
import pandas as pd
from datetime import date
import os
import streamlit as st

# 1. AUTHENTICATION
def get_config():
    config = SHConfig()
    # Prioritize Streamlit Secrets (Cloud), fallback to Env Vars (Local)
    if "SH_CLIENT_ID" in st.secrets:
        config.sh_client_id = st.secrets["SH_CLIENT_ID"]
        config.sh_client_secret = st.secrets["SH_CLIENT_SECRET"]
    else:
        config.sh_client_id = os.environ.get("SH_CLIENT_ID")
        config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET")
    
    if not config.sh_client_id:
        raise ValueError("Missing Sentinel Hub Credentials! Check Streamlit Secrets.")
    return config

# 2. DATA FETCHING (THE FIX IS HERE)
def get_sentinel_data(bbox_coords, time_interval):
    """
    Fetches historical NDVI values AND their dates.
    """
    config = get_config()
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
    # Evalscript: Calculates NDVI (Plant Health)
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
    
    # THE FIX: We request TWO outputs:
    # 1. "default": The Image Data (TIFF)
    # 2. "userdata": The Metadata (JSON) -> This contains the DATES
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=0.2 # 20% Cloud Cover Limit
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF),
            SentinelHubRequest.output_response("userdata", MimeType.JSON) 
        ],
        bbox=bbox,
        config=config,
    )

    # get_data() now returns a list of lists: [ [Images...], [JsonMetadata...] ]
    response_list = request.get_data()
    
    # Unpack the response
    image_data = response_list[0]   # The pixels
    metadata = response_list[1]     # The dates
    
    clean_dates = []
    ndvi_scores = []
    
    for i, img in enumerate(image_data):
        # Extract the date from the JSON metadata
        # Format comes in as: "2023-10-25T14:00:00Z"
        ts_str = metadata[i]['timestamp']
        ts_date = pd.to_datetime(ts_str).date()
        
        avg_ndvi = np.mean(img)
        
        # Filter out bad data (negatives usually mean water or error)
        if not np.isnan(avg_ndvi) and avg_ndvi > -0.5:
            clean_dates.append(ts_date)
            ndvi_scores.append(avg_ndvi)
            
    return clean_dates, ndvi_scores

# 3. VISUAL CONFIRMATION (RGB IMAGE)
def get_visual_confirm(bbox_coords, date_obj):
    """
    Fetches a True Color (RGB) image for visual confirmation.
    """
    config = get_config()
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
    # Convert date object to string for the API
    date_str = date_obj.strftime("%Y-%m-%d")
    
    # True Color Script (Brightened 2.5x)
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
    
    # We expand the window slightly (start=date, end=date)
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(date_str, date_str), 
                maxcc=1.0 # Allow clouds for the visual proof (it's better than no image)
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        config=config,
    )
    
    data = request.get_data()
    
    if len(data) > 0:
        return data[0] # Return the first image found
    return None

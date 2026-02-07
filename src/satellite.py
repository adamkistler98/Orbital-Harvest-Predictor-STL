# src/satellite.py
import sentinelhub
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS
import numpy as np
import pandas as pd
from datetime import date
import os
import streamlit as st

def get_sentinel_data(bbox_coords, time_interval):
    """
    Fetches historical NDVI values for a specific location over a time range.
    Returns: A list of dates and a list of mean NDVI scores.
    """
    
    # 1. AUTHENTICATION
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

    # 2. DEFINE THE REQUEST
    # We use BBox (Bounding Box), not Box.
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

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=20.0 
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF)
        ],
        bbox=bbox,
        config=config,
    )

    # 3. EXECUTE & PARSE
    data = request.get_data()
    dates = request.get_dates()
    
    clean_dates = []
    ndvi_scores = []
    
    for i, img in enumerate(data):
        avg_ndvi = np.mean(img)
        if not np.isnan(avg_ndvi) and avg_ndvi > -1:
            clean_dates.append(dates[i])
            ndvi_scores.append(avg_ndvi)
            
    return clean_dates, ndvi_scores

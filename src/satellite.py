# src/satellite.py
import sentinelhub
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, Box, BBox, CRS
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
    # We try to get keys from Streamlit Secrets (Cloud) first, then Env Vars (Local)
    config = SHConfig()
    
    if "SH_CLIENT_ID" in st.secrets:
        config.sh_client_id = st.secrets["SH_CLIENT_ID"]
        config.sh_client_secret = st.secrets["SH_CLIENT_SECRET"]
    else:
        # Fallback for local testing if secrets.toml isn't set up
        config.sh_client_id = os.environ.get("SH_CLIENT_ID")
        config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET")

    if not config.sh_client_id:
        raise ValueError("Missing Sentinel Hub Credentials!")

    # 2. DEFINE THE REQUEST
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
    # Evalscript: Calculates NDVI *on the satellite server* to save bandwidth
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

    # We ask for all available images in the time window (max 10 for speed)
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=20.0 # Ignore cloudy days (>20% cloud cover)
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
    
    # Calculate the average NDVI for the whole farm for each date
    # (data is a list of images. We want one number per image.)
    clean_dates = []
    ndvi_scores = []
    
    for i, img in enumerate(data):
        avg_ndvi = np.mean(img)
        # Filter out "empty" or bad data chunks
        if not np.isnan(avg_ndvi) and avg_ndvi > -1:
            clean_dates.append(dates[i])
            ndvi_scores.append(avg_ndvi)
            
    return clean_dates, ndvi_scores

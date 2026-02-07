# src/satellite.py
import sentinelhub
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS
import numpy as np
import pandas as pd
from datetime import date
import os
import streamlit as st

# AUTHENTICATION
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
    
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=0.2 # FIXED: 0.2 = 20% Cloud Cover
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        config=config,
    )

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

def get_visual_confirm(bbox_coords, date_str):
    config = get_config()
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    
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
    
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(date_str, date_str), 
                maxcc=0.8 # FIXED: 0.8 = 80% Cloud Cover allowed for visual
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        config=config,
    )
    
    data = request.get_data()
    if len(data) > 0:
        return data[0]
    return None

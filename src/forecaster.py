# src/forecaster.py
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

def predict_health(dates, ndvi_values):
    """
    Returns: future_days, predictions, trend_slope, r2_score
    """
    df = pd.DataFrame({'date': dates, 'ndvi': ndvi_values})
    df['days_from_start'] = (df['date'] - df['date'].min()).dt.days
    
    X = df[['days_from_start']]
    y = df['ndvi']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 1. PREDICT FUTURE
    last_day = df['days_from_start'].max()
    future_days = np.array(range(last_day + 1, last_day + 15)).reshape(-1, 1)
    predictions = model.predict(future_days)
    
    # 2. CALCULATE CONFIDENCE (R-Squared)
    # How well does the line fit the dots?
    r2_score = model.score(X, y)
    
    # 3. CALCULATE TREND
    trend_slope = model.coef_[0]
    
    return future_days, predictions, trend_slope, r2_score

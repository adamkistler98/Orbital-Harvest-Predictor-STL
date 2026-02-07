import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

def predict_health(dates, ndvi_values):
    """
    Takes historical dates and NDVI scores, returns a prediction for the next 14 days.
    """
    # 1. Convert Dates to "Days from Start" (Integers) for the AI model
    df = pd.DataFrame({'date': dates, 'ndvi': ndvi_values})
    df['days_from_start'] = (df['date'] - df['date'].min()).dt.days
    
    # 2. Train the Model (Simple Linear Regression)
    # We are teaching the computer: "As time passes, how does health change?"
    X = df[['days_from_start']] # Features (Time)
    y = df['ndvi']              # Target (Health)
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 3. Predict the Future (Next 14 Days)
    last_day = df['days_from_start'].max()
    future_days = np.array(range(last_day + 1, last_day + 15)).reshape(-1, 1)
    
    predictions = model.predict(future_days)
    
    # Calculate the Trend (Slope)
    # Positive Slope = Improving Health. Negative Slope = Dying Crops.
    trend_slope = model.coef_[0]
    
    return future_days, predictions, trend_slope

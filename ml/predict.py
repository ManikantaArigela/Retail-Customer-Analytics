
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

SAVED_MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))

def forecast_future_sales(user_id: int, days: int = 30) -> list:
    """
    Generates a 30-day sales forecast using the trained model and autoregressive feature rolling.
    """
    user_model_dir = os.path.join(SAVED_MODELS_DIR, f"user_{user_id}")
    
    forecaster_path = os.path.join(user_model_dir, "forecaster.pkl")
    seed_path = os.path.join(user_model_dir, "forecast_seed.pkl")
    
    if not os.path.exists(forecaster_path) or not os.path.exists(seed_path):
        # Fallback if models are not trained yet
        np.random.seed(42)
        base_revenue = 5000.0
        start_date = datetime.now()
        dummy_forecast = []
        for i in range(days):
            date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            noise = np.random.normal(0, 500)
            trend = i * 20.0
            weekly_pattern = 1000 * np.sin(2 * np.pi * (i + start_date.weekday()) / 7)
            dummy_forecast.append({
                "date": date_str,
                "predicted": float(max(100.0, base_revenue + trend + weekly_pattern + noise))
            })
        return dummy_forecast

    forecaster = joblib.load(forecaster_path)
    seed = joblib.load(seed_path)
    
    # We reconstruct features day-by-day.
    predictions = []
    
    feature_cols = [
        'day_of_week', 'day_of_month', 'month', 'year',
        'sales_lag_1', 'sales_lag_2', 'sales_lag_7', 'sales_lag_14',
        'sales_roll_mean_7', 'sales_roll_std_7', 'sales_roll_mean_14', 'sales_roll_std_14'
    ]
    
    # History of actual/predicted values to compute lags and rolling stats
    # Initialize history with the seed lags
    history = [
        seed.get('sales_lag_14', 1000.0),
        seed.get('sales_lag_7', 1000.0),
        seed.get('sales_lag_2', 1000.0),
        seed.get('sales_lag_1', 1000.0),
        seed.get('total_sales', 1000.0) # last target
    ]
    
    start_date = datetime.now()
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Calculate lag features based on historical queue
        lag_1 = history[-1]
        lag_2 = history[-2]
        lag_7 = history[-7] if len(history) >= 7 else history[-1]
        lag_14 = history[-14] if len(history) >= 14 else history[-1]
        
        # Rolling averages
        roll_mean_7 = np.mean(history[-7:]) if len(history) >= 7 else np.mean(history)
        roll_mean_14 = np.mean(history[-14:]) if len(history) >= 14 else np.mean(history)
        roll_std_7 = np.std(history[-7:]) if len(history) >= 7 else np.std(history)
        roll_std_14 = np.std(history[-14:]) if len(history) >= 14 else np.std(history)
        
        # Form feature dictionary
        feat_dict = {
            'day_of_week': current_date.weekday(),
            'day_of_month': current_date.day,
            'month': current_date.month,
            'year': current_date.year,
            'sales_lag_1': lag_1,
            'sales_lag_2': lag_2,
            'sales_lag_7': lag_7,
            'sales_lag_14': lag_14,
            'sales_roll_mean_7': roll_mean_7,
            'sales_roll_mean_14': roll_mean_14,
            'sales_roll_std_7': roll_std_7,
            'sales_roll_std_14': roll_std_14
        }
        
        # Predict
        X_pred = pd.DataFrame([feat_dict])[feature_cols]
        pred_val = float(forecaster.predict(X_pred)[0])
        pred_val = max(0.0, pred_val)
        
        # Append to prediction results
        predictions.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "predicted": pred_val
        })
        
        # Update history
        history.append(pred_val)
        
    return predictions

def predict_customer_segments(df: pd.DataFrame, user_id: int) -> pd.DataFrame:
    """
    Predicts customer segments for customer records.
    Returns df with customer_id and predicted segment.
    """
    user_model_dir = os.path.join(SAVED_MODELS_DIR, f"user_{user_id}")
    
    kmeans_path = os.path.join(user_model_dir, "kmeans.pkl")
    scaler_path = os.path.join(user_model_dir, "scaler.pkl")
    mapping_path = os.path.join(user_model_dir, "segment_mapping.pkl")
    
    # Aggregate transaction data to RFM
    df['date'] = pd.to_datetime(df['date'])
    reference_date = df['date'].max()
    
    rfm = df.groupby('customer_id').agg({
        'date': lambda x: (reference_date - x.max()).days,
        'id': 'count',
        'total_sales': 'sum'
    }).reset_index()
    rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
    
    if not (os.path.exists(kmeans_path) and os.path.exists(scaler_path) and os.path.exists(mapping_path)):
        # Fallback clustering based on Monetary quantile rules
        rfm['segment'] = 'Standard'
        m_q75 = rfm['monetary'].quantile(0.75) if len(rfm) > 1 else 1000
        m_q25 = rfm['monetary'].quantile(0.25) if len(rfm) > 1 else 100
        
        rfm.loc[rfm['monetary'] >= m_q75, 'segment'] = 'Champions'
        rfm.loc[(rfm['monetary'] < m_q75) & (rfm['frequency'] > 5), 'segment'] = 'Loyal Customers'
        rfm.loc[(rfm['monetary'] < m_q25) & (rfm['recency'] > 60), 'segment'] = 'At Risk'
        return rfm[['customer_id', 'segment']]
        
    kmeans = joblib.load(kmeans_path)
    scaler = joblib.load(scaler_path)
    mapping = joblib.load(mapping_path)
    
    # Scale RFM
    scaled_feats = scaler.transform(rfm[['recency', 'frequency', 'monetary']])
    
    # Predict clusters
    rfm['cluster'] = kmeans.predict(scaled_feats)
    rfm['segment'] = rfm['cluster'].map(mapping).fillna('Standard')
    
    return rfm[['customer_id', 'segment']]

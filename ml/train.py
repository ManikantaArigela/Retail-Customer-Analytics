import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, r2_score
from ml.preprocessing import prepare_forecasting_data, prepare_rfm_data

SAVED_MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "saved_models"))
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

def train_and_save_models(df: pd.DataFrame, user_id: int) -> dict:
    """
    Trains and saves forecasting and customer segmentation models.
    """
    user_model_dir = os.path.join(SAVED_MODELS_DIR, f"user_{user_id}")
    os.makedirs(user_model_dir, exist_ok=True)
    
    results = {}
    
    # ---------------------------------------------
    # 1. Train Sales Forecasting Model
    # ---------------------------------------------
    try:
        df_feat, X, y = prepare_forecasting_data(df)
        
        # Split into train/test (last 7 days for test if enough data, else simple split)
        test_size = min(7, int(len(X) * 0.2))
        if test_size < 1:
            test_size = 1
            
        X_train, X_test = X[:-test_size], X[-test_size:]
        y_train, y_test = y[:-test_size], y[-test_size:]
        
        # Try importing XGBoost, otherwise fallback to RandomForest
        try:
            from xgboost import XGBRegressor
            forecaster = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
            forecaster.fit(X_train, y_train)
            model_type = "XGBoost"
        except ImportError:
            forecaster = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
            forecaster.fit(X_train, y_train)
            model_type = "RandomForest"
            
        # Evaluate model
        y_pred = forecaster.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else 1.0
        
        # Save forecasting models
        joblib.dump(forecaster, os.path.join(user_model_dir, "forecaster.pkl"))
        
        # Save last row of training data to use as seed for autoregressive forecasting
        seed_data = df_feat.iloc[-1].to_dict()
        joblib.dump(seed_data, os.path.join(user_model_dir, "forecast_seed.pkl"))
        
        results["forecast"] = {
            "status": "success",
            "model_type": model_type,
            "mae": float(mae),
            "r2": float(r2),
            "data_points": len(df_feat)
        }
    except Exception as e:
        results["forecast"] = {
            "status": "failed",
            "error": str(e)
        }
        
    # ---------------------------------------------
    # 2. Train Customer Segmentation Model (K-Means)
    # ---------------------------------------------
    try:
        rfm, scaled_features, scaler = prepare_rfm_data(df)
        
        # Ensure we have enough unique customers for clustering
        num_customers = len(rfm)
        n_clusters = min(4, num_customers) if num_customers > 1 else 1
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        kmeans.fit(scaled_features)
        
        # Save segmentation models
        joblib.dump(kmeans, os.path.join(user_model_dir, "kmeans.pkl"))
        joblib.dump(scaler, os.path.join(user_model_dir, "scaler.pkl"))
        
        # Assign segments to RFM dataframe
        rfm['cluster'] = kmeans.labels_
        
        # Assign descriptive segment names
        # Segment characteristics mapping:
        # Cluster 0, 1, 2, 3 - rename them by order of total sales
        cluster_means = rfm.groupby('cluster')['monetary'].mean().sort_values(ascending=False)
        segment_mapping = {}
        names = ["Champions", "Loyal Customers", "At Risk", "New/Promising"]
        
        for i, (cluster_idx, _) in enumerate(cluster_means.items()):
            segment_mapping[cluster_idx] = names[min(i, len(names) - 1)]
            
        rfm['segment'] = rfm['cluster'].map(segment_mapping)
        
        # Save Segment Mapping for reference
        joblib.dump(segment_mapping, os.path.join(user_model_dir, "segment_mapping.pkl"))
        
        results["segmentation"] = {
            "status": "success",
            "clusters": n_clusters,
            "segments_count": rfm['segment'].value_counts().to_dict(),
            "customer_count": num_customers
        }
    except Exception as e:
        results["segmentation"] = {
            "status": "failed",
            "error": str(e)
        }
        
    return results

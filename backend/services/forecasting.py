import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from ml.predict import forecast_future_sales, predict_customer_segments
from backend.services.analytics import get_user_dataframe

def generate_forecast_and_insights(user_id: int, db: Session) -> dict:
    """
    Retrieves ML 30-day forecast, runs RFM segmentation,
    and returns metrics and business recommendations.
    """
    df = get_user_dataframe(user_id, db)
    
    # 1. 30-Day Sales Forecast
    forecast = forecast_future_sales(user_id, days=30)
    
    # 2. Customer Segmentation
    customer_segments = {"Champions": 0, "Loyal Customers": 0, "At Risk": 0, "New/Promising": 0}
    if not df.empty:
        try:
            segments_df = predict_customer_segments(df, user_id)
            counts = segments_df["segment"].value_counts().to_dict()
            for seg, count in counts.items():
                if seg in customer_segments:
                    customer_segments[seg] = int(count)
                else:
                    customer_segments[seg] = customer_segments.get(seg, 0) + int(count)
        except Exception:
            pass
            
    # 3. Formulate Recommendations
    recommendations = []
    
    if not df.empty:
        # Check low inventory items
        low_stock = df[df["inventory_level"] < 50].groupby("product_name")["inventory_level"].last().reset_index()
        if not low_stock.empty:
            top_low = low_stock.sort_values("inventory_level").head(3)
            for _, r in top_low.iterrows():
                recommendations.append(
                    f"CRITICAL: Stock for '{r['product_name']}' is critically low ({int(r['inventory_level'])} units remaining). Reorder immediately."
                )
                
        # Compare forecast trend
        forecast_vals = [f["predicted"] for f in forecast]
        if len(forecast_vals) > 0:
            first_half = np.mean(forecast_vals[:15])
            second_half = np.mean(forecast_vals[15:])
            pct_change = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            
            if pct_change > 5:
                recommendations.append(
                    f"SALES INSIGHT: Sales are projected to increase by {pct_change:.1f}% over the next 15 days. Restock high-demand products."
                )
            elif pct_change < -5:
                recommendations.append(
                    f"MARKET WARNING: Projected sales show a decrease of {abs(pct_change):.1f}% in the second half of the month. Consider promotional bundling."
                )
                
        # Segment-specific recommendations
        total_custs = sum(customer_segments.values())
        if total_custs > 0:
            champions_pct = (customer_segments.get("Champions", 0) / total_custs) * 100
            at_risk_pct = (customer_segments.get("At Risk", 0) / total_custs) * 100
            
            if champions_pct > 15:
                recommendations.append(
                    f"MARKETING: High density of Champions ({champions_pct:.1f}%). Launch a premium VIP early-access campaign to maximize margins."
                )
            if at_risk_pct > 25:
                recommendations.append(
                    f"RETENTION ALERT: At-Risk customers represent {at_risk_pct:.1f}% of your base. Run a win-back discount campaign this weekend."
                )
                
    # Add general fallback recommendations if list is empty
    if not recommendations:
        recommendations = [
            "Monitor daily inventory levels to prevent stockouts of top-performing items.",
            "Run seasonal promotions during weekends to capture maximum local demand.",
            "Segment customer email newsletters based on their past purchase categories."
        ]
        
    return {
        "forecast": forecast,
        "customer_segments": customer_segments,
        "recommendations": recommendations
    }

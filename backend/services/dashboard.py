from sqlalchemy.orm import Session
from backend.services.analytics import (
    get_user_dataframe,
    compute_kpis,
    get_sales_trend,
    get_monthly_revenue,
    get_category_distribution,
    get_product_performance,
    get_regional_sales
)
from backend.services.forecasting import generate_forecast_and_insights

def get_dashboard_payload(user_id: int, db: Session) -> dict:
    """
    Assembles the complete data package required by the front-end dashboard.
    """
    df = get_user_dataframe(user_id, db)
    
    if df.empty:
        return {
            "kpis": {
                "total_revenue": 0.0,
                "total_sales": 0,
                "total_customers": 0,
                "total_products": 0,
                "total_profit": 0.0,
                "avg_inventory": 0.0,
                "sales_growth": 0.0,
                "profit_margin": 0.0
            },
            "sales_trend": [],
            "monthly_revenue": [],
            "category_distribution": [],
            "top_products": [],
            "worst_products": [],
            "regional_sales": [],
            "customer_segments": {
                "Champions": 0,
                "Loyal Customers": 0,
                "At Risk": 0,
                "New/Promising": 0
            }
        }
        
    # Get KPIs & Analytics
    kpis = compute_kpis(df)
    sales_trend = get_sales_trend(df)
    monthly_revenue = get_monthly_revenue(df)
    category_distribution = get_category_distribution(df)
    top_products = get_product_performance(df, ascending=False, limit=5)
    worst_products = get_product_performance(df, ascending=True, limit=5)
    regional_sales = get_regional_sales(df)
    
    # Get segments
    insights = generate_forecast_and_insights(user_id, db)
    customer_segments = insights["customer_segments"]
    
    return {
        "kpis": kpis,
        "sales_trend": sales_trend,
        "monthly_revenue": monthly_revenue,
        "category_distribution": category_distribution,
        "top_products": top_products,
        "worst_products": worst_products,
        "regional_sales": regional_sales,
        "customer_segments": customer_segments
    }

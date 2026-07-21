import pandas as pd
from sqlalchemy.orm import Session
from backend.models.database import SalesRecord, Dataset

def get_user_dataframe(user_id: int, db: Session) -> pd.DataFrame:
    """
    Fetches all transactions for a user from the database and loads them into a Pandas DataFrame.
    """
    records = db.query(SalesRecord).filter(SalesRecord.user_id == user_id).all()
    if not records:
        return pd.DataFrame()
        
    data = []
    for r in records:
        data.append({
            "id": r.id,
            "dataset_id": r.dataset_id,
            "date": r.date,
            "product_name": r.product_name,
            "category": r.category,
            "sub_category": r.sub_category,
            "quantity": r.quantity,
            "unit_price": r.unit_price,
            "total_sales": r.total_sales,
            "total_profit": r.total_profit,
            "customer_id": r.customer_id,
            "customer_segment": r.customer_segment,
            "region": r.region,
            "inventory_level": r.inventory_level
        })
        
    return pd.DataFrame(data)

def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Computes key performance indicators (KPIs) from sales records.
    """
    if df.empty:
        return {
            "total_revenue": 0.0,
            "total_sales": 0,
            "total_customers": 0,
            "total_products": 0,
            "total_profit": 0.0,
            "avg_inventory": 0.0,
            "sales_growth": 0.0,
            "profit_margin": 0.0
        }
        
    total_revenue = float(df["total_sales"].sum())
    total_sales = int(df["quantity"].sum())
    total_customers = int(df["customer_id"].nunique())
    total_products = int(df["product_name"].nunique())
    total_profit = float(df["total_profit"].sum())
    avg_inventory = float(df["inventory_level"].mean())
    
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
    
    # Calculate Sales Growth Month-over-Month
    growth_rate = 0.0
    try:
        periods = pd.to_datetime(df['date']).dt.to_period('M')
        monthly_sales = df.groupby(periods)['total_sales'].sum().sort_index()
        if len(monthly_sales) >= 2:
            prev_month = monthly_sales.iloc[-2]
            curr_month = monthly_sales.iloc[-1]
            if prev_month > 0:
                growth_rate = float(((curr_month - prev_month) / prev_month) * 100)
    except Exception:
        pass
        
    return {
        "total_revenue": round(total_revenue, 2),
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_products": total_products,
        "total_profit": round(total_profit, 2),
        "avg_inventory": round(avg_inventory, 2),
        "sales_growth": round(growth_rate, 2),
        "profit_margin": round(profit_margin, 2)
    }

def get_sales_trend(df: pd.DataFrame) -> list:
    """
    Computes cumulative sales trend grouped daily.
    """
    if df.empty:
        return []
    df['date_only'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    trend = df.groupby('date_only')['total_sales'].sum().reset_index()
    trend = trend.sort_values('date_only')
    return [{"label": r["date_only"], "value": float(r["total_sales"])} for _, r in trend.iterrows()]

def get_monthly_revenue(df: pd.DataFrame) -> list:
    """
    Computes monthly revenue.
    """
    if df.empty:
        return []
    df['month_name'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
    monthly = df.groupby('month_name')['total_sales'].sum().reset_index()
    monthly = monthly.sort_values('month_name')
    return [{"label": r["month_name"], "value": float(r["total_sales"])} for _, r in monthly.iterrows()]

def get_category_distribution(df: pd.DataFrame) -> list:
    """
    Computes total sales and percentage per product category.
    """
    if df.empty:
        return []
    total = df["total_sales"].sum()
    dist = df.groupby('category')['total_sales'].sum().reset_index()
    dist = dist.sort_values('total_sales', ascending=False)
    
    results = []
    for _, r in dist.iterrows():
        pct = (r["total_sales"] / total * 100) if total > 0 else 0.0
        results.append({
            "category": str(r["category"]),
            "sales": float(r["total_sales"]),
            "percentage": round(pct, 2)
        })
    return results

def get_product_performance(df: pd.DataFrame, ascending: bool = False, limit: int = 5) -> list:
    """
    Gets top or worst performing products.
    """
    if df.empty:
        return []
    perf = df.groupby('product_name').agg({
        'total_sales': 'sum',
        'quantity': 'sum',
        'total_profit': 'sum'
    }).reset_index()
    
    perf = perf.sort_values('total_sales', ascending=ascending).head(limit)
    
    results = []
    for _, r in perf.iterrows():
        results.append({
            "product_name": str(r["product_name"]),
            "sales": round(float(r["total_sales"]), 2),
            "quantity": int(r["quantity"]),
            "profit": round(float(r["total_profit"]), 2)
        })
    return results

def get_regional_sales(df: pd.DataFrame) -> list:
    """
    Computes total sales by geographical region.
    """
    if df.empty:
        return []
    regions = df.groupby('region')['total_sales'].sum().reset_index()
    regions = regions.sort_values('total_sales', ascending=False)
    return [{"label": str(r["region"]), "value": float(r["total_sales"])} for _, r in regions.iterrows()]

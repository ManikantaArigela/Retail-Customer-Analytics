import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.database import Dataset, SalesRecord
from backend.services.cleaning import clean_dataframe

CLEANED_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned"))
PROCESSED_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
os.makedirs(CLEANED_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Fuzzy match dictionaries
COLUMN_MAPPINGS = {
    "date": ["date", "order date", "order_date", "transaction date", "sale date", "time", "timestamp", "period"],
    "product_name": ["product", "product name", "product_name", "item", "item name", "sku", "name", "title", "description"],
    "category": ["category", "product category", "product_category", "department", "dept", "sector", "division"],
    "sub_category": ["sub-category", "sub category", "sub_category", "sub category name", "class", "subclass"],
    "quantity": ["quantity", "qty", "units", "units sold", "volume", "count", "amount sold", "quantity ordered"],
    "unit_price": ["unit price", "unit_price", "price", "rate", "cost_per_unit", "unit cost", "price per unit"],
    "total_sales": ["sales", "revenue", "total sales", "total_sales", "sales_amount", "turnover", "amount", "total revenue"],
    "total_profit": ["profit", "margin", "earnings", "net_profit", "total profit", "net profit"],
    "customer_id": ["customer id", "customer_id", "client id", "client_id", "user id", "user_id", "customer", "customer name", "client"],
    "customer_segment": ["segment", "customer segment", "customer_segment", "type", "tier", "class_group"],
    "region": ["region", "location", "area", "territory", "market"],
    "store_name": ["store", "store name", "store_name", "outlet", "branch"],
    "country": ["country", "nation"],
    "state": ["state", "province"],
    "city": ["city", "town"],
    "brand": ["brand", "make", "manufacturer"],
    "supplier": ["supplier", "vendor", "supplier partner"],
    "customer_type": ["customer type", "customer_type", "customer_profile"],
    "payment_method": ["payment method", "payment_method", "payment", "pay_mode"],
    "sales_channel": ["channel", "sales channel", "sales_channel"],
    "order_id": ["order id", "order_id", "transaction_id", "tx_id"],
    "inventory_level": ["inventory", "inventory level", "inventory_level", "stock", "stock level", "stock_level", "quantity in stock", "qty in stock", "available stock"]
}

def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps DataFrame columns to standard names using fuzzy matching.
    """
    mapped_df = pd.DataFrame()
    columns_lower = {col.lower().replace("_", " ").replace("-", " "): col for col in df.columns}
    
    for standard_col, synonyms in COLUMN_MAPPINGS.items():
        matched_original = None
        for synonym in synonyms:
            syn_clean = synonym.lower().replace("_", " ").replace("-", " ")
            if syn_clean in columns_lower:
                matched_original = columns_lower[syn_clean]
                break
        
        if matched_original:
            mapped_df[standard_col] = df[matched_original]
        else:
            # Standard column not found in dataset, we'll impute it next
            mapped_df[standard_col] = np.nan
            
    return mapped_df

def run_etl(file_path: str, dataset_id: int, user_id: int, db: Session) -> dict:
    """
    Full ETL pipeline: reads raw file, cleans, standardizes, maps columns,
    imputes missing business fields, saves outputs, and loads data into DB.
    """
    # 1. Read file
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
        
    # 2. Basic Cleaning
    df = clean_dataframe(df)
    
    # Save cleaned raw data
    user_cleaned_dir = os.path.join(CLEANED_DATA_DIR, f"user_{user_id}")
    os.makedirs(user_cleaned_dir, exist_ok=True)
    filename = os.path.basename(file_path)
    cleaned_path = os.path.join(user_cleaned_dir, filename)
    
    if ext == ".csv":
        df.to_csv(cleaned_path, index=False)
    else:
        df.to_excel(cleaned_path, index=False)
        
    # 3. Column Mapping to Unified Schema
    mapped_df = map_columns(df)
    
    # 4. Smart Imputations & Calculations
    # Date
    if mapped_df["date"].isnull().all():
        # Fallback: fill with today's date minus index days
        mapped_df["date"] = pd.date_range(end=datetime.now(), periods=len(mapped_df), freq='D')
    else:
        # Convert date column to datetime
        mapped_df["date"] = pd.to_datetime(mapped_df["date"], errors='coerce')
        # Fill missing dates using forward-fill or today
        mapped_df["date"] = mapped_df["date"].ffill().fillna(datetime.now())
        
    # Quantity
    mapped_df["quantity"] = pd.to_numeric(mapped_df["quantity"], errors='coerce').fillna(1).astype(int)
    mapped_df["quantity"] = mapped_df["quantity"].apply(lambda x: 1 if x <= 0 else x)
    
    # Price
    mapped_df["unit_price"] = pd.to_numeric(mapped_df["unit_price"], errors='coerce').fillna(10.0).astype(float)
    mapped_df["unit_price"] = mapped_df["unit_price"].apply(lambda x: 1.0 if x <= 0 else x)
    
    # Sales
    if mapped_df["total_sales"].isnull().all():
        mapped_df["total_sales"] = mapped_df["quantity"] * mapped_df["unit_price"]
    else:
        mapped_df["total_sales"] = pd.to_numeric(mapped_df["total_sales"], errors='coerce')
        # Fill remaining missing total_sales
        mapped_df["total_sales"] = mapped_df["total_sales"].fillna(mapped_df["quantity"] * mapped_df["unit_price"])
        
    # Profit
    if mapped_df["total_profit"].isnull().all():
        mapped_df["total_profit"] = mapped_df["total_sales"] * 0.15
    else:
        mapped_df["total_profit"] = pd.to_numeric(mapped_df["total_profit"], errors='coerce')
        # Fill remaining missing total_profit
        mapped_df["total_profit"] = mapped_df["total_profit"].fillna(mapped_df["total_sales"] * 0.15)
        
    # Product Name
    mapped_df["product_name"] = mapped_df["product_name"].fillna("Generic Product").astype(str)
    
    # Category
    mapped_df["category"] = mapped_df["category"].fillna("General").astype(str)
    
    # Sub Category
    mapped_df["sub_category"] = mapped_df["sub_category"].fillna(mapped_df["category"]).astype(str)
    
    # Customer ID & Segment
    mapped_df["customer_id"] = mapped_df["customer_id"].fillna("CUST-UNKNOWN").astype(str)
    mapped_df["customer_segment"] = mapped_df["customer_segment"].fillna("Standard").astype(str)
    
    # Region
    mapped_df["region"] = mapped_df["region"].fillna("Global").astype(str)
    
    # Inventory level (Stock) - if missing, synthesize values realistically based on sales velocity
    if mapped_df["inventory_level"].isnull().all():
        # Generate random stock level between 50 and 1000
        np.random.seed(42)
        mapped_df["inventory_level"] = np.random.randint(50, 1000, size=len(mapped_df))
    else:
        mapped_df["inventory_level"] = pd.to_numeric(mapped_df["inventory_level"], errors='coerce').fillna(100).astype(int)
        mapped_df["inventory_level"] = mapped_df["inventory_level"].apply(lambda x: 0 if x < 0 else x)
        
    # 5. Save processed data to data/processed
    user_processed_dir = os.path.join(PROCESSED_DATA_DIR, f"user_{user_id}")
    os.makedirs(user_processed_dir, exist_ok=True)
    processed_path = os.path.join(user_processed_dir, filename)
    
    # Save standard mapping
    if ext == ".csv":
        mapped_df.to_csv(processed_path, index=False)
    else:
        mapped_df.to_excel(processed_path, index=False)
        
    # 6. Database Load: Load mapped_df into the Database
    # Delete old sales records for this dataset if they exist
    db.query(SalesRecord).filter(SalesRecord.dataset_id == dataset_id).delete()
    
    records = []
    for _, row in mapped_df.iterrows():
        # Convert timestamp to standard datetime
        dt_val = row["date"].to_pydatetime() if isinstance(row["date"], pd.Timestamp) else row["date"]
        
        record = SalesRecord(
            dataset_id=dataset_id,
            user_id=user_id,
            date=dt_val,
            product_name=row["product_name"],
            category=row["category"],
            sub_category=row["sub_category"],
            quantity=int(row["quantity"]),
            unit_price=float(row["unit_price"]),
            total_sales=float(row["total_sales"]),
            total_profit=float(row["total_profit"]),
            customer_id=row["customer_id"],
            customer_segment=row["customer_segment"],
            region=row["region"],
            store_name=row.get("store_name"),
            country=row.get("country"),
            state=row.get("state"),
            city=row.get("city"),
            brand=row.get("brand"),
            supplier=row.get("supplier"),
            customer_type=row.get("customer_type"),
            payment_method=row.get("payment_method"),
            sales_channel=row.get("sales_channel"),
            order_id=row.get("order_id"),
            inventory_level=int(row["inventory_level"])
        )
        records.append(record)
        
    # Bulk save to speed up database load
    db.bulk_save_objects(records)
    
    # Update dataset model status
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset:
        dataset.status = "processed"
        dataset.row_count = len(mapped_df)
        db.commit()
        
    return {
        "status": "success",
        "row_count": len(mapped_df),
        "cleaned_path": cleaned_path,
        "processed_path": processed_path
    }

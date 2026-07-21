import os
import sys
import shutil

# Add the workspace root to python path so we can import backend packages
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(WORKSPACE_DIR)

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import Base, engine

client = TestClient(app)

def generate_mock_csv() -> bytes:
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    np.random.seed(42)
    num_rows = 50
    start_date = datetime.now() - timedelta(days=60)
    
    dates = [start_date + timedelta(days=int(i)) for i in range(num_rows)]
    products = ["Apples", "Milk 1G", "Sourdough", "Orange Juice", "Cheddar Cheese"]
    categories = ["Produce", "Dairy", "Bakery", "Beverages", "Dairy"]
    cust_ids = [f"CUST-{100 + np.random.randint(1, 10)}" for _ in range(num_rows)]
    regions = np.random.choice(["East", "West", "Midwest"], size=num_rows)
    segments = np.random.choice(["Champions", "Loyal Customers", "At Risk"], size=num_rows)
    
    records = []
    for i in range(num_rows):
        idx = np.random.randint(0, len(products))
        prod = products[idx]
        cat = categories[idx]
        price = round(float(np.random.uniform(2.0, 15.0)), 2)
        qty = int(np.random.randint(1, 5))
        sales = round(price * qty, 2)
        profit = round(sales * 0.2, 2)
        stock = int(np.random.randint(10, 200))
        
        records.append({
            "Order Date": dates[i].strftime("%Y-%m-%d"),
            "Product Name": prod,
            "Category": cat,
            "Sub-Category": f"{cat} Special",
            "Quantity": qty,
            "Unit Price": price,
            "Sales": sales,
            "Profit": profit,
            "Customer ID": cust_ids[i],
            "Customer Segment": segments[i],
            "Region": regions[i],
            "Stock Level": stock
        })
        
    df = pd.DataFrame(records)
    return df.to_csv(index=False).encode('utf-8')

def run_tests():
    print("==================================================")
    print("  AI RETAIL INTELLIGENCE PLATFORM - INTEGRATION TEST ")
    print("==================================================")
    
    # 1. Clean previous SQLite test tables (if any) and reinit
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[1/6] Database initialized cleanly.")
    
    # 2. Register a new user
    user_payload = {
        "username": "testmerchant",
        "email": "test@merchant.com",
        "password": "strongpassword123",
        "company_name": "Test Wholesale Ltd",
        "business_category": "grocery"
    }
    
    reg_response = client.post("/api/auth/register", json=user_payload)
    assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
    print("[2/6] User registration successful.")
    
    # 3. Log in to get token
    login_payload = {
        "username": "testmerchant",
        "password": "strongpassword123"
    }
    login_response = client.post("/api/auth/login", json=login_payload)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[3/6] User login & JWT retrieval successful.")
    
    # 4. Generate mock CSV and upload to run ETL / ML pipelines
    csv_bytes = generate_mock_csv()
    files = {"file": ("test_grocery_sales.csv", csv_bytes, "text/csv")}
    form_data = {"sector": "grocery"}
    
    print("[...] Uploading dataset and running ETL/ML pipeline. Please wait...")
    upload_response = client.post("/api/upload", headers=headers, files=files, data=form_data)
    assert upload_response.status_code == 200, f"ETL Pipeline failed: {upload_response.text}"
    upload_data = upload_response.json()
    print(f"[4/6] File upload, data cleaning, fuzzy schema ETL, and ML training succeeded. Rows loaded: {upload_data['row_count']}")
    
    # 5. Verify analytical and forecast APIs
    dash_response = client.get("/api/dashboard", headers=headers)
    assert dash_response.status_code == 200
    dash_data = dash_response.json()
    print(f"      - Dashboard KPIs -> Revenue: ${dash_data['kpis']['total_revenue']:,}, Active SKUs: {dash_data['kpis']['total_products']}")
    
    fc_response = client.get("/api/forecast", headers=headers)
    assert fc_response.status_code == 200
    fc_data = fc_response.json()
    print(f"      - ML Predictions -> Forecast points generated: {len(fc_data['forecast'])}")
    print(f"      - ML Insights    -> Automated Recommendations: {len(fc_data['recommendations'])}")
    print("[5/6] Analytics dashboards and ML forecasting API calls succeeded.")
    
    # 6. Verify Reports and AI Assistant Chat
    # Assistant Chat query
    chat_payload = {"message": "Show me our total revenue"}
    chat_response = client.post("/api/assistant/chat", headers=headers, json=chat_payload)
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    print(f"      - AI assistant   -> Reply: '{chat_data['reply']}'")
    print(f"      - AI assistant   -> SQL Query executed: '{chat_data['query_used']}'")
    
    # Reports downloads
    for fmt in ["csv", "excel", "pdf"]:
        rep_resp = client.get(f"/api/reports/download?format={fmt}", headers=headers)
        assert rep_resp.status_code == 200, f"{fmt.upper()} report download failed."
    print("[6/6] Reports downloads (CSV, Excel, PDF) & Assistant chat queries succeeded.")
    
    print("\n==================================================")
    print("  ALL TESTS PASSED: SYSTEM INTEGRITY 100% HEALTHY   ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

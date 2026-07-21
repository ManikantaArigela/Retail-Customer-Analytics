import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.database import SalesRecord, Dataset

def process_assistant_query(user_id: int, message: str, db: Session) -> dict:
    """
    Parses natural language queries, executes matching database queries,
    and returns a formatted text reply along with structured data.
    """
    msg = message.lower()
    
    # Verify dataset exists
    has_records = db.query(SalesRecord).filter(SalesRecord.user_id == user_id).first() is not None
    if not has_records:
        return {
            "reply": "It looks like you haven't uploaded a dataset yet. Please go to the Dashboard or Settings page to upload your retail data, and then I'll be happy to answer your business questions!",
            "query_used": "None",
            "data": []
        }
        
    # Helper to format currency
    def fmt_curr(val):
        return f"₹{val:,.2f}"
        
    # Helper to format count
    def fmt_num(val):
        return f"{val:,}"
        
    # Match query types
    
    # 1. Sales / Revenue / Earning
    if any(kwd in msg for kwd in ["sales", "revenue", "income", "earning", "turnover"]):
        # Check if looking for a specific category
        categories = db.query(SalesRecord.category).filter(SalesRecord.user_id == user_id).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        target_cat = None
        for cat in categories:
            if cat.lower() in msg:
                target_cat = cat
                break
                
        # Check if looking for a specific region
        regions = db.query(SalesRecord.region).filter(SalesRecord.user_id == user_id).distinct().all()
        regions = [r[0] for r in regions if r[0]]
        
        target_reg = None
        for reg in regions:
            if reg.lower() in msg:
                target_reg = reg
                break
                
        if target_cat:
            val = db.query(func.sum(SalesRecord.total_sales)).filter(
                SalesRecord.user_id == user_id, 
                func.lower(SalesRecord.category) == target_cat.lower()
            ).scalar() or 0.0
            
            return {
                "reply": f"The total sales revenue generated for the **{target_cat}** category is **{fmt_curr(val)}**.",
                "query_used": f"SELECT SUM(total_sales) FROM sales_records WHERE category = '{target_cat}'",
                "data": [{"category": target_cat, "total_sales": val}]
            }
            
        elif target_reg:
            val = db.query(func.sum(SalesRecord.total_sales)).filter(
                SalesRecord.user_id == user_id, 
                func.lower(SalesRecord.region) == target_reg.lower()
            ).scalar() or 0.0
            
            return {
                "reply": f"The total sales revenue generated in the **{target_reg}** region is **{fmt_curr(val)}**.",
                "query_used": f"SELECT SUM(total_sales) FROM sales_records WHERE region = '{target_reg}'",
                "data": [{"region": target_reg, "total_sales": val}]
            }
            
        else:
            val = db.query(func.sum(SalesRecord.total_sales)).filter(SalesRecord.user_id == user_id).scalar() or 0.0
            qty = db.query(func.sum(SalesRecord.quantity)).filter(SalesRecord.user_id == user_id).scalar() or 0
            
            return {
                "reply": f"Your platform total revenue is **{fmt_curr(val)}** across **{fmt_num(qty)}** total units sold.",
                "query_used": "SELECT SUM(total_sales), SUM(quantity) FROM sales_records",
                "data": [{"total_revenue": val, "units_sold": qty}]
            }
            
    # 2. Profit / Margin
    elif any(kwd in msg for kwd in ["profit", "margin", "earnings"]):
        total_rev = db.query(func.sum(SalesRecord.total_sales)).filter(SalesRecord.user_id == user_id).scalar() or 0.0
        total_prof = db.query(func.sum(SalesRecord.total_profit)).filter(SalesRecord.user_id == user_id).scalar() or 0.0
        margin = (total_prof / total_rev * 100) if total_rev > 0 else 0.0
        
        return {
            "reply": f"Your net profit is **{fmt_curr(total_prof)}** on a profit margin of **{margin:.2f}%**.",
            "query_used": "SELECT SUM(total_sales), SUM(total_profit) FROM sales_records",
            "data": [{"total_revenue": total_rev, "total_profit": total_prof, "profit_margin_percent": margin}]
        }
        
    # 3. Best / Top / Worst products
    elif any(kwd in msg for kwd in ["product", "item", "sku"]):
        is_worst = "worst" in msg or "low" in msg or "least" in msg
        order_direction = SalesRecord.total_sales.asc() if is_worst else SalesRecord.total_sales.desc()
        title = "Least-Performing Products" if is_worst else "Top-Performing Products"
        
        top_items = db.query(
            SalesRecord.product_name,
            func.sum(SalesRecord.total_sales).label("sales"),
            func.sum(SalesRecord.quantity).label("qty")
        ).filter(SalesRecord.user_id == user_id).group_by(
            SalesRecord.product_name
        ).order_by(
            func.sum(SalesRecord.total_sales).asc() if is_worst else func.sum(SalesRecord.total_sales).desc()
        ).limit(5).all()
        
        data_list = []
        reply = f"Here are the **{title.lower()}** based on sales volume:\n\n"
        for i, item in enumerate(top_items):
            reply += f"{i+1}. **{item[0]}** - Revenue: {fmt_curr(item[1])} ({fmt_num(item[2])} units)\n"
            data_list.append({"product": item[0], "revenue": item[1], "quantity": item[2]})
            
        return {
            "reply": reply,
            "query_used": f"SELECT product_name, SUM(total_sales) FROM sales_records GROUP BY product_name ORDER BY total_sales {'ASC' if is_worst else 'DESC'} LIMIT 5",
            "data": data_list
        }
        
    # 4. Customers / Segments
    elif any(kwd in msg for kwd in ["customer", "client", "segment", "buyer"]):
        cust_count = db.query(SalesRecord.customer_id).filter(SalesRecord.user_id == user_id).distinct().count()
        segments = db.query(
            SalesRecord.customer_segment,
            func.count(SalesRecord.customer_id.distinct()).label("count")
        ).filter(SalesRecord.user_id == user_id).group_by(SalesRecord.customer_segment).all()
        
        reply = f"You have **{fmt_num(cust_count)}** unique customer identifiers recorded. Here is their segmentation breakdown:\n\n"
        data_list = []
        for seg in segments:
            seg_name = seg[0] or "Standard"
            reply += f"- **{seg_name}**: {fmt_num(seg[1])} customers\n"
            data_list.append({"segment": seg_name, "count": seg[1]})
            
        return {
            "reply": reply,
            "query_used": "SELECT customer_segment, COUNT(DISTINCT customer_id) FROM sales_records GROUP BY customer_segment",
            "data": data_list
        }
        
    # 5. Inventory / Stock
    elif any(kwd in msg for kwd in ["inventory", "stock", "warehouse"]):
        avg_stock = db.query(func.avg(SalesRecord.inventory_level)).filter(SalesRecord.user_id == user_id).scalar() or 0.0
        low_stock_count = db.query(SalesRecord.product_name).filter(
            SalesRecord.user_id == user_id, 
            SalesRecord.inventory_level < 50
        ).distinct().count()
        
        reply = f"Your average inventory stock level is **{int(avg_stock)}** units. "
        if low_stock_count > 0:
            reply += f"⚠️ **Attention**: There are **{low_stock_count}** products with critically low stock (under 50 units)."
        else:
            reply += "Inventory status is stable with no low stock warnings."
            
        # Get low stock list
        low_stock_items = db.query(
            SalesRecord.product_name,
            SalesRecord.inventory_level
        ).filter(
            SalesRecord.user_id == user_id, 
            SalesRecord.inventory_level < 50
        ).limit(5).all()
        
        data_list = [{"average_stock": avg_stock, "low_stock_count": low_stock_count}]
        for item in low_stock_items:
            data_list.append({"product": item[0], "stock_level": item[1]})
            
        return {
            "reply": reply,
            "query_used": "SELECT AVG(inventory_level) FROM sales_records; SELECT product_name, inventory_level FROM sales_records WHERE inventory_level < 50 LIMIT 5",
            "data": data_list
        }
        
    # 6. Categories
    elif any(kwd in msg for kwd in ["category", "categories", "department", "sector"]):
        cats = db.query(
            SalesRecord.category,
            func.sum(SalesRecord.total_sales).label("sales")
        ).filter(SalesRecord.user_id == user_id).group_by(SalesRecord.category).all()
        
        reply = "Here is the sales performance across your product categories:\n\n"
        data_list = []
        for c in cats:
            reply += f"- **{c[0]}**: Total Sales: {fmt_curr(c[1])}\n"
            data_list.append({"category": c[0], "sales": c[1]})
            
        return {
            "reply": reply,
            "query_used": "SELECT category, SUM(total_sales) FROM sales_records GROUP BY category",
            "data": data_list
        }
        
    # 7. Regions / Locations
    elif any(kwd in msg for kwd in ["region", "regions", "location", "city", "country"]):
        regs = db.query(
            SalesRecord.region,
            func.sum(SalesRecord.total_sales).label("sales")
        ).filter(SalesRecord.user_id == user_id).group_by(SalesRecord.region).all()
        
        reply = "Here is your regional sales breakdown:\n\n"
        data_list = []
        for r in regs:
            reply += f"- **{r[0]}**: {fmt_curr(r[1])}\n"
            data_list.append({"region": r[0], "sales": r[1]})
            
        return {
            "reply": reply,
            "query_used": "SELECT region, SUM(total_sales) FROM sales_records GROUP BY region",
            "data": data_list
        }
        
    # 8. Forecast / Future
    elif any(kwd in msg for kwd in ["forecast", "predict", "future", "ml"]):
        return {
            "reply": "To see detailed sales forecasts and customer segment recommendations, please head to the **AI Assistant** dashboard tab or check the ML charts in the **Analytics** page. I predict future sales using historical autoregressive trends and K-Means segmentation.",
            "query_used": "ML Model Predict API",
            "data": []
        }
        
    # Fallback Default Response
    return {
        "reply": "I can help you analyze your retail metrics! Try asking questions like:\n\n"
                 "- *What is our total revenue?*\n"
                 "- *How much profit did we make?*\n"
                 "- *What are our best selling products?*\n"
                 "- *Which categories perform the best?*\n"
                 "- *Are there any low stock inventory warnings?*\n"
                 "- *Show me a breakdown of our customer segments.*",
        "query_used": "None",
        "data": []
    }

def generate_sample_csv(sector: str) -> str:
    """
    Generates a realistic sample CSV dataset based on the selected retail sector.
    Returns the string CSV data.
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    # Define sector-specific profiles
    sector_data = {
        "healthcare": {
            "categories": {
                "Prescription": ["Amoxicillin", "Atorvastatin", "Metformin", "Lisinopril"],
                "OTC Medicine": ["Ibuprofen", "Acetaminophen", "Cough Syrup", "Allergy Relief"],
                "Supplements": ["Vitamin C", "Multivitamin", "Fish Oil", "Calcium"],
                "Personal Care": ["Antiseptic Soap", "Moisturizer", "Toothpaste", "Band-Aid"]
            },
            "price_range": (3.50, 85.00)
        },
        "grocery": {
            "categories": {
                "Produce": ["Organic Bananas", "Avocados", "Cherry Tomatoes", "Apples"],
                "Dairy & Eggs": ["Whole Milk 1G", "Greek Yogurt", "Cheddar Cheese", "Free Range Eggs"],
                "Bakery": ["Sourdough Bread", "Croissants", "Chocolate Chip Cookies", "Bagels"],
                "Beverages": ["Orange Juice", "Sparkling Water", "Ground Coffee", "Green Tea"]
            },
            "price_range": (1.50, 18.00)
        },
        "pharmacy": {
            "categories": {
                "Prescriptions": ["Lipitor", "Synthroid", "Gabapentin", "Albuterol inhaler"],
                "First Aid": ["Medical Tape", "Bandages", "Alcohol Wipes", "Ice Pack"],
                "OTC Drugs": ["Antacid", "Aspirin", "Nasal Spray", "Eye Drops"]
            },
            "price_range": (4.00, 120.00)
        },
        "fashion": {
            "categories": {
                "Apparel": ["Slim Fit Jeans", "Crewneck Sweater", "Graphic T-Shirt", "Chino Pants"],
                "Footwear": ["Leather Boots", "Running Sneakers", "Casual Loafers", "Sandals"],
                "Accessories": ["Leather Belt", "Sunglasses", "Wool Scarf", "Canvas Backpack"],
                "Outerwear": ["Denim Jacket", "Winter Parka", "Windbreaker", "Trench Coat"]
            },
            "price_range": (15.00, 250.00)
        },
        "electronics": {
            "categories": {
                "Computers": ["Ultra-thin Laptop", "Desktop PC", "27-inch Monitor", "Wireless Keyboard"],
                "Mobile Devices": ["Flagship Smartphone", "10-inch Tablet", "Smart Watch", "Power Bank"],
                "Audio": ["Noise Cancelling Headphones", "Bluetooth Speaker", "Wireless Earbuds"],
                "Accessories": ["USB-C Hub", "HDMI Cable", "Laptop Sleeve", "Phone Case"]
            },
            "price_range": (9.99, 1200.00)
        },
        "furniture": {
            "categories": {
                "Living Room": ["3-Seater Sofa", "Coffee Table", "Armchair", "TV Stand"],
                "Bedroom": ["Queen Bed Frame", "Memory Foam Mattress", "Nightstand", "Chest of Drawers"],
                "Office": ["Ergonomic Desk Chair", "Writing Desk", "Bookshelf", "File Cabinet"]
            },
            "price_range": (49.99, 850.00)
        },
        "beauty": {
            "categories": {
                "Skincare": ["Facial Cleanser", "Vitamin C Serum", "Hydrating Cream", "Sunscreen SPF 50"],
                "Makeup": ["Matte Lipstick", "Liquid Foundation", "Mascara", "Eyeshadow Palette"],
                "Haircare": ["Argan Oil Shampoo", "Conditioner", "Hair Serum", "Styling Clay"]
            },
            "price_range": (8.00, 95.00)
        },
        "automotive": {
            "categories": {
                "Maintenance": ["Synthetic Engine Oil", "Oil Filter", "Engine Air Filter", "Coolant"],
                "Accessories": ["All-Weather Floor Mats", "Steering Wheel Cover", "Car Cover", "Phone Mount"],
                "Tools": ["Socket Wrench Set", "Tire Inflator", "Jumper Cables", "Car Jack"]
            },
            "price_range": (5.00, 150.00)
        },
        "fmcg": {
            "categories": {
                "Household": ["Laundry Detergent", "Dish Soap", "Paper Towels", "Trash Bags"],
                "Packaged Foods": ["Cereal Box", "Pasta Noodles", "Olive Oil", "Canned Tuna"],
                "Personal Care": ["Body Wash", "Deodorant", "Shampoo", "Hand Sanitizer"]
            },
            "price_range": (2.00, 25.00)
        },
        "home_living": {
            "categories": {
                "Bedding": ["Sheet Set", "Duvet Cover", "Bed Pillows", "Blanket"],
                "Kitchen": ["Non-stick Skillet", "Knife Set", "Coffee Mug", "Storage Containers"],
                "Decor": ["Wall Clock", "Scented Candle", "Area Rug", "Throw Pillows"]
            },
            "price_range": (5.00, 180.00)
        }
    }
    
    # Get profile (or default to grocery)
    profile = sector_data.get(sector.lower().replace(" ", "_"), sector_data["grocery"])
    categories = profile["categories"]
    min_p, max_p = profile["price_range"]
    
    # Generate random seed
    np.random.seed(42)
    
    # Generate 300 records
    num_rows = 300
    start_date = datetime.now() - timedelta(days=365)
    
    dates = [start_date + timedelta(days=int(i * 1.2)) for i in range(num_rows)]
    cust_ids = [f"CUST-{1000 + np.random.randint(1, 101)}" for _ in range(num_rows)]
    regions = np.random.choice(["East Coast", "West Coast", "Midwest", "South", "Mountain"], size=num_rows)
    segments = np.random.choice(["Champions", "Loyal Customers", "At Risk", "New/Promising"], p=[0.15, 0.35, 0.20, 0.30], size=num_rows)
    
    records = []
    for i in range(num_rows):
        cat = np.random.choice(list(categories.keys()))
        prod = np.random.choice(categories[cat])
        
        # Quantity follows retail pattern: higher price = lower quantity
        price = round(np.random.uniform(min_p, max_p), 2)
        if price > 200:
            qty = int(np.random.choice([1, 2], p=[0.8, 0.2]))
        elif price > 50:
            qty = int(np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
        else:
            qty = int(np.random.randint(1, 6))
            
        sales = round(price * qty, 2)
        profit = round(sales * np.random.uniform(0.1, 0.3), 2) # 10% to 30% margin
        stock = int(np.random.randint(10, 800))
        
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
        
    df_sample = pd.DataFrame(records)
    return df_sample.to_csv(index=False)


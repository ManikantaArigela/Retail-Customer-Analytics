<<<<<<< HEAD
# AI Retail Intelligence Platform

An enterprise-ready, multi-tenant Business Intelligence (BI) and predictive analytics platform built from scratch. It allows retailers to upload raw transaction data (CSV or Excel) and automatically clean, model, forecast sales, segment customers, and query their database using a natural language AI Copilot.

Serve both the UI and FastAPI backend from a single Python process.

---

## 🌟 Key Features

1. **Automated Data Processing (ETL)**
   - Smart schema mapper aligning column headers from multiple industries (Grocery, Fashion, Pharmacy, etc.) to a unified database model.
   - Intelligent imputation of missing prices/quantities and auto-capping of stock levels and outlier sales.
   - Deduplication and outlier clipping using the Interquartile Range (IQR) method.

2. **Executive KPI Dashboard (Power BI / Tableau Style)**
   - Minimalist corporate design featuring blue & white palette, rounded card widgets, micro-animations, and full responsiveness.
   - KPIs: Total Revenue, Units Sold, Unique Customers, Active SKUs, Net Profit Margin, and Sales Growth.
   - Visualizations: Interactive line charts for daily sales trends, pie charts for category share distributions.

3. **Advanced Machine Learning**
   - **Sales Forecasting**: Uses autoregressive time-series features (lags, rolling standard deviation) trained on a Gradient Boosted (XGBoost) or Random Forest Regressor to forecast daily sales for the next 30 days.
   - **Customer Segmentation**: Clusters profiles using Recency, Frequency, and Monetary (RFM) metrics into distinct K-Means segments (Champions, Loyal, At-Risk, New).
   - **Strategic Recommendations**: Generates low-stock notifications and marketing campaign alerts based on ML patterns.

4. **Natural Language AI Assistant**
   - An interactive chat copilot that parses English questions (e.g., *"What is our revenue for Produce?"*, *"Show low stock warnings"*, *"List customer segments"*), translates them to structured SQL queries on the SQLite database, and returns conversational replies alongside structured HTML data tables.

5. **Reporting & Downloads**
   - Professional **PDF reports** featuring styled KPI cards and top products tables.
   - Multi-sheet **Excel workbooks** containing Executive Summaries, processed transaction archives, and future forecasts.
   - Clean standardized **CSV database dumps**.

---

## 🛠️ Technology Stack

- **Frontend**: Vanilla HTML5, CSS3 (Modern Glassmorphism & Animations), ES6 JavaScript, Chart.js, Font Awesome.
- **Backend**: FastAPI, Uvicorn, Python 3.10+.
- **Database**: SQLite3, SQLAlchemy ORM.
- **Data Engineering**: Pandas, NumPy, OpenPyXL.
- **Machine Learning**: Scikit-Learn, XGBoost, Joblib.
- **Reports**: ReportLab (PDF), OpenPyXL (Excel), Matplotlib.

---

## 📂 Project Structure

```text
retail-intelligence-platform/
├── backend/
│   ├── api/
│   │   ├── routes.py          # REST endpoints & file download controls
│   │   └── auth.py            # JWT token security & hashing
│   ├── services/
│   │   ├── upload.py          # Raw file limits & file storage
│   │   ├── etl.py             # Schema fuzzy-mapper & database loader
│   │   ├── cleaning.py        # Deduplication, outlier capping & null values
│   │   ├── analytics.py       # SQL/Pandas KPI aggregation calculations
│   │   ├── forecasting.py     # ML models predictor & recommendation builder
│   │   └── reports.py         # PDF and Multi-Sheet Excel generators
│   ├── models/
│   │   ├── database.py        # SQLite SQLAlchemy ORM Tables (User, Dataset, SalesRecord)
│   │   └── schemas.py         # Pydantic schemas validation
│   ├── utils/
│   │   └── helpers.py         # AI Assistant parsing & dynamic CSV generator
│   └── main.py                # App initializer, CORS, and UI static mounting
├── data/
│   ├── raw/                   # User uploaded files
│   ├── cleaned/               # Pre-processed clean files
│   ├── processed/             # Schema-mapped files
│   └── exports/               # Generated PDF/Excel reports
├── ml/
│   ├── preprocessing.py       # Forecasting feature extraction & RFM scaling
│   ├── train.py               # XGBoost & K-Means training pipelines
│   ├── predict.py             # Autoregressive forecaster & segment classifiers
│   └── saved_models/          # joblib serialized models (.pkl)
├── database/
│   └── retail.db              # Local SQLite database
├── frontend/
│   ├── assets/
│   │   ├── css/               # Core design tokens & dashboard responsiveness
│   │   ├── js/                # API client, upload handlers, and page initializers
│   │   └── images/
│   ├── pages/                 # SPA view html templates
│   └── index.html             # Shell viewport
├── requirements.txt           # Python library dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Installation
Clone the project, navigate to the folder, and install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launching the Server
Start the Uvicorn application:
```bash
uvicorn backend.main:app --reload
```
Once running, the entire application serves from: **`http://127.0.0.1:8000`**

### 3. Step-by-Step Evaluation Walkthrough
1. Open `http://127.0.0.1:8000` in your web browser.
2. Click **Sign Up** on the login page to create a merchant profile, and then log in.
3. You will be redirected to the **Settings** tab.
4. Select a retail sector (e.g. *Fashion*, *Grocery*, or *Electronics*) in the **Evaluation Sandbox** and click **Generate Sample CSV**. This downloads a custom mock dataset containing 300 realistic retail transactions.
5. Go to the **Dashboard** tab, select the matching sector in the dropdown, drag-and-drop the downloaded CSV file, and click **Process & Train AI**.
6. The system will automatically process the file.
7. You can now explore the **Dashboard** metrics, view time-series forecasts in the **Analytics** page, chat with the **AI Assistant**, and download formatted **PDF/Excel reports**.
=======
# Retail-Customer-Analytics
>>>>>>> 1d234c613627f3051acec21a4331d27d14b22189

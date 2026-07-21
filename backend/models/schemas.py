from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    company_name: Optional[str] = None
    business_category: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    company_name: Optional[str]
    business_category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenSchema(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    filename: str
    sector: str
    status: str
    row_count: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class KPIResponse(BaseModel):
    total_revenue: float
    total_sales: int
    total_customers: int
    total_products: int
    total_profit: float
    avg_inventory: float
    sales_growth: float
    profit_margin: float

class ChartDataPoint(BaseModel):
    label: str
    value: float

class CategoryDistribution(BaseModel):
    category: str
    sales: float
    percentage: float

class ProductPerformance(BaseModel):
    product_name: str
    sales: float
    quantity: int
    profit: float

class DashboardData(BaseModel):
    kpis: KPIResponse
    sales_trend: List[ChartDataPoint]
    monthly_revenue: List[ChartDataPoint]
    category_distribution: List[CategoryDistribution]
    top_products: List[ProductPerformance]
    worst_products: List[ProductPerformance]
    regional_sales: List[ChartDataPoint]
    customer_segments: Dict[str, int]

class ForecastDataPoint(BaseModel):
    date: str
    actual: Optional[float] = None
    predicted: float

class ForecastResponse(BaseModel):
    forecast: List[ForecastDataPoint]
    metrics: Dict[str, Any]
    recommendations: List[str]

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    query_used: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None

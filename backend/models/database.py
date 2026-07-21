import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'retail.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    business_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    sales_records = relationship("SalesRecord", back_populates="user", cascade="all, delete-orphan")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    status = Column(String, default="uploaded")  # uploaded, cleaned, processed, failed
    row_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="datasets")
    sales_records = relationship("SalesRecord", back_populates="dataset", cascade="all, delete-orphan")

class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    sub_category = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_sales = Column(Float, nullable=False)
    total_profit = Column(Float, nullable=False)
    customer_id = Column(String, nullable=True)
    customer_segment = Column(String, nullable=True)
    region = Column(String, nullable=True)
    store_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    supplier = Column(String, nullable=True)
    customer_type = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    sales_channel = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    inventory_level = Column(Integer, nullable=True)

    user = relationship("User", back_populates="sales_records")
    dataset = relationship("Dataset", back_populates="sales_records")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

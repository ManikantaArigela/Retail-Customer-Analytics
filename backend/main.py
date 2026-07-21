import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.models.database import init_db
from backend.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database (creates tables in database/retail.db if not exists)
    init_db()
    yield

app = FastAPI(
    title="Retail Customer Analytics",
    description="Production-quality AI Business Intelligence tool for retail customer data analytics.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(router, prefix="/api")

# Serve frontend static assets
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")

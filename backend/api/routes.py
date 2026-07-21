import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from backend.models.database import get_db, User, Dataset, SalesRecord
from backend.models.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenSchema, 
    DashboardData, ForecastResponse, ChatRequest, ChatResponse
)
from backend.api.auth import (
    get_password_hash, verify_password, create_access_token, get_current_user
)
from backend.services.upload import save_uploaded_file
from backend.services.etl import run_etl
from ml.train import train_and_save_models
from backend.services.dashboard import get_dashboard_payload
from backend.services.forecasting import generate_forecast_and_insights
from backend.utils.helpers import process_assistant_query, generate_sample_csv
from backend.services.reports import (
    generate_csv_report, generate_excel_report, generate_pdf_report
)

router = APIRouter()

# ---------------------------------------------
# 1. Authentication Routes
# ---------------------------------------------
@router.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
        
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw,
        company_name=user_data.company_name,
        business_category=user_data.business_category
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/auth/login", response_model=TokenSchema)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
        
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------
# 2. File Upload & Dataset Administration Routes
# ---------------------------------------------
@router.post("/upload")
def upload_dataset(
    sector: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save the file raw
    file_path = save_uploaded_file(file, current_user.id)
    
    # Save Dataset record
    dataset_rec = Dataset(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        sector=sector,
        status="uploaded"
    )
    db.add(dataset_rec)
    db.commit()
    db.refresh(dataset_rec)
    
    try:
        # Run ETL & Load database
        etl_result = run_etl(file_path, dataset_rec.id, current_user.id, db)
        
        # Load user transactions for ML training
        df = get_dashboard_payload(current_user.id, db) # triggers load
        from backend.services.analytics import get_user_dataframe
        df_data = get_user_dataframe(current_user.id, db)
        
        # Train forecasting and segmentation models
        train_and_save_models(df_data, current_user.id)
        
        return {
            "status": "success",
            "message": "Dataset uploaded, cleaned, processed, and ML models trained successfully.",
            "dataset_id": dataset_rec.id,
            "row_count": etl_result["row_count"]
        }
        
    except Exception as e:
        dataset_rec.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing dataset: {str(e)}"
        )

@router.get("/datasets")
def list_datasets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    datasets = db.query(Dataset).filter(Dataset.user_id == current_user.id).order_by(Dataset.uploaded_at.desc()).all()
    return datasets


# ---------------------------------------------
# 3. Analytics & Dashboard Data Routes
# ---------------------------------------------
@router.get("/dashboard", response_model=DashboardData)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_dashboard_payload(current_user.id, db)

@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    insights = generate_forecast_and_insights(current_user.id, db)
    # Return metrics along with forecast data
    return {
        "forecast": insights["forecast"],
        "metrics": {"model": "Autoregressive Time Series"},
        "recommendations": insights["recommendations"]
    }



# ---------------------------------------------
# 5. Report Exports Routes
# ---------------------------------------------
@router.get("/reports/download")
def download_report(
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fmt = format.lower()
    
    try:
        if fmt == "csv":
            path = generate_csv_report(current_user.id, db)
            media_type = "text/csv"
            filename = "retail_data_export.csv"
        elif fmt == "excel":
            path = generate_excel_report(current_user.id, db)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "retail_intelligence_report.xlsx"
        elif fmt == "pdf":
            path = generate_pdf_report(current_user.id, db)
            media_type = "application/pdf"
            filename = "retail_intelligence_report.pdf"
        else:
            raise HTTPException(status_code=400, detail="Invalid report format. Choose csv, excel, or pdf.")
            
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail="Generated report file not found on disk.")
            
        return FileResponse(
            path=path,
            media_type=media_type,
            filename=filename
        )
    except ValueError as ve:
         raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# ---------------------------------------------
# 6. Settings, Profile Updates, Sample Generator
# ---------------------------------------------
@router.put("/settings/profile", response_model=UserResponse)
def update_profile(
    company_name: str = Form(None),
    business_category: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if company_name:
        current_user.company_name = company_name
    if business_category:
        current_user.business_category = business_category
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/settings/reset")
def reset_account_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Deletes all datasets, sales records, and saved models of the user
    db.query(SalesRecord).filter(SalesRecord.user_id == current_user.id).delete()
    db.query(Dataset).filter(Dataset.user_id == current_user.id).delete()
    db.commit()
    
    # Wipe saved models from filesystem
    import shutil
    from ml.train import SAVED_MODELS_DIR
    user_model_dir = os.path.join(SAVED_MODELS_DIR, f"user_{current_user.id}")
    if os.path.exists(user_model_dir):
        shutil.rmtree(user_model_dir)
        
    return {"status": "success", "message": "Account data and models reset successfully."}

@router.get("/settings/sample")
def download_sample_data(sector: str = "grocery"):
    csv_data = generate_sample_csv(sector)
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=retail_{sector.lower()}_sample_dataset.csv"
        }
    )

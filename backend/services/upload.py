import os
import shutil
from fastapi import UploadFile, HTTPException

RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
os.makedirs(RAW_DATA_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE_MB = 20

def save_uploaded_file(file: UploadFile, user_id: int) -> str:
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Only CSV and Excel files are allowed."
        )
        
    # Create user-specific folder structure if needed
    user_raw_dir = os.path.join(RAW_DATA_DIR, f"user_{user_id}")
    os.makedirs(user_raw_dir, exist_ok=True)
    
    file_path = os.path.join(user_raw_dir, filename)
    
    # Write file content while checking size
    size = 0
    try:
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):  # 1MB chunks
                size += len(chunk)
                if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB."
                    )
                buffer.write(chunk)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    return file_path
